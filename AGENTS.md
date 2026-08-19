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

The codebase is aligned to a DDD + Onion style layout.

### Layers

- `domains`: entities, DTOs, and interfaces.
- `applications`: business services and orchestration.
- `infrastructures`: pigpio and JSON adapters.
- `controllers`: CLI request/response and coordination.
- `shared/constants`: centralized static strings and defaults.

Dependencies point inward. `controllers` and `infrastructures` may depend on application/domain contracts, while `domains` must stay independent of CLI parsing, JSON persistence, pigpio, GPIO, and filesystem concerns.

### Project-specific architecture

- `ir_emitter/domains/entities`: raw pulse frame and playback model objects.
- `ir_emitter/domains/dtos`: datastore-free transfer objects for pulse input/output.
- `ir_emitter/domains/interfaces`: domain-facing contracts; every interface must use the `Interface` suffix.
- `ir_emitter/applications/services`: emit/playback orchestration services.
- `ir_emitter/infrastructures/emitters`: concrete carrier-wave and pulse emission adapters.
- `ir_emitter/infrastructures/gpio`: pigpio/GPIO boundary implementations.
- `ir_emitter/infrastructures/persistences`: JSON pulse file loading adapters.
- `ir_emitter/controllers/requests` and `ir_emitter/controllers/responses`: CLI DTOs.
- `ir_emitter/shared/constants`: default GPIO, carrier, and static text values.

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

- Unit tests live in `tests/`.
- Run with:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

### API docs scope

No HTTP API exists. OpenAPI and `.http` artifacts are not applicable for the current project scope.
