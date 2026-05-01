# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
import asyncio

import click
import subprocess
from InPostReturnLabel.__about__ import __version__
from InPostReturnLabel.Label import renderAndSave
from InPostReturnLabel.Code import isCodeValid
from importlib.resources import files
from pathlib import Path
from InPostReturnLabel.config.schema import Mode
from InPostReturnLabel.config.load import load_config
from InPostReturnLabel.ipp import print_ipp

default_font = files("InPostReturnLabel.font").joinpath(
    "Inconsolata-Bold.ttf"
)  # /System/Library/Fonts/Monaco.ttf


@click.command()
@click.version_option(version=__version__, prog_name="InPostReturnLabel")
@click.argument("code", type=str)
@click.option(
    "--cfg",
    default="~/.config/InPostReturnLabel/config.yaml",
    type=click.Path(dir_okay=False),
    help="Path to configuration file.",
    show_default=True,
)
@click.option(
    "-p",
    "--printer",
    type=str,
    help="Local CUPS printer name; if ommited, then file will be opened",
)
@click.option(
    "-i",
    "--ipp-printer",
    type=str,
    help="IPP URL for printer; if ommited, then file will be opened",
)
@click.option(
    "-m",
    "--check-media",
    type=str,
    help="Enforce loaded media type for IPP printer",
)
@click.option(
    "--dpi",
    type=int,
    help="DPI for IPP printer (likely 203 or 300)",
    default=300,
)
@click.option(
    "-f",
    "--font",
    type=str,
    help=f"Path to font file, default: {default_font}",
    default=default_font,
)
def InPostReturnLabel(cfg, code, printer, ipp_printer, check_media, font, dpi):
    """InPostReturnLabel

    CODE is InPost return label code, 10 digits, e.g. 1234567890
    """
    code = code.replace(" ", "")
    if not isCodeValid(code):
        click.echo(f"{code} is not a valid InPost return label code")
        return
    cfg_path = Path(cfg).expanduser()
    mode = Mode.PREVIEW
    if printer:
        mode = Mode.CUPS
    elif ipp_printer:
        mode = Mode.IPP
    if cfg_path.is_file():
        _cfg = load_config(cfg_path.absolute().as_posix())
        if _cfg.default_mode:
            if not printer and not ipp_printer:
                mode = _cfg.default_mode
        if not printer and _cfg.cups_printer_name:
            printer = _cfg.cups_printer_name
        if not ipp_printer and _cfg.ipp_printer_uri:
            ipp_printer = _cfg.ipp_printer_uri
        if not font and _cfg.font_path:
            font = _cfg.font_path
        if not check_media and _cfg.ipp_check_media:
            check_media = _cfg.ipp_check_media
        if not dpi and _cfg.ipp_dpi:
            dpi = _cfg.ipp_dpi
        click.echo(f"Configuration loaded from {cfg_path}")
    click.echo(f"Using mode: {mode}")
    pathToLabel = renderAndSave(code, font)
    click.echo(f"Label generated and stored at {pathToLabel}")
    if mode == Mode.CUPS:
        click.echo(f"Sending label to {printer}")
        subprocess.run(["lpr", "-P", printer, pathToLabel])
    elif mode == Mode.IPP:
        click.echo(f"Sending label to {ipp_printer}")
        asyncio.run(print_ipp(ipp_printer, pathToLabel, code, check_media, dpi))
    else:
        click.echo("Opening label in default application")
        subprocess.run(["open", pathToLabel])


if __name__ == "__main__":
    InPostReturnLabel()
