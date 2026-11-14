"""Convert the covers in a Calibre library into Kindle-ready screensavers."""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from xml.etree import ElementTree as ET

from pathvalidate import sanitize_filename
from PIL import Image, ImageOps

logger = logging.getLogger("kindle_covers")

METADATA_FILE_NAME = "metadata.opf"


class Status(str, Enum):
    converted = "converted"
    exists = "exists"
    failed = "failed"
    filtered = "filtered"
    deleted = "deleted"


class Namespace(str, Enum):
    dc = "http://purl.org/dc/elements/1.1/"
    opf = "http://www.idpf.org/2007/opf"


@dataclass
class MetadataColumn:
    name: str
    label: str | None
    value: str


@dataclass
class BookMetadata:
    title: str
    author: str
    cover: str
    columns: list[MetadataColumn]


def process_library(
    path: Path,
    outdir: Path,
    width: int,
    height: int,
    filter_column: str | None = None,
    filter_value: str | None = None,
    force: bool = False,
    clean: bool = False,
    border_color: str = "white",
) -> dict[Status, int]:
    outdir.mkdir(parents=True, exist_ok=True)
    library: set[Path] = set()
    summary = {status: 0 for status in Status}
    for metadata in path.rglob(METADATA_FILE_NAME):
        status = process_book(
            metadata,
            outdir,
            width,
            height,
            filter_column,
            filter_value,
            force,
            border_color,
            library,
        )
        summary[status] += 1
    if clean:
        summary[Status.deleted] += delete_covers_not_in_library(outdir, library)
    log_summary(summary)
    return summary


def delete_covers_not_in_library(outdir: Path, library: set[Path]) -> int:
    deleted = 0
    for path in outdir.glob("*.png"):
        if path not in library:
            path.unlink()
            deleted += 1
            logger.warning("Deleted unneeded cover: %s", path)
    return deleted


def log_summary(summary: dict[Status, int]) -> None:
    total = sum(n for status, n in summary.items() if status != Status.deleted)
    if summary[Status.failed]:
        logger.warning(
            "Warning! %d books failed to convert, see above for errors.",
            summary[Status.failed],
        )
    if summary[Status.deleted]:
        logger.warning(
            "Note! %d covers were no longer needed and were deleted.",
            summary[Status.deleted],
        )
    logger.info(
        "Summary: from a total of %d books, converted %d. There were %d that had "
        "been previously converted, and %d that were filtered.",
        total,
        summary[Status.converted],
        summary[Status.exists],
        summary[Status.filtered],
    )


def process_book(
    metadata_path: Path,
    outdir: Path,
    width: int,
    height: int,
    filter_column: str | None,
    filter_value: str | None,
    force: bool,
    border_color: str,
    library: set[Path],
) -> Status:
    try:
        metadata = read_metadata(metadata_path)
    except Exception as e:
        logger.warning("Failed to read metadata (%s) for book: %s", e, metadata_path)
        return Status.failed

    if filter_column and filter_value:
        if not filter_passes(metadata.columns, filter_column, filter_value):
            logger.info("Book failed filter, skipping: %s", metadata_path)
            return Status.filtered

    cover_path = metadata_path.parent / metadata.cover
    if not cover_path.exists():
        logger.warning("Failed to find cover for book: %s", metadata_path)
        return Status.failed

    output_path = outdir / format_name(metadata)

    if output_path.exists() and not force:
        library.add(output_path)
        logger.info("Cover already exists, skipping: %s", output_path)
        return Status.exists

    try:
        convert_cover(cover_path, output_path, width, height, border_color)
    except Exception as e:
        logger.warning("Failed to convert cover (%s) for book: %s", e, metadata_path)
        return Status.failed
    logger.info("Created %s", output_path)
    library.add(output_path)
    return Status.converted


def format_name(metadata: BookMetadata) -> str:
    return sanitize_filename(f"{metadata.author} - {metadata.title}.png")


def filter_passes(
    columns: list[MetadataColumn],
    filter_column: str,
    filter_value: str,
) -> bool:
    """Match a Calibre custom column by display name ("Read") or lookup name ("#read")."""
    for column in columns:
        names = {column.name}
        if column.label:
            names |= {column.label, f"#{column.label}"}
        if filter_column in names and filter_value == str(column.value):
            return True
    return False


def read_metadata(metadata_path: Path) -> BookMetadata:
    tree = ET.parse(metadata_path)

    title = get_text(tree, Namespace.dc, "title")
    author = get_text(tree, Namespace.dc, "creator")
    cover = get_attr(tree, Namespace.opf, "reference[@type='cover']", "href")

    # Calibre stores custom columns as JSON in <meta content="..."> elements.
    columns = []
    for content in get_all_attr(tree, Namespace.opf, "meta", "content"):
        try:
            data = json.loads(content)
            columns.append(
                MetadataColumn(data["name"], data.get("label"), data["#value#"])
            )
        except (ValueError, KeyError, TypeError):
            pass

    return BookMetadata(title, author, cover, columns)


def get_all_attr(
    tree: ET.ElementTree, namespace: Namespace, tag: str, attr: str
) -> list[str]:
    elems = tree.findall(get_tag_path(namespace, tag))
    return [v for elem in elems if (v := elem.attrib.get(attr))]


def get_text(tree: ET.ElementTree, namespace: Namespace, tag: str) -> str:
    text = get_tag(tree, namespace, tag).text
    if text is None:
        raise ValueError(f"Unable to find text in tag '{tag}'")
    return text


def get_attr(tree: ET.ElementTree, namespace: Namespace, tag: str, attr: str) -> str:
    value = get_tag(tree, namespace, tag).attrib.get(attr)
    if value is None:
        raise ValueError(f"Unable to find attribute '{attr}' in tag '{tag}'")
    return value


def get_tag(tree: ET.ElementTree, namespace: Namespace, tag: str) -> ET.Element:
    path = get_tag_path(namespace, tag)
    elem = tree.find(path)
    if elem is None:
        raise ValueError(f"Unable to find tag '{path}'")
    return elem


def get_tag_path(namespace: Namespace, tag: str) -> str:
    return ".//{%s}%s" % (namespace.value, tag)


def convert_cover(
    cover_path: Path,
    output_path: Path,
    width: int,
    height: int,
    border_color: str,
) -> None:
    with Image.open(cover_path) as cover:
        converted = process_cover(cover, width, height, border_color)
    converted.save(output_path)


def process_cover(
    image: Image.Image,
    width: int,
    height: int,
    border_color: str,
) -> Image.Image:
    """Scale to fit the screen, pad the rest with border_color, make grayscale."""
    result = ImageOps.pad(image.convert("RGB"), (width, height), color=border_color)
    return result.convert("L")
