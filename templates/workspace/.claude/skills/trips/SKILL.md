---
name: trips
description: Finding and preparing trips for __OWNER__ - flights, hotels, bags, booking links, entry documents (visas, travel authorisations such as the UK ETA), the calendar and check-in. Load it when __OWNER__ asks about flights or hotels, the price of a trip, "send me the links", whether a travel permit is still valid, or to put a trip in the calendar, and when a booking confirmation arrives.
---

# Trips

__OWNER__ books and pays (or you pay with the limited card, only after their yes to that exact total, if they set
one up: `/usr/local/share/assistant/docs/permissions.md`, "paying with a limited card"). The recipe with the
risks: `/usr/local/share/assistant/docs/recipes/trips.md`. You search, compare, send the links, and check their
screenshots before they pay.

Before searching, read **"How __OWNER__ travels"** at the end of this file. If it is still empty, ask the ONE
question that changes the result most (usually who is travelling and from which airport), with your best guess so a
"yes" is enough, and write the answer there. Add to it whenever you learn something lasting; keep it short.

## 1. Flights: `google-travel.py` (Google Flights, no browser)

```
python3 -I /usr/local/share/assistant/tools/google-travel.py flights MAD LIS 2027-03-12 --currency EUR
    --after 09:00 --before 14:00   leaving in that window      --nonstop   direct flights only
    --max N   --json   --lang en|es   --country GB
```
- One leg and one day per call, one way: a return trip is two calls, three dates are three calls. Each takes a few
  seconds; for a wide search (many dates or airports), hand it to a helper and ask for the best five.
- Each line: the "from" price per person (the basic fare), airline, times (`+1` = arrives the next day, `+2` two days later, `-1` the day before when crossing the date line), duration,
  stops with the layover city, and "no cabin bag in this fare" when Google says so. Results Google mixes in for
  other days are left out. The last line is the Google Flights link.
- If it finds nothing (no flights, or Google changed its page), use the browser with the link it prints.
- **Prices move by the hour: check them again right before you send the links**, and say whether they went up or
  down since the last time. Say when each price is from.
- Always give the price **per person and the total for everyone**, and apart from it what is paid there (tourist
  tax, a deposit). The total __OWNER__ wants is everything: flights, bags, hotel, getting to and from the airport,
  tourist tax.

## 2. Hotels: Google Hotels with the browser

- The link with the dates and guests fixed:
  `python3 -I /usr/local/share/assistant/tools/google-travel.py link "hotels in Lisbon" 2027-03-12 2027-03-14 --adults 2 --currency EUR`
  Open it with agent-browser (skill `browser`) and read price, rating and number of reviews from the page. To
  compare many hotels, give the link to the `browser-fast` helper and ask for the best three with those details.
- **Trap: Google changes the dates quietly.** A search for one hotel without dates shows a price for nights Google
  picks. The links from `google-travel.py` carry the dates (the `ts` parameter), but still check the dates at the top
  of the page before you quote a price.
- To re-check one hotel's price without the browser:
  `python3 -I /usr/local/share/assistant/tools/google-travel.py hotel "Hotel Name, City" 2027-03-12 2027-03-14 --adults 2`
  It prints the hotel Google opened (make sure it is the one you meant), the total with taxes, and the nights and
  dates the page shows; it warns, and exits 1, when they are not the ones asked for.
- If a hotel __OWNER__ liked "has no rooms" those nights, say so plainly and give 2-3 alternatives in the same area,
  with rating and number of reviews.
- **Loyalty levels** (Booking's Genius and the like): their discount only shows with __OWNER__'s own session, so
  the price you see may be higher than theirs; ask for a screenshot from their account before comparing. If they are
  close to the next level, suggest holding a room with free cancellation and no prepayment, and booking the good one
  once the level is up.
- Look at reception and check-out hours (the hotel's details) and cross them with the flight times: arriving late or
  leaving late usually needs a word with the hotel.

## 3. Booking links and bags

Details and the link formats in `references/booking-links.md`. In short:
- An airline link that opens the flight already chosen is best (Ryanair's format is in the reference). The Google
  Flights link opens the airline **for 1 passenger**: if more are travelling, tell __OWNER__ to change it.
- A fare with a bag often applies to **every passenger** in the booking: if only one needs the bag, the basic fare
  plus a bag for that person alone is usually cheaper. Offer the checked bag too when it costs less.
- **Before they pay, check their screenshot**: the number of passengers and the total; names exactly as on the ID or
  passport; each extra on the right person; insurance, SMS and other extras left unticked unless wanted; free
  cancellation on the hotel, if that was the plan.

## 4. Documents to enter the country

See `references/entry-documents.md`. The rules:
- Check what the destination asks for __OWNER__'s nationality (visa, travel authorisation, passport validity) on the
  **official government site** of the destination, every time: the rules change, and paid look-alike sites are
  common. Never apply through an intermediary.
- If the official site lets you check a permit yourself, do it and send a screenshot of the result; do not send
  __OWNER__ to look it up.
- Passport and ID details: only from where __OWNER__ told you to keep them (noted below), and only typed into the
  official site. Never in a message, an event or a note.
- Authorisations are usually tied to one passport: a new passport needs a new one.

## 5. After booking

- For every confirmation email (an automatic notice from the email watch, or one __OWNER__ forwards): read it and
  create in their calendar one event per flight, with alerts the day before and 3 hours before, and in the
  description the booking reference, each person's bags and what was paid.
- Also an event for check-in at the time it opens (from the email or the airline's site; if you could not confirm
  the time, say so in the event), and a line in `notes/todo.md` so you remind them that day. Some airlines give
  boarding passes only in their app: say so.
- Hotel with free cancellation: the last day to cancel goes in `notes/todo.md` too, a couple of days before.
- File the trip's emails under a label `Trips/<destination> <year>` (create it if needed).
- "Send me the flights": one card per flight, with airline and number, times, booking reference, amount, each
  person's bags and when check-in opens.

## How __OWNER__ travels

(Fill this in as you learn it; one line each.)
- Who travels:
- Home airports:
- Bags:
- Searches in: `--currency EUR --lang en` (change to theirs)
- How they want the list (cheapest first, by time, at most N options):
- Loyalty accounts (names and level only, never passwords):
- Passport and ID details are kept in: (nowhere yet: ask them each time)
