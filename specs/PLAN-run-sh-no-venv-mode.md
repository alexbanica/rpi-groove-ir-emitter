# PLAN: run.sh native Python mode

Status: Approved

Approved spec: `specs/SPEC-run-sh-no-venv-mode.md`

## Target Branch

Use the current branch.

## Ownership Boundary

Allowed production files:

- `run.sh`

Allowed documentation files:

- `README.md`

Allowed validation or test files:

- `tests/test_run_sh_venv_bootstrap.py`

Allowed spec files:

- `specs/SPEC-run-sh-no-venv-mode.md`
- `specs/PLAN-run-sh-no-venv-mode.md`

Do not change IR playback behavior, JSON examples, package metadata, or Docker image files.

## Implementation Steps

1. Add tests for native Python mode:
   - `--no-venv` uses `python3 -m ir_emitter "$input_file"` and does not use an existing `.venv/bin/python`.
   - `RUN_SH_NO_VENV=1` uses `python3 -m ir_emitter "$input_file"` and does not bootstrap `.venv`.
2. Update `run.sh` as POSIX `sh`:
   - initialize native mode from `RUN_SH_NO_VENV=1`;
   - parse and consume `--no-venv`;
   - preserve existing `--input` validation and missing-file behavior;
   - in native mode, execute `python3 -m ir_emitter "$input_file"`;
   - otherwise keep existing `.venv` behavior.
3. Update `README.md` with container/native Python usage.
4. Validate with:
   - `sh -n run.sh`
   - `python3 -m unittest discover -s tests -p 'test_*.py'`
   - `git diff --check`
5. If available, run or inspect the target container enough to confirm no-venv mode bypasses `.venv`.

## Review Requirements

Review must check:

- default behavior still uses or creates `.venv`;
- `--no-venv` and `RUN_SH_NO_VENV=1` bypass `.venv`;
- input validation still occurs before Python startup;
- launcher-only flags are not passed to `ir_emitter`;
- README does not imply extra IR emitter flags are forwarded by `run.sh`.

## Commit And Push

Commit and push after validation if repository state remains clean and validation passes.
