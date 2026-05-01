# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel
from enum import StrEnum


class Mode(StrEnum):
    CUPS = "cups"
    IPP = "ipp"
    PREVIEW = "preview"


class Config(BaseModel):
    default_mode: Mode = Mode.PREVIEW
    cups_printer_name: Optional[str] = None
    ipp_printer_uri: Optional[str] = None
    ipp_check_media: Optional[str] = None
    ipp_dpi: Optional[int] = 300
    font_path: Optional[str] = None
