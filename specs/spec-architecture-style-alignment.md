# Spec: Architecture and Coding Style Alignment (Emitter)

## Metadata
- Spec ID: `SPEC-2026-03-08-EMITTER-ARCH-ALIGNMENT`
- Branch: `spec/architecture-style-alignment`
- Status: `Approved`
- Authoring Date: `2026-03-08`

## 1. Purpose
Realign the emitter project to the DDD + Onion architecture and coding rules, using the receiver project as structural reference, while preserving existing emitter behavior.

## 2. Definitions
- Entity: persisted domain object.
- DTO: non-persisted transfer object.
- Invariant: behavior that must remain unchanged after refactor.

## 3. Scope
### In Scope
- Full structural refactor to DDD + Onion Architecture.
- Separation of domain and infrastructure concerns.
- Interface-first contracts and concrete implementations.
- Naming/style alignment from AGENTS rules:
  - package names in plural form.
  - one class per file.
  - interfaces suffixed with `Interface`.
  - implementations matching interface names without `Interface`.
- Centralization of static strings/constants.
- Add `requirements.txt` with platform-specific dependencies.
- Fix packaging setup issues.
- Update `README.md` and `AGENTS.md`.
- Add tests for business logic and regression safety.

### Out of Scope
- New emitter features.
- Any functional behavior changes for valid existing workflows.

## 4. Mandatory Invariants (Behavior Must Not Change)
1. CLI arguments and defaults remain exactly:
   - positional `file`
   - `--out-gpio` default `12`
   - `--carrier` default `38000`
   - `--repeat` default `1`
2. JSON input shape compatibility remains:
   - `{ "gpio_in": <int>, "pulse_us": <list[int]> }`
3. Playback behavior remains functionally equivalent:
   - mark/space handling via pigpio pulses
   - carrier-wave generation logic and repeat loop semantics
4. pigpio connection failure exits with status code `2`.

## 5. Architecture Specification
Dependency direction must remain onion-compliant:
- `domains`: entities, DTOs, interfaces (no infrastructure/framework dependencies).
- `applications`: orchestration services using domain interfaces.
- `infrastructures`: pigpio integration and JSON persistence adapters.
- `controllers`: CLI argument parsing and use-case execution.

Outer layers may depend inward; inward layers must not depend outward.

## 6. API/Integration Documentation Rule
No HTTP API exists; OpenAPI and `/http/*.http` artifacts are not applicable.

## 7. Requirements File Specification
Create `requirements.txt` including:
- `pigpio`
- `RPi.GPIO`, `spidev`, `Hobot.GPIO`, `Jetson.GPIO` using platform markers.

## 8. Build, Quality, and Regression Requirements
1. Project builds successfully.
2. No warnings introduced by refactor.
3. Tests cover business logic.
4. All tests pass.
5. Regression safety verified against invariants.

## 9. Deliverables
- Refactored codebase aligned to architecture/style rules.
- `requirements.txt`.
- Updated packaging setup.
- Updated `README.md` and `AGENTS.md`.
- Passing tests.

## 10. Assumptions
- Linux SBC runtime and pigpio daemon usage remain valid assumptions.
- CLI remains the external interface.
