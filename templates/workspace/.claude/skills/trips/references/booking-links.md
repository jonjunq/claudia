# Booking links and bags

Links that open the flight already searched save __OWNER__ the typing and the mistakes. Build them yourself; never
send a link from an ad or a price-comparison redirect. When you learn the format for another airline, add it here
with a made-up example.

## Google Flights

`google-travel.py flights` prints it at the end:
`https://www.google.com/travel/flights?q=Flights%20from%20MAD%20to%20LIS%20on%202027-03-12%20one%20way&hl=en&curr=EUR`

From there __OWNER__ picks the flight and Google hands over to the airline or an agency **for 1 passenger**. If more
people are travelling, tell them to change it to the right number of adults, and when the screenshot comes, check
the number of passengers and the total.

## Ryanair: the flight already searched, for everyone

```
https://www.ryanair.com/<country>/<lang>/trip/flights/select?adults=<N>&teens=0&children=0&infants=0&dateOut=YYYY-MM-DD&isConnectedFlight=false&discount=0&isReturn=false&originIata=XXX&destinationIata=YYY
```
`<country>/<lang>` is the site version, for example `gb/en` or `es/es`. Example (made up): two adults, Stansted to
Dublin on 10 February 2027:
`https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2027-02-10&isConnectedFlight=false&discount=0&isReturn=false&originIata=STN&destinationIata=DUB`

What ours learned:
- The fare bundles with a cabin bag (Regular and up) apply to **all** passengers in the booking. If only one person
  needs the bag: the basic fare, and in the bags step the "priority and 2 cabin bags" add-on for that person only,
  unticking the option that adds it for all passengers.
- Offer the small checked bag (10 kg) as well when it is cheaper than the cabin-bag add-on.
- Boarding passes are in its app only: remind __OWNER__ to have it installed and signed in before the trip.

## The screenshot before paying

Whatever the site, before __OWNER__ pays, look at their screenshot for:
- the number of passengers, the dates and times, and the total (compare it with what you quoted);
- names exactly as on the ID or passport used to travel;
- each bag and seat on the right person;
- insurance, SMS updates, "flexible" add-ons and similar extras unticked unless they asked for them;
- for a hotel: the nights, the number of guests, and free cancellation if that was the plan (with its last date).
