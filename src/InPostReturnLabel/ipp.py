# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
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


async def ipp_printer_print(ipp_printer_uri, content, job_name, format="image/urf"):
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
            print("Printer response for job print request:")
            print(response)
        except IPPError as e:
            print(f"IPP error: {e}")


def mm_to_px(mm, dpi):
    return int(mm * dpi / 25.4)


async def print_ipp(ipp_printer_uri, pathToLabel, code, media=None, ipp_dpi=300):
    media_info = await ipp_printer_media_check(ipp_printer_uri)
    printer = media_info.get("printers", [{}])[0]
    media_ready = printer.get("media-ready", "UNKNOWN!")
    media_supported = printer.get("media-supported", ["UNKNOWN!"])
    if not media_ready:
        print("Printer does not report currently loaded media")
        return
    else:
        print(f"Printer has currently loaded media: {media_ready}")
    if media:
        if media not in media_supported:
            print(f"Media {media} is not supported by the printer")
            print(f"Supported media: {media_supported}")
            return
        if media != media_ready:
            print(f"Media {media} is not currently loaded in the printer")
            return
    img = Image.open(pathToLabel)
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
    await ipp_printer_print(ipp_printer_uri, content, job_name)
    state = await ipp_printer_check(ipp_printer_uri)
    print("Printer status after printing:")
    print(state)
