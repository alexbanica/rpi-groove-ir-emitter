# Fix publish-workflow secret test

Status: Approved

## Purpose

Keep the release workflow's deterministic contract test aligned with the
credential source used by the tagged `1.0.0` release workflow.

## Requested behavior

The publish-workflow test must require `FORGEJO_PACKAGE_USERNAME` to come from
the repository secret context, matching `.github/workflows/publish.yml`.

## Scope

- Update the one stale workflow-test assertion.
- Preserve the existing rule that release credentials are passed only to the
  publishing step.

## Out of scope

- Changing release credentials, workflow behavior, package publishing, or
  tags.

## Delivered behavior

The test now expects `secrets.FORGEJO_PACKAGE_USERNAME`; the existing expected
token secret and step-level credential-scope assertions remain unchanged.

## Validation performed

- `python -m unittest discover -s tests -p 'test_*.py'` using Python 3.11.14.
- `git diff --check`.

## Validation skipped

Hosted GitHub Actions re-run and a real Forgejo publication were not run.

## Documentation changes

This completed-work spec records the narrow CI repair; no user documentation
changed.
