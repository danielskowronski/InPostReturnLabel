# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
import click
import subprocess
from InPostReturnLabel.__about__ import __version__
from InPostReturnLabel.Label import renderAndSave
from InPostReturnLabel.Code import isCodeValid


@click.command()
@click.version_option(version=__version__, prog_name="InPostReturnLabel")
@click.argument("code", type=int)
@click.option(
    "-p",
    "--printer",
    type=str,
    help="Local CUPS printer name; if ommited, then file will be opened",
)
@click.option(
    "-f",
    "--font",
    type=str,
    help="Path to font file, default: /System/Library/Fonts/Monaco.ttf",
    default="/System/Library/Fonts/Monaco.ttf",
)
def InPostReturnLabel(code, printer, font):
    """InPostReturnLabel

    CODE is InPost return label code, 10 digits, e.g. 1234567890
    """
    if not isCodeValid(code):
        click.echo(f"{code} is not a valid InPost return label code")
        return
    pathToLabel = renderAndSave(code, font)
    click.echo(f"Label generated and stored at {pathToLabel}")
    if printer:
        click.echo(f"Sending label to {printer}")
        subprocess.run(["lpr", "-P", printer, pathToLabel])
    else:
        click.echo(f"Opening label in default application")
        subprocess.run(["open", pathToLabel])


if __name__ == "__main__":
    InPostReturnLabel()
