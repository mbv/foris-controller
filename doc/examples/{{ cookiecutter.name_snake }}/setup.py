{{ cookiecutter.license_short }}

from foris_controller_{{cookiecutter.name_snake}}_module import __version__
from setuptools import setup

DESCRIPTION = """
{{ cookiecutter.name }} module for Foris Controller
"""

setup(
    name="foris-controller-{{ cookiecutter.name_snake }}-module",
    version=__version__,
    author="CZ.NIC, z.s.p.o. (https://www.nic.cz/)",
    author_email="packaging@turris.cz",
    packages=[
        "foris_controller_{{ cookiecutter.name_snake }}_module",
        "foris_controller_backends",
        "foris_controller_backends.{{ cookiecutter.name_snake }}",
        "foris_controller_modules",
        "foris_controller_modules.{{ cookiecutter.name_snake }}",
        "foris_controller_modules.{{ cookiecutter.name_snake }}.handlers",
    ],
    package_data={"foris_controller_modules.{{ cookiecutter.name_snake }}": ["schema", "schema/*.json"]},
    namespace_packages=["foris_controller_modules", "foris_controller_backends"],
    license="GPLv3",
    description=DESCRIPTION,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["foris-controller"],
    setup_requires=['pytest-runner'],
    tests_require=[
        'pytest',
        'foris-controller-testtools',
        'foris-client',
        'ubus',
        'paho-mqtt',
    ],
    entry_points={
        "foris_controller_announcer": [
            "{{ cookiecutter.name_snake }} = foris_controller_{{ cookiecutter.name_snake }}_module.announcer:make_time_message"
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
