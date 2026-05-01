# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT

from .schema import Config
import yaml
from pathlib import Path


def load_config(path: str) -> Config:
    path_expanded = Path(path).expanduser()
    with open(path_expanded, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)
    _cfg = Config.model_validate(raw_cfg)
    return _cfg
