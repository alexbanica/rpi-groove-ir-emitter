# PLAN: Use venv Python in run.sh

Status: Approved

Approved spec: `specs/SPEC-use-venv-python-in-run-sh.md`

## Target Branch

Use the current branch unless the implementation command is instructed to create a dedicated branch before editing.

## Ownership Boundary

Allowed production files:

- `run.sh`

Allowed documentation files:

- `README.md`

Allowed validation or test files:

- `tests/test_run_sh_venv_bootstrap.py`

Do not change IR playback behavior, JSON examples, `setup.py`, or package metadata.

## Implementation Steps

1. Verify the implementation command is running in a clean context or has explicit same-context confirmation.
2. Re-read `AGENTS.md`, `/home/alexbanica/workspace.md`, the approved spec, this plan, `run.sh`, `README.md`, and relevant test patterns.
3. Inspect worktree status and preserve unrelated user changes.
4. Update `run.sh` as POSIX `sh` so it:
   - resolves the repository root from the script path;
   - validates `--input` and input file existence before Python startup;
   - uses `.venv/bin/python` under the repository root when executable;
   - when `.venv/bin/python` is missing, creates `.venv` with `python3 -m venv`;
   - installs the project from the repository root with `.venv/bin/python -m pip install .`;
   - exits non-zero before invoking `ir_emitter` if venv creation or dependency installation fails;
   - invokes `.venv/bin/python -m ir_emitter "$input_file"`.
5. Keep the existing user-facing error messages for missing `--input` and missing files unless a small wording change is required by the shell flow.
6. Update `README.md` to document `run.sh --input ...`, first-run `.venv` creation, dependency installation, and the continued requirement to start `pigpio`.
7. Add deterministic tests for the launcher by copying the repository to a temporary directory, injecting stub `python3` or stub `.venv/bin/python` executables through `PATH`, and asserting:
   - existing `.venv/bin/python` is used;
   - missing `.venv` triggers `python3 -m venv .venv` and `.venv/bin/python -m pip install .`;
   - missing `--input` exits before bootstrap;
   - missing input file exits before bootstrap.
8. Keep tests hardware-free and avoid running the real `ir_emitter` module.

## Test-First Requirements

Before production implementation, use exactly one clean-context test-focused subagent if subagent tooling is available.

The test-focused subagent should:

- Add `tests/test_run_sh_venv_bootstrap.py` before production changes.
- Keep tests deterministic, local, and independent of real GPIO hardware, real network access, or installing dependencies.
- Report any blocker if POSIX shell test stubbing cannot cover the approved behavior safely.

## Implementation Subagent Requirements

For behavior-changing implementation, use exactly one clean-context implementation subagent if subagent tooling is available.

The implementation subagent receives only:

- `specs/SPEC-use-venv-python-in-run-sh.md`
- `specs/PLAN-use-venv-python-in-run-sh.md`
- `run.sh`
- `README.md`
- `tests/test_run_sh_venv_bootstrap.py`

## Review Requirements

After implementation, use exactly one clean-context code-review subagent if subagent tooling is available.

The review must check:

- `run.sh` uses the project-local `.venv/bin/python` and no longer hardcodes `/usr/bin/python3`.
- `.venv` bootstrap is relative to the script location.
- Input validation occurs before bootstrap.
- Bootstrap failures exit before module execution.
- Tests do not require GPIO hardware, real package downloads, or the real `ir_emitter` module.
- README accurately documents first-run behavior and pigpio daemon requirements.

## Main-Agent QA

Run QA as the main agent after review findings are resolved:

1. `sh -n run.sh`
2. `python -m unittest discover -s tests -p 'test_*.py'`
3. `git diff --check`
4. If SSH access is available, inspect `pi11.pi.home` after implementation to verify:
   - the deployed checkout has `.venv/bin/python`;
   - `.venv/bin/python -m pip show pigpio` succeeds;
   - `run.sh` no longer contains `/usr/bin/python3`.

Expected results:

- Shell syntax validation succeeds.
- Unit tests pass.
- Whitespace validation passes.
- Remote inspection confirms the runtime environment can provide `pigpio`; real IR playback remains dependent on pigpio daemon and hardware availability.

## Documentation

Update `README.md` with the approved launcher and first-run virtual environment behavior.

## Commit And Push

- Commit only if implementation, review, QA, and final main-agent acceptance are complete.
- Use a non-draft commit message only when required validation completes successfully.
- Push only when repository policy and user instructions allow it.

## No-Research Constraint

Implementation must not perform product, architecture, scope, or plan research. It may inspect only the approved artifacts, applicable instructions, owned files listed above, minimal local test patterns, and validation output needed to execute this plan.
