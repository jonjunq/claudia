# Recipe: trips

> *"We want to go to Rome the last weekend of the month. Flights and a hotel near the centre, the whole price."*
> *"Pass me the links."* *"Put the flights in my calendar and remind me of the check-in."*

**Ours does this**: it searches flights and hotels, gives you the total with everything (flights, bags, hotel,
transfers, tourist tax), per person and for everyone, re-checks prices just before sending the links, checks the
entry documents of the destination on its official site, and once you book it puts each flight in your calendar and
reminds you when check-in opens. You pay; or it pays with the
[limited card](../permissions.md#optional-paying-with-a-limited-card) after your yes.

## What it uses

- The **`trips` skill** ([`SKILL.md`](../../templates/workspace/.claude/skills/trips/SKILL.md), installed with the
  assistant): how it searches, the gotchas ours learned (hotel searches that quietly change your dates, links that
  open for one passenger, fares that apply to every passenger), the checks on your screenshot before you pay, entry
  documents, and what it does when the confirmation arrives.
- **`google-travel.py`** (`templates/tools/`): flight prices from Google Flights and one hotel's total from Google
  Hotels, without a browser, and Google Hotels links with the dates fixed for its [browser](../browser.md). There is
  no free official API for flight prices: it reads the same public pages you see, so it will break now and then when
  Google changes them; then it says so and the browser takes over. Each price comes with the time it was checked.
- After you book, the confirmation email reaches it at once with the [n8n email watch](../n8n.md); without it, forward
  the email.

## Ask your assistant

> "When I ask for a trip, find flights and hotels, give me the total with everything per person and for both of us,
> and pass me the links. After I book, put everything in the calendar and remind me of the check-in."

The first time, it asks the one thing it is missing (usually who travels and from where) and writes your habits at
the end of the skill: home airports, bags, currency, how you want the list. It asks fewer questions after that.

## Risks

- Prices move by the hour: a quote from this morning is not a promise.
- Never book or pay without your yes to that exact total ([the limited card](../permissions.md#optional-paying-with-a-limited-card)).
- Names must match your documents exactly; it checks them in the booking screenshot.
- Passport details: it only uses them where you told it to keep them, and only types them into the official site.
