import os
import re
from pathlib import Path

from setuptools import find_packages, setup

dependencies = []


def _read_version() -> str:
    init_file = Path(__file__).resolve().parent / "ir_emitter" / "__init__.py"
    text = init_file.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*[\"\']([^\"\']+)[\"\']$', text, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not read __version__ from ir_emitter/__init__.py")
    return match.group(1)


if os.path.exists('/sys/bus/platform/drivers/gpiomem-bcm2835'):
    dependencies += ['RPi.GPIO', 'spidev']
elif os.path.exists('/sys/bus/platform/drivers/gpio-x3'):
    dependencies += ['Hobot.GPIO', 'spidev']
else:
    dependencies += ['Jetson.GPIO']

dependencies += ['pigpio']

setup(
    name='rpi-groove-ir-emitter',
    version=_read_version(),
    description='RPI Groove IR Emitter',
    long_description='',
    author='Alex Banica',
    author_email='ionut.alexandru.banica@gmail.com',
    python_requires='>=3.9',
    packages=find_packages(include=['ir_emitter', 'ir_emitter.*']),
    install_requires=dependencies,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX :: Linux',
    ],
)
