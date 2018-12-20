#!/usr/bin/env python
#
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

from setuptools import setup
from foris_controller import __version__

DESCRIPTION = """
An program which is placed in top of a message bus and translates requests to commands for backends.
"""

setup(
    name='foris-controller',
    version=__version__,
    author='CZ.NIC, z.s.p.o. (http://www.nic.cz/)',
    author_email='stepan.henek@nic.cz',
    packages=[
        'foris_controller',
        'foris_controller.controller',
        'foris_controller.notify',
        'foris_controller.buses',
        'foris_controller_backends',
        'foris_controller_backends.about',
        'foris_controller_backends.cmdline',
        'foris_controller_backends.dns',
        'foris_controller_backends.guest',
        'foris_controller_backends.lan',
        'foris_controller_backends.files',
        'foris_controller_backends.maintain',
        'foris_controller_backends.networks',
        'foris_controller_backends.password',
        'foris_controller_backends.router_notifications',
        'foris_controller_backends.services',
        'foris_controller_backends.uci',
        'foris_controller_backends.time',
        'foris_controller_backends.updater',
        'foris_controller_backends.wan',
        'foris_controller_backends.web',
        'foris_controller_backends.wifi',
        'foris_controller_modules',
        'foris_controller_modules.about',
        'foris_controller_modules.about.handlers',
        'foris_controller_modules.dns',
        'foris_controller_modules.dns.handlers',
        'foris_controller_modules.guest',
        'foris_controller_modules.guest.handlers',
        'foris_controller_modules.lan',
        'foris_controller_modules.lan.handlers',
        'foris_controller_modules.maintain',
        'foris_controller_modules.maintain.handlers',
        'foris_controller_modules.networks',
        'foris_controller_modules.networks.handlers',
        'foris_controller_modules.password',
        'foris_controller_modules.password.handlers',
        'foris_controller_modules.router_notifications',
        'foris_controller_modules.router_notifications.handlers',
        'foris_controller_modules.time',
        'foris_controller_modules.time.handlers',
        'foris_controller_modules.updater',
        'foris_controller_modules.updater.handlers',
        'foris_controller_modules.wan',
        'foris_controller_modules.wan.handlers',
        'foris_controller_modules.web',
        'foris_controller_modules.web.handlers',
        'foris_controller_modules.wifi',
        'foris_controller_modules.wifi.handlers',
    ],
    package_data={
        'foris_controller': [
            'schemas', 'schemas/*.json', 'schemas/definitions', "schemas/definitions/*.json"
        ],
        'foris_controller_modules.about': ['schema', 'schema/*.json'],
        'foris_controller_modules.dns': ['schema', 'schema/*.json'],
        'foris_controller_modules.guest': ['schema', 'schema/*.json'],
        'foris_controller_modules.lan': ['schema', 'schema/*.json'],
        'foris_controller_modules.maintain': ['schema', 'schema/*.json'],
        'foris_controller_modules.networks': ['schema', 'schema/*.json'],
        'foris_controller_modules.wan': ['schema', 'schema/*.json'],
        'foris_controller_modules.password': ['schema', 'schema/*.json'],
        'foris_controller_modules.router_notifications': ['schema', 'schema/*.json'],
        'foris_controller_modules.time': ['schema', 'schema/*.json'],
        'foris_controller_modules.updater': ['schema', 'schema/*.json'],
        'foris_controller_modules.web': ['schema', 'schema/*.json'],
        'foris_controller_modules.wifi': ['schema', 'schema/*.json'],
    },
    namespace_packages=[
        'foris_controller_modules',
        'foris_controller_backends',
    ],
    url='https://gitlab.labs.nic.cz/turris/foris-controller',
    license='COPYING',
    description=DESCRIPTION,
    long_description=open('README.rst').read(),
    install_requires=[
        "foris-schema @ git+https://gitlab.labs.nic.cz/turris/foris-schema.git",
        "python-prctl",
        "pbkdf2",
        "svupdater @ git+https://gitlab.labs.nic.cz/turris/updater.git#egg=svupdater&subdirectory=src/supervisor",
        "turrishw @ git+https://gitlab.labs.nic.cz/turris/turrishw.git",
        "ubus @ git+https://gitlab.labs.nic.cz/turris/python-ubus.git",
        "paho-mqtt",
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'foris-controller-testtools',
        'foris-client',
    ],
    extras_require={
        'client-socket': ["foris-client @ git+https://gitlab.labs.nic.cz/turris/foris-client.git@mqtt-bus"],
    },
    entry_points={
        "console_scripts": [
            "foris-controller = foris_controller.controller.__main__:main",
            "foris-notify = foris_controller.notify.__main__:main",
        ]
    },
    dependency_links=[
        "git+https://gitlab.labs.nic.cz/turris/foris-controller-testtools.git@mqtt-bus#egg=foris-controller-testtools",
        "git+https://gitlab.labs.nic.cz/turris/foris-client.git@mqtt-bus#egg=foris-client",
    ],
    include_package_data=True,
    zip_safe=False,
)
