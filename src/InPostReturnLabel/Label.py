# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
import io
import tempfile
from PIL import Image, ImageDraw, ImageFont
import segno


def renderAndSave(code, font_path) -> str:
    x = 1000  # 100mm
    y = 1500  # 150mm

    y_offset = int(y / 10)
    fs = x / 9
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
    path = tempfile.mktemp() + ".png"
    image.save(path)
    return path
