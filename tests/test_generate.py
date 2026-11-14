from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from kindle_covers.cli import app
from kindle_covers.generate import Status, process_library

runner = CliRunner()


def test_converts_all_books(library: Path, tmp_path: Path) -> None:
    out = tmp_path / "covers"
    summary = process_library(library, out, 758, 1024)

    assert summary[Status.converted] == 3
    names = sorted(p.name for p in out.glob("*.png"))
    assert names == [
        "Frank Herbert - Dune.png",
        "Ted Chiang - Exhalation.png",
        "Ursula K. Le Guin - A Wizard of Earthsea.png",
    ]
    with Image.open(out / "Ted Chiang - Exhalation.png") as img:
        assert img.size == (758, 1024)
        assert img.mode == "L"


def test_wide_cover_is_padded_with_border_color(library: Path, tmp_path: Path) -> None:
    out = tmp_path / "covers"
    process_library(library, out, 758, 1024, border_color="black")
    with Image.open(out / "Ted Chiang - Exhalation.png") as img:
        assert img.getpixel((0, 0)) == 0  # black border at the top
        assert img.getpixel((379, 512)) != 0  # cover in the middle


def test_filter_by_display_name_or_lookup_name(library: Path, tmp_path: Path) -> None:
    for column in ("Read", "#read"):
        out = tmp_path / column
        summary = process_library(library, out, 758, 1024, column, "True")
        assert summary[Status.converted] == 2
        assert summary[Status.filtered] == 1


def test_second_run_skips_and_clean_removes(library: Path, tmp_path: Path) -> None:
    out = tmp_path / "covers"
    process_library(library, out, 758, 1024)
    (out / "Someone - Removed Book.png").write_bytes(b"")

    summary = process_library(library, out, 758, 1024, "Read", "True", clean=True)

    assert summary[Status.exists] == 2
    assert summary[Status.deleted] == 2  # Dune (now filtered) + the stray file
    assert len(list(out.glob("*.png"))) == 2


def test_broken_book_is_reported_not_fatal(library: Path, tmp_path: Path) -> None:
    (library / "Broken").mkdir()
    (library / "Broken" / "metadata.opf").write_text("not xml")
    summary = process_library(library, tmp_path / "covers", 758, 1024)
    assert summary[Status.failed] == 1
    assert summary[Status.converted] == 3


def test_cli_with_device(library: Path, tmp_path: Path) -> None:
    out = tmp_path / "covers"
    result = runner.invoke(
        app, ["generate", str(library), str(out), "-d", "kindle_paperwhite3"]
    )
    assert result.exit_code == 0, result.output
    with Image.open(next(out.glob("*.png"))) as img:
        assert img.size == (1072, 1448)


def test_cli_rejects_missing_size(library: Path, tmp_path: Path) -> None:
    result = runner.invoke(app, ["generate", str(library), str(tmp_path / "o")])
    assert result.exit_code != 0
