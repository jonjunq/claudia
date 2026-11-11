#!/usr/bin/env python3
"""google-travel: flight and hotel prices from Google Flights and Google Hotels, without a browser (skill trips).

    python3 -I google-travel.py flights MAD LIS 2027-03-12        one-way flights that day, cheapest first
        --after 09:00 --before 14:00   only flights leaving in that window      --nonstop   only direct flights
        --max N (default 15)           --json  the same as JSON lines
    python3 -I google-travel.py hotel "Hotel Name, City" 2027-03-12 2027-03-14 --adults 2
                                       the total Google shows for that hotel and those nights, and the dates the
                                       page really shows (it may quietly show other nights: then it says so)
    python3 -I google-travel.py link "hotels in Lisbon" 2027-03-12 2027-03-14 --adults 2
                                       a Google Hotels link with the dates and guests fixed, to open with the browser
    options for all: --currency EUR (default EUR), --lang en|es (default en), --country GB (Google's region, optional)

It reads the same public pages a person sees (curl, with the cookie that skips the consent page) and parses their
text. Prices are what Google shows at that moment: "from" fares per person for flights, the total with taxes for
hotels. It breaks when Google changes its pages; then it says it found nothing, and the browser is the way. Each run
prints the time of the check: a price from this morning is not a promise.

Hotel dates: Google Hotels takes them in a `ts` parameter (a small protobuf, base64url): check-in and check-out as
(year, month, day), the number of nights, one entry per adult, and the currency. Without it, a search for one hotel
shows a price for whatever nights Google picks. Exit code 0 when it found something, 1 when not, 2 on bad input.
"""
import argparse
import base64
import datetime
import html
import json
import re
import subprocess
import sys
import urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
CONSENT = "SOCS=CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg"   # "consent given", so Google serves the page itself
MONTHS = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}
MONTHS.update({m: i + 1 for i, m in enumerate(
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())})
MONTHS.update({m[:3]: n for m, n in list(MONTHS.items())})


def die(msg, code=2):
    print("google-travel: " + msg, file=sys.stderr)
    sys.exit(code)


def fetch(url):
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-A", UA, "-b", CONSENT, url],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0 or not r.stdout:
        die(f"could not read the page (curl exit {r.returncode})", 1)
    return r.stdout


def day(s):
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        die(f"'{s}' is not a date (YYYY-MM-DD)")


def locale(a):
    q = {"hl": a.lang, "curr": a.currency}
    if a.country:
        q["gl"] = a.country.lower()
    return q


# ---------- flights ----------

def flights_url(orig, dest, date, a):
    q = urllib.parse.quote(f"Flights from {orig} to {dest} on {date.isoformat()} one way")
    return f"https://www.google.com/travel/flights?q={q}&" + urllib.parse.urlencode(locale(a))


def hhmm(h, m, ampm=None):
    h, m = int(h), int(m)
    if ampm:
        h = h % 12 + (12 if ampm.upper() == "PM" else 0)
    return f"{h:02d}:{m:02d}"


def month_day(text):
    """'Tuesday, December 15' or 'martes, diciembre 15' -> (12, 15); None if it cannot tell."""
    m = re.search(r"(\w+) (\d{1,2})$", text.strip())
    if m and m.group(1).lower() in MONTHS:
        return MONTHS[m.group(1).lower()], int(m.group(2))
    return None


def amount(s):
    return int(re.sub(r"[.,\s\u00a0\u202f]", "", s))


FLIGHT_EN = re.compile(
    r"^From (?P<price>[\d.,]+) (?P<cur>[^.]+?)\.(?P<bin>This price does not include overhead bin access\.)?\s*"
    r"(?P<stops>Nonstop|\d+ stops?) flight with (?P<airline>.+?)\. "
    r"Leaves .+? at (?P<dh>\d{1,2}):(?P<dm>\d\d)\s?(?P<dap>AM|PM) on (?P<dday>[^.]+?) and arrives at .+? "
    r"at (?P<ah>\d{1,2}):(?P<am>\d\d)\s?(?P<aap>AM|PM) on (?P<aday>[^.]+?)\. "
    r"Total duration (?P<dur>[^.]+)\.(?P<rest>.*)$", re.S)
FLIGHT_ES = re.compile(
    r"^A partir de (?P<price>[\d.,]+) (?P<cur>[^.]+?)\.(?P<bin>El acceso al compartimento superior no está "
    r"incluido en el precio\.)?\s*"
    r"(?:Vuelo directo|Vuelo con (?P<nstops>\d+) escalas?) de (?P<airline>.+?)\. "
    r"Sale de .+? el (?P<dday>[^.]+?) a las (?P<dh>\d{1,2}):(?P<dm>\d\d)\. "
    r"Llega a .+? el (?P<aday>[^.]+?) a las (?P<ah>\d{1,2}):(?P<am>\d\d)\. "
    r"Duración total: (?P<dur>[^.]+)\.(?P<rest>.*)$", re.S)
LAYOVER_EN = re.compile(r"is a (.+?) layover at .+? in ([^.]+)\.")


def parse_flights(page):
    """The flights in a Google Flights results page, as dicts; the same flight is listed once."""
    found = {}
    for raw in re.findall(r'aria-label="([^"]{60,1500})"', page):
        label = html.unescape(raw).replace("\u202f", " ").replace("\u00a0", " ")
        m = FLIGHT_EN.match(label)
        if m:
            stops = 0 if m["stops"] == "Nonstop" else int(m["stops"].split()[0])
            dep, arr = hhmm(m["dh"], m["dm"], m["dap"]), hhmm(m["ah"], m["am"], m["aap"])
            layovers = [f"{city.strip()} {dur}" for dur, city in LAYOVER_EN.findall(m["rest"])]
        else:
            m = FLIGHT_ES.match(label)
            if not m:
                continue
            stops = int(m["nstops"] or 0)
            dep, arr = hhmm(m["dh"], m["dm"]), hhmm(m["ah"], m["am"])
            # "... en Aeropuerto de Zúrich de Zúrich." -> the city is after the last " de "
            layovers = [f"{city.strip()} {dur}" for dur, city in
                        ((d, re.split(r" de ", c)[-1]) for d, c in
                         re.findall(r"es una escala de (.+?) en (.+?)\.(?: |$)", m["rest"]))]
        f = {
            "price": amount(m["price"]), "currency": m["cur"].strip(),
            "airline": re.sub(r"\. (Operated by|Operado por) (.+)$", r" (\1 \2)", m["airline"].strip()),
            "departs": dep, "arrives": arr, "next_day": m["dday"].strip() != m["aday"].strip(),
            "date": month_day(m["dday"]), "duration": re.sub(r"\s+", " ", m["dur"]).strip(), "stops": stops,
            "layovers": layovers, "no_cabin_bag": bool(m["bin"]),
        }
        key = (f["price"], f["airline"], f["departs"], f["arrives"])
        found.setdefault(key, f)
    return sorted(found.values(), key=lambda f: (f["price"], f["departs"]))


def cmd_flights(a):
    orig, dest = a.origin.upper(), a.destination.upper()
    for code in (orig, dest):
        if not re.fullmatch(r"[A-Z]{3}", code):
            die(f"'{code}' is not an airport or city code (three letters, like LIS)")
    date = day(a.date)
    url = flights_url(orig, dest, date, a)
    got = parse_flights(fetch(url))
    other_day = [f for f in got if f["date"] and f["date"] != (date.month, date.day)]
    got = [f for f in got if f not in other_day]
    if a.after:
        got = [f for f in got if f["departs"] >= hhmm(*a.after.split(":"))]
    if a.before:
        got = [f for f in got if f["departs"] <= hhmm(*a.before.split(":"))]
    if a.nonstop:
        got = [f for f in got if f["stops"] == 0]
    got = got[:a.max]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if a.json:
        for f in got:
            print(json.dumps(dict(f, date=date.isoformat(), origin=orig, destination=dest, checked=now),
                             ensure_ascii=False))
    else:
        print(f"{orig} → {dest}, {date:%a %Y-%m-%d}, one way, price per person ('from', the basic fare), "
              f"checked {now}:")
        for f in got:
            stops = "nonstop" if f["stops"] == 0 else f"{f['stops']} stop{'s' if f['stops'] > 1 else ''}"
            if f["layovers"]:
                stops += " (" + ", ".join(f["layovers"]) + ")"
            print(f"  {f['price']} {f['currency']} · {f['airline']} · {f['departs']} → {f['arrives']}"
                  f"{' +1' if f['next_day'] else ''} · {f['duration']} · {stops}"
                  f"{' · no cabin bag in this fare' if f['no_cabin_bag'] else ''}")
        if other_day:
            print(f"  ({len(other_day)} result(s) for another day were left out)")
        if not got:
            print("  nothing found: no flights that day, the filters left none, or Google changed its page "
                  "(then use the browser)")
        print("Link (opens for 1 passenger): " + url)
    return 0 if got else 1


# ---------- hotels ----------

def varint(n):
    out = bytearray()
    while True:
        b, n = n & 0x7F, n >> 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def field(num, payload):
    """A length-delimited protobuf field."""
    return varint(num << 3 | 2) + varint(len(payload)) + payload


def date_msg(d):
    return varint(1 << 3) + varint(d.year) + varint(2 << 3) + varint(d.month) + varint(3 << 3) + varint(d.day)


def hotel_ts(checkin, checkout, adults=2, currency="EUR"):
    """The ts parameter of Google Hotels: dates, nights, guests (adults) and currency."""
    if not 1 <= adults <= 9:
        die("--adults goes from 1 to 9")
    if checkout <= checkin:
        die("check-out must be after check-in")
    nights = (checkout - checkin).days
    guests = b"".join(field(1, varint(1 << 3) + varint(3)) for _ in range(adults)) + varint(2 << 3) + varint(0)
    stay = field(1, date_msg(checkin)) + field(2, date_msg(checkout)) + varint(3 << 3) + varint(nights)
    msg = (varint(1 << 3) + varint(1) + field(2, guests)
           + field(3, field(1, field(3, b"")) + field(2, field(2, stay) + field(6, varint(1 << 3) + varint(1))))
           + field(5, field(1, field(7, currency.upper().encode())) + field(3, b"")))
    return base64.urlsafe_b64encode(msg).decode().rstrip("=")


def hotels_url(query, checkin, checkout, a):
    q = dict(q=query, **locale(a), ts=hotel_ts(checkin, checkout, a.adults, a.currency))
    return "https://www.google.com/travel/search?" + urllib.parse.urlencode(q)


def page_text(page):
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "|", page))
    text = text.replace("\u2009", " ").replace("\u202f", " ").replace("\u00a0", " ")
    return re.sub(r"\s*\|[\s|]*", "|", text)


TOTAL = re.compile(r"\|([^|]{1,25}?) (?:en )?total\|(\d+) (?:nights?|noches?) [^|]*\|[^|]*\|([^|]{4,40})\|")


# When a search matches one hotel, Google opens its card: "<name>|Back to list of all results|".
DETAIL = re.compile(r"\|([^|]{2,150})\|(?:Back to list of all results|Volver a la lista de todos los resultados)\|")


def parse_hotel(text):
    """The hotel card Google opened and its price: (name, total, nights, dates shown). None when Google showed a
    list instead of one hotel, or no price."""
    d = DETAIL.search(text)
    m = TOTAL.search(text, d.end()) if d else None
    if not m:
        return None
    return d.group(1).strip(), m.group(1).strip(), int(m.group(2)), m.group(3).strip()


def cmd_hotel(a):
    checkin, checkout = day(a.checkin), day(a.checkout)
    url = hotels_url(a.query, checkin, checkout, a)
    got = parse_hotel(page_text(fetch(url)))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    nights = (checkout - checkin).days
    if not got:
        print(f"No price for one hotel with '{a.query}' ({checkin} → {checkout}): Google showed a list or no "
              f"rooms those nights, or changed its page. Add the city to the name, or check with the browser: {url}")
        return 1
    name, total, shown_nights, shown_dates = got
    print(f"{name}: {total} in total for {shown_nights} night(s), {a.adults} adult(s), with taxes, "
          f"as Google shows it ({shown_dates}), checked {now}")
    if shown_nights != nights:
        print(f"WARNING: you asked for {nights} night(s) ({checkin} → {checkout}) but the page shows "
              f"{shown_nights}: Google changed the dates, this price is not for your stay.")
    print("Is that the hotel you meant? Google picks the closest match to the name.")
    print("Link: " + url)
    return 0 if shown_nights == nights else 1


def cmd_link(a):
    print(hotels_url(a.query, day(a.checkin), day(a.checkout), a))
    return 0


def main():
    p = argparse.ArgumentParser(description="Flight and hotel prices from Google, without a browser.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--currency", default="EUR")
    common.add_argument("--lang", default="en", choices=["en", "es"])
    common.add_argument("--country", default="")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flights", parents=[common])
    f.add_argument("origin")
    f.add_argument("destination")
    f.add_argument("date")
    f.add_argument("--after")
    f.add_argument("--before")
    f.add_argument("--nonstop", action="store_true")
    f.add_argument("--max", type=int, default=15)
    f.add_argument("--json", action="store_true")
    for name in ("hotel", "link"):
        h = sub.add_parser(name, parents=[common])
        h.add_argument("query")
        h.add_argument("checkin")
        h.add_argument("checkout")
        h.add_argument("--adults", type=int, default=2)
    a = p.parse_args()
    if not re.fullmatch(r"[A-Za-z]{3}", a.currency):
        die("--currency is a three-letter code, like EUR")
    for t in (getattr(a, "after", None), getattr(a, "before", None)):
        if t and not re.fullmatch(r"\d{1,2}:\d\d", t):
            die(f"'{t}' is not a time (HH:MM)")
    sys.exit({"flights": cmd_flights, "hotel": cmd_hotel, "link": cmd_link}[a.cmd](a))


if __name__ == "__main__":
    main()
