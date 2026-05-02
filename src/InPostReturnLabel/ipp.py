# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
from io import BytesIO

from pyipp import IPP, IPPError
from pyipp.enums import IppOperation
import getpass
import socket
from PIL import Image
from InPostReturnLabel.urf import Urf


async def ipp_printer_media_check(ipp_printer_uri):
    async with IPP(ipp_printer_uri) as ipp:
        response = await ipp.execute(
            IppOperation.GET_PRINTER_ATTRIBUTES,
            {
                "version": (2, 0),
                "operation-attributes-tag": {
                    "requested-attributes": [
                        "media-ready",
                        "media-col-ready",
                        "media-supported",
                    ],
                },
            },
        )
        return response


async def ipp_printer_check(ipp_printer_uri):
    async with IPP(ipp_printer_uri) as ipp:
        response = await ipp.execute(
            IppOperation.GET_PRINTER_ATTRIBUTES,
            {
                "version": (2, 0),
                "operation-attributes-tag": {
                    "requested-attributes": [
                        "printer-state",
                        "printer-state-reasons",
                        "queued-job-count",
                    ],
                },
            },
        )
        return response


async def ipp_printer_print(
    ipp_printer_uri, content, job_name, format="image/urf"
) -> str:
    text_response = ""
    async with IPP(ipp_printer_uri) as ipp:
        try:
            response = await ipp.execute(
                IppOperation.PRINT_JOB,
                {
                    "operation-attributes-tag": {
                        "printer-uri": ipp_printer_uri,
                        "requesting-user-name": f"{getpass.getuser()}@{socket.gethostname()}/InPostReturnLabel",
                        "job-name": job_name,
                        "document-format": format,
                    },
                    "data": content,
                },
            )
            text_response += "Printer response for job print request:\n"
            text_response += str(response) + "\n"
        except IPPError as e:
            text_response += f"IPP error: {e}\n"
    return text_response


def mm_to_px(mm, dpi):
    return int(mm * dpi / 25.4)


async def print_ipp(ipp_printer_uri, imageBytes, code, media=None, ipp_dpi=300) -> str:
    return_text = ""
    media_info = await ipp_printer_media_check(ipp_printer_uri)
    printer = media_info.get("printers", [{}])[0]
    media_ready = printer.get("media-ready", "UNKNOWN!")
    media_supported = printer.get("media-supported", ["UNKNOWN!"])
    if not media_ready:
        return_text += "Printer does not report currently loaded media\n"
        return return_text
    else:
        return_text += f"Printer has currently loaded media: {media_ready}\n"
    if media:
        if media not in media_supported:
            return_text += f"Media {media} is not supported by the printer\n"
            for m in media_supported:
                return_text += f"Supported media: {m}\n"
            return return_text
        if media != media_ready:
            return_text += f"Media {media} is not currently loaded in the printer\n"
            return return_text
    buf = BytesIO(imageBytes)
    img = Image.open(buf)
    img = img.resize(
        (
            mm_to_px(100, ipp_dpi),
            mm_to_px(150, ipp_dpi),
        ),
        resample=Image.Resampling.LANCZOS,
    )
    urf = Urf()
    content = urf.encode(
        img,
        grey_scale=False,
        dpi=ipp_dpi,
        margin={"top": 0, "bottom": 0, "left": 0, "right": 0},
    )
    job_name = f"InPostReturnLabel_{code}"
    return_text += await ipp_printer_print(ipp_printer_uri, content, job_name)
    state = await ipp_printer_check(ipp_printer_uri)
    return_text += "Printer status after printing: \n"
    return_text += str(state) + "\n"
    return return_text
