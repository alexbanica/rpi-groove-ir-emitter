# AGENTS

## Domain-only test policy

- Automated tests of any kind, including unit, integration, contract, snapshot,
  workflow, and configuration tests, may be created or maintained only for
  deterministic domain source logic in this project.
- Do not create or maintain tests for anything outside domain source logic,
  including application orchestration, infrastructure and adapters,
  presentation, UI and controllers, Docker or container files, GitHub Actions
  or other CI/CD workflows, deployment and configuration, packaging and release
  scripts, tooling, or other operational code.
- Validate non-domain changes with appropriate static, syntax, lint, type,
  structural, build, dry-run, smoke, runtime, or operator checks instead of
  automated tests.
- If this project has no domain source logic, automated testing and test-first
  work are not applicable.
- This policy supersedes any more general testing or validation wording
  elsewhere in this file.

## Project implementation status

The tracked runtime is currently a compact legacy package centered on
`ir_emitter/IREmitter.py` and `ir_emitter/__main__.py`. It does not currently
contain separate domain, application, infrastructure, or controller package
trees. The dependency rules below govern future restructuring; do not describe
those layers as already implemented.

### Layers

- `domains`: entities, DTOs, and interfaces.
- `applications`: business services and orchestration.
- `infrastructures`: pigpio and JSON adapters.
- `controllers`: CLI request/response and coordination.
- `shared/constants`: centralized static strings and defaults.

Dependencies point inward. `controllers` and `infrastructures` may depend on application/domain contracts, while `domains` must stay independent of CLI parsing, JSON persistence, pigpio, GPIO, and filesystem concerns.

### Naming standards

- Interfaces are suffixed with `Interface`.
- Abstract classes are prefixed with `Abstract`.
- Implementations of abstract classes remove the `Abstract` prefix and keep the remaining name.
- Service implementations match interface names without suffix.

### Invariants

The following behavior must remain stable unless a new approved spec changes it:

1. CLI flags and defaults:
   - positional `file` required
   - `--out-gpio=12`
   - `--carrier=38000`
   - `--repeat=1`
2. Input JSON shape compatibility:
   - `{ "gpio_in": <int>, "pulse_us": <list[int]> }`
3. Playback behavior:
   - mark/space handling and carrier-wave generation semantics remain equivalent.
4. pigpio connection failure exits with status code `2`.

### Testing

- No tracked automated tests currently exist, and the tracked package has no
  separated deterministic domain source layer. Unit-test and test-first phases
  are therefore not applicable under the domain-only policy. Ignored
  `__pycache__` files are not source or test coverage.

### API docs scope

No HTTP API exists. OpenAPI and `.http` artifacts are not applicable for the current project scope.

## Durable Documentation Authority

- Current package source, `setup.py`, `MANIFEST.in`, launcher and publishing
  scripts, workflow files, and `README.md` supersede removed completed
  SPEC/PLAN history. Historical artifacts remain available in Git.
- Keep CLI, pulse format, installation, wiring, package, release, and operator
  behavior in `README.md`.
- Static checks cannot prove hosted GitHub Actions, Forgejo authentication or
  publication, anonymous installation, board-specific dependency selection,
  pigpio connectivity, GPIO electrical safety, carrier timing, IR transmission,
  or physical-device response. Report those outcomes as unverified unless they
  are exercised in the corresponding environment.
