#!/usr/bin/env python3
"""Offline checks for templates/tools/google-travel.py: how it reads Google Flights and Google Hotels pages, and the
hotel dates it sends. No network: the pages are small copies of the real structure, with made-up airlines and
hotels. Prints one "ok"/"FAIL" line per check, exits 1 on a failure."""
import argparse
import base64
import contextlib
import datetime
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "templates", "tools", "google-travel.py")
spec = importlib.util.spec_from_file_location("google_travel", TOOL)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += 0 if cond else 1


def label(text):
    return f'<li><div aria-label="{text}">x</div></li>'


EN = "".join([
    label("From 1,204 British pounds. Nonstop flight with Example Air. Leaves Alpha Airport at 9:05 PM on "
          "Friday, March 12 and arrives at Beta Airport at 6:30 AM on Saturday, March 13. Total duration 8 hr "
          "25 min.   Select flight"),
    label("From 48 British pounds.This price does not include overhead bin access. Nonstop flight with Budget Wings. "
          "Leaves Alpha Airport at 7:10 AM on Friday, March 12 and arrives at Beta Airport at 9:35 AM on "
          "Friday, March 12. Total duration 2 hr 25 min.   Select flight"),
    # the same flight twice (Google lists it in two places)
    label("From 48 British pounds.This price does not include overhead bin access. Nonstop flight with Budget Wings. "
          "Leaves Alpha Airport at 7:10 AM on Friday, March 12 and arrives at Beta Airport at 9:35 AM on "
          "Friday, March 12. Total duration 2 hr 25 min.   Select flight"),
    label("From 95 British pounds. 1 stop flight with Example Air and Other Air. Leaves Alpha Airport at 12:15 PM "
          "on Friday, March 12 and arrives at Beta Airport &quot;Central&quot; at 6:50 PM on Friday, March 12. "
          "Total duration 6 hr 35 min.  Layover (1 of 1) is a 1 hr 40 min layover at Gamma International Airport in "
          "Gamma City. Select flight"),
    # another day: Google sometimes mixes in neighbouring dates
    label("From 30 British pounds. Nonstop flight with Budget Wings. Leaves Alpha Airport at 6:00 AM on "
          "Thursday, March 11 and arrives at Beta Airport at 8:25 AM on Thursday, March 11. Total duration 2 hr "
          "25 min.   Select flight"),
    label("Flight details. Leaves Alpha Airport at 7:10 AM on Friday, March 12 and arrives at Beta Airport."),
])
ES = "".join([
    label("A partir de 1.310 euros. Vuelo directo de Example Air. Sale de Aeropuerto Alfa el viernes, marzo 12 a "
          "las 21:05. Llega a Aeropuerto Beta el sábado, marzo 13 a las 6:30. Duración total: 8 h 25 min.   "
          "Seleccionar vuelo"),
    label("A partir de 112 euros. Vuelo con 2 escalas de Example Air y Other Air. Sale de Aeropuerto Alfa el "
          "viernes, marzo 12 a las 8:00. Llega a Aeropuerto Beta el viernes, marzo 12 a las 19:40. Duración total: "
          "11 h 40 min.  Esta escala (1 de 2) es una escala de 2 h 5 min en Aeropuerto de Gamma de Gamma. Esta "
          "escala (2 de 2) es una escala de 1 h en Aeropuerto Internacional Delta de Delta. Seleccionar vuelo"),
])

en = g.parse_flights(EN)
check("flights: English labels read, the same flight once", len(en) == 4)
check("flights: cheapest first", [f["price"] for f in en] == [30, 48, 95, 1204])
f48 = next(f for f in en if f["price"] == 48)
check("flights: 12-hour clock to 24 h, airline, no cabin bag flagged",
      (f48["departs"], f48["arrives"], f48["airline"], f48["no_cabin_bag"]) == ("07:10", "09:35", "Budget Wings", True))
big = next(f for f in en if f["price"] == 1204)
check("flights: thousands separator, overnight arrival marked",
      big["departs"] == "21:05" and big["arrives"] == "06:30" and big["next_day"] and not big["no_cabin_bag"])
one = next(f for f in en if f["price"] == 95)
check("flights: stops and layover city", one["stops"] == 1 and one["layovers"] == ["Gamma City 1 hr 40 min"])
check("flights: the day each result is for", big["date"] == (3, 12) and next(f for f in en if f["price"] == 30)["date"] == (3, 11))

es = g.parse_flights(ES)
check("flights: Spanish labels read", [f["price"] for f in es] == [112, 1310])
check("flights: Spanish stops and layovers",
      es[0]["stops"] == 2 and es[0]["layovers"] == ["Gamma 2 h 5 min", "Delta 1 h"] and es[0]["airline"] == "Example Air y Other Air")
check("flights: Spanish overnight and date", es[1]["next_day"] and es[1]["date"] == (3, 12) and es[1]["departs"] == "21:05")
check("flights: nothing in a page without results", g.parse_flights("<html><div aria-label='x'></div></html>") == [])


def run(fn, page, **kw):
    """Runs a command with a fake page instead of the network; returns (exit code, output)."""
    real = g.fetch
    g.fetch = lambda url: page
    opts = dict(currency="EUR", lang="en", country="", after=None, before=None, nonstop=False, max=15, json=False,
                adults=2)
    a = argparse.Namespace(**dict(opts, **kw))
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = fn(a)
    finally:
        g.fetch = real
    return code, out.getvalue()


code, out = run(g.cmd_flights, EN, origin="aaa", destination="BBB", date="2027-03-12")
check("flights command: other days left out and said so", code == 0 and "30 British" not in out and "another day" in out)
check("flights command: shows the check time and the link", "checked " in out and "Link (opens for 1 passenger): https://www.google.com/travel/flights?q=Flights%20from%20AAA%20to%20BBB%20on%202027-03-12" in out)
code, out = run(g.cmd_flights, EN, origin="AAA", destination="BBB", date="2027-03-12", after="10:00", before="22:00")
check("flights command: departure window", "12:15" in out and "21:05" in out and "07:10" not in out)
code, out = run(g.cmd_flights, EN, origin="AAA", destination="BBB", date="2027-03-12", nonstop=True)
check("flights command: --nonstop", "stop (" not in out and "07:10" in out)
code, out = run(g.cmd_flights, "<html></html>", origin="AAA", destination="BBB", date="2027-03-12")
check("flights command: exit 1 and a way out when nothing is found", code == 1 and "use the browser" in out)

LONG = label("A partir de 359 euros. Vuelo con 1 escala de Shenzhen. Sale de Aeropuerto Alfa el viernes, diciembre 11 a "
             "las 11:35. Llega a Aeropuerto Beta el domingo, diciembre 13 a las 1:20. Duración total: 31 h 45 min.  "
             "Esta escala (1 de 1) es una escala de 16 h 10 min en Aeropuerto Internacional de Shenzhen-Bao&#39;an de "
             "Shenzhen. Seleccionar vuelo")
lf = g.parse_flights(LONG)
check("flights: arriving two days later shows +2, not +1",
      len(lf) == 1 and lf[0]["days_later"] == 2 and lf[0]["layovers"] == ["Shenzhen 16 h 10 min"])
check("flights: +1 for the next day, nothing on the same day", big["days_later"] == 1 and f48["days_later"] == 0)
check("days_later: new year, the date line westwards, a label without a date",
      g.days_later("Thursday, December 31", "Friday, January 1") == 1
      and g.days_later("Saturday, January 1", "Friday, December 31") == -1
      and g.days_later("viernes, marzo 12", "jueves, marzo 11") == -1
      and g.days_later("Friday", "Saturday") == 1)

# Hotels: the dates go in ts. These values were checked against Google Hotels: the page showed those dates and guests.
d = datetime.date
check("hotel ts: dates, nights, 2 adults, currency (checked on Google)",
      g.hotel_ts(d(2027, 2, 10), d(2027, 2, 13), 2, "GBP") == "CAESCgoCCAMKAggDEAAaIAoCGgASGhIUCgcI6w8QAhgKEgcI6w8QAhgNGAMyAggBKgkKBToDR0JQGgA")
check("hotel ts: 1 adult (checked on Google)",
      g.hotel_ts(d(2027, 2, 10), d(2027, 2, 13), 1, "EUR") == "CAESBgoCCAMQABogCgIaABIaEhQKBwjrDxACGAoSBwjrDxACGA0YAzICCAEqCQoFOgNFVVIaAA")
check("hotel ts: 3 adults (checked on Google)",
      g.hotel_ts(d(2027, 2, 10), d(2027, 2, 13), 3, "EUR") == "CAESDgoCCAMKAggDCgIIAxAAGiAKAhoAEhoSFAoHCOsPEAIYChIHCOsPEAIYDRgDMgIIASoJCgU6A0VVUhoA")
t = g.hotel_ts(d(2027, 12, 28), d(2028, 1, 30), 2, "usd")
raw = base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))
check("hotel ts: across a new year, 33 nights, currency in capitals",
      bytes.fromhex("0a07 08eb0f 100c 181c 1207 08ec0f 1001 181e 1821") in raw and b"\x3a\x03USD" in raw and "=" not in t)


def hotel_page(name, total, nights, dates, lang="en"):
    back = "Back to list of all results" if lang == "en" else "Volver a la lista de todos los resultados"
    word = f"{total} total|{nights} nights with taxes + fees" if lang == "en" else \
        f"{total} en total|{nights} noches con impuestos y tasas incluidos"
    return (f"<html><head><title>{name} - Google Hotel Search</title></head><body><div>Other Hotel</div>"
            f"<div>€99</div><div>€999 total</div><div>9 nights with taxes + fees</div><div>€99</div><div>Jan 1 – 10</div>"
            f"<h1>{name}</h1><a>{back}</a><div>4.4</div><div>Some Street 1</div><div>€120</div><div>{word.split('|')[0]}</div>"
            f"<div>{word.split('|')[1]}</div><div>€120</div><div>{dates}</div><div>Website</div></body></html>")


code, out = run(g.cmd_hotel, hotel_page("Hotel Example Centre", "€360", 3, "Mar 12 – 15, 2027"),
                query="Hotel Example Centre, Beta", checkin="2027-03-12", checkout="2027-03-15")
check("hotel: the price of the hotel Google opened, not of another one on the page",
      code == 0 and out.startswith("Hotel Example Centre: €360 in total for 3 night(s)") and "999" not in out)
check("hotel: says the dates the page shows", "(Mar 12 – 15, 2027)" in out and "WARNING" not in out)
code, out = run(g.cmd_hotel, hotel_page("Hotel Example Centre", "€120", 1, "Mar 20 – 21"),
                query="Hotel Example Centre", checkin="2027-03-12", checkout="2027-03-15")
check("hotel: warns and exits 1 when Google changed the nights", code == 1 and "WARNING" in out and "not for your stay" in out)
code, out = run(g.cmd_hotel, hotel_page("Hotel Ejemplo", "360 €", 3, "12–15 mar 2027", lang="es"),
                query="Hotel Ejemplo", checkin="2027-03-12", checkout="2027-03-15")
check("hotel: Spanish page", code == 0 and "360 € in total for 3 night(s)" in out)
code, out = run(g.cmd_hotel, "<html><div>Other Hotel</div><div>€999 total</div><div>9 nights with taxes</div>"
                             "<div>€99</div><div>Jan 1 – 10</div></html>",
                query="Nowhere Inn", checkin="2027-03-12", checkout="2027-03-15")
check("hotel: a list instead of one hotel is no price", code == 1 and "No price for one hotel" in out and "999" not in out)

code, out = run(g.cmd_link, "", query="hotels in Beta", checkin="2027-02-10", checkout="2027-02-13")
check("link: Google Hotels with the dates fixed",
      out.strip() == "https://www.google.com/travel/search?q=hotels+in+Beta&hl=en&curr=EUR&ts="
      + g.hotel_ts(d(2027, 2, 10), d(2027, 2, 13), 2, "EUR"))

sys.exit(1 if fails else 0)
