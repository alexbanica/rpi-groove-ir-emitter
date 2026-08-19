# Remove infrastructure tests plan

Status: Approved

## Spec reference

`specs/SPEC-remove-infrastructure-tests.md`

## Affected files

- `tests/test_packaging_metadata.py` (deleted)
- `tests/test_publish_forgejo_package.py` (deleted)
- `tests/test_run_sh_venv_bootstrap.py` (deleted)
- `specs/SPEC-remove-infrastructure-tests.md` (added)
- `specs/PLAN-remove-infrastructure-tests.md` (added)

## Implementation performed

1. Inspected the clean invoking checkout and complete tracked test inventory.
2. Classified all three tracked tests as packaging, release-tooling, or launcher
   tests outside deterministic domain source logic.
3. Deleted the three non-domain test files without changing production or
   workflow code.
4. Verified that no tracked test file remains under `tests/`.
5. Recorded the completed work in the approved spec and plan.

## Validation run

- Tracked test inventory before and after deletion.
- `git diff --check`.
- Staged path-list and staged-diff inspection.

## Validation skipped

- Automated tests because non-domain test maintenance is prohibited and no
  tracked domain test remains to execute.
- Hosted GitHub Actions and package publication.

## QA and code review

QA and independent code review were skipped as required by `$super-agent`.

## Documentation updates

The approved completed-work artifacts document the removal. README and operator
documentation remain unchanged because the discovery command remains available
for future domain tests.

## Staging and delivery status

All accepted in-scope changes are staged. No commit or push was performed
because this invocation did not explicitly request either operation.

## Residual risk

Hosted workflow behavior and a new package release remain unverified. Release
tag `1.0.1` still points to the previously pushed commit and therefore does not
contain this staged-only removal.
