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
import os
import pytest
import base64
import sys

from foris_controller_testtools.fixtures import (
    uci_configs_init, infrastructure, ubusd_test, file_root_init, only_backends,
    init_script_result, FILE_ROOT_PATH, network_restart_command, lock_backend,
    device, turris_os_version,
)
from foris_controller_testtools.utils import FileFaker, get_uci_module, prepare_turrishw_root
from foris_controller import profiles
from foris_controller.exceptions import UciRecordNotFound


NEW_WORKFLOWS = [e for e in profiles.WORKFLOWS if e != profiles.WORKFLOW_OLD]

EXPECTED_WORKFLOWS = {
    ("mox", "4.0"): NEW_WORKFLOWS,
    ("mox", "3.10.7"): [],
    ("omnia", "4.0"): [profiles.WORKFLOW_MIN, profiles.WORKFLOW_ROUTER],
    ("omnia", "3.10.7"): [profiles.WORKFLOW_OLD],
    ("turris", "4.0"): [profiles.WORKFLOW_OLD],
    ("turris", "3.10.7"): [profiles.WORKFLOW_OLD],
}

RECOMMENDED_WORKFLOWS = {
    ("mox", "4.0"): profiles.WORKFLOW_ROUTER,
    ("mox", "3.10.7"): profiles.WORKFLOW_OLD,
    ("omnia", "4.0"): profiles.WORKFLOW_ROUTER,
    ("omnia", "3.10.7"): profiles.WORKFLOW_OLD,
    ("turris", "4.0"): profiles.WORKFLOW_OLD,
    ("turris", "3.10.7"): profiles.WORKFLOW_OLD,
}


@pytest.fixture(scope="function")
def installed_languages(request):
    trans_dir = "/usr/lib/python%s.%s/site-packages/foris/langs/" % (
        sys.version_info.major, sys.version_info.minor
    )
    with \
            FileFaker(FILE_ROOT_PATH, os.path.join(trans_dir, "cs.py"), False, "") as f1, \
            FileFaker(FILE_ROOT_PATH, os.path.join(trans_dir, "de.py"), False, "") as f2, \
            FileFaker(FILE_ROOT_PATH, os.path.join(trans_dir, "nb_NO.py"), False, "") as f3:
        yield f1, f2, f3


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
        ("mox", "3.10.7"),
        ("omnia", "4.0"),
        ("omnia", "3.10.7"),
        ("turris", "4.0"),
        ("turris", "3.10.7"),
    ],
    indirect=True
)
def test_get_data(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, device, turris_os_version
):
    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert set(res["data"].keys()) == {
        u"language", u"reboot_required", u"notification_count", u"updater_running",
        u"guide", u"password_ready", u"turris_os_version", u"device"
    }
    assert len(res["data"]["language"]) in [2, 5]  # en, en_US
    assert res["data"]["notification_count"] >= 0
    assert "enabled" in res["data"]["guide"]
    assert "passed" in res["data"]["guide"]
    assert "workflow" in res["data"]["guide"]
    assert "workflow_steps" in res["data"]["guide"]


@pytest.mark.parametrize("code", ["cs", "nb_NO"])
def test_set_language(installed_languages, code, file_root_init, uci_configs_init, infrastructure, ubusd_test):
    filters = [("web", "set_language")]
    old_notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message({
        "module": "web",
        "action": "set_language",
        "kind": "request",
        "data": {"language": code},
    })
    assert res == {
        u'action': u'set_language',
        u'data': {u'result': True},
        u'kind': u'reply',
        u'module': u'web'
    }
    assert infrastructure.get_notifications(old_notifications, filters=filters)[-1] == {
        u"module": u"web",
        u"action": u"set_language",
        u"kind": u"notification",
        u"data": {
            u"language": code,
        }
    }


def test_set_language_missing(
    installed_languages, file_root_init, uci_configs_init, infrastructure, ubusd_test
):
    res = infrastructure.process_message({
        "module": "web",
        "action": "set_language",
        "kind": "request",
        "data": {"language": "zz"},
    })
    assert res == {
        u'action': u'set_language',
        u'data': {u'result': False},
        u'kind': u'reply',
        u'module': u'web'
    }


def test_list_languages(
    installed_languages, file_root_init, uci_configs_init, infrastructure, ubusd_test
):
    res = infrastructure.process_message({
        "module": "web",
        "action": "list_languages",
        "kind": "request",
    })
    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert u"languages" in res["data"].keys()
    assert set(res["data"]["languages"]) == {'en', 'cs', 'de', 'nb_NO'}


def test_set_language_missing_data(
    installed_languages, file_root_init, uci_configs_init, infrastructure, ubusd_test
):
    res = infrastructure.process_message({
        "module": "web",
        "action": "set_language",
        "kind": "request",
    })
    assert "errors" in res


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
        ("mox", "3.10.7"),
        ("omnia", "4.0"),
        ("omnia", "3.10.7"),
        ("turris", "4.0"),
        ("turris", "3.10.7"),
    ],
    indirect=True
)
def test_get_guide(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, device, turris_os_version
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_guide",
        "kind": "request",
    })

    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert set(res["data"].keys()) == {
        u"current_workflow", u"available_workflows", "recommended_workflow",
    }


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
        ("mox", "3.10.7"),
        ("omnia", "4.0"),
        ("omnia", "3.10.7"),
        ("turris", "4.0"),
        ("turris", "3.10.7"),
    ],
    indirect=True
)
@pytest.mark.only_backends(['openwrt'])
def test_get_guide_openwrt(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, device, turris_os_version
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_guide",
        "kind": "request",
    })
    assert set(res["data"]["available_workflows"]) == \
        set(EXPECTED_WORKFLOWS[device, turris_os_version])
    assert res["data"]["recommended_workflow"] == RECOMMENDED_WORKFLOWS[device, turris_os_version]


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
    ],
    indirect=True
)
def test_update_guide(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, device, turris_os_version
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    res = infrastructure.process_message({
        "module": "web",
        "action": "update_guide",
        "kind": "request",
        "data": {"enabled": True, "workflow": profiles.WORKFLOW_OLD},  # doesn't matter which
    })

    assert set(res.keys()) == {"action", "kind", "data", "module"}
    assert set(res["data"].keys()) == {u"result"}


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
        ("mox", "3.10.7"),
        ("omnia", "4.0"),
        ("omnia", "3.10.7"),
        ("turris", "4.0"),
        ("turris", "3.10.7"),
    ],
    indirect=True
)
@pytest.mark.only_backends(['openwrt'])
@pytest.mark.parametrize("workflow", list(profiles.WORKFLOWS))
def test_update_guide_openwrt(
    file_root_init, init_script_result, uci_configs_init, infrastructure, ubusd_test,
    network_restart_command, workflow, lock_backend, device, turris_os_version,
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    uci = get_uci_module(lock_backend)

    with uci.UciBackend() as backend:
        data = backend.read()

    try:
        orig = uci.get_option_named(data, "foris", "wizard", "workflow")
    except UciRecordNotFound:
        orig = None

    res = infrastructure.process_message({
        "module": "web",
        "action": "update_guide",
        "kind": "request",
        "data": {"enabled": True, "workflow": workflow},
    })
    assert res["data"]["result"] is (workflow in EXPECTED_WORKFLOWS[device, turris_os_version])

    with uci.UciBackend() as backend:
        data = backend.read()

    if res["data"]["result"]:
        assert uci.get_option_named(data, "foris", "wizard", "workflow") == workflow
        passed = uci.get_option_named(data, "foris", "wizard", "passed")
        assert "profile" in passed
        if set(profiles.WORKFLOWS[workflow]).issubset(set(passed)):
            assert uci.parse_bool(uci.get_option_named(data, "foris", "wizard", "finished"))
    else:
        try:
            new = uci.get_option_named(data, "foris", "wizard", "workflow", None)
        except UciRecordNotFound:
            new = None
        assert orig == new


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
    ],
    indirect=True
)
def test_reset_guide(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, device, turris_os_version
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    res = infrastructure.process_message({
        "module": "web",
        "action": "reset_guide",
        "kind": "request",
    })
    assert res["data"] == {"result": True}
    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert res["data"]["guide"]["enabled"] is True
    assert res["data"]["guide"]["workflow"] in [profiles.WORKFLOW_MIN, profiles.WORKFLOW_OLD]
    assert res["data"]["guide"]["passed"] == []

    res = infrastructure.process_message({
        "module": "web",
        "action": "update_guide",
        "kind": "request",
        "data": {"enabled": False, "workflow": profiles.WORKFLOW_ROUTER},
    })
    assert res["data"]["result"] is True

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert res["data"]["guide"]["enabled"] is False
    assert res["data"]["guide"]["workflow"] == profiles.WORKFLOW_ROUTER
    assert res["data"]["guide"]["passed"] == ['profile']

    res = infrastructure.process_message({
        "module": "web",
        "action": "reset_guide",
        "kind": "request",
    })
    assert res["data"] == {"result": True}

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert res["data"]["guide"]["enabled"] is True
    assert res["data"]["guide"]["workflow"] in [profiles.WORKFLOW_MIN, profiles.WORKFLOW_OLD]
    assert res["data"]["guide"]["passed"] == []


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
        ("mox", "3.10.7"),
        ("omnia", "4.0"),
        ("omnia", "3.10.7"),
        ("turris", "4.0"),
        ("turris", "3.10.7"),
    ],
    indirect=True
)
@pytest.mark.only_backends(['openwrt'])
def test_reset_guide_openwrt(
    file_root_init, uci_configs_init, infrastructure, ubusd_test, lock_backend,
    device, turris_os_version,
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    uci = get_uci_module(lock_backend)

    res = infrastructure.process_message({
        "module": "web",
        "action": "reset_guide",
        "kind": "request",
    })
    assert res["data"] == {"result": True}

    with uci.UciBackend() as backend:
        data = backend.read()

    assert uci.get_option_named(data, "foris", "wizard", "workflow") in [
        profiles.WORKFLOW_MIN, profiles.WORKFLOW_OLD
    ]
    assert not uci.parse_bool(
        uci.get_option_named(data, "foris", "wizard", "finished", uci.store_bool(False)))

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert res["data"]["guide"]["enabled"] is True
    allowed_workflows = EXPECTED_WORKFLOWS[device, turris_os_version]
    assert (res["data"]["guide"]["workflow"] in allowed_workflows) or not allowed_workflows
    assert res["data"]["guide"]["passed"] == []

    res = infrastructure.process_message({
        "module": "web",
        "action": "update_guide",
        "kind": "request",
        "data": {
            "enabled": False,
            "workflow": allowed_workflows[0] if allowed_workflows else profiles.WORKFLOW_OLD
        },
    })
    assert res["data"]["result"] is bool(allowed_workflows)

    if allowed_workflows:
        res = infrastructure.process_message({
            "module": "web",
            "action": "get_data",
            "kind": "request",
        })
        assert res["data"]["guide"]["enabled"] is False
        assert (res["data"]["guide"]["workflow"] in allowed_workflows) or not allowed_workflows
        assert res["data"]["guide"]["passed"] == ['profile']
        assert res["data"]["device"] == device
        assert res["data"]["turris_os_version"] == turris_os_version

    res = infrastructure.process_message({
        "module": "web",
        "action": "reset_guide",
        "kind": "request",
    })
    assert res["data"] == {"result": True}

    with uci.UciBackend() as backend:
        data = backend.read()

    assert uci.get_option_named(data, "foris", "wizard", "workflow") in [
        profiles.WORKFLOW_MIN, profiles.WORKFLOW_OLD
    ]
    assert not uci.parse_bool(
        uci.get_option_named(data, "foris", "wizard", "finished", uci.store_bool(False)))

    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert res["data"]["guide"]["enabled"] is True
    assert (res["data"]["guide"]["workflow"] in allowed_workflows) or not allowed_workflows
    assert res["data"]["guide"]["passed"] == []


@pytest.mark.parametrize(
    "device,turris_os_version",
    [
        ("mox", "4.0"),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    "old_workflow,new_workflow", [
        (profiles.WORKFLOW_OLD, profiles.WORKFLOW_OLD),
    ] + [
        (profiles.WORKFLOW_MIN, e) for e in NEW_WORKFLOWS
    ]
)
def test_walk_through_guide(
    file_root_init, init_script_result, uci_configs_init, infrastructure, ubusd_test,
    network_restart_command, old_workflow, new_workflow, device, turris_os_version,
):
    if infrastructure.backend_name in ['openwrt']:
        prepare_turrishw_root(device, turris_os_version)

    res = infrastructure.process_message({
        "module": "web",
        "action": "reset_guide",
        "kind": "request",
        "data": {"new_workflow": old_workflow},
    })
    assert res["data"] == {"result": True}
    res = infrastructure.process_message({
        "module": "web",
        "action": "get_data",
        "kind": "request",
    })
    assert old_workflow == res["data"]["guide"]["workflow"]

    def get_passed(passed, workflow, enabled):
        res = infrastructure.process_message({
            "module": "web",
            "action": "get_data",
            "kind": "request",
        })
        assert res["data"]["guide"]["enabled"] is enabled
        assert res["data"]["guide"]["workflow"] == workflow
        assert res["data"]["guide"]["passed"] == passed
        assert res["data"]["guide"]["workflow_steps"] == [e for e in profiles.WORKFLOWS[workflow]]
        if enabled:
            assert res["data"]["guide"]["next_step"] == profiles.next_step(passed, workflow)
        else:
            assert "next_step" not in res["data"]["guide"]

    def pass_step(msg, passed, target_workflow, enabled):
        res = infrastructure.process_message(msg)
        assert res["data"]["result"] is True
        get_passed(passed, target_workflow, enabled)

    def password_step(passed, target_workflow, enabled):
        # Update password
        msg = {
            "module": "password",
            "action": "set",
            "kind": "request",
            "data": {"password": base64.b64encode(b"heslo").decode("utf-8"), "type": "foris"},
        }
        pass_step(msg, passed, target_workflow, enabled)

    def profile_step(passed, target_workflow, enabled):
        # Update guide
        msg = {
            "module": "web",
            "action": "update_guide",
            "kind": "request",
            "data": {"workflow": new_workflow, "enabled": True},
        }
        pass_step(msg, passed, target_workflow, enabled)

    def networks_step(passed, target_workflow, enabled):
        # Update networks
        res = infrastructure.process_message({
            "module": "networks",
            "action": "get_settings",
            "kind": "request",
        })
        ports = res["data"]["networks"]["wan"] + res["data"]["networks"]["lan"] \
            + res["data"]["networks"]["guest"] + res["data"]["networks"]["none"]
        wan_port = ports.pop()["id"]
        lan_ports, guest_ports, none_ports = [], [], []
        for i, port in enumerate(ports):
            if i % 3 == 0:
                lan_ports.append(port["id"])
            elif i % 3 == 1:
                guest_ports.append(port["id"])
            elif i % 3 == 2:
                none_ports.append(port["id"])

        msg = {
            "module": "networks",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "firewall": {
                    "ssh_on_wan": True,
                    "http_on_wan": False,
                    "https_on_wan": True,
                },
                "networks": {
                    "wan": [wan_port],
                    "lan": lan_ports,
                    "guest": guest_ports,
                    "none": none_ports,
                }
            }
        }
        pass_step(msg, passed, target_workflow, enabled)

    def wan_step(passed, target_workflow, enabled):
        # Update wan
        msg = {
            "module": "wan",
            "action": "update_settings",
            "kind": "request",
            "data": {
                'wan_settings': {'wan_type': 'dhcp', 'wan_dhcp': {}},
                'wan6_settings': {'wan6_type': 'none'},
                'mac_settings': {'custom_mac_enabled': False},
            }
        }
        pass_step(msg, passed, target_workflow, enabled)

    def time_step(passed, target_workflow, enabled):
        # Update timezone
        msg = {
            "module": "time",
            "action": "update_settings",
            "kind": "request",
            "data": {
                u"region": u"Europe",
                u"city": u"Prague",
                u"timezone": u"CET-1CEST,M3.5.0,M10.5.0/3",
                u"time_settings": {
                    u"how_to_set_time": u"manual",
                    u"time": u"2018-01-30T15:51:30.482515",
                }
            }
        }
        pass_step(msg, passed, target_workflow, enabled)

    def dns_step(passed, target_workflow, enabled):
        # Update dns
        msg = {
            "module": "dns",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "forwarding_enabled": False,
                "dnssec_enabled": False,
                "dns_from_dhcp_enabled": False,
            }
        }
        pass_step(msg, passed, target_workflow, enabled)

    def updater_step(passed, target_workflow, enabled):
        # update Updater
        msg = {
            "module": "updater",
            "action": "update_settings",
            "kind": "request",
            "data": {
                "enabled": False,
            },
        }
        pass_step(msg, passed, target_workflow, enabled)

    MAP = {
        "password": password_step,
        "profile": profile_step,
        "networks": networks_step,
        "wan": wan_step,
        "time": time_step,
        "dns": dns_step,
        "updater": updater_step,
    }

    passed = []

    get_passed(passed, old_workflow, True)
    active_workflow = old_workflow
    for step in profiles.WORKFLOWS[old_workflow]:
        if step == profiles.STEP_PROFILE:
            active_workflow = new_workflow
        last = set(profiles.WORKFLOWS[active_workflow]) != set(passed + [step])
        MAP[step](passed + [step], active_workflow, last)
        passed.append(step)
    for step in profiles.WORKFLOWS[active_workflow]:
        if step in passed:
            continue
        last = set(profiles.WORKFLOWS[active_workflow]) != set(passed + [step])
        MAP[step](passed + [step], active_workflow, last)
        passed.append(step)
