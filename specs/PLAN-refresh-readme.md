# Refresh README to match the tracked project plan

Status: Approved

Spec: `specs/SPEC-refresh-readme.md`

## Affected files

- `README.md`
- `specs/SPEC-refresh-readme.md`
- `specs/PLAN-refresh-readme.md`

## Implementation steps performed

1. Inspected branch and worktree status and confirmed the invoking checkout was
   clean.
2. Compared the existing README with tracked runtime, launcher, package metadata,
   examples, manifest, workflows, publisher, and repository inventory.
3. Rewrote the README to describe actual behavior and explicitly distinguish
   tracked source from ignored cache directories.
4. Added these auto-approved completed-work artifacts.
5. Ran short validation and reconciled the final Git diff and staging state.

## Validation run

- `sh -n run.sh`
- `git diff --check`
- Structural searches for documented CLI defaults, workflow commands, tracked
  tests, and tracked runtime paths.
- Attempted `python3 -m ruff check setup.py ir_emitter scripts`; the command
  stopped immediately because Ruff is not installed in the system interpreter.

## Validation skipped

- Automated tests: not applicable under the domain-only test policy because the
  repository has no tracked deterministic domain source logic.
- Hardware IR playback and pigpio daemon integration.
- Package build, hosted GitHub Actions, and live Forgejo publication/install.
- Ruff linting because no project virtual environment exists and Ruff is not
  installed in the system Python environment.

## QA and code review

- QA skipped as required by `$super-agent`.
- Independent code review skipped as required by `$super-agent`.

## Documentation updates

- README now covers actual scope, dependencies, installation, wiring, input
  format, CLI and launcher use, troubleshooting, tracked layout, development
  checks, CI, and release behavior.

## Staging status

- All accepted in-scope paths are staged for user review.

## Commit and push status

- No commit created.
- No branch pushed.

## Residual risk

- Installation commands and hardware behavior were verified against repository
  contracts but not exercised on a Raspberry Pi during this documentation-only
  direct run.
