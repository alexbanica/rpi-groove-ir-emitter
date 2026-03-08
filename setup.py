from pathlib import Path

from setuptools import find_packages, setup

requirements = [
    "pigpio>=1.78",
    "spidev>=3.6; platform_system == 'Linux'",
    "RPi.GPIO>=0.7.1; platform_system == 'Linux' and (platform_machine == 'armv7l' or platform_machine == 'armv6l')",
    "Hobot.GPIO>=0.1.0; platform_system == 'Linux' and platform_machine == 'aarch64'",
    "Jetson.GPIO>=2.1.0; platform_system == 'Linux' and platform_machine == 'aarch64'",
]

setup(
    name="rpi-groove-ir-emitter",
    version="1.0.0",
    description="RPI Groove IR Emitter",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Alex Banica",
    author_email="ionut.alexandru.banica@gmail.com",
    python_requires=">=3.9",
    packages=find_packages(include=["ir_emitter", "ir_emitter.*"]),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX :: Linux",
    ],
)
