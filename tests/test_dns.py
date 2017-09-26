#
# foris-controller
# Copyright (C) 2017 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

from .fixtures import backend, infrastructure, ubusd_test


def test_get_settings(infrastructure, ubusd_test):
    res = infrastructure.process_message({
        "module": "dns",
        "action": "get_settings",
        "kind": "request",
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "forwarding_enabled" in res["data"].keys()
    assert "dnssec_enabled" in res["data"].keys()
    assert "dns_from_dhcp_enabled" in res["data"].keys()


def test_update_settings(infrastructure, ubusd_test):
    res = infrastructure.process_message({
        "module": "dns",
        "action": "update_settings",
        "kind": "request",
        "data": {
            "forwarding_enabled": False,
            "dnssec_enabled": False,
            "dns_from_dhcp_enabled": False,
        }
    })
    assert res == {
        u'action': u'update_settings',
        u'data': {u'result': True},
        u'kind': u'reply',
        u'module': u'dns'
    }
    res = infrastructure.process_message({
        "module": "dns",
        "action": "update_settings",
        "kind": "request",
        "data": {
            "forwarding_enabled": False,
            "dnssec_enabled": False,
            "dns_from_dhcp_enabled": False,
            "dns_from_dhcp_domain": "test",
        }
    })
    assert res == {
        u'action': u'update_settings',
        u'data': {u'result': True},
        u'kind': u'reply',
        u'module': u'dns'
    }


def test_update_and_get_settings(infrastructure, ubusd_test):
    res = infrastructure.process_message({
        "module": "dns",
        "action": "update_settings",
        "kind": "request",
        "data": {
            "forwarding_enabled": False,
            "dnssec_enabled": False,
            "dns_from_dhcp_enabled": False,
        }
    })
    assert res == {
        u'action': u'update_settings',
        u'data': {u'result': True},
        u'kind': u'reply',
        u'module': u'dns'
    }
    res = infrastructure.process_message({
        "module": "dns",
        "action": "get_settings",
        "kind": "request",
    })
    assert res['data']["forwarding_enabled"] is False
    assert res['data']["dnssec_enabled"] is False
    assert res['data']["dns_from_dhcp_enabled"] is False
    res = infrastructure.process_message({
        "module": "dns",
        "action": "update_settings",
        "kind": "request",
        "data": {
            "forwarding_enabled": True,
            "dnssec_enabled": True,
            "dns_from_dhcp_enabled": True,
            "dns_from_dhcp_domain": "test",
        }
    })
    assert res == {
        u'action': u'update_settings',
        u'data': {u'result': True},
        u'kind': u'reply',
        u'module': u'dns'
    }
    res = infrastructure.process_message({
        "module": "dns",
        "action": "get_settings",
        "kind": "request",
    })
    assert res['data']["forwarding_enabled"] is True
    assert res['data']["dnssec_enabled"] is True
    assert res['data']["dns_from_dhcp_enabled"] is True
    assert res['data']["dns_from_dhcp_domain"] == "test"
