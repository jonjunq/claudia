#!/usr/bin/env python3
"""Generate the "how it works" diagram at the top of the README, in English and Spanish.

Drawn with the diagram-design skill (https://github.com/cathrynlavery/diagram-design, MIT): architecture type,
"faithful" detail level (10 pieces in three zones), the skill's editorial tokens plus one colour per kind of piece.

    python3 how-it-works.py [output-dir]

writes, for each language (`<lang>` is empty for English and `.es` for Spanish):

    how-it-works<lang>.html              the page published on GitHub Pages: light or dark following the
                                         reader's system, with a short summary under the diagram
    build/how-it-works-light[-es].html   one bare page per skin, the input of the skill's export_svg.py
    build/how-it-works-dark[-es].html

build.sh runs this, the skill's checks, the SVG export and embed-fonts.py.
"""
import html
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------------------------------------------
# Skins. The skill's semantic roles, plus one colour per kind of piece, in light and dark.
# ---------------------------------------------------------------------------------------------------------------
SKINS = {
    "light": {
        "paper": "#f5f5f5", "paper2": "#ececec", "card": "#ffffff", "ink": "#2d3142", "muted": "#4f5d75",
        "soft": "#5a6580", "accent": "#a21caf", "link": "#1d4ed8", "ink_rgb": (45, 49, 66),
        "acc_rgb": (162, 28, 175),
        # kind: (stroke, ink, tint)
        "kinds": {
            "frontend": ("#0891b2", "#0e718c", "rgba(34,211,238,0.16)"),
            "backend": ("#059669", "#047454", "rgba(52,211,153,0.18)"),
            "edge": ("#ea580c", "#b13b0b", "rgba(251,146,60,0.18)"),
            "store": ("#a16207", "#935906", "rgba(250,204,21,0.22)"),
            "security": ("#e11d48", "#be123c", "rgba(251,113,133,0.16)"),
            "async": ("#7c3aed", "#6d28d9", "rgba(167,139,250,0.18)"),
            "external": ("#64748b", "#475569", "rgba(148,163,184,0.18)"),
        },
    },
    "dark": {
        "paper": "#2d3142", "paper2": "#393e53", "card": "#393e53", "ink": "#f5f5f5", "muted": "#bfc0c0",
        "soft": "#a3acbf", "accent": "#ec8cf9", "link": "#7db6fc", "ink_rgb": (245, 245, 245),
        "acc_rgb": (236, 140, 249),
        "kinds": {
            "frontend": ("#22d3ee", "#67e8f9", "rgba(6,182,212,0.16)"),
            "backend": ("#34d399", "#6ee7b7", "rgba(16,185,129,0.16)"),
            "edge": ("#fb923c", "#fdba74", "rgba(249,115,22,0.16)"),
            "store": ("#facc15", "#fde047", "rgba(234,179,8,0.14)"),
            "security": ("#fb7185", "#fda4af", "rgba(244,63,94,0.16)"),
            "async": ("#a78bfa", "#c4b5fd", "rgba(139,92,246,0.18)"),
            "external": ("#94a3b8", "#cbd5e1", "rgba(100,116,139,0.24)"),
        },
    },
}
MONO = "'Geist Mono', ui-monospace, monospace"
SANS = "'Geist', system-ui, sans-serif"
SERIF = "'Instrument Serif', 'Noto Serif', serif"
FONT_LINK = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1"
             "&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&family=Noto+Serif:ital@0;1"
             "&display=swap")

ZONE_FILL = {1: 0.02, 2: 0.03}   # ink wash of a zone, by nesting depth


def rgba(rgb, a):
    return "rgba({},{},{},{})".format(*rgb, a)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def token(skin, name):
    """Colour of a named token in a skin. Names: roles, k.<kind>.<stroke|ink|tint|tagst>, mask.<depth>,
    zone.<depth>, zrule, rule, lead.accent."""
    s = SKINS[skin]
    if name in s and isinstance(s[name], str):
        return s[name]
    head, _, rest = name.partition(".")
    if head == "k":
        kind, part = rest.split(".")
        stroke, ink, tint = s["kinds"][kind]
        return {"stroke": stroke, "ink": ink, "tint": tint, "tagst": rgba(hex_rgb(stroke), 0.45)}[part]
    if head == "mask":   # paper with the zone washes of `depth` nested zones on top: opaque label plate
        r, g, b = hex_rgb(s["paper"])
        ir, ig, ib = s["ink_rgb"]
        for d in range(1, int(rest) + 1):
            o = ZONE_FILL[d]
            r, g, b = r + (ir - r) * o, g + (ig - g) * o, b + (ib - b) * o
        return "#%02x%02x%02x" % (round(r), round(g), round(b))
    if head == "zone":
        return rgba(s["ink_rgb"], ZONE_FILL[int(rest)])
    if name == "zrule":
        return rgba(s["ink_rgb"], 0.10)
    if name == "rule":
        return rgba(s["ink_rgb"], 0.12)
    if name == "lead.accent":
        return rgba(s["acc_rgb"], 0.50)
    raise KeyError(name)


class Painter:
    """Writes fill/stroke attributes for one skin. In "auto" mode it writes the light values and a class per
    token, and collects the dark values so the page can switch with prefers-color-scheme."""

    def __init__(self, skin):
        self.auto = skin == "auto"
        self.skin = "light" if self.auto else skin
        self.used = set()

    def __call__(self, fill=None, stroke=None):
        attrs, classes = [], []
        for prop, name in (("fill", fill), ("stroke", stroke)):
            if name is None:
                continue
            if name == "none":
                attrs.append(f'{prop}="none"')
                continue
            attrs.append(f'{prop}="{token(self.skin, name)}"')
            if self.auto:
                cls = prop[0] + "-" + name.replace(".", "-")
                classes.append(cls)
                self.used.add((cls, prop, name))
        if classes:
            attrs.append('class="{}"'.format(" ".join(classes)))
        return " ".join(attrs)

    def dark_css(self):
        return "\n".join(f"      .{cls} {{ {prop}: {token('dark', name)}; }}"
                         for cls, prop, name in sorted(self.used))


# ---------------------------------------------------------------------------------------------------------------
# Words. Everything that is text in the figure, per language.
# ---------------------------------------------------------------------------------------------------------------
TEXT = {
    "en": {
        "html_lang": "en",
        "page_title": "How the assistant fits together",
        "eyebrow": "Architecture · claudia",
        "subtitle": ("You chat with a Telegram bot. Behind it is one Claude Code session on a machine of yours, with "
                     "its notes and tools, and a few small helpers that keep it going."),
        "other_lang": ("Leer en castellano", "how-it-works.es.html"),
        "svg_title": "How the assistant fits together",
        "svg_desc": ("You chat on your phone with a Telegram bot, and the official channel plugin connects it to a "
                     "Claude Code session that runs in tmux, in auto mode, on your Claude subscription, on an "
                     "always-on machine of yours, set up as you like. The session reads and writes CLAUDE.md, its "
                     "notes and memory, runs voice and browser tools, and uses the Gmail, Calendar and Drive "
                     "connectors of claude.ai. Hooks on every tool call send its status and permission buttons to "
                     "Telegram. A nightly cycle saves the day, reviews memory, updates and restarts it. Optionally, "
                     "n8n alerts you directly when nothing needs thinking, and otherwise hands a one-line notice to "
                     "the wake-up, which types it into the session; the session builds n8n workflows through MCP."),
        "nodes": {
            "you": ("USER", "You", ["on your phone"]),
            "telegram": ("BOT", "Telegram", ["official channel plugin"]),
            "google": ("CLAUDE.AI", "Gmail · Calendar · Drive", ["connectors: read and draft"]),
            "session": ("SESSION", "Claude Code", ["in tmux · auto mode", "your Claude subscription"]),
            "memory": ("NOTES", "Notes and memory", ["CLAUDE.md · recall · history"]),
            "voice": ("SKILLS", "Voice and browser", ["Whisper · TTS · agent-browser"]),
            "daily": ("SYSTEMD · CRON", "Daily cycle", ["end of day · review · restart"]),
            "hooks": ("HOOKS", "Telegram hooks", ["status · permission buttons"]),
            "wakeup": ("DAEMON", "Wake-up", ["watches logs · POST /wake"]),
            "n8n": ("WORKFLOWS", "n8n", ["new email · page watches"]),
        },
        "labels": {
            "chat": "CHAT", "memory": "READS + WRITES", "voice": "RUNS", "daily": "EVERY NIGHT",
            "hooks": "TOOL EVENTS", "botapi": "BOT API", "wakeup": "TYPES A NOTICE", "mcp": "MCP",
            "think": "NEEDS THINKING", "alert": "ALERT TO YOU",
        },
        "zones": {
            "online": "ONLINE SERVICES",
            "machine": "AN ALWAYS-ON MACHINE OF YOURS",
            "optional": "OPTIONAL · NO TOKENS UNTIL SOMETHING HAPPENS",
        },
        "aside": "a container, a VM, a plain user or root: your call",
        "legend": "LEGEND",
        "kinds": [("external", "Person or outside service"), ("edge", "Messaging platform"),
                  ("backend", "Process"), ("store", "Notes"), ("security", "Permissions"),
                  ("async", "Notices and alerts")],
        "focus": "Focus: the session",
        "arrows": [("accent", "Main path"), ("link", "API call"), ("muted", "Internal"),
                   ("async", "Notice or alert (async)")],
        "cards": [
            ("external", "YOUR ACCOUNT", "Your plan, your machine",
             ["Unmodified Claude Code, signed in with your own subscription",
              "The Telegram allowlist only lets you in",
              "Its own container or VM, a user on a server you have, root on a machine of its own: the same files"]),
            ("security", "PERMISSIONS", "Asks before it acts",
             ["Reads and drafts run alone; sending and deleting ask you, with Allow / Deny buttons",
              "What the auto-mode classifier blocks can be approved once, from Telegram",
              "Payments are blocked outright"]),
            ("async", "ON ITS OWN", "Keeps itself going",
             ["Every night: save the day, review skills and memory, update Claude Code, fresh start",
              "n8n tells you directly what needs no thinking; the rest reaches the session as a notice"]),
        ],
        "footer": ("claudia · how it works", "drawn with diagram-design"),
    },
    "es": {
        "html_lang": "es",
        "page_title": "Cómo está montado el asistente",
        "eyebrow": "Arquitectura · claudia",
        "subtitle": ("Hablas con un bot de Telegram. Detrás hay una sesión de Claude Code en una máquina tuya, con sus "
                     "notas y herramientas, y unas pocas piezas pequeñas que la mantienen en marcha."),
        "other_lang": ("Read in English", "how-it-works.html"),
        "svg_title": "Cómo está montado el asistente",
        "svg_desc": ("Hablas desde el móvil con un bot de Telegram, y el plugin oficial de canal lo conecta con una "
                     "sesión de Claude Code que corre en tmux, en modo auto, con tu suscripción de Claude, en una "
                     "máquina tuya siempre encendida, montada como prefieras. La sesión lee y escribe CLAUDE.md, sus "
                     "notas y su memoria, usa herramientas de voz y de navegador, y los conectores de Gmail, Calendar "
                     "y Drive de claude.ai. Unos hooks en cada herramienta mandan a Telegram su estado y los botones "
                     "de permiso. Un ciclo nocturno guarda el día, repasa la memoria, actualiza y reinicia. Si "
                     "quieres, n8n te avisa directamente de lo que no hace falta pensar, y si no, pasa un aviso de "
                     "una línea al despertador, que lo escribe en la sesión; la sesión monta flujos de n8n por MCP."),
        "nodes": {
            "you": ("PERSONA", "Tú", ["en el móvil"]),
            "telegram": ("BOT", "Telegram", ["plugin oficial de canal"]),
            "google": ("CLAUDE.AI", "Gmail · Calendar · Drive", ["conectores: lee y redacta"]),
            "session": ("SESIÓN", "Claude Code", ["en tmux · modo auto", "tu suscripción de Claude"]),
            "memory": ("NOTAS", "Notas y memoria", ["CLAUDE.md · recall · historial"]),
            "voice": ("SKILLS", "Voz y navegador", ["Whisper · TTS · agent-browser"]),
            "daily": ("SYSTEMD · CRON", "Ciclo diario", ["cierre · repaso · reinicio"]),
            "hooks": ("HOOKS", "Hooks de Telegram", ["estado · botones de permiso"]),
            "wakeup": ("SERVICIO", "Despertador", ["vigila logs · POST /wake"]),
            "n8n": ("FLUJOS", "n8n", ["correo nuevo · vigilar webs"]),
        },
        "labels": {
            "chat": "CHAT", "memory": "LEE Y ESCRIBE", "voice": "EJECUTA", "daily": "CADA NOCHE",
            "hooks": "EVENTOS", "botapi": "API DEL BOT", "wakeup": "ESCRIBE AVISO", "mcp": "MCP",
            "think": "HAY QUE PENSAR", "alert": "AVISO PARA TI",
        },
        "zones": {
            "online": "SERVICIOS EN LÍNEA",
            "machine": "UNA MÁQUINA TUYA SIEMPRE ENCENDIDA",
            "optional": "OPCIONAL · SIN TOKENS HASTA QUE PASA ALGO",
        },
        "aside": "un contenedor, una VM, un usuario o root: tú eliges",
        "legend": "LEYENDA",
        "kinds": [("external", "Persona o servicio externo"), ("edge", "Plataforma de mensajería"),
                  ("backend", "Proceso"), ("store", "Notas"), ("security", "Permisos"),
                  ("async", "Avisos y alertas")],
        "focus": "Foco: la sesión",
        "arrows": [("accent", "Ruta principal"), ("link", "Llamada a API"), ("muted", "Interna"),
                   ("async", "Aviso o alerta (asíncrono)")],
        "cards": [
            ("external", "TU CUENTA", "Tu plan, tu máquina",
             ["Claude Code sin modificar, con tu propia suscripción",
              "La lista blanca de Telegram solo te deja entrar a ti",
              "En su propio contenedor o VM, como usuario de un servidor que ya tienes o como root de una máquina "
              "solo para él: los mismos ficheros"]),
            ("security", "PERMISOS", "Pregunta antes de actuar",
             ["Leer y redactar lo hace solo; enviar y borrar te lo pregunta, con botones Permitir / Denegar",
              "Lo que bloquea el clasificador del modo auto se puede aprobar una vez desde Telegram",
              "Los pagos están bloqueados del todo"]),
            ("async", "POR SU CUENTA", "Se mantiene solo",
             ["Cada noche: guarda el día, repasa skills y memoria, actualiza Claude Code y empieza de cero",
              "n8n te avisa directamente de lo que no hace falta pensar; lo demás llega a la sesión como aviso"]),
        ],
        "footer": ("claudia · cómo funciona", "dibujado con diagram-design"),
    },
}

# ---------------------------------------------------------------------------------------------------------------
# Geometry. Everything on the 4px grid.
# ---------------------------------------------------------------------------------------------------------------
W, H = 1000, 776
NH = 64
NODES = {   # id: (x, y, w, h, kind)
    "you": (40, 264, 120, NH, "external"),
    "google": (216, 112, 184, NH, "external"),
    "telegram": (216, 264, 184, NH, "edge"),
    "memory": (456, 112, 192, NH, "store"),
    "session": (456, 240, 192, 128, "backend"),
    "hooks": (456, 432, 192, NH, "security"),
    "n8n": (456, 560, 192, NH, "async"),
    "voice": (744, 112, 192, NH, "backend"),
    "daily": (744, 256, 192, NH, "backend"),
    "wakeup": (744, 560, 192, NH, "async"),
}
FOCAL = {"session"}
ZONES = [   # (x, y, w, h, key, depth)
    (204, 80, 208, 264, "online", 1),
    (432, 80, 528, 568, "machine", 1),
    (444, 528, 504, 108, "optional", 2),
]
# Connectors: (points, style). Points are the corners of an orthogonal route; corners are rounded at r=8.
ROUTES = {
    "chat": ([(160, 296), (216, 296)], "accent"),
    "channel": ([(400, 296), (456, 296)], "accent"),
    "memory": ([(552, 240), (552, 176)], "muted"),
    "google": ([(456, 256), (424, 256), (424, 144), (400, 144)], "link"),
    "voice": ([(648, 256), (680, 256), (680, 144), (744, 144)], "muted"),
    "daily": ([(744, 288), (648, 288)], "async"),
    "hooks": ([(552, 368), (552, 432)], "muted"),
    "botapi": ([(456, 464), (344, 464), (344, 328)], "link"),
    "wakeup": ([(792, 560), (792, 336), (648, 336)], "async"),
    "mcp": ([(648, 352), (712, 352), (712, 576), (648, 576)], "link"),
    "think": ([(648, 600), (744, 600)], "async"),
    "alert": ([(456, 600), (272, 600), (272, 328)], "async"),
}
# Arrow labels: route key -> (x, y, anchor, depth of zones under the plate). anchor "c" centres the plate on x,
# "l" puts its left edge at x. y is the top of the 12px plate.
LABELS = {
    "chat": (186, 278, "c", 0),
    "memory": (560, 202, "l", 1),
    "voice": (712, 126, "c", 1),
    "daily": (696, 270, "c", 1),
    "hooks": (560, 394, "l", 1),
    "botapi": (384, 446, "c", 0),
    "wakeup": (800, 440, "l", 1),
    "mcp": (672, 440, "l", 1),
    "think": (696, 606, "c", 2),
    "alert": (352, 582, "c", 0),
}
LEGEND_Y = 680


def mono_w(text, size=8, track=0.06, pad=12):
    w = len(text) * (0.62 * size + track * size) + pad
    return int((w + 3) // 4 * 4)


def rounded(points, r=8):
    """Orthogonal polyline with rounded corners, as an SVG path."""
    d = [f"M {points[0][0]},{points[0][1]}"]
    for i in range(1, len(points)):
        x, y = points[i]
        px, py = points[i - 1]
        if i == len(points) - 1:
            d.append(f"H {x}" if y == py else f"V {y}")
            break
        nx, ny = points[i + 1]
        # stop r before the corner, curve through it, continue r after it
        if y == py:   # horizontal into the corner
            sx = x - r if x > px else x + r
            ey = y + r if ny > y else y - r
            d.append(f"H {sx} Q {x},{y} {x},{ey}")
        else:          # vertical into the corner
            sy = y - r if y > py else y + r
            ex = x + r if nx > x else x - r
            d.append(f"V {sy} Q {x},{y} {ex},{y}")
    return " ".join(d)


def check_geometry():
    for nid, (x, y, w, h, _) in NODES.items():
        assert all(v % 4 == 0 for v in (x, y, w, h)), nid
    for key, (pts, _) in ROUTES.items():
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            assert ax == bx or ay == by, f"{key}: diagonal segment"


def svg(lang, skin, slug):
    T = TEXT[lang]
    p = Painter(skin)
    out = []
    a = out.append
    a(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
      f'aria-labelledby="{slug}-title {slug}-desc">')
    a(f'<title id="{slug}-title">{html.escape(T["svg_title"])}</title>')
    a(f'<desc id="{slug}-desc">{html.escape(T["svg_desc"])}</desc>')
    a('<defs>')
    for mid, tok in (("arrow", "muted"), ("arrow-accent", "accent"), ("arrow-link", "link"),
                     ("arrow-async", "k.async.stroke")):
        a(f'<marker id="{mid}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
          f'<polygon points="0 0, 8 3, 0 6" {p(fill=tok)}/></marker>')
    a('</defs>')
    a(f'<rect width="100%" height="100%" {p(fill="paper")}/>')

    # Zones first, then connectors, labels, nodes (paint order of the skill).
    a('<!-- Zones -->')
    for x, y, w, h, key, depth in ZONES:
        text = T["zones"][key]
        lw = mono_w(text, size=7, track=0.14, pad=12)
        assert lw <= w - 24, f"zone label too wide: {text}"
        a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" {p(fill=f"zone.{depth}", stroke="zrule")} '
          f'stroke-width="0.8"/>')
        a(f'<rect x="{x + 12}" y="{y + 4}" width="{lw}" height="12" rx="2" {p(fill=f"mask.{depth}")}/>')
        a(f'<text x="{x + 12 + lw // 2}" y="{y + 13}" {p(fill="soft")} font-size="7" font-family="{MONO}" '
          f'text-anchor="middle" letter-spacing="0.14em">{html.escape(text)}</text>')

    a('<!-- Connectors -->')
    for key, (pts, style) in ROUTES.items():
        d = rounded(pts)
        if style == "accent":
            a(f'<path d="{d}" {p(fill="none", stroke="accent")} stroke-width="1.4" marker-end="url(#arrow-accent)"/>')
        elif style == "link":
            a(f'<path d="{d}" {p(fill="none", stroke="link")} stroke-width="1.2" marker-end="url(#arrow-link)"/>')
        elif style == "async":
            a(f'<path d="{d}" {p(fill="none", stroke="k.async.stroke")} stroke-width="1.2" '
              f'stroke-dasharray="5,4" marker-end="url(#arrow-async)"/>')
        else:
            a(f'<path d="{d}" {p(fill="none", stroke="muted")} stroke-width="1.2" marker-end="url(#arrow)"/>')

    a('<!-- Connector labels -->')
    colour = {"accent": "accent", "link": "link", "async": "k.async.ink", "muted": "soft"}
    for key, (x, y, anchor, depth) in LABELS.items():
        text = T["labels"][key]
        w = mono_w(text)
        left = x - w // 2 if anchor == "c" else x
        a(f'<rect x="{left}" y="{y}" width="{w}" height="12" rx="2" {p(fill=f"mask.{depth}")}/>')
        a(f'<text x="{left + w // 2}" y="{y + 9}" {p(fill=colour[ROUTES[key][1]])} font-size="8" '
          f'font-family="{MONO}" text-anchor="middle" letter-spacing="0.06em">{html.escape(text)}</text>')

    a('<!-- Nodes -->')
    for nid, (x, y, w, h, kind) in NODES.items():
        tag, name, subs = T["nodes"][nid]
        focal = nid in FOCAL
        tw = mono_w(tag, size=7, track=0.08, pad=8)
        cx = x + w // 2
        assert len(name) * 7.2 <= w - 8 or name.startswith("Gmail"), f"name too long: {name}"
        for s in subs:
            assert len(s) * 5.58 <= w - 12, f"sublabel too long: {s}"
        a(f'<!-- {html.escape(name)}{" (focus)" if focal else ""} -->')
        a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" {p(fill="paper")}/>')
        a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" {p(fill=f"k.{kind}.tint", stroke=f"k.{kind}.stroke")} '
          f'stroke-width="{"1.8" if focal else "1"}"/>')
        if focal:
            a(f'<rect x="{x + 8}" y="{y + 6}" width="{tw}" height="12" rx="2" '
              f'{p(fill=f"k.{kind}.ink", stroke=f"k.{kind}.ink")} stroke-width="0.8"/>')
            a(f'<text x="{x + 8 + tw // 2}" y="{y + 15}" {p(fill="paper")} font-size="7" font-family="{MONO}" '
              f'font-weight="600" text-anchor="middle" letter-spacing="0.08em">{html.escape(tag)}</text>')
        else:
            a(f'<rect x="{x + 8}" y="{y + 6}" width="{tw}" height="12" rx="2" '
              f'{p(fill="none", stroke=f"k.{kind}.tagst")} stroke-width="0.8"/>')
            a(f'<text x="{x + 8 + tw // 2}" y="{y + 15}" {p(fill=f"k.{kind}.ink")} font-size="7" '
              f'font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{html.escape(tag)}</text>')
        # name + sublabels, centred in the box below the tag strip
        block = 14 + 16 * len(subs)
        top = y + 20 + (h - 20 - block) // 2
        a(f'<text x="{cx}" y="{top + 12}" {p(fill="ink")} font-size="12" font-weight="600" font-family="{SANS}" '
          f'text-anchor="middle">{html.escape(name)}</text>')
        for i, s in enumerate(subs):
            a(f'<text x="{cx}" y="{top + 28 + 16 * i}" {p(fill="muted")} font-size="9" font-family="{MONO}" '
              f'text-anchor="middle">{html.escape(s)}</text>')

    a('<!-- Aside -->')
    a(f'<text x="936" y="52" {p(fill="accent")} font-size="14" font-style="italic" font-family="{SERIF}" '
      f'text-anchor="end">{html.escape(T["aside"])}</text>')
    a(f'<path d="M 900 60 Q 904 72 896 80" {p(fill="none", stroke="lead.accent")} stroke-width="1" '
      f'stroke-dasharray="4,3"/>')
    a(f'<circle cx="896" cy="80" r="2" {p(fill="accent")}/>')

    a('<!-- Legend -->')
    ly = LEGEND_Y
    a(f'<line x1="40" y1="{ly - 8}" x2="{W - 40}" y2="{ly - 8}" {p(stroke="zrule")} stroke-width="0.8"/>')
    a(f'<text x="40" y="{ly + 8}" {p(fill="muted")} font-size="8" font-family="{MONO}" '
      f'letter-spacing="0.18em">{T["legend"]}</text>')

    def advance(x, text):
        return x + 24 + int(len(text) * 4.6) + 28

    x, row = 40, ly + 20
    for kind, text in T["kinds"]:
        a(f'<rect x="{x}" y="{row}" width="14" height="10" rx="2" {p(fill="paper")}/>')
        a(f'<rect x="{x}" y="{row}" width="14" height="10" rx="2" {p(fill=f"k.{kind}.tint", stroke=f"k.{kind}.stroke")} '
          f'stroke-width="1"/>')
        a(f'<text x="{x + 20}" y="{row + 8}" {p(fill="muted")} font-size="8.5" font-family="{SANS}">'
          f'{html.escape(text)}</text>')
        x = advance(x, text)
    a(f'<rect x="{x}" y="{row}" width="14" height="10" rx="2" {p(fill="none", stroke="ink")} stroke-width="1.8"/>')
    a(f'<rect x="{x + 2}" y="{row + 2}" width="5" height="3" rx="0.5" {p(fill="ink")}/>')
    a(f'<text x="{x + 20}" y="{row + 8}" {p(fill="muted")} font-size="8.5" font-family="{SANS}">'
      f'{html.escape(T["focus"])}</text>')
    x = advance(x, T["focus"])
    assert x - 28 <= W - 40, f"legend row 1 too wide: {x}"
    x, row = 40, ly + 44
    for style, text in T["arrows"]:
        d = f"M {x},{row + 5} H {x + 28}"
        if style == "accent":
            a(f'<path d="{d}" {p(fill="none", stroke="accent")} stroke-width="1.4" marker-end="url(#arrow-accent)"/>')
        elif style == "link":
            a(f'<path d="{d}" {p(fill="none", stroke="link")} stroke-width="1.2" marker-end="url(#arrow-link)"/>')
        elif style == "async":
            a(f'<path d="{d}" {p(fill="none", stroke="k.async.stroke")} stroke-width="1.2" stroke-dasharray="5,4" '
              f'marker-end="url(#arrow-async)"/>')
        else:
            a(f'<path d="{d}" {p(fill="none", stroke="muted")} stroke-width="1.2" marker-end="url(#arrow)"/>')
        a(f'<text x="{x + 36}" y="{row + 8}" {p(fill="muted")} font-size="8.5" font-family="{SANS}">'
          f'{html.escape(text)}</text>')
        x += 36 + int(len(text) * 4.6) + 28
    assert x - 28 <= W - 40, f"legend row 2 too wide: {x}"
    a('</svg>')
    return "\n".join(out), p


def bare_page(lang, skin):
    """A minimal page around one skin's SVG: the input of export_svg.py."""
    slug = f"how-it-works-{skin}{'' if lang == 'en' else '-es'}"
    body, _ = svg(lang, skin, slug)
    s = SKINS[skin]
    return f'''<!DOCTYPE html>
<html lang="{TEXT[lang]["html_lang"]}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(TEXT[lang]["page_title"])}</title>
  <link href="{html.escape(FONT_LINK)}" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: {SANS}; background: {s["paper"]}; color: {s["ink"]}; padding: 2rem; }}
    .diagram-container {{ width: 100%; overflow-x: auto; }}
    svg {{ width: 100%; min-width: {W}px; display: block; }}
    @media print {{
      .diagram-container {{ overflow-x: visible; }}
      svg {{ min-width: 0; }}
    }}
  </style>
</head>
<body>
  <div class="diagram-container">
{body}
  </div>
</body>
</html>
'''


def full_page(lang):
    """The page published on GitHub Pages: header, the diagram (light or dark following the system), summary."""
    T = TEXT[lang]
    slug = f"how-it-works{'' if lang == 'en' else '-es'}"
    body, painter = svg(lang, "auto", slug)
    L, D = SKINS["light"], SKINS["dark"]
    cards = []
    for kind, eyebrow, title, items in T["cards"]:
        lis = "".join(f"<li>{html.escape(i)}</li>" for i in items)
        cards.append(f'<div class="card"><p class="card-eyebrow">{eyebrow}</p><div class="card-header">'
                     f'<span class="card-dot {kind}"></span><h3>{html.escape(title)}</h3></div><ul>{lis}</ul></div>')
    other_text, other_href = T["other_lang"]

    def dots(skin):
        return " ".join(f".card-dot.{k} {{ background: {SKINS[skin]['kinds'][k][0]}; }}"
                        for k in ("external", "security", "async"))

    return f'''<!DOCTYPE html>
<html lang="{T["html_lang"]}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <title>{html.escape(T["page_title"])}</title>
  <link href="{html.escape(FONT_LINK)}" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --paper: {L["paper"]}; --card: {L["card"]}; --ink: {L["ink"]}; --muted: {L["muted"]}; --soft: {L["soft"]};
      --rule: {token("light", "rule")}; --link: {L["link"]};
      --font-sans: {SANS}; --font-serif: {SERIF}; --font-mono: {MONO};
    }}
    body {{ font-family: var(--font-sans); background: var(--paper); color: var(--ink); min-height: 100vh;
            padding: 3rem 2rem; }}
    .container {{ max-width: 1080px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; }}
    .header-eyebrow {{ font-family: var(--font-mono); font-size: 0.66rem; font-weight: 500; letter-spacing: 0.18em;
                       text-transform: uppercase; color: var(--muted); margin-bottom: 0.75rem;
                       display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }}
    .header-eyebrow a {{ color: var(--link); text-decoration: none; letter-spacing: 0.06em; text-transform: none; }}
    .header-eyebrow a:hover {{ text-decoration: underline; }}
    h1 {{ font-family: var(--font-serif); font-size: clamp(1.75rem, 3vw + 1rem, 2.5rem); font-weight: 400;
          letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 0.5rem; }}
    .subtitle {{ font-size: 1rem; line-height: 1.55; color: var(--muted); max-width: 70ch; }}
    .diagram-container {{ width: 100%; overflow-x: auto; }}
    svg {{ width: 100%; min-width: {W}px; display: block; }}
    .cards {{ display: grid; grid-template-columns: 1.1fr 1fr 0.9fr; gap: 1rem; margin-top: 1.5rem; }}
    @media (max-width: 820px) {{ .cards {{ grid-template-columns: 1fr; }} }}
    .card {{ background: var(--card); border-radius: 6px; border: 1px solid var(--rule); padding: 1.25rem; }}
    .card-eyebrow {{ font-family: var(--font-mono); font-size: 0.55rem; letter-spacing: 0.18em; text-transform: uppercase;
                     color: var(--muted); margin-bottom: 0.5rem; }}
    .card-header {{ display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.875rem; padding-bottom: 0.875rem;
                    border-bottom: 1px solid var(--rule); }}
    .card-dot {{ width: 7px; height: 7px; border-radius: 50%; flex: none; }}
    {dots("light")}
    .card h3 {{ font-size: 0.875rem; font-weight: 600; letter-spacing: -0.005em; }}
    .card ul {{ color: var(--muted); font-size: 0.8125rem; line-height: 1.55; list-style: none; }}
    .card li {{ margin-bottom: 0.3rem; padding-left: 0.875rem; position: relative; }}
    .card li::before {{ content: '—'; position: absolute; left: 0; color: var(--soft); font-size: 0.75rem; }}
    .footer {{ margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--rule); font-family: var(--font-mono);
               font-size: 0.72rem; letter-spacing: 0.06em; color: var(--soft); display: flex;
               justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --paper: {D["paper"]}; --card: {D["card"]}; --ink: {D["ink"]}; --muted: {D["muted"]}; --soft: {D["soft"]};
        --rule: {token("dark", "rule")}; --link: {D["link"]};
      }}
      {dots("dark")}
{painter.dark_css()}
    }}
    @media print {{
      .diagram-container {{ overflow-x: visible; }}
      svg {{ min-width: 0; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <p class="header-eyebrow"><span>{html.escape(T["eyebrow"])}</span><a href="{other_href}">{other_text}</a></p>
      <h1>{html.escape(T["page_title"])}</h1>
      <p class="subtitle">{html.escape(T["subtitle"])}</p>
    </div>
    <div class="diagram-container">
{body}
    </div>
    <div class="cards">{"".join(cards)}</div>
    <div class="footer"><span>{html.escape(T["footer"][0])}</span><span>{html.escape(T["footer"][1])}</span></div>
  </div>
</body>
</html>
'''


def main():
    check_geometry()
    os.makedirs(os.path.join(OUT, "build"), exist_ok=True)
    for lang, suffix in (("en", ""), ("es", ".es")):
        with open(os.path.join(OUT, f"how-it-works{suffix}.html"), "w", encoding="utf-8") as f:
            f.write(full_page(lang))
        for skin in ("light", "dark"):
            name = f"how-it-works-{skin}{'' if lang == 'en' else '-es'}.html"
            with open(os.path.join(OUT, "build", name), "w", encoding="utf-8") as f:
                f.write(bare_page(lang, skin))
    print("written to", OUT)


if __name__ == "__main__":
    main()
