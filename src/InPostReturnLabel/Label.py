# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
from importlib.resources import files
import io
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
import segno

default_font = files("InPostReturnLabel.font").joinpath(
    "Inconsolata-Bold.ttf"
)  # /System/Library/Fonts/Monaco.ttf


def render(code, font_path) -> io.BytesIO:
    # FIXME: this should be parametrized at this stage instead of resize later
    x = 1000  # 100mm
    y = 1500  # 150mm

    y_offset = int(y / 10)
    fs = x / 7.6  # 9 for Monaco, 7.6 for Inconsolata
    th = x + y_offset + (y - x) / 2 + -fs / 2
    th = x + y_offset
    scale = x / 25

    qr_rendered = io.BytesIO()
    qrcode = segno.make_qr(code)
    qrcode.save(qr_rendered, scale=scale, kind="png", border=2)
    qr = Image.open(qr_rendered)
    code_text = f"{code:010}"
    code_fmt = f" {code_text[0:3]} {code_text[3:6]} {code_text[6:9]} {code_text[9]} "
    image = Image.new("RGB", (x, y), color=(255, 255, 255))
    image.paste(qr, (0, y_offset))
    image_draw = ImageDraw.Draw(image)
    fnt = ImageFont.truetype(font_path, fs)
    image_draw.text((0, th), code_fmt, font=fnt, fill=(0, 0, 0))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf


def renderAndSave(code, font_path) -> str:
    bytes_io = render(code, font_path)
    bytes_io.seek(0)
    fd, path = tempfile.mkstemp(suffix=".png")
    try:
        with open(path, "wb") as f:
            f.write(bytes_io.getvalue())
    finally:
        os.close(fd)
    return path
