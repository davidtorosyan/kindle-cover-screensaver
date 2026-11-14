import json
from pathlib import Path

import pytest
from PIL import Image

OPF_TEMPLATE = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{title}</dc:title>
        <dc:creator opf:file-as="{author}" opf:role="aut">{author}</dc:creator>
        <meta name="calibre:user_metadata:#read" content="{read_json}"/>
    </metadata>
    <guide>
        <reference type="cover" title="Cover" href="cover.jpg"/>
    </guide>
</package>
"""


def add_book(
    library: Path,
    author: str,
    title: str,
    read: bool,
    size: tuple[int, int] = (400, 600),
) -> Path:
    """Create a minimal book folder the way Calibre lays it out."""
    book = library / author / f"{title} (1)"
    book.mkdir(parents=True)
    read_json = json.dumps(
        {"name": "Read", "label": "read", "datatype": "bool", "#value#": read}
    ).replace('"', "&quot;")
    (book / "metadata.opf").write_text(
        OPF_TEMPLATE.format(title=title, author=author, read_json=read_json),
        encoding="utf-8",
    )
    Image.new("RGB", size, "red").save(book / "cover.jpg")
    return book


@pytest.fixture
def library(tmp_path: Path) -> Path:
    lib = tmp_path / "library"
    add_book(lib, "Ursula K. Le Guin", "A Wizard of Earthsea", read=True)
    add_book(lib, "Ted Chiang", "Exhalation", read=True, size=(1200, 600))
    add_book(lib, "Frank Herbert", "Dune", read=False)
    return lib
