#!/usr/bin/env python3
"""pdf-read: the text of a PDF as Markdown, page by page, for the assistant to read (docs/setup.md, capability pdf).

    python3 -I pdf-read.py <file.pdf>                      the first pages (up to --max-pages), as Markdown
    python3 -I pdf-read.py <file.pdf> --pages 1-3,7        only those pages (counted from 1)
    python3 -I pdf-read.py <file.pdf> --images DIR         also a PNG of each page with no text (a scan), in DIR,
                                                           to look at with Read
    python3 -I pdf-read.py <file.pdf> --images DIR --every-page   a PNG of every page asked for, text or not
    options: --max-pages N (default 30, at most 200), --dpi N (default 110), --timeout S (default 120)

It runs PyMuPDF and pymupdf4llm from their venv (~/pdf, or PDF_VENV), in a child process with a time limit, a CPU
limit and a cap on what it may write. A PDF is untrusted data: this only reads its text and draws its pages; links,
JavaScript, attachments, forms and anything else in it are never opened, run or followed, and it writes nothing but
the PNGs in DIR. Files over 200 MB, or that are not PDFs, are refused. Exit code 0 when it read something.
"""
import os
import re
import subprocess
import sys

MAX_MB = 200
MAX_PAGES = 200
MAX_OUT = 400_000           # characters of Markdown printed at most
MAX_PX = 4000               # longest side of a PNG
HERE = os.path.realpath(__file__)


def die(msg, code=2):
    print("pdf-read: " + msg, file=sys.stderr)
    sys.exit(code)


def parse_pages(spec, count, limit):
    """'1-3,7' -> [0, 1, 2, 6] (0-based, in order, once each, only pages that exist), at most limit of them."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)(?:-(\d+|end))?", part)
        if not m:
            die(f"--pages: '{part}' is not a page or a range (1-3,7)")
        a = int(m.group(1))
        b = count if m.group(2) == "end" else int(m.group(2) or a)
        if a < 1 or b < a:
            die(f"--pages: '{part}' is not a range of pages counted from 1")
        for p in range(a, min(b, count) + 1):
            if p - 1 not in out:
                out.append(p - 1)
            if len(out) >= limit:
                return out
    return out


def args():
    a = sys.argv[1:]
    o = {"file": None, "pages": None, "images": None, "every": False, "max": 30, "dpi": 110, "timeout": 120}
    i = 0
    while i < len(a):
        x = a[i]
        if x in ("--pages", "--images", "--max-pages", "--dpi", "--timeout"):
            if i + 1 >= len(a):
                die(x + " needs a value")
            v = a[i + 1]
            i += 2
            if x == "--pages":
                o["pages"] = v
            elif x == "--images":
                o["images"] = v
            else:
                if not v.isdigit():
                    die(x + " takes a number")
                o[{"--max-pages": "max", "--dpi": "dpi", "--timeout": "timeout"}[x]] = int(v)
        elif x == "--every-page":
            o["every"] = True
            i += 1
        elif x in ("-h", "--help"):
            print(__doc__.strip())
            sys.exit(0)
        elif x.startswith("-") and x != "-":
            die("unknown option " + x)
        elif o["file"] is None:
            o["file"] = x
            i += 1
        else:
            die("one PDF at a time")
    if not o["file"]:
        die("which PDF? pdf-read.py <file.pdf> [--pages 1-3] [--images DIR]")
    o["max"] = max(1, min(o["max"], MAX_PAGES))
    o["dpi"] = max(50, min(o["dpi"], 200))
    o["timeout"] = max(5, min(o["timeout"], 600))
    if o["every"] and not o["images"]:
        die("--every-page goes with --images DIR")
    return o


def check_file(path):
    try:
        st = os.stat(path)
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    if not os.path.isfile(path):
        die(path + " is not a regular file")
    if st.st_size > MAX_MB * 1024 * 1024:
        die(f"{path} is {st.st_size // 1048576} MB; at most {MAX_MB} MB")
    with open(path, "rb") as f:
        head = f.read(1024)
    if b"%PDF-" not in head:
        die(path + " is not a PDF (no %PDF- header)")


def venv_python():
    venv = os.environ.get("PDF_VENV") or os.path.expanduser("~/pdf")
    py = os.path.join(venv, "bin", "python")
    if not os.access(py, os.X_OK):
        die(f"no PDF reader in {venv}: assistant-setup install pdf", 3)
    return py


def limits(timeout):
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout + 5))
    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024,) * 2)   # no file it writes grows past 100 MB
    os.setsid()


def parent():
    o = args()
    check_file(o["file"])
    if o["images"]:
        os.makedirs(o["images"], mode=0o700, exist_ok=True)
        if not os.path.isdir(o["images"]):
            die(o["images"] + " is not a folder")
    cmd = [venv_python(), "-I", HERE, "--worker"] + sys.argv[1:]
    # A clean environment: no proxies, no Python paths, nothing the PDF could use to reach anything.
    env = {"PATH": "/usr/bin:/bin", "HOME": os.path.expanduser("~"), "LANG": "C.UTF-8",
           "OMP_NUM_THREADS": "2", "PDF_READ_WORKER": "1"}
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=o["timeout"], env=env,
                           preexec_fn=lambda: limits(o["timeout"]))
    except subprocess.TimeoutExpired:
        die(f"stopped after {o['timeout']} s (a very heavy or broken PDF): try fewer pages with --pages", 4)
    out = p.stdout.decode("utf-8", "replace")
    if len(out) > MAX_OUT:
        out = out[:MAX_OUT] + f"\n\n[pdf-read: cut at {MAX_OUT} characters: ask for fewer pages with --pages]\n"
    sys.stdout.write(out)
    err = p.stderr.decode("utf-8", "replace").strip()
    if p.returncode < 0:
        die(f"stopped by signal {-p.returncode} (too much CPU or output): try fewer pages with --pages", 4)
    # onnxruntime (pymupdf4llm's layout model) complains in containers that it cannot pin its threads: harmless.
    err = "\n".join(ln for ln in err.splitlines() if "pthread_setaffinity_np" not in ln).strip()
    if err:
        print(err[-2000:], file=sys.stderr)
    return p.returncode


def worker():
    sys.argv.remove("--worker")
    o = args()
    import pymupdf
    try:
        import pymupdf4llm
    except Exception:   # the plain text still works without it
        pymupdf4llm = None
    try:
        pymupdf.TOOLS.mupdf_display_errors(False)
        pymupdf.TOOLS.mupdf_display_warnings(False)
    except Exception:
        pass
    try:
        doc = pymupdf.open(o["file"], filetype="pdf")
    except Exception as e:
        die("cannot open it as a PDF: " + str(e)[:200])
    if doc.needs_pass:
        die("it is protected with a password", 5)
    n = doc.page_count
    if n == 0:
        die("it has no pages")
    pages = parse_pages(o["pages"] or f"1-{n}", n, o["max"])
    if not pages:
        die(f"it has {n} pages; none of those")
    asked = len(parse_pages(o["pages"] or f"1-{n}", n, MAX_PAGES * 100))
    md = {}
    if pymupdf4llm:
        try:
            chunks = pymupdf4llm.to_markdown(doc, pages=pages, page_chunks=True, use_ocr=False, write_images=False,
                                             embed_images=False, show_progress=False)
            for ch in chunks:
                num = (ch.get("metadata") or {}).get("page_number") or (ch.get("metadata") or {}).get("page")
                if isinstance(num, int):
                    md[num - 1] = ch.get("text") or ""
        except Exception as e:
            print("pdf-read: Markdown failed (" + str(e)[:120] + "); plain text instead", file=sys.stderr)
            md = {}
    scanned = []
    print(f"# {os.path.basename(o['file'])} · {n} page{'s' if n != 1 else ''}"
          + (f" · pages {', '.join(str(p + 1) for p in pages)}" if len(pages) < n else ""))
    for p in pages:
        page = doc[p]
        plain = page.get_text().strip()
        text = (md.get(p) or "").strip() or plain
        print(f"\n## Page {p + 1}\n")
        if len(re.sub(r"\s", "", plain)) < 8:
            scanned.append(p)
            print("[no text on this page: probably a scan or a picture"
                  + (": see the image below]" if o["images"] else ": run again with --images DIR and look at it]"))
        else:
            print(text)
        if o["images"] and (o["every"] or p in scanned):
            r = page.rect
            dpi = o["dpi"]
            side = max(r.width, r.height) / 72 * dpi
            if side > MAX_PX:
                dpi = max(20, int(dpi * MAX_PX / side))
            png = os.path.join(o["images"], f"page-{p + 1}.png")
            page.get_pixmap(dpi=dpi).save(png)
            print(f"[image of page {p + 1}: {png}]")
    if asked > len(pages):
        print(f"\n[pdf-read: {asked - len(pages)} more page(s) not shown (at most {o['max']} at a time): use --pages]")
    if scanned and len(scanned) == len(pages):
        print("\n[pdf-read: no page had text: a scanned document; read the images]")
    return 0


if __name__ == "__main__":
    if "--worker" in sys.argv[1:] and os.environ.get("PDF_READ_WORKER") == "1":
        sys.exit(worker())
    sys.exit(parent())
