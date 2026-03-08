# Raspberry Pi Grove IR Emitter

Python library and CLI for transmitting raw IR pulse/space timings from JSON recordings over GPIO using `pigpio`.

## Features

- Emit raw IR pulse durations stored in JSON files.
- Configure output GPIO, carrier frequency, and replay count.
- Compatible JSON input format from the receiver project.
- Layered architecture aligned to DDD and Onion principles.

## Requirements

- Python 3.9+
- Linux SBC (Raspberry Pi, Hobot, or Jetson)
- `pigpiod` daemon running

Install dependencies:

```bash
pip install -r requirements.txt
```

Install and enable `pigpiod`:

```bash
sudo apt-get update
sudo apt-get install -y python3-pigpio pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Platform-specific dependency policy

`requirements.txt` includes marker-based platform-specific packages:

- Raspberry Pi: `RPi.GPIO`, `spidev`
- Hobot: `Hobot.GPIO`
- Jetson: `Jetson.GPIO`
- Common: `pigpio`

## Project structure

```text
ir_emitter/
  applications/services/
  controllers/
    requests/
    responses/
  domains/
    dtos/
    entities/
    interfaces/
  infrastructures/
    emitters/
    gpio/
    persistences/
  shared/constants/
```

## CLI usage

Emit one JSON pulse frame:

```bash
python -m ir_emitter examples/ventilator-onoff.json --out-gpio 12 --carrier 38000 --repeat 1
```

Arguments and defaults:

- `file` (required positional)
- `--out-gpio` (default: `12`)
- `--carrier` (default: `38000`)
- `--repeat` (default: `1`)

Input JSON schema remains:

```json
{
  "gpio_in": 16,
  "pulse_us": [9000, 4500, 560]
}
```

## Development

Run tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Troubleshooting

- Cannot import `pigpio`:
  - `pip install pigpio`
- Cannot connect to daemon:
  - `sudo systemctl start pigpiod`
- Weak or unreliable transmission:
  - Validate wiring and BCM pin.
  - Use transistor/resistor drive as required by emitter hardware.

## License

See [LICENSE](LICENSE).
