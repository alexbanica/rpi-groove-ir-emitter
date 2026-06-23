# SPEC: run.sh native Python mode

Status: Approved

## Purpose

Allow containerized deployments that already include Python dependencies in the image to run `run.sh` without using or bootstrapping the repository `.venv`.

## Problem Statement

The repository `.venv` can be shared through a Docker volume, but Python virtual environments are not portable across incompatible host and container Python runtimes. A `.venv` generated on the Raspberry Pi host with Python 3.13 can be visible inside an Alpine container whose `/usr/bin/python3` is Python 3.9, causing packages installed under `.venv/lib/python3.13/site-packages` to be invisible to the container runtime.

Some Docker images already provide the required Python dependencies natively. Those containers need a deterministic way to bypass `.venv` selection so `run.sh` executes with the image's `python3`.

## Scope

- Add an explicit `run.sh` native Python mode.
- Support `--no-venv` as a launcher-only flag.
- Support `RUN_SH_NO_VENV=1` as an environment-based equivalent.
- Preserve the existing `--input <file>` launcher interface.
- Preserve input-file validation before Python startup.
- Preserve default bare-metal behavior that uses or creates `.venv`.
- Update launcher documentation.
- Add deterministic launcher tests that do not require GPIO hardware.

## Out Of Scope

- Changing IR playback behavior, carrier generation, GPIO defaults, or JSON input compatibility.
- Changing package metadata or Docker images.
- Automatically detecting containers.
- Repairing or deleting incompatible `.venv` directories.
- Starting or managing the `pigpio` daemon.
- Passing extra IR emitter flags through `run.sh`.

## Definitions

- Native Python mode: `run.sh` executes `python3 -m ir_emitter "$input_file"` and does not inspect, create, install into, or execute `.venv`.
- Venv mode: existing behavior where `run.sh` uses `.venv/bin/python`, creating `.venv` and installing the project when that interpreter is missing.

## Deterministic Behavior

- By default, `run.sh` keeps using venv mode.
- When invoked with `--no-venv`, `run.sh` uses native Python mode.
- When `RUN_SH_NO_VENV=1`, `run.sh` uses native Python mode.
- The `--no-venv` flag is consumed by `run.sh` and is not passed to `ir_emitter`.
- Native Python mode still validates missing `--input` and missing input files before invoking Python.
- Native Python mode does not hide module import failures, pigpio daemon connection failures, or playback failures.

## Assumptions

- Containers using native Python mode provide `python3` on `PATH`.
- Containers using native Python mode already have the required Python dependencies installed in the image or system environment.

## Impact And Regression Considerations

- Existing bare-metal users are unaffected because venv mode remains the default.
- Container users can bypass incompatible mounted `.venv` directories without deleting or modifying the volume.
- If the container image lacks `pigpio` or other runtime dependencies, native Python mode will fail with the existing import error.

## Validation Plan

- Run shell syntax validation:
  `sh -n run.sh`
- Run unit tests:
  `python3 -m unittest discover -s tests -p 'test_*.py'`
- Run `git diff --check`.
- If the target container is available, verify `./run.sh --no-venv --input examples/ventilator-onoff.json` no longer uses `.venv`.

## Documentation Requirements

- Update `README.md` to document `--no-venv` and `RUN_SH_NO_VENV=1` for containers that already include dependencies.
