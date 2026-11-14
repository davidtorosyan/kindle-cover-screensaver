from pathlib import Path

import pytest
from typer.testing import CliRunner

from kindle_covers.cli import app
from kindle_covers.rotate import choose_and_copy_cover, state_path

runner = CliRunner()


def make_covers(folder: Path, *names: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_bytes(name.encode())


def test_never_repeats_current_cover(tmp_path: Path) -> None:
    covers = tmp_path / "covers"
    make_covers(covers, "a.png", "b.png")
    out = tmp_path / "www" / "cover.png"

    previous = choose_and_copy_cover(covers, out).name
    for _ in range(10):
        chosen = choose_and_copy_cover(covers, out).name
        assert chosen != previous
        assert out.read_bytes() == chosen.encode()
        assert state_path(out).read_text() == chosen
        previous = chosen


def test_single_cover_is_reused(tmp_path: Path) -> None:
    covers = tmp_path / "covers"
    make_covers(covers, "only.png")
    out = tmp_path / "cover.png"
    choose_and_copy_cover(covers, out)
    assert choose_and_copy_cover(covers, out).name == "only.png"


def test_empty_folder_errors(tmp_path: Path) -> None:
    (tmp_path / "covers").mkdir()
    with pytest.raises(FileNotFoundError):
        choose_and_copy_cover(tmp_path / "covers", tmp_path / "cover.png")

    result = runner.invoke(
        app, ["rotate", str(tmp_path / "covers"), str(tmp_path / "cover.png")]
    )
    assert result.exit_code == 1


def test_state_files_stay_out_of_covers_folder(tmp_path: Path) -> None:
    covers = tmp_path / "covers"
    make_covers(covers, "a.png")
    out = tmp_path / "cover.png"
    choose_and_copy_cover(covers, out)
    assert not list(covers.glob(".*"))
