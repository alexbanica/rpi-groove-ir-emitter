# Fix publish-workflow secret test plan

Status: Approved

Spec: `specs/SPEC-fix-publish-workflow-secret-test.md`

## Affected files

- `tests/test_github_workflows.py`
- `specs/SPEC-fix-publish-workflow-secret-test.md`
- `specs/PLAN-fix-publish-workflow-secret-test.md`

## Steps performed

1. Retrieved the failed GitHub Actions job log and identified the release
   script's captured unit-test failure.
2. Reproduced the suite locally and identified the stale `vars` expectation
   after the workflow changed the username to a secret.
3. Updated the assertion to match the workflow's step-scoped secret input.

## Validation run

- `PYENV_VERSION=3.11.14 python -m unittest discover -s tests -p 'test_*.py'`
- `git diff --check`

## Validation skipped

- Hosted GitHub Actions re-run.
- Live Forgejo upload and public package verification.

## QA and review

QA and code review were skipped under the requested `super-agent` workflow.

## Staging and delivery

All accepted paths are staged. No commit or push was requested or performed.

## Residual risk

The hosted runner and release publication have not been re-executed; the next
tagged run must verify the repair in GitHub Actions.
