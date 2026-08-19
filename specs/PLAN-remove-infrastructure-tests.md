# Remove infrastructure tests plan

Status: Approved

## Spec reference

`specs/SPEC-remove-infrastructure-tests.md`

## Affected files

- `tests/test_packaging_metadata.py` (deleted)
- `tests/test_publish_forgejo_package.py` (deleted)
- `tests/test_run_sh_venv_bootstrap.py` (deleted)
- `.github/workflows/ci.yml` (updated)
- `scripts/publish_forgejo.py` (updated)
- `README.md` (updated)
- `specs/SPEC-remove-infrastructure-tests.md` (updated)
- `specs/PLAN-remove-infrastructure-tests.md` (updated)

## Implementation performed

1. Inspected the clean invoking checkout and complete tracked test inventory.
2. Classified all three tracked tests as packaging, release-tooling, or launcher
   tests outside deterministic domain source logic.
3. Deleted the three non-domain test files.
4. Verified that no tracked test file remains under `tests/`.
5. Removed the CI test job and the stale CI Ruff test-directory target.
6. Removed unittest discovery and the stale Ruff target from the publisher's
   quality gates.
7. Updated README to describe lint-only CI and publisher validation.
8. Recorded the completed final behavior in the approved spec and plan.

## Validation run

- Tracked test inventory before and after deletion.
- YAML parsing for `.github/workflows/ci.yml`.
- Bytecode-free Python compilation for `scripts/publish_forgejo.py`.
- Structural confirmation that active CI, publisher, and README commands no
  longer reference the deleted test directory or unittest discovery.
- `git diff --check`.
- Staged path-list and staged-diff inspection.

## Validation skipped

- Automated tests because non-domain test maintenance is prohibited and no
  tracked domain test remains to execute.
- Hosted GitHub Actions and package publication.
- Ruff because it is unavailable in the local Python 3 environment and no
  project virtual environment is present.

## QA and code review

QA and independent code review were skipped as required by `$super-agent`.

## Documentation updates

README documents the lint-only CI job and release publisher quality gate. The
approved completed-work artifacts document the final aligned removal.

## Staging and delivery status

The initial test removals were committed and pushed as `fbea757`. All accepted
consumer-alignment changes from this invocation are staged. No additional
commit or push was performed because this invocation did not explicitly request
either operation.

## Residual risk

Hosted workflow behavior and a new package release remain unverified. Existing
release tag `1.0.1` does not contain these staged consumer-alignment changes; a
new release tag should be created only after the fix is committed and pushed.
