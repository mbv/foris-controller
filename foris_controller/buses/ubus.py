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

from __future__ import absolute_import

import logging
import ubus
import inspect
import prctl
import signal
import multiprocessing

logger = logging.getLogger("buses.ubus")

from foris_controller.message_router import Router
from foris_controller.app import app_info
from foris_controller.utils import get_modules


def _get_method_names_from_module(module):
    module_class = getattr(module, "Class", None)

    if not module_class:
        # Class not found
        return None

    # read all names fucntions which starts with action_
    res = [
        e[0] for e in inspect.getmembers(
            module_class, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x)
        ) if e[0].startswith("action_")
    ]

    # remove action_ prefix
    return [e.lstrip("action_") for e in res]


def _register_object(module_name, module):
    methods = _get_method_names_from_module(module)
    if not methods:
        logger.warning("No suitable method found in '%s' module. Skipping" % module_name)

    object_name = 'foris-controller-%s' % module_name
    logger.debug("Trying to register '%s' object." % object_name)

    def handler_gen(module, action):
        def handler(handler, data):
            logger.debug("Handling request")
            logger.debug("Data received '%s'." % str(data))
            router = Router()
            data["module"] = module
            data["action"] = action
            data["kind"] = "request"
            if not data["data"]:
                del data["data"]
            response = router.process_message(data)
            logger.debug("Sending response %s" % str(response))
            logger.debug("Handling finished.")
            handler.reply(response)
        return handler

    ubus.add(
        object_name,
        {
            method_name: {"method": handler_gen(module_name, method_name), "signature": {
                "data": ubus.BLOBMSG_TYPE_TABLE
            }} for method_name in methods
        }
    )
    logger.debug("Object '%s' was successfully registered." % object_name)


def ubus_listener_worker(socket_path, module_name, module):
    ubus.connect(socket_path)
    prctl.set_pdeathsig(signal.SIGKILL)
    _register_object(module_name, module)
    try:
        while True:
            ubus.loop(500)
    finally:
        ubus.disconnect()


def ubus_all_in_one_worker(socket_path, modules_list):
    ubus.connect(socket_path)
    prctl.set_pdeathsig(signal.SIGKILL)
    for module_name, module in modules_list:
        _register_object(module_name, module)
    try:
        while True:
            ubus.loop(500)
    finally:
        ubus.disconnect()


class UbusListener(object):

    def __init__(self, socket_path):
        logger.debug("Starting to create workers for ubus.")

        self.workers = []
        if app_info["ubus_single_process"]:
            worker = multiprocessing.Process(
                name="all-in-one", target=ubus_all_in_one_worker,
                args=(socket_path, get_modules(), )
            )
            self.workers.append(worker)
        else:
            for module_name, module in get_modules():
                worker = multiprocessing.Process(
                    name=module_name, target=ubus_listener_worker,
                    args=(socket_path, module_name, module)
                )
                self.workers.append(worker)

        logger.debug("Ubus workers successfully initialized.")

    def serve_forever(self):
        logger.debug("Starting to run workers.")

        for worker in self.workers:
            worker.start()

        logger.debug("All workers started.")

        # wait for all processes to finish
        for worker in self.workers:
            worker.join()

        logger.warning("All workers finished.")
