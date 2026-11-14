"""Pick a random cover and publish it at a fixed path for the Kindle to fetch."""

import logging
import os
import random
import shutil
from pathlib import Path

logger = logging.getLogger("kindle_covers")


def state_path(outpath: Path) -> Path:
    """Hidden file next to the output that remembers which cover is current."""
    return outpath.with_name(f".{outpath.name}.source")


def choose_and_copy_cover(covers_dir: Path, outpath: Path) -> Path:
    state = state_path(outpath)
    current = state.read_text().strip() if state.exists() else None

    covers = sorted(covers_dir.glob("*.png"))
    if not covers:
        raise FileNotFoundError(f"No .png covers found in {covers_dir}")

    # Avoid showing the same cover twice in a row, unless it is the only one.
    candidates = [c for c in covers if c.name != current] or covers
    chosen = random.choice(candidates)

    if current:
        logger.info("Chose '%s', replacing old cover '%s'", chosen.name, current)
    else:
        logger.info("Chose '%s'", chosen.name)

    # Copy to a temp file and rename, so a web server never serves half a file.
    outpath.parent.mkdir(parents=True, exist_ok=True)
    tmp = outpath.with_name(f".{outpath.name}.tmp")
    shutil.copyfile(chosen, tmp)
    os.replace(tmp, outpath)
    state.write_text(chosen.name)
    return chosen
