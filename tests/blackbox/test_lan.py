#
# foris-controller
# Copyright (C) 2018-2023 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

import json
import os
import typing
from pathlib import Path

import pytest
from foris_controller_testtools.fixtures import FILE_ROOT_PATH, UCI_CONFIG_DIR_PATH
from foris_controller_testtools.utils import (
    FileFaker,
    check_service_result,
    get_uci_module,
    match_subdict,
    prepare_turrishw,
)

from .helpers.common import query_infrastructure

WIFI_ROOT_PATH = Path(__file__).resolve().parent / "test_wifi_files"
UBUS_TEST_MOCK_DATA_FILE = "/tmp/ubus_test_mock_data.json"
WIFI_DEFAULT_ENCRYPTION = "WPA2/3"


@pytest.fixture(scope="function")
def dhcpv6_leases_ipv6_prefix():
    """Test data for downsteam router.

    If IPv6 prefix assigned to main router is large enough,
    downstream router should get both `ipv6-addr` and `ipv6-prefix`.
    """
    # NOTE: keep these data in sync with ubus-cli mock data structure
    leases = {
        "dhcp": {
            "ipv6leases": {
                "device": {
                    "br-guest-turris": {
                        "leases": []
                    },
                    "br-lan": {
                        "leases": [
                            {
                                "duid": "00010003d8e63397f73ed8cd7cda",
                                "iaid": 987654321,
                                "hostname": "downstream-router",
                                "accept-reconf": False,
                                "assigned": 801,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-addr": [
                                    {
                                        "address": "fd60:ad42:a6c9::4",
                                        "preferred-lifetime": 42,
                                        "valid-lifetime": 42
                                    }
                                ],
                                "valid": 42
                            },
                            {
                                "duid": "00010003d8e63397f73ed8cd7cda",
                                "iaid": 987654321,
                                "hostname": "downstream-router",
                                "accept-reconf": False,
                                "assigned": 2033,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-prefix": [
                                    {
                                        "address": "fd60:ad42:910e::11",
                                        "preferred-lifetime": 4096,
                                        "valid-lifetime": 4096,
                                        "prefix-length": 62,
                                    }
                                ],
                                "valid": 4096
                            }
                        ]
                    }
                }
            }
        }
    }

    with FileFaker(
        FILE_ROOT_PATH, UBUS_TEST_MOCK_DATA_FILE, False, json.dumps(leases, indent=2)
    ) as ubus_dhcp_mock_file:
        yield ubus_dhcp_mock_file


@pytest.fixture(scope="function")
def dhcpv6_leases_missing_lan_bridge():
    """Test data for missing lan bridge or case when lan bridge is not managed by odhcpd."""
    # NOTE: keep these data in sync with ubus-cli mock data structure
    leases = {
        "dhcp": {
            "ipv6leases": {
                "device": {
                    "br-guest-turris": {
                        "leases": []
                    }
                }
            }
        }
    }

    with FileFaker(
        FILE_ROOT_PATH, UBUS_TEST_MOCK_DATA_FILE, False, json.dumps(leases, indent=2)
    ) as ubus_dhcp_mock_file:
        yield ubus_dhcp_mock_file


@pytest.fixture(scope="function")
def dhcpv6_leases_negative_leasetime():
    """Test data for dhcpv6 lease with negative leasetime - aka something is wrong with leasetime (see odhcpd)."""
    # NOTE: keep these data in sync with ubus-cli mock data structure
    leases = {
        "dhcp": {
            "ipv6leases": {
                "device": {
                    "br-guest-turris": {
                        "leases": []
                    },
                    "br-lan": {
                        "leases": [
                            {
                                "duid": "00010003d8e63397f73ed8cd7cda",
                                "iaid": 987654321,
                                "hostname": "device1",
                                "accept-reconf": False,
                                "assigned": 801,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-addr": [
                                    {
                                        "address": "fd60:ad42:a6c9::4",
                                        "preferred-lifetime": 3600,
                                        "valid-lifetime": 3600
                                    }
                                ],
                                "valid": 3600
                            },
                            {
                                "duid": "00020000df167896750a08ce0782",
                                "iaid": 123456789,
                                "hostname": "device2",
                                "accept-reconf": False,
                                "assigned": 2033,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-addr": [
                                    {
                                        "address": "fd52:ad42:910e::11",
                                        "preferred-lifetime": -1,
                                        "valid-lifetime": -1,
                                    }
                                ],
                                "valid": -1
                            }
                        ]
                    }
                }
            }
        }
    }

    with FileFaker(
        FILE_ROOT_PATH, UBUS_TEST_MOCK_DATA_FILE, False, json.dumps(leases, indent=2)
    ) as ubus_dhcp_mock_file:
        yield ubus_dhcp_mock_file


@pytest.fixture(scope="function")
def dhcpv6_leases_junk_leasetime():
    """Test data for dhcpv6 lease with "junk" leasetime - value that cannot be cast into int.

    Aka something is very wrong with leasetime and probably odhcpd too.
    """
    # NOTE: keep these data in sync with ubus-cli mock data structure
    leases = {
        "dhcp": {
            "ipv6leases": {
                "device": {
                    "br-guest-turris": {
                        "leases": []
                    },
                    "br-lan": {
                        "leases": [
                            {
                                "duid": "00010003d8e63397f73ed8cd7cda",
                                "iaid": 987654321,
                                "hostname": "good-lease",
                                "accept-reconf": False,
                                "assigned": 801,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-addr": [
                                    {
                                        "address": "fd60:ad42:a6c9::4",
                                        "preferred-lifetime": 3600,
                                        "valid-lifetime": 3600
                                    }
                                ],
                                "valid": 60
                            },
                            {
                                "duid": "00020000df167896750a08ce0782",
                                "iaid": 123456789,
                                "hostname": "junk-lease",
                                "accept-reconf": False,
                                "assigned": 2033,
                                "flags": [
                                    "bound"
                                ],
                                "ipv6-addr": [
                                    {
                                        "address": "fd52:ad42:910e::11",
                                        "preferred-lifetime": -1,
                                        "valid-lifetime": -1,
                                    }
                                ],
                                "valid": "non-int junk data"
                            }
                        ]
                    }
                }
            }
        }
    }

    with FileFaker(
        FILE_ROOT_PATH, UBUS_TEST_MOCK_DATA_FILE, False, json.dumps(leases, indent=2)
    ) as ubus_dhcp_mock_file:
        yield ubus_dhcp_mock_file


def all_equal(first, *items):
    return all(first == item for item in items)


def test_get_settings(uci_configs_init, infrastructure, lan_dnsmasq_files):
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert res.keys() == {"action", "kind", "data", "module"}
    assert res["data"].keys() == {
        "mode",
        "mode_managed",
        "mode_unmanaged",
        "interface_count",
        "interface_up_count",
        "lan_redirect",
        "qos"
    }
    assert res["data"]["mode"] in ["managed", "unmanaged"]

    assert set(res["data"]["mode_managed"].keys()) == {"router_ip", "netmask", "dhcp"}
    assert set(res["data"]["mode_managed"]["dhcp"].keys()) == {
        "enabled",
        "start",
        "limit",
        "lease_time",
        "clients",
        "ipv6clients"
    }

    assert set(res["data"]["mode_unmanaged"].keys()) == {"lan_type", "lan_static", "lan_dhcp"}
    assert res["data"]["mode_unmanaged"]["lan_type"] in ["static", "dhcp", "none"]
    assert set(res["data"]["mode_unmanaged"]["lan_dhcp"].keys()) in [{"hostname"}, set()]
    assert set(res["data"]["mode_unmanaged"]["lan_static"].keys()).issubset(
        {"ip", "netmask", "gateway", "dns1", "dns2"}
    )


# NOTE: Keep the fetch test here before updates as workaround.
# Ifrastructucture does not reset between tests, so mock backend keeps its
# state across multiple tests.
# Which leads to weird test results based on the order of the test execution.
@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
def test_dhcp_clients_leasetime_format(
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
):
    """Test that DHCPv6 leases provides the same timestamp format as DHCPv4 leases.

    odhcpd reports DHCPv6 lease time in seconds => meaning lease time duration.
    Which is unfortunately treated as unix timestamp in reForis Lan page (e.g.
    1970-01-01 <some time>).

    DHCPv4 lease time, on the other hand, is reported as timestamp of end of
    the lease (e.g. 2022-01-11 20:41).

    DHCPv6 lease timestamp from backend should have the same meaning =>
    timestamp of end of the lease.
    """
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    timestamp_limit = 946681260  # timestamp should be later than 2000-01-01 00:01:00

    ipv4clients = res["data"]["mode_managed"]["dhcp"]["clients"]
    assert ipv4clients[0]["expires"] > timestamp_limit

    ipv6clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert ipv6clients[0]["expires"] > timestamp_limit
    assert ipv6clients[1]["expires"] > timestamp_limit


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_update_settings(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version, lan_dnsmasq_files
):
    filters = [("lan", "update_settings")]

    def update(data):
        notifications = infrastructure.get_notifications(filters=filters)
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_settings", "kind": "request", "data": data}
        )
        assert res == {
            "action": "update_settings",
            "data": {"result": True},
            "kind": "reply",
            "module": "lan",
        }
        notifications = infrastructure.get_notifications(notifications, filters=filters)
        assert notifications[-1]["module"] == "lan"
        assert notifications[-1]["action"] == "update_settings"
        assert notifications[-1]["kind"] == "notification"
        assert match_subdict(data, notifications[-1]["data"])

        res = infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )
        assert res["module"] == "lan"
        assert res["action"] == "get_settings"
        assert res["kind"] == "reply"

        data_lan_redirect = data.pop("lan_redirect", None)
        res_lan_redirect = res["data"].pop("lan_redirect")
        if data_lan_redirect:
            # we can get lan_redirect in reply data regardless of whether we updated it or not
            # so compare it only in case of updated lan_redirect
            assert data_lan_redirect == res_lan_redirect

        assert match_subdict(data, res["data"])

    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.5.8",
                "netmask": "255.255.255.0",
                "dhcp": {"enabled": False},
            },
            "lan_redirect": False,
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.0.0.3",
                "netmask": "255.255.0.0",
                "dhcp": {"enabled": False},
            },
            "lan_redirect": True,
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.3",
                "netmask": "255.252.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 1,
                },
            },
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.2.0.3",
                "netmask": "255.255.0.0",
                "dhcp": {"enabled": False},
            },
        }
    )

    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {"hostname": "bogatyr"}},
        }
    )

    update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {}}})

    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                },
            },
        }
    )

    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                    "dns1": "1.1.1.1",
                },
            },
        }
    )

    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                    "dns1": "1.1.1.2",
                    "dns2": "8.8.8.8",
                },
            },
        }
    )

    update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "none"}})


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_wrong_update(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,
):
    def update(data):
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_settings", "kind": "request", "data": data}
        )
        assert "errors" in res

    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.3",
                "netmask": "255.255.0.0",
                "dhcp": {
                    "enabled": False,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 2,
                },
            },
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.3",
                "netmask": "255.250.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 3,
                },
            },
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.256",
                "netmask": "255.255.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 4,
                },
            },
        }
    )
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.1",
                "netmask": "255.255.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 119,  # too small
                },
            },
        }
    )

    update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "dhcp"}})
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.256",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                },
            },
        }
    )
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.250.0.0",
                    "gateway": "10.4.0.1",
                },
            },
        }
    )
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.256.1",
                },
            },
        }
    )
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                    "dns1": "192.168.256.1",
                },
            },
        }
    )
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                    "dns2": "192.168.256.1",
                },
            },
        }
    )
    update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "none", "lan_none": {}}})


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.parametrize(
    "orig_backend_val,api_val,new_backend_val",
    [
        ["", 12 * 60 * 60, "43200"],
        ["infinite", 0, "infinite"],
        ["120", 120, "120"],
        ["3m", 180, "180"],
        ["2h", 7200, "7200"],
        ["1d", 86400, "86400"],
    ],
    ids=["none", "infinite", "120", "3m", "2h", "1d"],
)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_lease(
    uci_configs_init,
    infrastructure,
    network_restart_command,
    orig_backend_val,
    api_val,
    new_backend_val,
    device,
    turris_os_version,
    lan_dnsmasq_files
):
    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("dhcp", "lan", "leasetime", orig_backend_val)

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["mode_managed"]["dhcp"]["lease_time"] == api_val

    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "10.1.0.3",
                    "netmask": "255.252.0.0",
                    "dhcp": {"enabled": True, "start": 10, "limit": 50, "lease_time": api_val},
                },
            },
        }
    )
    assert res["data"]["result"]

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()

    assert uci.get_option_named(data, "dhcp", "lan", "leasetime") == new_backend_val


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("device,turris_os_version", [("mox","5.0")], indirect=True)
def test_dhcp_lease_multi_mac(uci_configs_init, infrastructure, device, turris_os_version):
    """ In case user sets `host` with list of options or string separated by space for mac address. """
    uci = get_uci_module(infrastructure.name)

    # list
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.114")
        backend.set_option("dhcp", section, "name", "grogu")
        backend.add_to_list("dhcp", section, "mac", ['A4:34:D9:ED:8B:6D', '50:7B:9D:D5:A9:65'])

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    # space separated
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_section("dhcp","@host[0]")
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.114")
        backend.set_option("dhcp", section, "name", "grogu")
        backend.set_option("dhcp", section, "mac", 'A4:34:D9:ED:8B:6D 50:7B:9D:D5:A9:65')

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("device,turris_os_version", [("mox","5.0")], indirect=True)
def test_dhcp_lease_static_attr(uci_configs_init, infrastructure, device, turris_os_version, lan_dnsmasq_files):
    """Test whether static lease which is at the same time in dhcp.leases file is considered as 'static'
    I.e. Check that dynamic and static info of host gets merged into one static record
    """
    # prepare static record
    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.101")
        backend.set_option("dhcp", section, "name", "prvni")
        backend.set_option("dhcp", section, "mac", "11:22:33:44:55:66")

    res = query_infrastructure(infrastructure, {"module": "lan", "action": "get_settings", "kind": "request"})

    clients = res["data"]["mode_managed"]["dhcp"]["clients"]
    assert len(clients) == 1
    assert clients[0]["ip"] == "192.168.1.101"
    assert clients[0]["hostname"] == "prvni"
    assert clients[0]["static"] is True


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_update_settings_openwrt(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,
):
    uci = get_uci_module(infrastructure.name)

    def update(data):
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_settings", "kind": "request", "data": data}
        )
        assert "errors" not in res
        assert res["data"]["result"]

        with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
            return backend.read()

    data = update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.5.8",
                "netmask": "255.255.255.0",
                "dhcp": {"enabled": False},
            },
            "lan_redirect": False,
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "managed"
    assert uci.get_option_named(data, "network", "lan", "proto") == "static"
    assert uci.get_option_named(data, "network", "lan", "ipaddr") == ["192.168.5.8/24"]
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "network", "lan", "device") == "br-lan"
    assert not uci.parse_bool(uci.get_option_named(data, "firewall", "redirect_192_168_1_1", "enabled"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.3",
                "netmask": "255.252.0.0",
                "dhcp": {"enabled": True, "start": 10, "limit": 50, "lease_time": 0},
            },
            "lan_redirect": True,
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "managed"
    assert uci.get_option_named(data, "network", "lan", "proto") == "static"
    assert uci.get_option_named(data, "network", "lan", "ipaddr") == ["10.1.0.3/14"]
    assert not uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "start") == "10"
    assert uci.get_option_named(data, "dhcp", "lan", "limit") == "50"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcp_option") == ["6,10.1.0.3"]
    assert uci.parse_bool(uci.get_option_named(data, "firewall", "redirect_192_168_1_1", "enabled"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "server"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "server"

    data = update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {"hostname": "bogatyr"}},
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "dhcp"
    assert uci.get_option_named(data, "network", "lan", "hostname") == "bogatyr"
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {}}})
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "dhcp"
    assert uci.get_option_named(data, "network", "lan", "hostname") == "bogatyr"
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {"hostname": ""}},
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "dhcp"
    assert uci.get_option_named(data, "network", "lan", "hostname", "") == ""
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                },
            },
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "static"
    assert uci.get_option_named(data, "network", "lan", "ipaddr") == ["10.4.0.2/15"]
    assert uci.get_option_named(data, "network", "lan", "gateway") == "10.4.0.1"
    assert uci.get_option_named(data, "network", "lan", "dns", []) == []
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.5.0.2",
                    "netmask": "255.255.254.0",
                    "gateway": "10.4.0.8",
                    "dns1": "1.1.1.1",
                },
            },
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "static"
    assert uci.get_option_named(data, "network", "lan", "ipaddr") == ["10.5.0.2/23"]
    assert uci.get_option_named(data, "network", "lan", "gateway") == "10.4.0.8"
    assert uci.get_option_named(data, "network", "lan", "dns") == ["1.1.1.1"]
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {
                "lan_type": "static",
                "lan_static": {
                    "ip": "10.4.0.2",
                    "netmask": "255.254.0.0",
                    "gateway": "10.4.0.1",
                    "dns1": "1.1.1.2",
                    "dns2": "8.8.8.8",
                },
            },
        }
    )
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "static"
    assert uci.get_option_named(data, "network", "lan", "ipaddr") == ["10.4.0.2/15"]
    assert uci.get_option_named(data, "network", "lan", "gateway") == "10.4.0.1"
    assert uci.get_option_named(data, "network", "lan", "dns") == ["8.8.8.8", "1.1.1.2"]
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"

    data = update({"mode": "unmanaged", "mode_unmanaged": {"lan_type": "none"}})
    assert uci.get_option_named(data, "network", "lan", "_turris_mode") == "unmanaged"
    assert uci.get_option_named(data, "network", "lan", "proto") == "none"
    assert uci.parse_bool(uci.get_option_named(data, "dhcp", "lan", "ignore"))
    assert uci.get_option_named(data, "dhcp", "lan", "ra") == "disabled"
    assert uci.get_option_named(data, "dhcp", "lan", "dhcpv6") == "disabled"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt(
    uci_configs_init,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
):
    def update(data, clients):
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_settings", "kind": "request", "data": data}
        )
        assert res == {
            "action": "update_settings",
            "data": {"result": True},
            "kind": "reply",
            "module": "lan",
        }
        res = infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )
        assert res["data"]["mode_managed"]["dhcp"]["clients"] == clients

    # Return both
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.1.1",
                "netmask": "255.252.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 1,
                },
            },
        },
        [
            {
                "ip": "192.168.1.101",
                "mac": "11:22:33:44:55:66",
                "expires": 1539350186,
                "active": True,
                "hostname": "prvni",
                "static": False,
            },
            {
                "ip": "192.168.2.1",
                "mac": "99:88:77:66:55:44",
                "expires": 1539350188,
                "active": False,
                "hostname": "*",
                "static": False,
            },
        ],
    )

    # Return other mode
    update(
        {
            "mode": "unmanaged",
            "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {"hostname": "bogatyr"}},
        },
        [],
    )

    # Return empty when disabled
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.1.1",
                "netmask": "255.252.0.0",
                "dhcp": {"enabled": False},
            },
        },
        [],
    )

    # Return first
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.1.1",
                "netmask": "255.255.255.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 1,
                },
            },
        },
        [
            {
                "ip": "192.168.1.101",
                "mac": "11:22:33:44:55:66",
                "expires": 1539350186,
                "active": True,
                "hostname": "prvni",
                "static": False,
            }
        ],
    )

    # Return second
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.2.1",
                "netmask": "255.255.255.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 1,
                },
            },
        },
        [
            {
                "ip": "192.168.2.1",
                "mac": "99:88:77:66:55:44",
                "expires": 1539350188,
                "active": False,
                "hostname": "*",
                "static": False,
            }
        ],
    )

    # Missed range
    update(
        {
            "mode": "managed",
            "mode_managed": {
                "router_ip": "10.1.0.3",
                "netmask": "255.252.0.0",
                "dhcp": {
                    "enabled": True,
                    "start": 10,
                    "limit": 50,
                    "lease_time": 24 * 60 * 60 + 1,
                },
            },
        },
        [],
    )


@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_case_insensitive_mac_addreses(
    uci_configs_init,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
):
    """Test whether foris-controller can handle case insensitive MAC adresses lookup"""

    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.128")
        backend.set_option("dhcp", section, "name", "myhost")
        backend.set_option("dhcp", section, "mac", "1a:2b:3c:4d:5e:6f")

    case_sensitive_data = {
        "hostname": "newhostname",
        "ip": "192.168.1.150",
        "mac": "1a:2b:3c:4d:5e:6f",
    }

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": case_sensitive_data},
    )
    assert res["data"]["reason"] == "mac-exists"

    # upper case MAC lookup
    case_sensitive_data["mac"] = "1A:2B:3C:4D:5E:6F"
    query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": case_sensitive_data},
    )
    assert res["data"]["reason"] == "mac-exists"

    # mixed case MAC lookup
    case_sensitive_data["mac"] = "1a:2b:3c:4D:5E:6F"
    query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": case_sensitive_data},
    )
    assert res["data"]["reason"] == "mac-exists"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_multimac_openwrt(
    uci_configs_init,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    init_script_result,
):
    """Test static leases management with multiple macs set on dhcp hosts

    1) Getting client list should return only first mac address from record with multiple mac addresses.
    1a) MAC addresses as uci `option` with space separated MACs
    1b) MAC addresses as uci `list`
    2) Set/Update allow only single mac address.
    3) Create new record should check for duplicity of mac address in multimac records,
        i.e. don't check "if new_mac == record_mac", but check "if new_mac in record_mac" instead.
    3a) MAC addresses as uci `list`
    3b) MAC addresses as uci `option` with space separated MACs
    4) Update of record with multiple mac addresses should delete the original record
        and create new with just one mac address (requested in update) to avoid collisions of ip/hostname
    5) Delete of record with multiple mac addresses
    5a) Deleting record with multiple mac addresses should only delete the specific mac address
         and keep the rest of original record intact.
    5b) Deleting single mac from multiple mac addresses (>2) should keep remaining macs (>=2)
    """
    def host_in_result(clients: typing.List[dict], ip: str, mac: str, hostname: str, present: bool = True):
        assert (
            len(
                [
                    e
                    for e in clients
                    if e["ip"] == ip
                    and e["mac"] == mac
                    and e["hostname"] == hostname
                ]
            )
            == (1 if present else 0)
        )

    def get_dhcpv4_clients() -> typing.List[dict]:
        """Get dhcpv4 clients records from backend."""
        message = {"module": "lan", "action": "get_settings", "kind": "request"}
        reply = query_infrastructure(infrastructure, message)

        return reply["data"]["mode_managed"]["dhcp"]["clients"]

    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.126")
        backend.set_option("dhcp", section, "name", "multimac1")
        backend.set_option("dhcp", section, "mac", "11:22:33:11:22:33 33:22:11:11:22:33")

    # (1a)
    clients_list = get_dhcpv4_clients()
    clients_count = len(clients_list)

    host_in_result(clients_list, "192.168.1.126", "11:22:33:11:22:33", "multimac1", present=True)

    # (1b)
    # list of macs
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_option("dhcp", section, "mac")
        backend.add_to_list("dhcp", section, "mac", ["11:22:33:11:22:33", "33:22:11:11:22:33"])

    clients_list = get_dhcpv4_clients()
    clients_count = len(clients_list)

    host_in_result(clients_list, "192.168.1.126", "11:22:33:11:22:33", "multimac1", present=True)

    # (2)
    multimac_data = {
        "mac": "44:55:66:66:55:44 55:66:77:77:66:55",
        "ip": "192.168.1.120",
        "hostname": "multimac2",
    }

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": multimac_data},
        expect_success=False
    )
    assert "ValidationError" in res["errors"][0]["stacktrace"]

    clients_list = get_dhcpv4_clients()

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "129.168.1.120", "44:55:66:66:55:44 55:66:77:77:66:55", "multimac2", present=False)

    single_mac_data = {
        "mac": "44:55:66:66:55:44",
        "ip": "192.168.1.120",
        "hostname": "singlemac",
    }

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": single_mac_data}
    )

    clients_list = get_dhcpv4_clients()
    clients_count += 1

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.120", "44:55:66:66:55:44", "singlemac", present=True)

    # (3a)
    mac_already_in_multimac_data = {
        "mac": "33:22:11:11:22:33",
        "ip": "192.168.1.121",
        "hostname": "newclient",
    }
    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": mac_already_in_multimac_data}
    )

    clients_list = get_dhcpv4_clients()

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.121", "33:22:11:11:22:33", "newclient", present=False)

    # (3b)
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_from_list("dhcp", section, "mac")
        backend.set_option("dhcp", section, "mac", "11:22:33:11:22:33 33:22:11:11:22:33")

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": mac_already_in_multimac_data}
    )

    clients_list = get_dhcpv4_clients()

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.121", "33:22:11:11:22:33", "newclient", present=False)

    # (4)
    part_of_multimac_data_update = {
        "old_mac": "33:22:11:11:22:33",
        "mac": "33:22:11:11:22:33",
        "ip": "192.168.1.121",
        "hostname": "newsplit",
    }

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "update_dhcp_client", "kind": "request", "data": part_of_multimac_data_update}
    )

    clients_list = get_dhcpv4_clients()
    assert len(clients_list) == clients_count

    host_in_result(clients_list, "192.168.1.126", "11:22:33:11:22:33", "multimac1", present=False)
    host_in_result(clients_list, "192.168.1.121", "33:22:11:11:22:33", "newsplit", present=True)

    # (5a)
    # prepare another multimac record first
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.128")
        backend.set_option("dhcp", section, "name", "multimac2")
        backend.set_option("dhcp", section, "mac", "44:55:66:44:55:66 77:88:99:99:88:77")

    clients_list = get_dhcpv4_clients()
    clients_count += 1

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.128", "44:55:66:44:55:66", "multimac2", present=True)

    cut_single_mac_out_data = {"mac": "44:55:66:44:55:66"}
    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "delete_dhcp_client", "kind": "request", "data": cut_single_mac_out_data}
    )

    clients_list = get_dhcpv4_clients()

    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.128", "77:88:99:99:88:77", "multimac2", present=True)
    host_in_result(clients_list, "192.168.1.128", "44:55:66:44:55:66", "multimac2", present=False)

    # (5b)
    # prepare another multimac record first
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_section("dhcp","@host[-1]")
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.128")
        backend.set_option("dhcp", section, "name", "multimac3")
        backend.set_option("dhcp", section, "mac", "44:55:66:44:55:66 77:88:99:99:88:77 AA:BB:CC:DD:EE:FF")

    res = query_infrastructure(
        infrastructure,
        {"module": "lan", "action": "delete_dhcp_client", "kind": "request", "data": cut_single_mac_out_data}
    )

    clients_list = get_dhcpv4_clients()
    assert len(clients_list) == clients_count
    host_in_result(clients_list, "192.168.1.128", "77:88:99:99:88:77", "multimac3", present=True)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()
    assert uci.get_option_anonymous(data, "dhcp", "host", -1, "mac") == "77:88:99:99:88:77 AA:BB:CC:DD:EE:FF"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt_ipv6leases(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
):
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    dhcpv6_clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert len(dhcpv6_clients) == 3
    assert dhcpv6_clients[2]["active"]
    assert dhcpv6_clients[2]["ipv6"] == "fd52:ad42:910e::64fa"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt_ipv6leases_with_ipv6_prefix(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    dhcpv6_leases_ipv6_prefix,
):
    """We are interested only in IPv6 addresses for reForis LAN page.

    Test that dhcpv6 leases with IPv6 prefix (e.g. for downstream IPv6 capable router) are ignored
    and only IPv6 addresses of such devices are returned.
    """
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    dhcpv6_clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert len(dhcpv6_clients) == 1
    assert dhcpv6_clients[0]["active"]
    assert dhcpv6_clients[0]["ipv6"] == "fd60:ad42:a6c9::4"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt_ipv6leases_missing_lan_bridge(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    dhcpv6_leases_missing_lan_bridge,
):
    """Test that missing dhcpv6 leases info for lan bridge won't break fetching dhcpv6 clients.

    In case that odhcpd is not managing leases for lan bridge, we should get no leases.
    """
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    dhcpv6_clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert len(dhcpv6_clients) == 0


@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt_ipv6leases_negative_leasetime(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    dhcpv6_leases_negative_leasetime,
):
    """Test that dhcpv6 leases with negative lease time does not break fetching of leases.

    According to `odhcpd` source code, negative lease time points to some errors with lease time string.
    However, in that case we should fall back to some value that passes json schema validation.

    For instance: "-1" => "0"
    """
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    dhcpv6_clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert len(dhcpv6_clients) == 2
    assert dhcpv6_clients[0]["expires"] >= 0  # regular leasetime
    assert dhcpv6_clients[1]["expires"] == 0  # negative leasetime


@pytest.mark.parametrize("device,turris_os_version", [("mox", "6.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_clients_openwrt_ipv6leases_junk_leasetime(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    dhcpv6_leases_junk_leasetime,
):
    """Test that dhcpv6 leases with some sort of "junk" lease time does not break fetching of leases.

    These junk values are really not expected during regular operation and such leases should be ignored.
    """
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    dhcpv6_clients = res["data"]["mode_managed"]["dhcp"]["ipv6clients"]
    assert len(dhcpv6_clients) == 1  # the other malformed lease should not be there
    assert dhcpv6_clients[0]["hostname"] == "good-lease"
    assert isinstance(dhcpv6_clients[0]["expires"], int)
    assert dhcpv6_clients[0]["expires"] >= 0


@pytest.mark.file_root_path(WIFI_ROOT_PATH)
@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_interface_count(
    file_root_init,
    uci_configs_init,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    fix_mox_wan
):
    prepare_turrishw("mox")  # plain mox without any boards

    def set_and_test(networks, wifi_devices, count):
        res = infrastructure.process_message(
            {
                "module": "networks",
                "action": "update_settings",
                "kind": "request",
                "data": {
                    "firewall": {"ssh_on_wan": False, "http_on_wan": False, "https_on_wan": False},
                    "networks": networks,
                },
            }
        )
        assert res["data"] == {"result": True}
        res = infrastructure.process_message(
            {
                "module": "wifi",
                "action": "update_settings",
                "kind": "request",
                "data": {"devices": wifi_devices},
            }
        )
        assert res["data"] == {"result": True}
        res = infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )
        assert res["data"]["interface_count"] == count

    # No wifi no interfaces
    set_and_test(
        {"wan": [], "lan": [], "guest": [], "none": ["eth0"]},
        [{"id": 0, "enabled": False}, {"id": 1, "enabled": False}],
        0,
    )

    # Single interface no wifi
    set_and_test(
        {"wan": [], "lan": ["eth0"], "guest": [], "none": []},
        [{"id": 0, "enabled": False}, {"id": 1, "enabled": False}],
        1,
    )

    # One wifi no interface
    set_and_test(
        {"wan": ["eth0"], "lan": [], "guest": [], "none": []},
        [
            {
                "id": 0,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 11,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {"enabled": False},
            },
            {"id": 1, "enabled": False},
        ],
        1,
    )
    set_and_test(
        {"wan": [], "lan": [], "guest": ["eth0"], "none": []},
        [
            {"id": 0, "enabled": False},
            {
                "id": 1,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 11,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {
                    "enabled": True,
                    "SSID": "Turris-testik",
                    "password": "ssapssap",
                    "encryption": WIFI_DEFAULT_ENCRYPTION,
                },
            },
        ],
        1,
    )

    # two wifis no interface
    set_and_test(
        {"wan": [], "lan": [], "guest": ["eth0"], "none": []},
        [
            {
                "id": 0,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 11,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {"enabled": False},
            },
            {
                "id": 1,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 8,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {
                    "enabled": True,
                    "SSID": "Turris-testik",
                    "password": "ssapssap",
                    "encryption": WIFI_DEFAULT_ENCRYPTION,
                },
            },
        ],
        2,
    )

    # interface and wifis enabled
    set_and_test(
        {"wan": [], "lan": ["eth0"], "guest": [], "none": []},
        [
            {
                "id": 0,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 11,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {"enabled": False},
            },
            {
                "id": 1,
                "enabled": True,
                "SSID": "Turris",
                "hidden": False,
                "channel": 8,
                "htmode": "HT20",
                "hwmode": "11g",
                "encryption": WIFI_DEFAULT_ENCRYPTION,
                "ieee80211w_disabled": False,
                "password": "passpass",
                "guest_wifi": {
                    "enabled": True,
                    "SSID": "Turris-testik",
                    "password": "ssapssap",
                    "encryption": WIFI_DEFAULT_ENCRYPTION,
                },
            },
        ],
        3,
    )


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_update_settings_dhcp_range(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,
):
    def update(ip, netmask, start, limit, result):
        res = infrastructure.process_message(
            {
                "module": "lan",
                "action": "update_settings",
                "kind": "request",
                "data": {
                    "mode": "managed",
                    "mode_managed": {
                        "router_ip": ip,
                        "netmask": netmask,
                        "dhcp": {
                            "enabled": True,
                            "start": start,
                            "limit": limit,
                            "lease_time": 24 * 60 * 60 + 1,
                        },
                    },
                },
            }
        )
        assert res == {
            "action": "update_settings",
            "data": {"result": result},
            "kind": "reply",
            "module": "lan",
        }

    # default
    update("192.168.1.1", "255.255.255.0", 150, 100, True)
    # last
    update("192.168.1.1", "255.255.255.0", 150, 104, True)
    # first wrong
    update("192.168.1.1", "255.255.255.0", 150, 106, False)
    # other range
    update("10.10.0.1", "255.255.192.0", (2 ** 13), (2 ** 13) - 2, True)
    # too high number
    update("10.10.0.1", "255.255.192.0", (2 ** 32), 1, False)
    # last valid router ip
    update("192.168.1.99", "255.255.255.0", 100, 150, True)
    # router ip in range
    update("192.168.1.100", "255.255.255.0", 100, 150, False)


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_get_settings_dns_option(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,
):
    uci = get_uci_module(infrastructure.name)

    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "unmanaged",
                "mode_unmanaged": {
                    "lan_type": "static",
                    "lan_static": {
                        "ip": "10.4.0.2",
                        "netmask": "255.254.0.0",
                        "gateway": "10.4.0.1",
                        "dns1": "2.2.2.2",
                        "dns2": "8.8.8.8",
                    },
                },
            },
        }
    )
    assert res["data"]["result"]

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_option("network", "lan", "dns")
        backend.set_option("network", "lan", "dns", "1.1.1.1 8.8.8.8")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["mode_unmanaged"]["lan_static"]["dns1"] == "8.8.8.8"
    assert res["data"]["mode_unmanaged"]["lan_static"]["dns2"] == "1.1.1.1"


@pytest.mark.only_backends(["openwrt"])
def test_get_settings_missing_wireless(uci_configs_init, infrastructure, lan_dnsmasq_files):
    os.unlink(os.path.join(uci_configs_init[0], "wireless"))
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_dhcp_client_settings(
    uci_configs_init,
    init_script_result,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
):
    filters = [("lan", "set_dhcp_client")]

    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 10,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    def set_client(data, reason=None):
        notifications = infrastructure.get_notifications(filters=filters)
        res = infrastructure.process_message(
            {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": data}
        )

        assert res["data"]["result"] is True or res["data"]["reason"] == reason
        if not reason:
            notifications = infrastructure.get_notifications(notifications, filters=filters)
            assert notifications[-1] == {
                "module": "lan",
                "action": "set_dhcp_client",
                "kind": "notification",
                "data": data,
            }

        return infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )["data"]["mode_managed"]["dhcp"]["clients"]

    def update_client(data, reason=None):
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_dhcp_client", "kind": "request", "data": data}
        )
        assert res["data"]["result"] is True or res["data"]["reason"] == reason

        return infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )["data"]["mode_managed"]["dhcp"]["clients"]

    # set all
    client_list = set_client(
        {"mac": "81:22:33:44:55:66", "hostname": "static-client1", "ip": "192.168.1.5"}
    )
    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.5"
                and e["mac"] == "81:22:33:44:55:66"
                and e["hostname"] == "static-client1"
            ]
        )
        == 1
    )

    # ignore -> don't assign ip
    client_list = set_client({"mac": "84:22:33:44:55:66", "hostname": "static2", "ip": "ignore"})
    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "ignore" and e["mac"] == "84:22:33:44:55:66" and e["hostname"] == "static2"
            ]
        )
        == 1
    )

    # test uppercase conversion
    client_list = set_client({"mac": "aa:bb:cc:dd:55:66", "hostname": "static3", "ip": "192.168.1.7"})
    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.7"
                and e["mac"] == "AA:BB:CC:DD:55:66"
                and e["hostname"] == "static3"
            ]
        )
        == 1
    )

    # do not allow set the same IP for two macs
    update_client(
        {"old_mac": "81:22:33:44:55:66", "mac": "81:22:33:44:55:66", "hostname": "static-client1", "ip": "192.168.1.3"}
    )
    set_client({"mac": "82:22:33:44:55:66", "hostname": "static4", "ip": "192.168.1.3"}, "ip-exists")

    client_list = set_client({"mac": "82:22:33:44:55:66", "hostname": "static4", "ip": "192.168.1.9"})

    orig_client_list = client_list

    # out of lan
    client_list = update_client(
        {"old_mac": "82:22:33:44:55:66", "mac": "82:22:33:44:55:66", "hostname": "static4", "ip": "192.168.2.3"},
        "out-of-network"
    )
    assert orig_client_list == client_list

    # clear if in dynamic
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 5,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]
    assert "192.168.1.9" not in [e["ip"] for e in client_list]

    # clear when out of network range
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.5.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 5,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]
    assert "192.168.1.3" not in [e["ip"] for e in client_list]

    orig_client_list = client_list

    # dhcp disabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.5.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {"enabled": False},
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    set_client({"mac": "82:22:33:44:55:66", "hostname": "static4", "ip": "192.168.5.3"}, "disabled")

    # unmanaged mode
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "unmanaged",
                "mode_unmanaged": {"lan_type": "dhcp", "lan_dhcp": {"hostname": "gromoboj"}},
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    set_client({"mac": "82:22:33:44:55:66", "hostname": "static4", "ip": "192.168.5.3"}, "disabled")


@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
def test_dhcp_update_non_existing_client(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    network_restart_command,
):
    """Test that we cannot update non-existing dhcp client settings"""
    data = {
        "old_mac": "DE:AD:BE:EF:12:34",
        "mac": "DE:AD:BE:EF:12:34",
        "hostname": "static-client1",
        "ip": "192.168.1.10",
    }

    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    res = infrastructure.process_message(
        {"module": "lan", "action": "update_dhcp_client", "kind": "request", "data": data}
    )
    assert "errors" not in res.keys()
    assert res["data"]["result"] is False
    assert "reason" in res["data"]
    assert res["data"]["reason"] == "mac-not-exists"


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
def test_dhcp_update_multi_mac_client(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    network_restart_command,
):
    """Test that we cannot update client with multiple macs set

    NOTE: is this test still needed?
    """
    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.123")
        backend.set_option("dhcp", section, "name", "multimac")
        backend.set_option("dhcp", section, "mac", 'A4:34:D9:ED:8B:6D 50:7B:9D:D5:A9:65')

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    client_list = res["data"]["mode_managed"]["dhcp"]["clients"]
    assert len(client_list) == 1
    assert client_list[0]["mac"] == "A4:34:D9:ED:8B:6D"

    data = {
        "old_mac": "A4:34:D9:ED:8B:6D",
        "mac": "A4:34:D9:ED:8B:6D 50:7B:9D:D5:A9:65",
        "ip": "192.168.1.456",
        "name": "multimac",
    }

    # this update should fail
    res = infrastructure.process_message(
        {"module": "lan", "action": "update_dhcp_client", "kind": "request", "data": data}
    )
    assert "errors" in res.keys()
    assert "Incorrect input" in res["errors"][0]["description"]


@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
def test_dhcp_set_client(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    network_restart_command,
    lan_dnsmasq_files,
    init_script_result,
):
    """Test that setting new client cannot overwrite existing record with the same MAC address"""
    data = {
        "mac": "DE:AD:BE:EF:12:34",
        "hostname": "static-client1",
        "ip": "192.168.1.10",
    }

    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    # set dhcp lease first
    res = infrastructure.process_message(
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": data}
    )
    assert "errors" not in res.keys()
    assert "result" in res["data"]
    assert res["data"]["result"] is True

    newdata = {
        "mac": "DE:AD:BE:EF:12:34",
        "hostname": "static-client2",
        "ip": "192.168.1.20",
    }

    # try to set new lease with the same mac
    res = infrastructure.process_message(
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": newdata}
    )

    assert "errors" not in res.keys()
    assert "result" in res["data"]
    assert res["data"]["result"] is False
    assert "reason" in res["data"]
    assert res["data"]["reason"] == "mac-exists"


@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
def test_dhcp_delete_client(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    network_restart_command,
    lan_dnsmasq_files,
    init_script_result,
):
    data = {
        "mac": "DE:AD:BE:EF:56:78",
        "hostname": "static1",
        "ip": "192.168.1.11",
    }

    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    res = infrastructure.process_message(
        {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": data}
    )
    assert "errors" not in res.keys()
    assert "result" in res["data"]
    assert res["data"]["result"] is True
    assert "reason" not in res["data"]  # setting dhcp client succeeded

    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]

    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.11"
                and e["mac"] == "DE:AD:BE:EF:56:78"
                and e["hostname"] == "static1"
            ]
        )
        == 1
    )

    res = infrastructure.process_message(
        {"module": "lan", "action": "delete_dhcp_client", "kind": "request", "data": {"mac": "DE:AD:BE:EF:56:78"}}
    )
    assert "errors" not in res.keys()

    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]

    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.11"
                and e["mac"] == "DE:AD:BE:EF:56:78"
                and e["hostname"] == "static-client1"
            ]
        )
        == 0
    )


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("device,turris_os_version", [("mox", "5.0")], indirect=True)
def test_dhcp_delete_client_openwrt(
    uci_configs_init,
    infrastructure,
    device,
    turris_os_version,
    network_restart_command,
    lan_dnsmasq_files,
    init_script_result,
):
    # make sure that dhcp is enabled
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 20,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section, "ip", "192.168.1.123")
        backend.set_option("dhcp", section, "name", "multimac")
        backend.set_option("dhcp", section, "mac", 'A4:34:D9:ED:8B:6D 50:7B:9D:D5:A9:65')

    res = infrastructure.process_message(
        {"module": "lan", "action": "delete_dhcp_client", "kind": "request", "data": {"mac": "A4:34:D9:ED:8B:6D"}}
    )
    assert "errors" not in res.keys()

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()

    dhcp_hosts_uci = [dict(e["data"]) for e in uci.get_sections_by_type(data, "dhcp", "host")]
    assert len(dhcp_hosts_uci) == 1

    first_record = dhcp_hosts_uci[0]
    assert first_record["mac"] == "50:7B:9D:D5:A9:65"

    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]

    # make sure that we accidentally didn't deleted wrong mac
    # this should not exists anymore
    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.123"
                and e["mac"] == "A4:34:D9:ED:8B:6D"
                and e["hostname"] == "multimac"
            ]
        )
        == 0
    )
    # but second mac should still exists
    assert (
        len(
            [
                e
                for e in client_list
                if e["ip"] == "192.168.1.123"
                and e["mac"] == "50:7B:9D:D5:A9:65"
                and e["hostname"] == "multimac"
            ]
        )
        == 1
    )


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_dhcp_client_settings_openwrt(
    uci_configs_init,
    infrastructure,
    network_restart_command,
    device,
    turris_os_version,
    lan_dnsmasq_files,
    init_script_result,
):

    uci = get_uci_module(infrastructure.name)

    def get_uci_data():
        with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
            data = backend.read()

        return [dict(e["data"]) for e in uci.get_sections_by_type(data, "dhcp", "host")]

    def set_client(data):
        res = infrastructure.process_message(
            {"module": "lan", "action": "set_dhcp_client", "kind": "request", "data": data}
        )
        assert res == {
            "action": "set_dhcp_client",
            "kind": "reply",
            "module": "lan",
            "data": {"result": True},
        }

        infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )
        check_service_result("dnsmasq", "restart", True)

        return get_uci_data()

    def update_client(data):
        res = infrastructure.process_message(
            {"module": "lan", "action": "update_dhcp_client", "kind": "request", "data": data}
        )
        assert res == {
            "action": "update_dhcp_client",
            "kind": "reply",
            "module": "lan",
            "data": {"result": True},
        }

        infrastructure.process_message(
            {"module": "lan", "action": "get_settings", "kind": "request"}
        )
        check_service_result("dnsmasq", "restart", passed=True)

        return get_uci_data()

    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.8.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 10,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }

    # full
    data = set_client(
        {"mac": "AA:22:33:44:55:66", "hostname": "my-second-hostname", "ip": "192.168.8.4"}
    )
    assert {
        "ip": "192.168.8.4",
        "name": "my-second-hostname",
        "mac": "AA:22:33:44:55:66",
        "leasetime": "infinite",
        "dns": "1",
    } in data

    # ignored
    data = set_client({"mac": "CC:22:33:44:55:66", "hostname": "ignored", "ip": "ignore"})
    assert {
        "ip": "ignore", "mac": "CC:22:33:44:55:66", "name": "ignored", "leasetime": "infinite", "dns": "1"
    } in data

    # multiple macs
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]

    assert len(res) == 2  # full, ignore

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("dhcp", "@host[0]", "mac", "DD:22:33:44:55:66 EE:22:33:44:55:66")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]

    assert len(res) == 2  # multimac, but only first mac is returned
    assert "DD:22:33:44:55:66" in [e["mac"] for e in res]

    # split records on save - delete original and create new one with single mac address
    uci_data = update_client(
        {
            "old_mac": "EE:22:33:44:55:66",
            "mac": "EE:22:33:44:55:66",
            "hostname": "splitted",
            "ip": "192.168.8.2",
        }
    )
    assert len(uci_data) == 2
    assert "DD:22:33:44:55:66" not in [e["mac"] for e in uci_data]
    assert "EE:22:33:44:55:66" in [e["mac"] for e in uci_data]

    # delete record if dynamic overlaps
    set_client({"mac": "BB:22:33:44:55:66", "hostname": "out-of-network", "ip": "192.168.8.8"})
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.8.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 5,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )
    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    uci_data = get_uci_data()
    assert len(uci_data) == 2
    assert "192.168.8.8" not in [e["ip"] for e in uci_data]

    # delete record if it doesn't fit in network range
    assert "192.168.8.2" in [e["ip"] for e in uci_data]
    res = infrastructure.process_message(
        {
            "module": "lan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "mode": "managed",
                "mode_managed": {
                    "router_ip": "192.168.9.1",
                    "netmask": "255.255.255.0",
                    "dhcp": {
                        "enabled": True,
                        "start": 5,
                        "limit": 50,
                        "lease_time": 24 * 60 * 60,
                    },
                },
            },
        }
    )

    assert res == {
        "action": "update_settings",
        "data": {"result": True},
        "kind": "reply",
        "module": "lan",
    }
    uci_data = get_uci_data()
    assert len(uci_data) == 1
    assert "192.168.8.2" not in [e["ip"] for e in uci_data]
    assert "192.168.8.4" not in [e["ip"] for e in uci_data]

    # test missing mac in dhcp client
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        section_name = backend.add_section("dhcp", "host")
        backend.set_option("dhcp", section_name, "ip", "192.168.9.25")  # only ip is mandatory
    client_list = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )["data"]["mode_managed"]["dhcp"]["clients"]
    assert "192.168.9.25" not in [e["ip"] for e in client_list]

    # test tab in macaddress field
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("dhcp", "@host[0]", "mac", "\tEE:22:33:44:55:66")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_ipv6_address_in_dns(uci_configs_init, infrastructure, device, turris_os_version, lan_dnsmasq_files):
    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("network", "lan", "dns", "ff::")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res


def test_get_settings_lan_redirect(uci_configs_init, infrastructure, lan_dnsmasq_files):
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert res["data"]["lan_redirect"]


@pytest.mark.only_backends(["openwrt"])
def test_get_settings_lan_redirect_openwrt(uci_configs_init, infrastructure, lan_dnsmasq_files):
    uci = get_uci_module(infrastructure.name)

    # with redirect_192_168_1_1.enabled set it should return its value
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("firewall", "redirect_192_168_1_1", "enabled", 0)

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert res["data"]["lan_redirect"] is False

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.set_option("firewall", "redirect_192_168_1_1", "enabled", 1)

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert res["data"]["lan_redirect"]

    # with redirect_192_168_1_1.enabled unset it should return lan_redirect == True
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_option("firewall", "redirect_192_168_1_1", "enabled")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )

    assert "errors" not in res.keys()
    assert res["data"]["lan_redirect"]

    # with missing section redirect_192_168_1_1 it shouldn't return lan_redirect
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_section("firewall", "redirect_192_168_1_1")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )

    assert "errors" not in res.keys()
    assert "lan_redirect" not in res["data"].keys()


@pytest.mark.only_backends(["openwrt"])
def test_ip_slash_netmask(uci_configs_init, infrastructure):
    uci = get_uci_module(infrastructure.name)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        backend.del_option("network", "lan", "netmask", fail_on_error=False)
        backend.del_option("network", "lan", "ipaddr")
        backend.set_option("network", "lan", "ipaddr", "192.168.1.1/24")

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )

    assert "errors" not in res.keys()

    mode_managed = res["data"]["mode_managed"]
    mode_unmanaged = res["data"]["mode_unmanaged"]["lan_static"]

    assert all_equal(mode_managed["router_ip"], mode_unmanaged["ip"], "192.168.1.1")
    assert all_equal(mode_managed["netmask"], mode_unmanaged["netmask"], "255.255.255.0")


@pytest.mark.parametrize('device,turris_os_version', [('mox', '4.0')], indirect=True)
def test_qos(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,
):
    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert not res["data"]["qos"]["enabled"]
    assert res["data"]["qos"]["download"] == 1024
    assert res["data"]["qos"]["upload"] == 1024

    res = infrastructure.process_message({
        "module": "lan", "action": "update_settings", "kind": "request", "data":{
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.5.8",
                "netmask": "255.255.255.0",
                "dhcp": {"enabled": False},
            },
            "lan_redirect": False,
            "qos": {
                "download": 1200, "upload": 512, "enabled": True
            }
        }
    })

    assert "errors" not in res.keys()

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )

    assert "errors" not in res.keys()
    qos = res["data"]["qos"]
    assert qos["enabled"]
    assert qos["upload"] == 512
    assert qos["download"] == 1200


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize('device,turris_os_version', [('mox', '4.0')], indirect=True)
def test_qos_openwrt(
    uci_configs_init, infrastructure, network_restart_command, device, turris_os_version,

):
    def _assert_sqm_option(uci, key, expected_value):
        with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
            data = backend.read()
        assert uci.get_option_named(data, "sqm", "limit_lan_turris", key) == expected_value

    res = infrastructure.process_message(
        {"module": "lan", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert not res["data"]["qos"]["enabled"]
    assert res["data"]["qos"]["download"] == 1024
    assert res["data"]["qos"]["upload"] == 1024

    res = infrastructure.process_message({
        "module": "lan", "action": "update_settings", "kind": "request", "data":{
            "mode": "managed",
            "mode_managed": {
                "router_ip": "192.168.5.8",
                "netmask": "255.255.255.0",
                "dhcp": {"enabled": False},
            },
            "lan_redirect": False,
            "qos": {
                "download": 1200, "upload": 512, "enabled": True
            }
        }
    })

    uci = get_uci_module(infrastructure.name)

    _assert_sqm_option(uci, "download", "512")
    _assert_sqm_option(uci, "upload", "1200")
    _assert_sqm_option(uci, "enabled", "1")
    _assert_sqm_option(uci, "interface", "br-lan")
    _assert_sqm_option(uci, "qdisc", "fq_codel")
    _assert_sqm_option(uci, "script", "simple.qos")
    _assert_sqm_option(uci, "link_layer", "none")
    _assert_sqm_option(uci, "verbosity", "5")
    _assert_sqm_option(uci, "debug_logging", "1")
