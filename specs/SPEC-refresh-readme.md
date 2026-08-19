# Refresh README to match the tracked project

Status: Approved

## Purpose

Make the root README an accurate operator and contributor guide for the code,
launcher, packaging, CI, and repository structure that are currently tracked.

## Requested behavior

Replace stale or misleading statements with documentation derived from the
current implementation. In particular, document the pigpio runtime boundary,
actual CLI and launcher interfaces, pulse format, packaging behavior, current
flat source layout, domain-only test status, and release workflow.

## Scope

- Rewrite `README.md`.
- Add this completed-work spec and its matching completed-work plan.

## Out of scope

- Runtime, launcher, packaging, CI, or release behavior changes.
- Changes to `AGENTS.md`.
- Creation of domain/application/infrastructure/controller source layers.
- Adding automated tests.
- Hardware playback or registry publication.

## Inputs and constraints

- Treat tracked files as the source of truth.
- Do not infer implemented architecture from ignored cache directories.
- Preserve the package's historical `groove` distribution name while naming
  the Grove hardware use case accurately.
- Keep the documented CLI defaults and JSON compatibility invariants intact.
- Apply the repository's domain-only test policy.

## Deterministic behavior delivered

- README describes the checked-in three-module runtime and its pigpio behavior.
- CLI options, defaults, launcher behavior, and JSON mark/space interpretation
  match current source.
- Installation guidance no longer presents shell commands as pip packages.
- Duty-cycle control is described as a Python API capability, not a CLI flag.
- Current source and test absence are distinguished from ignored cache paths.
- CI and Forgejo publication documentation matches active workflow and publisher
  files.

## Assumptions and impact

- Raspberry Pi with pigpio is the supported runtime documented because all
  emission uses the pigpio client and daemon.
- Board-specific dependency selection remains documented as packaging behavior,
  without claiming those dependencies replace pigpio at runtime.
- Documentation changes do not alter executable behavior.

## Validation performed

- Compared README claims against tracked runtime, launcher, packaging, workflow,
  publisher, manifest, and example files.
- Ran short documentation, shell, and structural checks recorded in the matching
  plan. Ruff was attempted but unavailable in the system Python environment.

## Validation skipped

- Automated tests are not applicable to this documentation-only change and no
  tracked deterministic domain tests exist.
- Hardware playback, package building, hosted CI, and Forgejo publication exceed
  the short-validation boundary for this direct workflow.
- Ruff validation was skipped after the system Python reported that the module
  is not installed; dependency installation was not performed for this
  documentation-only run.
- Independent QA and code review are skipped by the `$super-agent` workflow.

## Documentation changes

- Replaced the root README with a current usage, behavior, layout, development,
  and release guide.
- Added this completed-work spec and its plan.
