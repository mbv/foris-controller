#
# foris-controller
# Copyright (C) 2020 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#


import pytest

from foris_controller_testtools.fixtures import (
    infrastructure,
    only_backends,
    start_buses,
    ubusd_test,
    mosquitto_test,
)


@pytest.mark.only_backends(["mock"])
def test_list_modules(infrastructure, start_buses):
    res = infrastructure.process_message(
        {
            "module": "introspect",
            "action": "list_modules",
            "kind": "request",
        }
    )

    assert "error" not in res
    assert "data" in res
    assert isinstance(res["data"]["modules"], list)
