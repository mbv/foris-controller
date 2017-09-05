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
import random

from foris_controller.handler_base import BaseMockHandler
from foris_controller.utils import logger_wrapper

from .. import Handler

logger = logging.getLogger("data_collect.handlers.mock")


class MockDataCollectHandler(Handler, BaseMockHandler):

    @logger_wrapper(logger)
    def get_registered(self, email, language):
        """ Mocks registration info

        :param email: email which was used during the registration
        :type email: str
        :param language: language which will be used in the server query (iso2)
        :type language: str

        :returns: Mocked result
        :rtype: dict
        """
        registration_code = "%016X" % random.randrange(0x10000000000000000)
        return random.choice([
            {
                "status": "free",
                "url": "https://some.page/%s/data?email=%s&registration_code=%s" %
                (language, email, registration_code),
                "registration_number": registration_code,
            },
            {
                "status": "foreign",
                "url": "https://some.page/%s/data?email=%s&registration_code=%s" %
                (language, email, registration_code),
                "registration_number": registration_code,
            },
            {
                "status": "unknown",
            },
            {
                "status": "not_found",
            },
            {
                "status": "owned",
            },
        ])