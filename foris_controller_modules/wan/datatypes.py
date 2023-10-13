# foris-controller-wan-module
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2023, CZ.NIC z.s.p.o. (https://www.nic.cz/)

from enum import Enum
import typing


# class WanOperationModes(Enum):
#     WIRED = "wired"
#     WIRELESS = "wireless"

WanOperationModesValue = typing.Literal["wired", "wireless"]

WanOperationModes = Enum('', {
    name.upper(): name for name in typing.get_args(WanOperationModesValue)
})
