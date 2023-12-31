{{ cookiecutter.license_short }}

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def uci_config_default_path():
    return Path(__file__).resolve().parent / "uci_configs"


@pytest.fixture(scope="session")
def cmdline_script_root():
    return Path(__file__).resolve().parent / "test_root"


@pytest.fixture(scope="session")
def file_root():
    return Path(__file__).resolve().parent / "test_root"


@pytest.fixture(scope="module")
def controller_modules():
    return ["remote", "{{ cookiecutter.name_snake }}"]


def pytest_addoption(parser):
    parser.addoption(
        "--backend",
        action="append",
        default=[],
        help=("Set test backend here. available values = (mock, openwrt)"),
    )
    parser.addoption(
        "--message-bus",
        action="append",
        default=[],
        help=("Set test bus here. available values = (unix-socket, ubus, mqtt)"),
    )
    parser.addoption(
        "--debug-output",
        action="store_true",
        default=False,
        help=("Whether show output of foris-controller cmd"),
    )


def pytest_generate_tests(metafunc):
    if "backend" in metafunc.fixturenames:
        backend = metafunc.config.option.backend
        if not backend:
            backend = ["openwrt"]
        metafunc.parametrize("backend_param", backend, scope="module")

    if "message_bus" in metafunc.fixturenames:
        message_bus = metafunc.config.option.message_bus
        if not message_bus:
            message_bus = ["mqtt"]
        metafunc.parametrize("message_bus_param", message_bus, scope="module")
