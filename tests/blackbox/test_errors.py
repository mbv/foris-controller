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


def test_wrong_input_data(infrastructure):
    res = infrastructure.process_message(
        {"module": "about", "action": "get", "kind": "request", "data": {"extra": "data"}}
    )
    assert res["action"] == "get"
    assert res["kind"] == "reply"
    assert res["module"] == "about"
    assert "errors" in res
    assert "Incorrect input." in res["errors"][0]["description"]


@pytest.mark.only_message_buses(["unix-socket", "mqtt"])
def test_wrong_input_kind(infrastructure):
    res = infrastructure.process_message(
        {
            "module": "about",
            "action": "get",
            "kind": "reply",
            "data": {
                "model": "Turris Omnia",
                "kernel": "4.4.77-967673b9d511e4292e3bcb76c9e064bc-0",
                "os_version": "3.7",
                "serial": "0000000B00009CD6",
            },
        }
    )
    assert "errors" in res
    assert res["action"] == "get"
    assert res["kind"] == "reply"
    assert res["module"] == "about"
    assert res["errors"][0][
        "description"
    ] == "Wrong message kind (only request are allowed)." or res["errors"][0][
        "description"
    ].startswith(
        "Incorrect input"
    )


@pytest.mark.only_message_buses(["unix-socket", "mqtt"])
def test_wrong_input_action(infrastructure):
    res = infrastructure.process_message(
        {"module": "about", "action": "non-exiting", "kind": "request"}
    )
    assert res["action"] == "non-exiting"
    assert res["kind"] == "reply"
    assert res["module"] == "about"
    assert "errors" in res
    assert "Incorrect input." in res["errors"][0]["description"]


@pytest.mark.only_message_buses(["unix-socket", "mqtt"])
def test_wrong_input_module(infrastructure):
    res = infrastructure.process_message(
        {"module": "non-exiting", "action": "get", "kind": "request"}
    )
    assert res["action"] == "get"
    assert res["kind"] == "reply"
    assert res["module"] == "non-exiting"
    assert "errors" in res
    assert "Incorrect input." in res["errors"][0]["description"]
