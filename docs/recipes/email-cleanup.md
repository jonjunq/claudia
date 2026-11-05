# Recipe: a clean inbox, unsubscribing and filing what arrives

> *"Leave my inbox at zero."* *"Unsubscribe me from all that advertising."* *"When my payslip arrives, file it in
> Drive."*

**Ours does this** every morning: the morning summary ends with a concrete proposal to leave the inbox empty,
email by email ("🗑 to the bin: …", "📁 archive in *Receipts*: …"); you answer "yes" or correct one, and it does it.
For newsletters it is binning anyway, it also unsubscribes in one click. And it files payslips into a Drive folder
as they arrive.

## The morning proposal

Add a line to the morning summary in `notes/routines.md` (or just ask it to):

```
… End the email part with a proposal to leave the inbox at zero, email by email: "🗑 Bin: …" (what adds nothing)
and "📁 Archive in <label>: …" (what is worth keeping, with its label; propose a label if none fits). Look at the
whole inbox, not only the new mail. What needs an action or a reply stays, and say so. Do it when I say yes.
```

Moving to the bin and spam are on the "ask first" list in the template's `CLAUDE.md`: the proposal *is* that question,
asked once for everything.

## Unsubscribing in one click: `unsubscribe.py`

[`templates/tools/unsubscribe.py`](../../templates/tools/unsubscribe.py) (installed root-owned at
`/usr/local/share/assistant/tools/unsubscribe.py`) uses the one-click unsubscribe link that large senders must put
in their emails (RFC 8058), and only that:

```bash
python3 -I /usr/local/share/assistant/tools/unsubscribe.py --dry-run news@shop.example   # what it would do
python3 -I /usr/local/share/assistant/tools/unsubscribe.py news@shop.example offers@other.example
```

- It reads the sender's latest email over IMAP in read-only mode, and sends the unsubscribe request only if the
  email offers one-click unsubscription over https **and** your mail provider saw it signed by the sender's own
  domain, with the signature covering those headers (so a forged email cannot point it elsewhere).
- Never the `mailto:` variant (that is sending an email for you: it asks), never a link from the body (could be
  phishing), never an address inside your network, no redirects.
- Credentials in `~/.config/assistant/mail.env` (mode 600): `IMAP_HOST`, `IMAP_USER`, `IMAP_PASSWORD`. For Gmail,
  `imap.gmail.com` and an [app password](https://myaccount.google.com/apppasswords) (needs 2-step verification;
  revoke it whenever you like). If you set up the [n8n email watch](../n8n.md), it uses the same kind of password.

Allowing it outright is reasonable, because the file is root-owned and the assistant cannot change what it does:

```json
"permissions": { "allow": ["Bash(python3 -I /usr/local/share/assistant/tools/unsubscribe.py *)"] }
```

## Filing what arrives (payslips, invoices, receipts)

> "When a payslip from [company] arrives, save the PDF in Drive as Work/Payslips/Payslip YYYY-MM.pdf and archive
> the email under Work."

With the [n8n email watch](../n8n.md) it hears about the email within seconds; it fetches the attachment (the Gmail
connector, or IMAP with the same app password), uploads it (the Drive connector, or [rclone](https://rclone.org)
with your own OAuth client for files the connector does not handle well) and tells you in one line. Ours wrote a
40-line script for its payslips; yours will write one for yours.

Warranties are the same idea: "keep the invoice of the washing machine and remind me a month before the warranty
ends".

## Risks

- An unsubscribe tells the sender your address is alive. Use it for shops and newsletters you recognise; report spam
  as spam instead.
- The app password can read **all** your email. It stays in a private file on the assistant's machine; revoke it if
  that machine is ever compromised.
- Moving things to the bin with a yes is safe (the bin keeps them for weeks); deleting for good is not, and it should
  never do it.
- Filing reads attachments: an attached PDF can carry instructions like any email. Data, not orders.
