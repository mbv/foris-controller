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


def pytest_addoption(parser):
    parser.addoption(
        "--backend", action="append",
        default=[],
        help=("Set test backend here. available values = (mock, openwrt)")
    )
    parser.addoption(
        "--suppress-output", action="store_true",
        default=False,
        help=("Whether to suppress the output of foris-controller cmd")
    )


def pytest_generate_tests(metafunc):
    if 'backend' in metafunc.fixturenames:
        backend = set(metafunc.config.option.backend)
        if not backend:
            backend = ['mock']
        metafunc.parametrize("backend_param", backend, scope='module')