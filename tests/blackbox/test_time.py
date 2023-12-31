#
# foris-controller
# Copyright (C) 2020-2021 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

from foris_controller_testtools.fixtures import UCI_CONFIG_DIR_PATH
from foris_controller_testtools.utils import check_service_result, get_uci_module


_EXTRA_SERVERS = [
    "time.google.com",
    "time1.google.com",
    "time.facebook.com",
    "time.windows.com"
]


NTPDATE_INDICATOR_PATH = "/tmp/foris-controller-ntp-fail"
REGULATORY_DOMAIN_INDICATOR = "/tmp/foris-controller-test-regulatory-domain"


def cmd_mock_gen(path):
    def inner_function():
        def try_unlink():
            try:
                os.unlink(path)
            except Exception:
                pass

        def read():
            res = None
            try:
                with open(path) as f:
                    res = f.read().strip()
            except Exception:
                pass
            try_unlink()

            return res

        try_unlink()
        yield read
        try_unlink()

    return inner_function


hwclock_mock = pytest.fixture(
    cmd_mock_gen("/tmp/foris-controller-tests-hwclock-called"), name="hwclock_mock"
)
date_mock = pytest.fixture(
    cmd_mock_gen("/tmp/foris-controller-tests-date-called"), name="date_mock"
)


@pytest.fixture
def fail_ntpdate():
    try:
        os.unlink(NTPDATE_INDICATOR_PATH)
    except Exception:
        pass

    with open(NTPDATE_INDICATOR_PATH, "w") as f:
        f.flush()

    yield NTPDATE_INDICATOR_PATH

    try:
        os.unlink(NTPDATE_INDICATOR_PATH)
    except Exception:
        pass


@pytest.fixture
def pass_ntpdate():
    try:
        os.unlink(NTPDATE_INDICATOR_PATH)
    except Exception:
        pass

    yield NTPDATE_INDICATOR_PATH


@pytest.fixture
def regulatory_domain():
    with open(REGULATORY_DOMAIN_INDICATOR, "w") as f:
        f.truncate(0)
        f.flush()

    yield

    try:
        os.unlink(REGULATORY_DOMAIN_INDICATOR)
    except Exception:
        pass


def test_get_settings(uci_configs_init, infrastructure):
    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "region" in res["data"].keys()
    assert "country" in res["data"].keys()
    assert "city" in res["data"].keys()
    assert "timezone" in res["data"].keys()
    assert "time_settings" in res["data"].keys()
    assert "how_to_set_time" in res["data"]["time_settings"].keys()
    assert "ntp_servers" in res["data"]["time_settings"].keys()
    assert "time" in res["data"]["time_settings"].keys()


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_update_settings(
    uci_configs_init,
    init_script_result,
    infrastructure,
    device,
    turris_os_version,
    regulatory_domain,
):
    filters = [("time", "update_settings")]
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "region": "Europe",
                "country": "RU",
                "city": "Moscow",
                "time_settings": {"how_to_set_time": "ntp"},
            },
        }
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "result" in res["data"].keys()
    assert res["data"]["result"] is True
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "time",
        "action": "update_settings",
        "kind": "notification",
        "data": {
            "region": "Europe",
            "country": "RU",
            "city": "Moscow",
            "time_settings": {"how_to_set_time": "ntp"},
        },
    }
    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["region"] == "Europe"
    assert res["data"]["country"] == "RU"
    assert res["data"]["city"] == "Moscow"
    assert res["data"]["timezone"] == "MSK-3"
    assert res["data"]["time_settings"]["how_to_set_time"] == "ntp"

    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "region": "Europe",
                "country": "CZ",
                "city": "Prague",
                "time_settings": {
                    "how_to_set_time": "manual",
                    "time": "2018-01-30T15:51:30.482515",
                },
            },
        }
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "result" in res["data"].keys()
    assert res["data"]["result"] is True
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "time",
        "action": "update_settings",
        "kind": "notification",
        "data": {
            "region": "Europe",
            "country": "CZ",
            "city": "Prague",
            "time_settings": {
                "how_to_set_time": "manual",
                "time": "2018-01-30T15:51:30.482515",
            },
        },
    }
    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["region"] == "Europe"
    assert res["data"]["country"] == "CZ"
    assert res["data"]["city"] == "Prague"
    assert res["data"]["timezone"] == "CET-1CEST,M3.5.0,M10.5.0/3"
    assert res["data"]["time_settings"]["how_to_set_time"] == "manual"


def test_get_router_time(uci_configs_init, infrastructure):
    res = infrastructure.process_message(
        {"module": "time", "action": "get_router_time", "kind": "request"}
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "time" in res["data"].keys()


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
@pytest.mark.only_backends(["openwrt"])
def test_openwrt_complex(
    uci_configs_init,
    init_script_result,
    date_mock,
    hwclock_mock,
    cmdline_script_root,
    infrastructure,
    device,
    turris_os_version,
    regulatory_domain,
):
    def check_regulatory_domain(cmd_args):
        with open(REGULATORY_DOMAIN_INDICATOR) as f:
            assert f.read().strip().endswith(cmd_args)

    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "region": "Europe",
                "country": "RU",
                "city": "Moscow",
                "time_settings": {"how_to_set_time": "ntp"},
            },
        }
    )
    assert res["data"]["result"] is True
    check_service_result("sysntpd", "restart", True)

    uci = get_uci_module(infrastructure.name)
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()

    assert uci.get_option_anonymous(data, "system", "system", 0, "timezone") == "MSK-3"
    assert uci.get_option_anonymous(data, "system", "system", 0, "_country") == "RU"
    assert uci.get_option_anonymous(data, "system", "system", 0, "zonename") == "Europe/Moscow"
    assert uci.parse_bool(uci.get_option_named(data, "system", "ntp", "enabled"))
    assert all(
        [
            e["data"].get("country") == "RU"
            for e in uci.get_sections_by_type(data, "wireless", "wifi-device")
        ]
    )
    check_regulatory_domain("reg set RU")

    assert not date_mock()
    assert not hwclock_mock()

    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "region": "Europe",
                "country": "CZ",
                "city": "Prague",
                "time_settings": {
                    "how_to_set_time": "manual",
                    "time": "2018-01-30T15:51:30.482515",
                },
            },
        }
    )
    assert res["data"]["result"] is True
    check_service_result("sysntpd", "stop", True)

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()

    assert uci.get_option_anonymous(data, "system", "system", 0, "_country") == "CZ"
    assert (
        uci.get_option_anonymous(data, "system", "system", 0, "timezone")
        == "CET-1CEST,M3.5.0,M10.5.0/3"
    )
    assert uci.get_option_anonymous(data, "system", "system", 0, "zonename") == "Europe/Prague"
    assert not uci.parse_bool(uci.get_option_named(data, "system", "ntp", "enabled"))
    assert all(
        [
            e["data"].get("country") == "CZ"
            for e in uci.get_sections_by_type(data, "wireless", "wifi-device")
        ]
    )

    check_regulatory_domain("reg set CZ")

    assert "2018-01-30" in date_mock()
    assert hwclock_mock()


@pytest.mark.only_backends(["mock"])
def test_ntpdate_trigger_mock(uci_configs_init, infrastructure):
    res = infrastructure.process_message(
        {"module": "time", "action": "ntpdate_trigger", "kind": "request"}
    )
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert "id" in res["data"].keys()


@pytest.mark.only_backends(["openwrt"])
def test_ntpdate_trigger_pass_openwrt(
    uci_configs_init,
    init_script_result,
    date_mock,
    hwclock_mock,
    cmdline_script_root,
    infrastructure,
    pass_ntpdate,
):
    filters = [("time", "ntpdate_started"), ("time", "ntpdate_finished")]
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {"module": "time", "action": "ntpdate_trigger", "kind": "request"}
    )
    async_id = res["data"]["id"]

    # get started notification
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "time",
        "action": "ntpdate_started",
        "kind": "notification",
        "data": {"id": async_id},
    }

    # get finished notification
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1]["action"] == "ntpdate_finished"
    assert notifications[-1]["data"]["id"] == async_id
    assert notifications[-1]["data"]["result"]
    assert "time" in notifications[-1]["data"].keys()
    assert not date_mock()
    assert hwclock_mock()


@pytest.mark.only_backends(["openwrt"])
def test_ntpdate_trigger_fail_openwrt(
    uci_configs_init,
    init_script_result,
    date_mock,
    hwclock_mock,
    cmdline_script_root,
    infrastructure,
    fail_ntpdate,
):
    filters = [("time", "ntpdate_started"), ("time", "ntpdate_finished")]
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {"module": "time", "action": "ntpdate_trigger", "kind": "request"}
    )
    async_id = res["data"]["id"]

    # get started notification
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "time",
        "action": "ntpdate_started",
        "kind": "notification",
        "data": {"id": async_id},
    }

    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "time",
        "action": "ntpdate_finished",
        "kind": "notification",
        "data": {"id": async_id, "result": False},
    }
    assert not date_mock()
    assert not hwclock_mock()


@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_ntp_servers_add_and_delete(
    uci_configs_init,
    init_script_result,
    infrastructure,
    device,
    turris_os_version,
    regulatory_domain,
):
    # get defaults
    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    data = res["data"]

    # if `how_to_set_time` is in `manual` mode, `time` field not required
    if data["time_settings"]["how_to_set_time"] == "ntp":
        data["time_settings"].pop("time")

    # do not send `ntp_servers` back
    data["time_settings"].pop("ntp_servers")

    data["time_settings"]["ntp_extras"] = _EXTRA_SERVERS
    # update with `ntp_extras`
    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": data
        }
    )
    assert res["data"]["result"]

    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert "time.google.com" not in res["data"]["time_settings"]["ntp_servers"]
    assert "time.google.com" in res["data"]["time_settings"]["ntp_extras"]


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("device,turris_os_version", [("mox", "4.0")], indirect=True)
def test_add_extras_uci(
    uci_configs_init,
    init_script_result,
    infrastructure,
    device,
    turris_os_version,
    regulatory_domain,
):
    # get defaults
    res = infrastructure.process_message(
        {"module": "time", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()

    data = res["data"]

    # if `how_to_set_time` is in `manual` mode, `time` field not required
    if data["time_settings"]["how_to_set_time"] == "ntp":
        data["time_settings"].pop("time")

    # do not send `ntp_servers` back
    _DEFAULT_SERVERS = data["time_settings"].pop("ntp_servers")

    data["time_settings"]["ntp_extras"] = _EXTRA_SERVERS
    # update with `ntp_extras`
    res = infrastructure.process_message(
        {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": data
        }
    )
    assert res["data"]["result"]

    # assert that data all in uci `system.ntp.server`
    uci = get_uci_module(infrastructure.name)
    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as backend:
        data = backend.read()

    ntp_servers = uci.get_option_named(data, "system", "ntp", "server")

    # in uci all data in one list
    assert ntp_servers == _DEFAULT_SERVERS + _EXTRA_SERVERS
