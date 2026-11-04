#!/usr/bin/env python3
"""Embed the fonts a standalone SVG uses, as subsets, so it looks the same inside an <img>.

A browser draws an SVG loaded through <img> (as GitHub does in a README) in a sandbox that fetches nothing:
no Google Fonts, so the text falls back to system faces. This script reads which characters each face draws
(family, weight, style of every <text>), asks the Google Fonts css2 API for a subset with exactly those
characters (`&text=`), and writes them into the SVG as @font-face rules with data: URIs.

    python3 embed-fonts.py in.svg out.svg

Geist, Geist Mono and Instrument Serif are under the SIL Open Font License 1.1, which allows embedding and
subsetting; the notices are in FONTS-LICENSE.txt next to the SVGs. Needs network access to fonts.googleapis.com.
"""
import base64
import re
import sys
import urllib.parse
import urllib.request

FAMILIES = ("Geist Mono", "Geist", "Instrument Serif")   # longest first: "Geist Mono" also starts with "Geist"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
NOTICE = ("Font subsets: Geist and Geist Mono, Copyright 2024 The Geist Project Authors; Instrument Serif, "
          "Copyright 2022 The Instrument Serif Project Authors. SIL Open Font License 1.1, see FONTS-LICENSE.txt")

TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)


def attr(attrs, name, default):
    m = re.search(rf'\b{name}="([^"]*)"', attrs)
    return m.group(1) if m else default


def unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#x27;", "'")
            .replace("&#39;", "'").replace("&amp;", "&"))


def faces(svg):
    """{family: {(weight, style): set(chars)}} for every <text> in the SVG."""
    used = {}
    for attrs, body in TEXT_RE.findall(svg):
        stack = unescape(attr(attrs, "font-family", "'Geist'"))
        first = stack.split(",")[0].strip().strip("'\"")
        family = next((f for f in FAMILIES if first == f), None)
        if family is None:
            sys.exit(f"embed-fonts: unexpected font family {first!r}")
        key = (attr(attrs, "font-weight", "400"), attr(attrs, "font-style", "normal"))
        used.setdefault(family, {}).setdefault(key, set()).update(unescape(re.sub(r"<[^>]+>", "", body)))
    return used


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def font_faces(family, keys, chars):
    italic = sorted({s == "italic" for _, s in keys})
    weights = sorted({int(w) for w, _ in keys})
    if family == "Instrument Serif":   # a single weight; only the axis of italics
        axis = "ital@" + ";".join("1" if i else "0" for i in italic)
    else:
        axis = "wght@" + ";".join(str(w) for w in weights)
    url = ("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(family) + ":" + axis
           + "&text=" + urllib.parse.quote("".join(sorted(chars))))
    css = fetch(url)
    blocks = re.findall(r"@font-face\s*{(.*?)}", css, re.S)
    if not blocks:
        sys.exit(f"embed-fonts: no @font-face for {family} in {url}")
    by_src = {}   # Geist is a variable font: several weights come back as the same file
    for b in blocks:
        src = re.search(r"url\((https://[^)]+)\)\s*format\('woff2'\)", b)
        style = re.search(r"font-style:\s*(\w+)", b).group(1)
        weight = int(re.search(r"font-weight:\s*(\d+)", b).group(1))
        if not src:
            sys.exit(f"embed-fonts: no woff2 source for {family}")
        entry = by_src.setdefault((src.group(1), style), [])
        entry.append(weight)
    rules = []
    for (src, style), ws in by_src.items():
        data = base64.b64encode(fetch(src, binary=True)).decode("ascii")
        weight = str(ws[0]) if len(set(ws)) == 1 else f"{min(ws)} {max(ws)}"
        rules.append(f"@font-face {{ font-family: '{family}'; font-style: {style}; font-weight: {weight}; "
                     f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    return rules


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    with open(src, encoding="utf-8") as f:
        svg = f.read()
    if "data:font/woff2" in svg:
        sys.exit("embed-fonts: fonts are already embedded")
    rules = []
    for family, keyed in sorted(faces(svg).items()):
        chars = set().union(*keyed.values())
        rules += font_faces(family, list(keyed), chars)
    style = f"<style>/* {NOTICE} */\n" + "\n".join(rules) + "\n</style>\n"
    # Put the fonts first inside the existing <defs>, after <title> and <desc> (the accessible-name contract).
    if svg.count("<defs>") < 1:
        sys.exit("embed-fonts: no <defs> in the SVG")
    svg = svg.replace("<defs>", "<defs>\n" + style, 1)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{dst}: {len(rules)} font faces, {len(svg.encode('utf-8')) // 1024} KB")


if __name__ == "__main__":
    main()
