# foris-controller-wan-module
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2023, CZ.NIC z.s.p.o. (https://www.nic.cz/)

from enum import Enum


class WanOperationModes(Enum):
    WIRED = "wired"
    WIRELESS = "wireless"
