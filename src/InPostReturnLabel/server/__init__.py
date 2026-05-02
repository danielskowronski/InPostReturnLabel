# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT

import asyncio
import base64
from encodings.base64_codec import base64_encode
import os
from pathlib import Path

from InPostReturnLabel.Code import isCodeValid
from InPostReturnLabel.ipp import print_ipp
from flask import Flask, render_template, redirect, request
from InPostReturnLabel.__about__ import __version__
from InPostReturnLabel.config.schema import DefaultMode, Config
from InPostReturnLabel.config.load import load_config
from InPostReturnLabel.Label import render, default_font

app = Flask(__name__)
_cfg: Config


def get_cfg() -> Config:
    cfg = app.config.get("server_config")
    if cfg is None or not isinstance(cfg, Config):
        cfg_path = os.environ.get(
            "INPOST_RETURN_LABEL_CONFIG", "~/.config/InPostReturnLabel/config.yaml"
        )
        cfg_path = Path(cfg_path).expanduser()
        if not cfg_path.is_file():
            raise FileNotFoundError(
                f"Configuration file {cfg_path} not found, cannot start server"
            )
        cfg = load_config(cfg_path.absolute().as_posix())
        app.config["server_config"] = cfg
    return cfg


@app.route("/")
def index():
    cfg = get_cfg()
    return render_template(
        "index.html.j2",
        version=__version__,
        timestamp=int(__import__("time").time()),
        cfg=cfg,
    )


@app.route("/print", methods=["POST"])
def print_label():
    code = request.form["code"].replace(" ", "")
    timestamp = request.form["timestamp"]
    now = int(__import__("time").time())

    if (
        not code
        or not timestamp
        or not code.strip()
        or not timestamp.strip()
        or not timestamp.isdigit()
        or not isCodeValid(code)
    ):
        return redirect(
            "/"
        )  # no message, this form should have been validated by JS before submit
    timestamp = int(timestamp)

    cfg = get_cfg()
    if now - timestamp > 60:
        return redirect("/")

    result = ""
    img = render(
        code,
        cfg.template.font_path
        if cfg.template and cfg.template.font_path
        else default_font,
    )
    img.seek(0)
    imageBytes = img.read()
    if request.form.get("print", "off") == "on":
        if cfg.default_mode == DefaultMode.IPP:
            if (
                not cfg.printer
                or not cfg.printer.ipp
                or not cfg.printer.ipp.printer_uri
            ):
                return "IPP printer is not configured", 500
            dpi = cfg.printer.ipp.dpi if cfg.printer.ipp.dpi else 300
            result = asyncio.run(
                print_ipp(
                    ipp_printer_uri=cfg.printer.ipp.printer_uri,
                    imageBytes=imageBytes,
                    code=code,
                    media=cfg.printer.ipp.check_media,
                    ipp_dpi=dpi,
                )
            )
        elif cfg.default_mode == DefaultMode.CUPS:
            result = "CUPS printing is not supported in server mode yet"
        else:
            result = "Server runs in preview mode, not printing"
    else:
        result = "Print option not selected, showing preview only"

    return render_template(
        "print.html.j2",
        version=__version__,
        img_data=base64.b64encode(imageBytes).decode("ascii"),
        info_text=result,
    )


def start_server() -> None:
    cfg = get_cfg()
    app.run(host=cfg.server.bind_address, port=cfg.server.port, debug=cfg.server.debug)
