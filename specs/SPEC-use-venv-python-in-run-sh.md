# SPEC: Use venv Python in run.sh

Status: Approved

## Purpose

Make `run.sh` execute the IR emitter with the project virtual environment Python, creating that environment and installing project dependencies when needed, so deployed Raspberry Pi runs use the required runtime dependencies.

## Problem Statement

On `pi11.pi.home`, the project is deployed at `/home/alexbanica/rpi-groove-ir-emitter` with a `.venv` virtual environment. That venv contains the `pigpio` Python package, but `run.sh` hardcodes `/usr/bin/python3`, so even an activated virtual environment is bypassed.

Running:

```bash
sh ./run.sh --input examples/ventilator-onoff.json
```

therefore imports `ir_emitter` with the system interpreter and fails with `ModuleNotFoundError: No module named 'pigpio'`.

## Scope

- Update `run.sh` so it selects a Python interpreter that can use the project virtual environment.
- When the project virtual environment is missing, create `.venv` under the repository root.
- Install the project and its declared dependencies into `.venv` when the environment is created.
- Preserve the existing `--input <file>` interface.
- Preserve existing input-file validation and error behavior.
- Preserve the final module execution form `python -m ir_emitter <file>`.
- Update documentation if the launcher behavior or recommended runtime command changes.
- Add deterministic validation that can run without Raspberry Pi GPIO hardware where practical.

## Out Of Scope

- Changing IR playback semantics, carrier generation, pulse timing, GPIO defaults, or JSON input compatibility.
- Changing `setup.py` package metadata.
- Adding a console-script entry point.
- Starting or managing the `pigpio` daemon in `run.sh`.
- Changing the documented pigpio connection failure exit status.

## Definitions

- Project virtual environment: a Python virtual environment at `.venv` under the repository root, with its interpreter at `.venv/bin/python`.
- Active virtual environment: an executable Python interpreter at `$VIRTUAL_ENV/bin/python` when `VIRTUAL_ENV` is set.
- Bootstrap interpreter: `python3` found on `PATH`, used to create `.venv` when `.venv/bin/python` is missing.

## Inputs And Constraints

- `run.sh` is POSIX `sh`.
- The deployed Pi path may differ from a developer checkout path, so interpreter selection must be relative to the script location, not the caller's current directory.
- `python3` must be available on `PATH` to bootstrap a missing `.venv`.
- The bootstrap flow may require network access or locally available package indexes to install dependencies declared by `setup.py`.
- The command must continue accepting `--input <file>`.
- The input file path is interpreted relative to the caller's current working directory, matching current behavior.
- The existing CLI module still requires `pigpio` and a running pigpio daemon for real playback.

## Deterministic Behavior

- When `.venv/bin/python` exists next to `run.sh`, `run.sh` uses that interpreter.
- When `.venv/bin/python` is missing, `run.sh` creates `.venv` next to the script using `python3 -m venv`.
- After creating `.venv`, `run.sh` installs the project into that environment using `.venv/bin/python -m pip install .` from the repository root.
- If `.venv` creation or dependency installation fails, `run.sh` exits non-zero before invoking `ir_emitter`.
- `run.sh --input examples/ventilator-onoff.json` invokes `ir_emitter` as a module with the selected interpreter and the input file as the positional module argument.
- Missing `--input` and non-existent input file errors remain user-facing validation failures before Python starts.
- The launcher does not hide module import failures, pigpio daemon connection failures, or playback failures.

## Assumptions

- The `.venv` directory on `pi11.pi.home` is the intended runtime environment for this deployment.
- Always using the project-local `.venv` is preferred over an already active venv because it makes deployment behavior deterministic from the repository checkout.
- The existing `pigpio` package installed in the remote `.venv` is sufficient to resolve the reported import failure.

## Impact And Regression Considerations

- Hardcoding `/usr/bin/python3` currently makes deployed behavior independent of the venv but breaks dependency resolution. The new selection order changes that dependency boundary intentionally.
- Resolving paths relative to the script location avoids accidental dependence on the caller's current working directory.
- Creating `.venv` from `run.sh` makes first-run behavior more convenient but introduces possible first-run failures when Python venv support, pip, or dependency network access is unavailable.
- Hardware playback still depends on pigpio daemon availability and GPIO access; this change only selects the interpreter.

## Validation Plan

- Run the repository unit tests:
  `python -m unittest discover -s tests -p 'test_*.py'`
- Run shell syntax validation for `run.sh`:
  `sh -n run.sh`
- Add or run deterministic launcher validation that verifies `run.sh` creates or uses a project-local `.venv/bin/python` without requiring GPIO hardware.
- Run `git diff --check`.
- If SSH access is available, verify on `pi11.pi.home` that `.venv/bin/python -m pip show pigpio` succeeds and that `run.sh` no longer invokes `/usr/bin/python3`.

## Documentation Requirements

- Update `README.md` to document that `run.sh` creates `.venv` on first use, installs dependencies, and then runs with `.venv/bin/python`.
