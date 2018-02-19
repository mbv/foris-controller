#
# foris-controller
# Copyright (C) 2018 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import os
import json

from foris_controller_testtools.fixtures import (
    only_backends, uci_configs_init, infrastructure, ubusd_test, lock_backend
)

STORED_NOTIFICATIONS = [
    {
        "displayed": False,
        "id": "1518776436-2593",
        "severity": "restart",
        "messages": {
            "cs": "REBOOT1 CS",
            "en": "REBOOT1 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2598",
        "severity": "restart",
        "messages": {
            "cs": "REBOOT2 CS",
            "en": "REBOOT2 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2603",
        "severity": "news",
        "messages": {
            "cs": "NEWS1 CS",
            "en": "NEWS1 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2608",
        "severity": "news",
        "messages": {
            "cs": "NEWS2 CS",
            "en": "NEWS2 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2613",
        "severity": "error",
        "messages": {
            "cs": "ERROR1 CS",
            "en": "ERROR1 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2618",
        "severity": "error",
        "messages": {
            "cs": "ERROR2 CS",
            "en": "ERROR2 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2623",
        "severity": "update",
        "messages": {
            "cs": "UPDATE1 CS",
            "en": "UPDATE1 EN"
        }
    },
    {
        "displayed": False,
        "id": "1518776436-2628",
        "severity": "update",
        "messages": {
            "cs": "UPDATE2 CS",
            "en": "UPDATE2 EN"
        }
    }
]


@pytest.fixture(scope="function")
def stored_notifications():
    path = "/tmp/foris-controller-stored-notifications.json"
    try:
        os.unlink(path)
    except Exception:
        pass

    with open(path, "w") as f:
        json.dump({"notifications": STORED_NOTIFICATIONS}, f)
        f.flush()

    yield path

    try:
        os.unlink(path)
    except Exception:
        pass


def test_list(stored_notifications, uci_configs_init, infrastructure, ubusd_test):
    res = infrastructure.process_message({
        "module": "router_notifications",
        "action": "list",
        "kind": "request",
        "data": {"lang": "en"}
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "notifications" in res["data"].keys()

    res = infrastructure.process_message({
        "module": "router_notifications",
        "action": "list",
        "kind": "request",
        "data": {"lang": "cs"}
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "notifications" in res["data"].keys()

    res = infrastructure.process_message({
        "module": "router_notifications",
        "action": "list",
        "kind": "request",
        "data": {"lang": "pl"}
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "notifications" in res["data"].keys()


def test_mark_as_displayed(stored_notifications, uci_configs_init, infrastructure, ubusd_test):
    ids = ["1518776436-2598", "1518776436-2628"]
    res = infrastructure.process_message({
        "module": "router_notifications",
        "action": "mark_as_displayed",
        "kind": "request",
        "data": {"ids": ids}
    })
    assert res == {
        u"module": u"router_notifications",
        u"action": u"mark_as_displayed",
        u"kind": u"reply",
        u"data": {u"result": True},
    }
    res = infrastructure.process_message({
        "module": "router_notifications",
        "action": "list",
        "kind": "request",
        "data": {"lang": "en"}
    })
    assert "notifications" in res["data"].keys()
    for notification in res["data"]["notifications"]:
        assert notification["displayed"] == (notification["id"] in ids)
