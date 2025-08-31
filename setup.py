import os
from setuptools import setup

dependencies = []

if os.path.exists('/sys/bus/platform/drivers/gpiomem-bcm2835'):
    dependencies += ['RPi.GPIO', 'spidev']
elif os.path.exists('/sys/bus/platform/drivers/gpio-x3'):
    dependencies += ['Hobot.GPIO', 'spidev']
else:
    dependencies += ['Jetson.GPIO']

dependencies += ['pigpio']

setup(
    name='rpi-groove-ir-emitter',
    version='1.0.0',
    description='RPI Groove IR Emitter',
    long_description='',
    author='Alex Banica',
    author_email='ionut.alexandru.banica@gmail.com',
    python_requires='>=3.9',
    package_dir={'': 'ir_emitter'},
    packages=['rpi-groove-ir-emitter', ''],
    install_requires=dependencies,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX :: Linux',
    ],
)
