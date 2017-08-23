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

import os
import logging

from foris_schema import ForisValidator

from foris_controller.utils import get_modules, get_handler


logger = logging.getLogger("app")

app_info = {
}


def set_app_info(program_options):
    global app_info
    app_info["bus"] = program_options.bus
    app_info["debug"] = program_options.debug
    app_info["backend"] = program_options.backend

    import multiprocessing
    import threading
    app_info["lock_backend"] = multiprocessing if app_info["bus"] in ["ubus"] else threading
    if app_info["bus"] == "ubus":
        app_info["ubus_single_process"] = program_options.single


def prepare_app_modules(base_handler_class):
    app_info["modules"] = {}

    # use root schema dir
    schema_dirs = [
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "schemas"),
    ]

    for module_name, module in get_modules():
        logger.debug("Trying to load module '%s'." % module_name)
        handler = get_handler(module, base_handler_class)
        if not handler:
            logger.error(
                "Failed to find handler '%s' for base '%s'. Skipping module."
                % (module_name, base_handler_class.__name__)
            )
            continue

        app_info["modules"][module_name] = module.Class(handler)
        schema_dirs.append(os.path.join(module.__path__[0], "schema"))

    logger.debug("Modules loaded %s." % app_info["modules"].keys())
    app_info["validator"] = ForisValidator(schema_dirs)