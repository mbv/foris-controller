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

import logging

from foris_controller.handler_base import BaseMockHandler
from foris_controller.utils import logger_wrapper

from .. import Handler

logger = logging.getLogger(__name__)


class MockGuestHandler(Handler, BaseMockHandler):
    enabled = False
    router_ip = "192.168.1.1"
    netmask = "255.255.255.0"
    dhcp = {
        "enabled": False,
        "start": 100,
        "limit": 150,
    }
    qos = {
        "enabled": False,
        "download": 1200,
        "upload": 1200,
    }

    @logger_wrapper(logger)
    def get_settings(self):
        """ Mocks get guest settings

        :returns: current guest settiongs
        :rtype: str
        """
        result = {
            "enabled": MockGuestHandler.enabled,
            "ip": MockGuestHandler.router_ip,
            "netmask": MockGuestHandler.netmask,
            "dhcp": MockGuestHandler.dhcp,
            "qos": MockGuestHandler.qos,
        }
        return result

    @logger_wrapper(logger)
    def update_settings(self, new_settings):
        """ Mocks updates current guest settings
        :returns: True if update passes
        :rtype: bool
        """
        MockGuestHandler.enabled = new_settings["enabled"]
        if MockGuestHandler.enabled:
            MockGuestHandler.router_ip = new_settings["ip"]
            MockGuestHandler.netmask = new_settings["netmask"]
            MockGuestHandler.dhcp["enabled"] = new_settings["dhcp"]["enabled"]
            MockGuestHandler.dhcp["start"] = new_settings["dhcp"].get(
                "start", MockGuestHandler.dhcp["start"])
            MockGuestHandler.dhcp["limit"] = new_settings["dhcp"].get(
                "limit", MockGuestHandler.dhcp["limit"])
            MockGuestHandler.qos["enabled"] = new_settings["qos"]["enabled"]
            if MockGuestHandler.qos["enabled"]:
                MockGuestHandler.qos["download"] = new_settings["qos"]["download"]
                MockGuestHandler.qos["upload"] = new_settings["qos"]["upload"]

        return True