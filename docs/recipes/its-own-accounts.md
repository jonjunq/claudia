# Recipe: accounts of its own

> *"Sign up for that service for me."* *"Make yourself an account on the second-hand app and list my old bike."*
> *"Create a developer account so you can set up the TV."*

**Ours does this**: it signs up for services on your behalf when you ask, accepting their terms, with an email
alias per service; and it has an email address of its own for the accounts it runs itself.

## Email addresses

- **An alias per service** (`you+service@example.com`, which most providers deliver to you): you can tell which
  service sold your address and filter or burn one without touching the others. Some sites ignore or reject the `+`
  and treat it as your main address: use the next option for those.
- **A mailbox of its own** (`assistant.yourname@example.com`) for accounts the assistant runs (a seller account, a
  social account). Forward everything to you: it reads it in your inbox, you see everything it receives, and it
  needs no second mail connector. Big providers often refuse automated sign-ups: you create this one yourself from
  your phone, in two minutes.
- **A phone number** is the usual blocker: many services want one for verification and refuse one already used by
  your own account. A cheap prepaid SIM in a drawer works; virtual numbers are often rejected.

## Passwords and codes

- It generates the password and keeps it in a private file (`~/.config/assistant/<service>.env`, mode 600), outside
  the workspace and its history. When you need it, it sends it to you alone in one message.
- Two-step verification goes to **your** phone or authenticator. Its accounts are yours; it operates them.
- Captchas and "unusual sign-in" checks: you solve them in its browser from your phone
  ([browser.md](../browser.md#a-remote-window-for-captchas-and-logins)).

## Ask your assistant to set it up

> "From now on, when I ask you to sign up for something, do it with the alias me+<service>@… and my details, and
> keep the password in a private file. For accounts you run yourself, I'll make you your own email address."

## Permissions

Without a rule the classifier blocks accepting terms and consenting on your behalf, even when you asked. The
`allow` sentence is in [permissions.md](../permissions.md#examples) ("create accounts on services and accept their
terms…"). Paid plans stay blocked by `hard_deny` unless you set up the [limited card](../permissions.md#optional-paying-with-a-limited-card).

## Risks

- Accepting terms in your name is a legal act in your name: it should tell you what it accepted, in one line, and
  never sign up for something you did not ask for.
- An account it runs speaks for you: it should say it is an assistant where the service allows it, and never claim
  to be you to a person.
- Each account is one more place your data lives. The alias makes it easy to find and close later; ask it for the
  list of accounts it created now and then.
