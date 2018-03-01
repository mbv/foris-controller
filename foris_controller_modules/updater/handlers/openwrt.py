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

from foris_controller.handler_base import BaseOpenwrtHandler
from foris_controller.utils import logger_wrapper
from foris_controller_backends.updater import UpdaterUci, Updater

from .. import Handler

logger = logging.getLogger(__name__)


class OpenwrtUpdaterHandler(Handler, BaseOpenwrtHandler):
    uci = UpdaterUci()
    updater = Updater()

    @logger_wrapper(logger)
    def get_settings(self):
        """ get updater settings

        :returns: current updater settings
        :rtype: dict
        """
        return OpenwrtUpdaterHandler.uci.get_settings()

    @logger_wrapper(logger)
    def update_settings(self, user_lists, required_languages, approvals_settings, enabled, branch):
        """ update updater settings

        :param user_lists: new user-list set
        :type user_lists: list
        :param required_languages: languages which will be installed
        :type required_languages: list
        :param approvals_settings: new approval settings
        :type approvals_settings: dict
        :param enable: is updater enabled indicator
        :type enable: bool
        :param branch: which branch is updater using default("" == "stable")
        :type enable: string
        :returns: True on success False otherwise
        :rtype: bool
        """
        return OpenwrtUpdaterHandler.uci.update_settings(
            user_lists, required_languages, approvals_settings['status'],
            approvals_settings.get("delay", None), enabled, branch
        )

    @logger_wrapper(logger)
    def get_approval(self):
        """ Returns current approval
        :returns: current approval or {"present": False}
        :rtype: dict
        """
        return self.updater.get_approval()
