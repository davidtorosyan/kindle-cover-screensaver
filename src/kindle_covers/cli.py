import logging
from pathlib import Path
from typing import Annotated, Optional

import typer

from kindle_covers.devices import SIZE_MAP, Device
from kindle_covers.generate import Status, process_library
from kindle_covers.rotate import choose_and_copy_cover

app = typer.Typer(
    help="Turn your Calibre library into rotating Kindle screensavers.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


@app.command()
def generate(
    library_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            help="A Calibre library to scan for books.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Argument(file_okay=False, help="Where to write the converted covers."),
    ],
    device: Annotated[
        Optional[Device],
        typer.Option("--device", "-d", help="Use this device's screen size."),
    ] = None,
    width: Annotated[
        Optional[int],
        typer.Option("--width", "-w", help="Custom width (use with --height)."),
    ] = None,
    height: Annotated[
        Optional[int],
        typer.Option("--height", "-h", help="Custom height (use with --width)."),
    ] = None,
    filter_column: Annotated[
        Optional[str],
        typer.Option(
            "--filter-column",
            "-f",
            help='Only include books where this custom column (e.g. "Read" or "#read")...',
        ),
    ] = None,
    filter_value: Annotated[
        Optional[str],
        typer.Option("--filter-value", "-v", help='...has this value (e.g. "True").'),
    ] = None,
    border_color: Annotated[
        str,
        typer.Option("--border-color", "-b", help="Color of the padding around covers."),
    ] = "white",
    force: Annotated[bool, typer.Option(help="Regenerate existing covers.")] = False,
    clean: Annotated[
        bool, typer.Option(help="Delete covers that are no longer in the library.")
    ] = False,
) -> None:
    """Convert every cover in a Calibre library to a Kindle-sized grayscale PNG."""
    if bool(filter_column) != bool(filter_value):
        raise typer.BadParameter(
            "--filter-column and --filter-value must be used together"
        )

    if device:
        if width or height:
            raise typer.BadParameter("use either --device or --width/--height")
        width, height = SIZE_MAP[device]
    elif not (width and height):
        raise typer.BadParameter("specify --device, or both --width and --height")

    summary = process_library(
        library_dir,
        output_dir,
        width,
        height,
        filter_column,
        filter_value,
        force,
        clean,
        border_color,
    )
    if summary[Status.failed]:
        raise typer.Exit(code=2)


@app.command()
def rotate(
    covers_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            help="The folder of covers made by 'generate'.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(dir_okay=False, help="Where to put the chosen cover."),
    ],
) -> None:
    """Copy a random cover (different from the current one) to OUTPUT_PATH."""
    try:
        choose_and_copy_cover(covers_dir, output_path)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
