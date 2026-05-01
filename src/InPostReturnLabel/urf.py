# SPDX-FileCopyrightText: Copyright (c) 2017 David Dillkötter
#
# SPDX-License-Identifier: MIT
#
# Taken from https://github.com/DkDavid/imageurf/blob/master/urf.js and adapted to Python

# FIXME: this should probably be a separate package, but for now it's just a module in this project

from __future__ import annotations
from dataclasses import dataclass, field

from PIL import Image


@dataclass
class UrfMargin:
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0


@dataclass
class Urf:
    margin: UrfMargin = field(default_factory=UrfMargin)
    turn: bool = False
    width: int = 0
    height: int = 0
    greyscale: bool = True
    dpi: int = 300

    def encode(
        self,
        img: Image.Image,
        *,
        width: int | None = None,
        height: int | None = None,
        margin: dict[str, int] | None = None,
        grey_scale: bool | None = None,
        dpi: int = 300,
        turn: bool = False,
    ) -> bytes:

        if margin:
            for key, value in margin.items():
                if hasattr(self.margin, key):
                    setattr(self.margin, key, int(value))

        if img.mode not in ("L", "LA", "RGB", "RGBA"):
            img = img.convert("RGBA")

        width = width or img.width
        height = height or img.height

        if img.width != width or img.height != height:
            img = img.resize((width, height))

        img_data = img.tobytes()
        channels = len(img.getbands())
        bytes_per_pixel = channels

        blob = bytearray()

        # Header
        blob += bytes.fromhex("554e495241535400")  # UNIRAST\0
        blob += bytes.fromhex("00000001")

        greyscale = bool(grey_scale) or bytes_per_pixel <= 2

        if greyscale:
            blob += bytes.fromhex("08")
            blob += bytes.fromhex("00")
        else:
            blob += bytes.fromhex("18")
            blob += bytes.fromhex("01")

        blob += bytes.fromhex("00")  # duplex mode
        blob += bytes.fromhex("04")  # quality
        blob += bytes.fromhex("0000000100000000")

        new_height = width if turn else height
        new_width = height if turn else width

        blob += int(new_width + self.margin.left + self.margin.right).to_bytes(4, "big")
        blob += int(new_height + self.margin.top + self.margin.bottom).to_bytes(
            4, "big"
        )
        blob += int(dpi).to_bytes(4, "big")
        blob += bytes.fromhex("0000000000000000")

        def write_empty_lines(count: int) -> None:
            while count:
                if count > 256:
                    blob.extend(bytes.fromhex("ff80"))
                    count -= 256
                else:
                    blob.append(count - 1)
                    blob.extend(bytes.fromhex("80"))
                    count = 0

        def write_empty_pixel(count: int) -> None:
            while count:
                if count > 128:
                    blob.append(0x7F)
                    count -= 128
                else:
                    blob.append(count - 1)
                    count = 0

                blob.append(0xFF)

                if not greyscale:
                    blob.extend(bytes.fromhex("ffff"))

        write_empty_lines(self.margin.top)

        for y in range(new_height):
            blob.append(0x00)  # line repeat code

            write_empty_pixel(self.margin.left)

            for x in range(new_width):
                blob.append(0x00)  # PackBits code

                if turn:
                    index = ((new_height * (new_width - 1 - x)) + y) * bytes_per_pixel
                else:
                    index = ((new_width * y) + x) * bytes_per_pixel

                if greyscale:
                    if bytes_per_pixel == 1:
                        grey_value = img_data[index]

                    elif bytes_per_pixel == 2:
                        grey = img_data[index]
                        alpha = img_data[index + 1]
                        grey_value = grey * alpha / 255 + 255 - alpha

                    else:
                        r = img_data[index]
                        g = img_data[index + 1]
                        b = img_data[index + 2]
                        grey_value = 0.299 * r + 0.587 * g + 0.114 * b

                        if bytes_per_pixel == 4:
                            alpha = img_data[index + 3]
                            grey_value = grey_value * alpha / 255 + 255 - alpha

                    blob.append(int(grey_value) & 0xFF)

                else:
                    for i in range(3):
                        color_value = img_data[index + i]

                        if bytes_per_pixel == 4:
                            alpha = img_data[index + 3]
                            color_value = color_value * alpha / 255 + 255 - alpha

                        blob.append(int(color_value) & 0xFF)

            write_empty_pixel(self.margin.right)

        write_empty_lines(self.margin.bottom)

        return bytes(blob)

    def decode(self, buf: bytes) -> Image.Image:

        config = {
            "bit_per_pixel": buf[12],
            "color_values": 1 if buf[13] == 0 else 3,
            "width": int.from_bytes(buf[24:28], "big"),
            "height": int.from_bytes(buf[28:32], "big"),
            "duplex": buf[14],
            "quality": buf[15],
            "dpi": int.from_bytes(buf[32:36], "big"),
        }

        img = Image.new(
            "RGBA", (config["width"], config["height"]), (255, 255, 255, 255)
        )
        pixels = img.load()

        x = 0
        y = 0
        k = 44

        def copy_single_pixel(pixel: list[int], px: int, py: int) -> None:
            if py >= config["height"] or px >= config["width"]:
                return

            if len(pixel) == 1:
                pixels[px, py] = (pixel[0], pixel[0], pixel[0], 255)
            else:
                pixels[px, py] = (pixel[0], pixel[1], pixel[2], 255)

        def fill_rest_of_line_empty() -> None:
            nonlocal x

            for i in range(x, config["width"]):
                copy_single_pixel([0xFF], i, y)

            x = config["width"]

        def check_end_of_line() -> bool:
            nonlocal x, y

            if x >= config["width"]:
                x = 0
                y += 1
                return True

            return False

        while k < len(buf) - 1 and y < config["height"]:
            line_repeat_number = buf[k]
            k += 1

            line_to_repeat = k

            for _ in range(line_repeat_number + 1):
                k = line_to_repeat
                end_of_line = False

                while not end_of_line and k < len(buf):
                    code = int.from_bytes(buf[k : k + 1], "big", signed=True)
                    k += 1

                    if code == -128:
                        fill_rest_of_line_empty()

                    elif code >= 0:
                        pixel = []

                        for _ in range(config["color_values"]):
                            pixel.append(buf[k])
                            k += 1

                        for _ in range(code + 1):
                            copy_single_pixel(pixel, x, y)
                            x += 1

                    else:
                        for _ in range((-code) + 1):
                            pixel = []

                            for _ in range(config["color_values"]):
                                pixel.append(buf[k])
                                k += 1

                            copy_single_pixel(pixel, x, y)
                            x += 1

                    end_of_line = check_end_of_line()

        return img
