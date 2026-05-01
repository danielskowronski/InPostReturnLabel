# SPDX-FileCopyrightText: 2025-present Daniel Skowroński <daniel@skowron.ski>
#
# SPDX-License-Identifier: MIT
# TODO: this should be some kind of a class


def isCodeValid(code):
    if not code.isdigit():
        return False
    code = int(code)
    if not code >= 0 and code <= 9999999999:
        return False
    return True
