# SPEC: Fix pip install package metadata

Status: Approved

## Purpose

Allow installing the project from the repository root with `pip install .` without build metadata errors.

## Problem Statement

`pip install .` currently fails while preparing wheel metadata because `setup.py` declares invalid package names and maps them through `package_dir` to a non-existent path:

- `packages=['rpi-groove-ir-emitter', '']`
- `package_dir={'': 'ir_emitter'}`

The actual import package in the repository is `ir_emitter`.

## Scope

- Correct Python packaging metadata so the existing `ir_emitter` package is included by installation.
- Preserve the distribution name `rpi-groove-ir-emitter`.
- Preserve the existing import path `ir_emitter`.
- Preserve current install-time dependency selection behavior.
- Preserve CLI behavior, defaults, JSON compatibility, playback behavior, and pigpio failure exit behavior.

## Out Of Scope

- Migrating packaging to `pyproject.toml`.
- Renaming the Python import package.
- Adding console-script entry points.
- Refactoring runtime code or project architecture.
- Changing dependency selection rules for Raspberry Pi, Hobot, Jetson, or generic Linux environments.

## Definitions

- Distribution name: the package name used by pip metadata, currently `rpi-groove-ir-emitter`.
- Import package: the Python module package imported by users and runtime code, currently `ir_emitter`.

## Inputs And Constraints

- The repository root contains `setup.py`.
- The source package directory is `ir_emitter/`.
- The project supports Python 3.9+.
- Repository invariants from `AGENTS.md` remain unchanged.

## Deterministic Behavior

- Running `pip install .` from the repository root must no longer fail with `package directory 'ir_emitter/rpi-groove-ir-emitter' does not exist`.
- Package metadata generation must include the `ir_emitter` package.
- After installation, `python -m ir_emitter ...` remains the executable module form.
- Existing runtime imports such as `from ir_emitter.IREmitter import IREmitter` remain valid.

## Assumptions

- The user-reported installation failure is caused by the current `setup.py` package declaration.
- A package metadata-only correction is sufficient to unblock wheel metadata generation.

## Impact And Regression Considerations

- Incorrect package discovery could produce a wheel that installs no runtime package or changes the import path.
- Validation must check both metadata generation and importability of `ir_emitter`.
- Runtime behavior is not expected to change.

## Validation Plan

- Run the repository unit test command if source tests are present:
  `python -m unittest discover -s tests -p 'test_*.py'`
- Run a no-dependency local install/build validation that avoids downloading hardware-specific GPIO packages when possible.
- Verify `python -c "import ir_emitter; print(ir_emitter.__version__)"` succeeds in the validation environment after local installation or equivalent metadata check.
- Run `git diff --check`.

## Documentation Requirements

- Update documentation only if the installation command or supported import/module usage changes.
- No documentation update is required when `pip install .` remains the documented installation command.
