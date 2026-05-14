# Privacy and Release Checklist

Use this checklist before publishing or pushing the repository.

## Exclude

- `outputs/`
- `task/`, `task_*/`
- private style-example folders
- downloaded WeChat article folders
- PDF, DOCX, CAJ, RTF, and raw HTML source files from third parties
- QR code images for real public accounts
- generated article packages
- local browser caches
- screenshots that expose accounts, paths, names, or private material

## Search Before Release

Run searches for:

```text
Windows absolute drive paths
user home paths
downloads folders
camera-roll folders
qrcode
二维码
真实姓名
真实机构
```

Also search for any account-specific labels, public-account names, or private project names.

## Replace With Placeholders

Use placeholders such as:

```text
编辑丨姓名，机构/身份
审核丨姓名，机构/身份
校对丨姓名，机构/身份
整理丨姓名，机构/身份
课题组/公众号名称
assets/public_account_qr.png
```

## Copyright

Do not publish full third-party articles, downloaded WeChat pages, paper PDFs, or long copied passages. Example outputs should be synthetic or based on material you have the right to share.
