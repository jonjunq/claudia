# Recipe: your money, read only

> *"How much is my portfolio worth today, and how much have I made?"* *"Draw me how my savings went this year."*
> *"Is there anything odd in my bank account?"* *"Will I have enough on the card when the subscription renews?"*

**Ours does this**: it reads balances and movements from a bank, a broker's fund exports, a crypto exchange and a
card on a public blockchain, draws charts of how each one evolved, and checks the bank quietly every morning,
speaking up only when something looks wrong. **It cannot move a cent**: that is set at the provider, not in a prompt.

This recipe is ideas and risks, not code: every provider is different, the scripts depend on their APIs, and your
assistant writes the small script for yours in a few minutes once you have chosen the safe route below.

## The safe routes, from safest

1. **Files you export yourself.** Most brokers and banks let you download your orders and movements as CSV. You
   send them on Telegram once a month (it reminds you); it adds the current prices from a public source (a fund's
   published net asset value, an index quote) and works out value, cost and gain. No credentials at all.
2. **Public data.** A card or wallet that lives on a public blockchain can be read from a public RPC node with only
   its address: no key, no login. (Anyone else can read it too: that is the nature of a public chain.)
3. **A read-only API key.** Many crypto exchanges and some brokers let you create keys with permissions you choose:
   tick *query funds / ledger / orders / export* and nothing else, never *trade*, *withdraw* or *transfer*. The
   provider then refuses anything else, whatever the assistant is told.
4. **Open banking with read consent.** In the EU and the UK (PSD2 / Open Banking), a licensed aggregator can read
   your balances and movements with a consent you approve in your bank's app, typically for 90 or 180 days. Some
   aggregators have a free tier for personal use. The consent is read-only by design, and the rules cap how often it
   can read without you present (about four times a day).

**Do not** give it your online-banking password to scrape the bank's website. It breaks the bank's terms, can lock
your account as suspected fraud, and the password can also send money.

## Ask your assistant to set it up

> "I want you to see my [bank / broker / exchange] in read only. Find the safest way for it (exports, a read-only
> key or open banking), tell me what I have to do, and write a small script that only reads. Keep the credentials
> in a private file outside your workspace."

Then, once it works:

> "Every morning, check my main account quietly. Only tell me if something is odd: a charge you don't recognise, a
> duplicate, an unusual amount, or not enough to cover a payment that is due."

## Where the credentials go

- A file per provider in `~/.config/assistant/` (mode 600): outside the workspace, so outside its git history and
  its notes. Scripts read the file; the values never go into a command line or the chat.
- You create the key or approve the consent yourself. If a key is ever shown in the chat, revoke it and make a new
  one: everything that reaches the session stays in its transcripts, and `recall` indexes them.

## Permissions

Nothing special for reading. The template's `autoMode.hard_deny` already blocks payments and transfers outright; if
you added the [limited card](../permissions.md#optional-paying-with-a-limited-card), name your accounts in its
`hard_deny` sentence as off-limits ("no bank, broker or exchange accounts").

## Risks

- ⚠️ **Read-only must be true at the provider.** A key with trading or withdrawal rights is one fooled request away
  from a loss; the classifier is a second line, not the first. Check the key's permissions in the provider's page
  before you hand it over.
- ⚠️ **Your financial data goes through the model.** Balances and movements end up in the conversation, its
  transcripts and the nightly review. Ask it to keep summaries in notes, not statements, and decide whether you are
  comfortable with that before connecting your main account.
- Consents expire (open banking every 90-180 days) and rate limits are real: if it reads too often, the bank answers
  "too many requests" until the next day. Ask it to note the renewal date in your calendar.
- Scraped prices break when a site changes; it should say which day a price is from.
- Charts and figures are for you: it is not a financial adviser, and investment ideas it finds are a starting point
  to check, not advice.
