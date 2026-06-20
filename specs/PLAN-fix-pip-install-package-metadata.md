# PLAN: Fix pip install package metadata

Status: Approved

Approved spec: `specs/SPEC-fix-pip-install-package-metadata.md`

## Target Branch

Use the current branch unless the implementation command is instructed to create a dedicated branch before editing.

## Ownership Boundary

Allowed production file:

- `setup.py`

Allowed validation-only or test file changes:

- Add or update packaging-focused tests only if a deterministic test can be kept local and does not require downloading hardware-specific dependencies.

No runtime behavior files are in scope unless validation proves the packaging fix cannot work without them.

## Implementation Steps

1. Verify the implementation command is running in a clean context or has explicit same-context confirmation.
2. Re-read `AGENTS.md`, `/home/alexbanica/workspace.md`, the approved spec, this plan, and `setup.py`.
3. Inspect worktree status and preserve unrelated user changes.
4. Update `setup.py` so setuptools packages the existing `ir_emitter` import package.
5. Preserve:
   - distribution name `rpi-groove-ir-emitter`
   - Python requirement `>=3.9`
   - existing version metadata
   - existing install-time dependency selection behavior
   - documented module execution path `python -m ir_emitter`
6. Do not add console scripts, migrate to `pyproject.toml`, rename packages, or refactor runtime code.

## Test-First Requirements

The change is packaging metadata behavior. Before production implementation, use exactly one clean-context test-focused subagent if subagent tooling is available.

The test-focused subagent should:

- Determine whether a local deterministic packaging metadata test is practical without network access or hardware dependencies.
- Add a focused test only if it can validate package discovery or metadata without forcing dependency downloads.
- Otherwise report that automated test addition is not practical and rely on direct packaging validation.

## Implementation Subagent Requirements

For behavior-changing implementation, use exactly one clean-context implementation subagent if subagent tooling is available.

The implementation subagent receives only:

- `specs/SPEC-fix-pip-install-package-metadata.md`
- `specs/PLAN-fix-pip-install-package-metadata.md`
- `setup.py`
- Any test file created by the test-focused subagent

## Review Requirements

After implementation, use exactly one clean-context code-review subagent if subagent tooling is available.

The review must check:

- `setup.py` packages `ir_emitter`, not an invalid hyphenated import package.
- The distribution name remains `rpi-groove-ir-emitter`.
- Runtime and CLI behavior files were not changed out of scope.
- Validation coverage is sufficient for a metadata-only packaging fix.

## Main-Agent QA

Run QA as the main agent after review findings are resolved:

1. `python -m unittest discover -s tests -p 'test_*.py'`
2. A local packaging validation that avoids dependency downloads where possible, such as:
   `python setup.py egg_info`
3. If feasible in an isolated environment without dependency downloads, validate local install/import behavior.
4. `git diff --check`

Expected results:

- Packaging metadata generation succeeds.
- `ir_emitter` remains importable in the validation environment.
- Repository tests pass or are reported as unavailable when no source tests exist.
- No whitespace errors are present.

## Documentation

No documentation update is expected because the documented installation command remains `pip install .`.

## Commit And Push

- Commit only if implementation, review, QA, and final main-agent acceptance are complete.
- Use a non-draft commit message only when required validation completes successfully.
- Push only when repository policy and user instructions allow it.

## No-Research Constraint

Implementation must not perform product, architecture, scope, or plan research. It may inspect only the approved artifacts, applicable instructions, `setup.py`, any packaging test file, and minimal local validation output needed to execute this plan.
