"""A stand-in for PyMuPDF in the tests (tests/installer-tests.sh): a "PDF" is a text file, one line per page:
'P <text>' (an empty text is a scan). 'PASSWORD' asks for one, 'SLOW' takes a minute to open."""
import builtins
import time

__version__ = "2.1"


class _Tools:
    def mupdf_display_errors(self, on):
        pass

    def mupdf_display_warnings(self, on):
        pass


TOOLS = _Tools()


class Rect:
    def __init__(self, width, height):
        self.width, self.height = width, height


class Pixmap:
    def __init__(self, dpi):
        self.dpi = dpi

    def save(self, path):
        with builtins.open(path, "w") as f:
            f.write(f"PNG dpi={self.dpi}")


class Page:
    def __init__(self, text, width=612):
        self.text, self.rect = text, Rect(width, 792)

    def get_text(self):
        return self.text

    def get_pixmap(self, dpi=72):
        return Pixmap(dpi)

    def insert_text(self, pos, text):
        self.text += text


class Document:
    def __init__(self, pages=None, needs_pass=False):
        self.pages, self.needs_pass = pages or [], needs_pass

    @property
    def page_count(self):
        return len(self.pages)

    def __getitem__(self, i):
        return self.pages[i]

    def new_page(self):
        self.pages.append(Page(""))
        return self.pages[-1]

    def tobytes(self):
        return ("%PDF-1.7\n" + "".join(f"P {p.text}\n" for p in self.pages)).encode()


def open(path=None, filetype=None, stream=None):
    if path is None and stream is None:
        return Document()
    data = stream.decode() if stream is not None else builtins.open(path).read()
    if not data.startswith("%PDF-"):
        raise RuntimeError("not a PDF")
    if "SLOW" in data:
        time.sleep(60)
    pages = [Page(line[2:], 20000 if "WIDE" in line else 612) for line in data.splitlines() if line.startswith("P")]
    return Document(pages, "PASSWORD" in data)
