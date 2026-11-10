"""A stand-in for pymupdf4llm in the tests: Markdown is the page's text in bold."""


def to_markdown(doc, pages=None, page_chunks=False, **kw):
    pages = range(doc.page_count) if pages is None else pages
    chunks = [{"metadata": {"page_number": p + 1}, "text": f"**{doc[p].text}**" if doc[p].text else ""} for p in pages]
    return chunks if page_chunks else "\n".join(c["text"] for c in chunks)
