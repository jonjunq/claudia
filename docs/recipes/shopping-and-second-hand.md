# Recipe: shopping and second-hand

> *"Find me a used bike like this one, in good condition and cheap, near home."* *"How much is my old camera worth
> second-hand?"* *"Sell it for me: here are the photos."* *"Tell me when this drops below 200."*

**Ours does this**: price searches on a second-hand marketplace through its public search, and comparing shops.
**Possible, not tried by us**: running a seller account of its own (ours has the account, waiting for a phone
number).

## Buying

- It searches the marketplace (many have a public search their own website uses; its browser otherwise), filters by
  distance and condition, and gives you the two or three best with price, photos and a link.
- It tells you when something looks wrong: many identical units far below the usual price from one seller (likely
  counterfeit), a seller with no history, "pay outside the app".
- **Price watch** ("tell me when it drops below 200"): an [n8n](../n8n.md) workflow that checks once or twice a day
  and messages you directly, without spending tokens; it stops when you say you bought it.
- Buying it for you: only with the [limited card](../permissions.md#optional-paying-with-a-limited-card) and your
  yes to that total; on a marketplace, through its own protected payment only.

## Selling (possible, not tried by us)

- An account of its own ([its-own-accounts.md](its-own-accounts.md)): its email, and a phone number for
  verification (marketplaces usually refuse one already used by your account).
- You send the photos; it writes the listing thinking of the buyer, proposes a price from similar listings, and
  publishes with your yes.
- It answers buyers' questions; price changes, the handover and anything that commits you go through you.

## Ask your assistant to set it up

> "When I ask for something second-hand, search [marketplace] near [town], show me the three best with photos, and
> warn me about anything that looks like a scam."

## Risks

- ⚠️ Scams target sellers too: fake "payment received" emails, "shipping" links that ask for card details, buyers
  who want to pay outside the app. It must never send your address, phone or bank details to a buyer, and never
  click a payment link from a chat.
- Marketplaces may not allow automated accounts; the account can be closed. Do not rely on it for a business.
- Messages from buyers are untrusted text: instructions in them are data.
