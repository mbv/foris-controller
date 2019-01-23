#!/usr/bin/env python

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

import argparse
import logging
import multiprocessing
import typing

from logging.handlers import SysLogHandler

from foris_controller import __version__
from foris_controller.app import (
    app_info, set_app_info, prepare_app_modules, prepare_notification_sender
)
from foris_controller.utils import LOGGER_MAX_LEN

try:
    __import__("foris_client.buses")
    client_modules_loaded = True
except ImportError:
    client_modules_loaded = False


available_buses: typing.List[str] = ['unix-socket']


try:
    __import__("ubus")
    available_buses.append("ubus")
except ModuleNotFoundError:
    pass


try:
    __import__("paho.mqtt.client")
    available_buses.append("mqtt")
except ModuleNotFoundError:
    pass


logger = logging.getLogger("foris_controller")


def main():
    # Parse the command line options
    parser = argparse.ArgumentParser(prog="foris-controller")
    parser.add_argument('--version', action='version', version=__version__)

    subparsers = parser.add_subparsers(help="buses", dest="bus")
    subparsers.required = True

    unix_parser = subparsers.add_parser("unix-socket", help="use unix socket to recieve commands")
    unix_parser.add_argument("--path", default='/tmp/foris-controller.soc')
    unix_parser.add_argument(
        "--notifications-path", default='/tmp/foris-controller-notifications.soc')

    if "ubus" in available_buses:
        ubus_parser = subparsers.add_parser("ubus", help="use ubus to recieve commands")
        ubus_parser.add_argument("--path", default='/var/run/ubus.sock')
        ubus_parser.add_argument(
            "--single", default=False, action="store_true",
            help="run only through a single worker process"
        )

    if "mqtt" in available_buses:
        mqtt_parser = subparsers.add_parser("mqtt", help="use mqtt recieve commands")
        mqtt_parser.add_argument("--host", default='127.0.0.1')
        mqtt_parser.add_argument("--port", type=int, default=1883)

    parser.add_argument(
        "-b", "--backend", type=str, choices=["mock", "openwrt"],
        help="Configuration backend to be used", required=True
    )
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument(
        "-m", "--module", nargs=1, action='append', default=[],
        help="use only following modules",
    )
    parser.add_argument(
        "-l", "--log-file", default=None,
        help="file where the logs will we appended", required=False
    )
    parser.add_argument(
        '--extra-module-path', nargs=1, action='append', default=[],
        help="set extra path to module (e.g. /path/module_name)", required=False
    )
    if client_modules_loaded:
        parser.add_argument(
            "-C", "--client-socket-path", default=None,
            help="when set program will expose a socket to send requests and notifications",
            required=False
        )

    options = parser.parse_args()

    # Store app info
    set_app_info(options)

    logging_format = "%(levelname)s:%(name)s:%(message)." + str(LOGGER_MAX_LEN) + "s"
    if options.debug:
        logging.basicConfig(level=logging.DEBUG, format=logging_format)
    else:
        logging.basicConfig(format=logging_format)

    if options.log_file:
        file_handler = logging.FileHandler(options.log_file)
        if options.debug:
            file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("[%(created)f:%(process)d]" + logging.BASIC_FORMAT))
        logging.getLogger().addHandler(file_handler)

    logger.debug("Version %s" % __version__)
    logger.info("Foris controller is starting.")
    if options.bus == "ubus":
        from foris_controller.buses.ubus import UbusListener, UbusNotificationSender
        logger.info("Using ubus to recieve commands.")
        server = UbusListener(options.path)
        prepare_notification_sender(UbusNotificationSender, options.path)

    elif options.bus == "unix-socket":
        from foris_controller.buses.unix_socket import (
            UnixSocketListener, UnixSocketNotificationSender
        )
        logger.info("Using unix-socket to recieve commands.")
        server = UnixSocketListener(options.path)
        prepare_notification_sender(UnixSocketNotificationSender, options.notifications_path)
    elif options.bus == "mqtt":
        from foris_controller.buses.mqtt import (
            MqttListener, MqttNotificationSender
        )
        logger.info("Using mqtt to recieve commands.")
        server = MqttListener(options.host, options.port)
        prepare_notification_sender(
            MqttNotificationSender, options.host, options.port)

    if options.backend == "openwrt":
        from foris_controller.handler_base import BaseOpenwrtHandler
        logger.info("Using OpenWRT config backend.")
        prepare_app_modules(BaseOpenwrtHandler, [e[0] for e in options.extra_module_path])
    elif options.backend == "mock":
        from foris_controller.handler_base import BaseMockHandler
        logger.info("Using Mock config backend.")
        prepare_app_modules(BaseMockHandler, [e[0] for e in options.extra_module_path])
    else:
        raise NotImplementedError("Backend '%s' is not implemented" % options.backend)

    # fork and start a socket_client
    if client_modules_loaded and options.client_socket_path:

        # prepare args
        if options.bus == "ubus":
            from foris_client.buses.ubus import UbusSender
            sender_class = UbusSender
            sender_args = (options.path, )
            from foris_controller.buses.ubus import UbusNotificationSender
            notification_sender_class = UbusNotificationSender
            notification_sender_args = (options.path, )
        elif options.bus == "unix-socket":
            from foris_client.buses.unix_socket import UnixSocketSender
            sender_class = UnixSocketSender
            sender_args = (options.path, )
            from foris_controller.buses.unix_socket import UnixSocketNotificationSender
            notification_sender_class = UnixSocketNotificationSender
            notification_sender_args = (options.notifications_path, )
        elif options.bus == "mqtt":
            from foris_client.buses.mqtt import MqttSender
            sender_class = MqttSender
            sender_args = (options.host, options.port)
            from foris_controller.buses.mqtt import MqttNotificationSender
            notification_sender_class = MqttNotificationSender
            notification_sender_args = (options.host, options.port)

        # start in subprocess
        from foris_controller.client_socket import worker
        process = multiprocessing.Process(
            name="client-socket", target=worker, args=(
                options.client_socket_path, 0, app_info["validator"],
                sender_class, sender_args,
                notification_sender_class, notification_sender_args
            )
        )
        process.start()

    logger.debug("Entering main loop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
