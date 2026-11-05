# Recipe: trips

> *"We want to go to Rome the last weekend of the month. Flights and a hotel near the centre, the whole price."*
> *"Pass me the links."* *"Put the flights in my calendar and remind me of the check-in."*

**Ours does this**: it searches flights and hotels, gives you the total with everything (flights, bags, hotel,
transfers, tourist tax), per person and for everyone, re-checks prices just before sending the links, and once you
book it puts each flight in your calendar and reminds you when check-in opens. You pay; or it pays with the
[limited card](../permissions.md#optional-paying-with-a-limited-card) after your yes.

## How it searches

- There is no free official API for flight prices. Ours reads the public flight-search pages (and its browser for
  hotels); yours will do the same, and it will break now and then when a site changes. It should say which day and
  time each price is from.
- Write your travel habits into a skill once: home airports, who travels with you, bags, how you want the list
  (cheapest first, or by time). It will ask fewer questions.

## Gotchas it should know (ours learned them)

- **Hotel searches can silently change your dates** to show a price for other nights. It must check the dates on the
  page before quoting a price.
- **Links often open for one passenger.** When you travel with someone, it tells you to change the number, and
  checks your screenshot before you pay.
- **Fares apply to every passenger**: a bag for only one of you may be cheaper as an add-on for that person.
- Check-in, reception hours and late arrivals: it crosses the hotel's hours with your flight times.

## After you book

When the confirmation email arrives (instantly, with the [n8n email watch](../n8n.md)):
- one calendar event per flight, with an alert the day before and three hours before, and the booking reference, the
  bags of each person and what was paid in the description;
- an event for check-in at the time it opens;
- the emails archived under a label for the trip.

## Ask your assistant to set it up

> "When I ask for a trip, find flights and hotels, give me the total with everything per person and for both of us,
> and pass me the links. After I book, put everything in the calendar and remind me of the check-in. Write a
> skill with how I like to travel."

## Risks

- Prices move by the hour: a quote from this morning is not a promise.
- Never book or pay without your yes to that exact total ([the limited card](../permissions.md#optional-paying-with-a-limited-card)).
- Names must match your documents exactly; it should check them in the booking screenshot.
