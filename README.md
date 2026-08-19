# Raspberry Pi Grove IR Emitter

`rpi-groove-ir-emitter` replays raw infrared pulse timings through a Raspberry
Pi GPIO pin. It reads pulse captures from JSON, converts each mark into a
pigpio carrier waveform, and keeps the output low during each space.

The package name contains the historical spelling `groove`; the supported
hardware use case is a Grove IR emitter, or another correctly driven IR LED,
connected to a Raspberry Pi running the pigpio daemon.

## What it currently does

- Loads the receiver-compatible JSON shape
  `{ "gpio_in": <int>, "pulse_us": <list[int]> }`.
- Treats zero-based even-numbered pulse entries, starting with the first entry,
  as carrier marks and the alternating entries as spaces, with every duration
  expressed in microseconds.
- Emits on BCM GPIO 12 by default, at a 38 kHz carrier and a 33% duty cycle.
- Allows the output GPIO, carrier frequency, and whole-frame repeat count to be
  changed through the Python module CLI.
- Includes three sample captures for a ventilator under `examples/`.

`gpio_in` is capture metadata only. It is printed when the file is loaded and
does not select the output pin. The CLI does not currently expose the duty
cycle; changing it requires using `IREmitter` from Python.

## Requirements

- A Raspberry Pi with Linux and a usable BCM GPIO pin.
- A Grove IR emitter or an IR LED with appropriate current limiting and drive
  circuitry. Do not drive a high-current IR LED directly from a GPIO pin.
- Python 3.9 or newer.
- The pigpio daemon and Python package.

The package installer selects an additional board GPIO dependency by inspecting
the target system: `RPi.GPIO` and `spidev` on Raspberry Pi, `Hobot.GPIO` and
`spidev` on supported Hobot systems, or `Jetson.GPIO` otherwise. Install the
project on the target device so that detection reflects the actual board.

Install pigpio using the method provided by your operating system, then start
the daemon with `sudo pigpiod` (or the equivalent service supplied by the
system). The emitter exits with status 2 if it cannot connect to pigpio.

## Installation

From a source checkout:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install .
```

Published releases are available from the public Forgejo package index. PyPI is
kept as an additional index because runtime dependencies are not hosted in the
Forgejo registry:

```bash
python3 -m pip install \
  --index-url https://forgejo.alexlab.nl/api/packages/public/pypi/simple \
  --extra-index-url https://pypi.org/simple \
  rpi-groove-ir-emitter
```

## Wiring

The default output is BCM GPIO 12, not physical header pin 12. Connect the
emitter according to its electrical requirements and use a transistor driver
when the GPIO cannot safely provide the required current. Verify pin numbering,
polarity, voltage, and current limits before enabling playback.

## Pulse file format

The input file must be JSON with a `pulse_us` list. Receiver captures also carry
`gpio_in` metadata:

```json
{
  "gpio_in": 16,
  "pulse_us": [9050, 4490, 595, 565, 565, 570]
}
```

Durations are converted to integers. The first duration is a mark, the second
is a space, and the sequence continues alternating between them. Use positive
microsecond durations captured from the source remote. When `gpio_in` is absent,
the loader reports its value as `-1`; playback is otherwise unchanged.

## Usage

For the full CLI, invoke the module directly:

```bash
python3 -m ir_emitter examples/ventilator-onoff.json
python3 -m ir_emitter examples/ventilator-speed.json \
  --out-gpio 12 \
  --carrier 38000 \
  --repeat 2
```

CLI arguments:

- `file`: required path to a pulse JSON file.
- `--out-gpio`: BCM output pin; default `12`.
- `--carrier`: carrier frequency in hertz; default `38000`.
- `--repeat`: number of complete frame transmissions; default `1`.

On successful playback the command reports the number of loaded durations and
prints `Playback finished.`. Interruptions and malformed files are not converted
into custom error messages; Python reports those failures directly.

### Repository launcher

The checkout also contains a convenience launcher:

```bash
./run.sh --input examples/ventilator-onoff.json
```

By default, `run.sh` uses `.venv/bin/python`. If that interpreter does not
exist, the script creates `.venv` and installs the project into it before
running. It does not start pigpio.

For a container or system image that already contains all runtime dependencies,
bypass the repository virtual environment with either form:

```bash
./run.sh --no-venv --input examples/ventilator-onoff.json
RUN_SH_NO_VENV=1 ./run.sh --input examples/ventilator-onoff.json
```

The launcher recognizes only `--input` and `--no-venv`; other arguments are
ignored. It passes only the resolved file path to `python -m ir_emitter`, so use
the module CLI when changing GPIO, carrier, or repeat settings.

## Troubleshooting

- `Could not connect to pigpio daemon`: start `pigpiod` and confirm its socket
  is reachable. This failure exits with status 2.
- `Error importing pigpio`: install the `pigpio` Python package in the same
  interpreter or virtual environment used to run the emitter.
- Weak or unreliable transmission: check emitter polarity, line of sight,
  current limiting, transistor drive, supply voltage, and ambient IR noise.
- Incorrect command response: confirm the captured carrier frequency and that
  `pulse_us` begins with a mark and alternates mark/space durations.

## Current project layout

The tracked runtime is intentionally small:

- `ir_emitter/__main__.py`: argument parsing, pigpio connection, and playback
  coordination.
- `ir_emitter/IREmitter.py`: JSON loading and pigpio waveform construction.
- `ir_emitter/__init__.py`: package version and carrier/duty-cycle defaults.
- `run.sh`: repository virtual-environment launcher.
- `examples/`: sample ventilator pulse captures.
- `scripts/publish_forgejo.py`: release build, validation, publication, and
  anonymous install verification.

There are currently no tracked domain, application, infrastructure, controller,
or automated-test source files. Ignored `__pycache__` directories do not
represent implemented package layers.

## Development

Install the pinned development tools and run the repository's active local
checks:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m ruff check setup.py ir_emitter scripts
sh -n run.sh
```

The repository currently has no tracked deterministic domain source logic, so
its domain-only test policy leaves no applicable automated tests. Non-domain
changes are validated with lint, syntax, build, structural, smoke, or operator
checks as appropriate.

## CI and releases

- `.github/workflows/ci.yml` runs the Ruff command above on Python 3.13 for
  pull requests targeting `main` and pushes to `main`.
- `.github/workflows/publish.yml` runs on exact release tags and publishes a
  source distribution and pure-Python wheel to the public Forgejo PyPI registry.
- Stable tags use `X.Y.Z`; beta tags use `X.Y.Z-betaN` with `N >= 1` and are
  published with the Python version `X.Y.ZbN`. Tags do not have a leading `v`.
- Publication requires the repository secrets `FORGEJO_PACKAGE_USERNAME` and
  `FORGEJO_PACKAGE_TOKEN`.
- The publisher runs Ruff, validates package contents and metadata, rejects an
  already-published version, verifies downloaded artifact hashes, and performs
  an anonymous exact-version installation with dependency resolution.

The registry upload endpoint is
`https://forgejo.alexlab.nl/api/packages/public/pypi`; the public package index
is
`https://forgejo.alexlab.nl/api/packages/public/pypi/simple/rpi-groove-ir-emitter/`.

## License

See [LICENSE](LICENSE).
