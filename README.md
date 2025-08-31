# RPI GROOVE IR Emitter

Transmit infrared (IR) signals from a Raspberry Pi (and compatible SBCs) using JSON-defined pulse sequences. Useful for automating IR-controlled devices such as fans, TVs, air conditioners, and more.

## Features

- Plays raw IR pulse sequences defined in JSON files
- Supports carrier frequency and duty cycle control
- Repeats entire frames as needed
- Includes example IR command files for a ventilator device

## Requirements

- Hardware:
    - Raspberry Pi (or compatible board with GPIO)
    - IR LED/emitter module (e.g., Grove IR Emitter) and proper drive circuitry
    - Wiring or Grove/Base HAT for connectivity

- Software:
    - Python 3.9+
    - pigpio (daemon + Python package)
    - One of the board-specific GPIO packages (auto-detected during install):
        - RPi.GPIO + spidev (Raspberry Pi)
        - Hobot.GPIO + spidev (Certain Hobot boards)
        - Jetson.GPIO (NVIDIA Jetson)
    - Linux (GPIO access required)

Notes:
- Start the pigpio daemon before running: `sudo pigpiod`
- Ensure your user has permissions to access GPIO and pigpio socket, or run with `sudo` when necessary.

## Installation

From the project root:
```bash 
pip install .
```

If pigpio is not present, install the Python package and start the daemon:
```bash
pip install pigpio sudo pigpiod
```

## Wiring

- Connect your IR LED/emitter to a suitable GPIO pin via a current-limiting resistor and a transistor driver if required by your emitter module.
- Default transmit pin in examples is BCM GPIO 12. You can change it with `--out-gpio`.

Always verify polarity and maximum current ratings for your emitter module.

## Usage

Play a JSON pulse file:
```bash
/usr/bin/python3 -m ir_emitter examples/ventilator-onoff.json --out-gpio 12 --carrier 38000 --repeat 1
```

Parameters:
- `file` (positional): Path to JSON file containing the recorded pulses
- `--out-gpio`: BCM pin number for the transmitter (default: 12)
- `--carrier`: Carrier frequency in Hz (default: commonly 38000)
- `--repeat`: How many times to replay the entire frame (default: 1)

Before running, ensure:
```bash
sudo pigpiod
```

## Troubleshooting

- pigpio daemon not running:
    - Error: cannot connect to pigpio → run `sudo pigpiod`
- Weak or unreliable transmission:
    - Verify emitter orientation and line of sight
    - Use a transistor driver and proper resistor
    - Reduce ambient IR noise or move closer
- Timing issues:
    - Confirm correct carrier frequency (38 kHz is common but not universal)
    - Validate the pulse list alternates mark/space and uses microseconds
- Permissions:
    - If GPIO access fails, try `sudo` or adjust user group permissions

## Development

- Use editable installs (`pip install -e .`) for local development
- Keep JSON command files small and test frequently on hardware
- Contributions are welcome via pull requests and issues

## License

See the `LICENSE` file for license details.
