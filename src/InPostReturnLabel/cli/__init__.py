# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
import asyncio
import logging

import click
import subprocess
from InPostReturnLabel.__about__ import __version__
from InPostReturnLabel.Label import renderAndSave, default_font
from InPostReturnLabel.Code import isCodeValid
from pathlib import Path
from InPostReturnLabel.config.schema import DefaultMode
from InPostReturnLabel.config.load import load_config
from InPostReturnLabel.ipp import print_ipp
from InPostReturnLabel.server import start_server

logger = logging.getLogger(__name__)


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="InPostReturnLabel")
@click.option(
    "--cfg",
    default="~/.config/InPostReturnLabel/config.yaml",
    type=click.Path(dir_okay=False),
    help="Path to configuration file.",
    show_default=True,
)
@click.option(
    "--verbosity",
    "-v",
    count=True,
    help="Increase output verbosity (can be used multiple times).",
)
@click.pass_context
def InPostReturnLabel(ctx: click.Context, cfg: str, verbosity: int) -> None:
    """InPostReturnLabel init."""
    ctx.ensure_object(dict)
    ctx.obj["cfg"] = cfg
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
    click.echo(f"InPostReturnLabel {__version__}")
    lvl = logging.INFO
    if verbosity := ctx.params.get("verbosity", 0):
        if verbosity == 1:
            lvl = logging.DEBUG
    logging.basicConfig(level=lvl)


@InPostReturnLabel.command(
    "print", help="Locally generate and print InPost return label from CODE"
)
@click.argument("code")
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
@click.pass_context
def print_code(
    ctx: click.Context,
    code: str,
    printer: str,
    ipp_printer: str,
    check_media: str,
    font: str,
    dpi: int,
) -> None:
    """InPostReturnLabel

    CODE is InPost return label code, 10 digits, e.g. 1234567890
    """
    cfg = ctx.obj["cfg"]
    code = code.replace(" ", "")
    if not isCodeValid(code):
        click.echo(f"{code} is not a valid InPost return label code")
        return
    cfg_path = Path(cfg).expanduser()
    mode = DefaultMode.PREVIEW
    if printer:
        mode = DefaultMode.CUPS
    elif ipp_printer:
        mode = DefaultMode.IPP
    if cfg_path.is_file():
        _cfg = load_config(cfg_path.absolute().as_posix())
        if _cfg.default_mode:
            if not printer and not ipp_printer:
                mode = _cfg.default_mode
        if (
            not printer
            and _cfg.printer
            and _cfg.printer.cups
            and _cfg.printer.cups.printer_name
        ):
            printer = _cfg.printer.cups.printer_name
        if (
            not ipp_printer
            and _cfg.printer
            and _cfg.printer.ipp
            and _cfg.printer.ipp.printer_uri
        ):
            ipp_printer = _cfg.printer.ipp.printer_uri
        if not font and _cfg.template and _cfg.template.font_path:
            font = _cfg.template.font_path
        if (
            not check_media
            and _cfg.printer
            and _cfg.printer.ipp
            and _cfg.printer.ipp.check_media
        ):
            check_media = _cfg.printer.ipp.check_media
        if not dpi and _cfg.printer and _cfg.printer.ipp and _cfg.printer.ipp.dpi:
            dpi = _cfg.printer.ipp.dpi
        click.echo(f"Configuration loaded from {cfg_path}")
    click.echo(f"Using mode: {mode}")
    pathToLabel = renderAndSave(code, font)
    click.echo(f"Label generated and stored at {pathToLabel}")
    imageBytes = open(pathToLabel, "rb").read()
    if mode == DefaultMode.CUPS:
        click.echo(f"Sending label to {printer}")
        subprocess.run(["lpr", "-P", printer, pathToLabel])
    elif mode == DefaultMode.IPP:
        click.echo(f"Sending label to {ipp_printer}")
        result = asyncio.run(print_ipp(ipp_printer, imageBytes, code, check_media, dpi))
        click.echo(result)
    else:
        click.echo("Opening label in default application")
        subprocess.run(["open", pathToLabel])


@InPostReturnLabel.command(
    "server", help="Host simple web server for InPost return label generation"
)
@click.pass_context
def server(ctx: click.Context) -> None:
    """InPostReturnLabel server

    Host simple web server for InPost return label generation
    """
    start_server()


if __name__ == "__main__":
    InPostReturnLabel()
