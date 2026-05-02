# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel
from enum import StrEnum


class CliDefaultMode(StrEnum):
    CUPS = "cups"
    IPP = "ipp"
    PREVIEW = "preview"

class TemplateOptions(BaseModel):
    font_path: Optional[str] = None

class CupsPrinterOptions(BaseModel):
    printer_name: str

class IppPrinterOptions(BaseModel):
    printer_uri: str
    check_media: Optional[str] = None
    dpi: Optional[int] = 300

class PrinterOptions(BaseModel):
    cups: Optional[CupsPrinterOptions] = None
    ipp: Optional[IppPrinterOptions] = None

class Config(BaseModel):
    cli_default_mode: CliDefaultMode = CliDefaultMode.PREVIEW
    printer: PrinterOptions = PrinterOptions()
    template: TemplateOptions = TemplateOptions()

