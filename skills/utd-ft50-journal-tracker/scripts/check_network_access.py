#!/usr/bin/env python
"""Check whether Python sees proxy env vars and inspect one publisher/DOI request."""

from __future__ import annotations

import argparse
import os
from urllib.parse import quote

import requests

PROXY_ENV_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")
HTML_LOGIN_PATTERNS = (
    "login",
    "sign in",
    "institutional login",
    "shibboleth",
    "saml",
    "captcha",
    "access denied",
    "forbidden",
    "unauthorized",
    "权限",
    "登录",
    "验证码",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Python network/proxy access for one DOI or URL.")
    parser.add_argument("--url", help="Article, DOI, or publisher PDF URL to test.")
    parser.add_argument("--doi", help="DOI to test when --url is not supplied.")
    parser.add_argument("--access-mode", choices=["campus_ip", "env"], default="campus_ip")
    return parser.parse_args()


def target_url(args: argparse.Namespace) -> str:
    if args.url:
        return args.url
    if args.doi:
        return f"https://doi.org/{quote(args.doi.strip())}"
    return "https://doi.org/10.1287/isre.2023.0561"


def make_session(access_mode: str) -> requests.Session:
    session = requests.Session()
    if access_mode == "campus_ip":
        session.trust_env = False
        session.proxies = {}
    session.headers.update({"User-Agent": "utd-ft-journal-tracker/0.1 network check"})
    return session


def is_pdf(content_type: str, body: bytes) -> bool:
    return "pdf" in content_type.lower() or body.startswith(b"%PDF")


def suspected_login(content_type: str, body: bytes, encoding: str | None) -> bool:
    text = body[:8192].decode(encoding or "utf-8", errors="ignore").lower()
    return "html" in content_type.lower() and any(pattern in text for pattern in HTML_LOGIN_PATTERNS)


def main() -> int:
    args = parse_args()
    url = target_url(args)
    print("Proxy environment variables:")
    for key in PROXY_ENV_KEYS:
        print(f"- {key}: {os.environ.get(key, '') or '<not set>'}")

    session = make_session(args.access_mode)
    print("")
    print(f"access_mode: {args.access_mode}")
    print(f"requests.Session.trust_env: {session.trust_env}")
    print(f"session.proxies: {session.proxies or '{}'}")
    print(f"target_url: {url}")

    try:
        response = session.get(url, timeout=60, allow_redirects=True, stream=True)
        with response:
            sample = next(response.iter_content(chunk_size=8192), b"")
            content_type = response.headers.get("content-type", "")
            print(f"final_url: {response.url}")
            print(f"http_status: {response.status_code}")
            print(f"content_type: {content_type or '<missing>'}")
            print(f"is_pdf: {is_pdf(content_type, sample)}")
            print(f"suspected_login_or_captcha_page: {suspected_login(content_type, sample, response.encoding)}")
            if response.history:
                print("redirect_chain:")
                for item in response.history:
                    print(f"- {item.status_code} {item.url}")
    except requests.RequestException as exc:
        print(f"request_error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
