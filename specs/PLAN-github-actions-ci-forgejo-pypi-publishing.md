# PLAN: Python 3.13-only GitHub Actions CI

Status: Approved

Approved spec:
`specs/SPEC-github-actions-ci-forgejo-pypi-publishing.md`

## Requested Outcome

Remove Python 3.9 from hosted GitHub Actions because the pinned
`build==1.5.0` development dependency requires Python 3.10 or newer. Keep the
distinct `lint` and `tests` checks, run both on Python 3.13, and preserve the
package's declared Python 3.9 runtime compatibility and all publishing behavior.

## Worktree And Delivery

- Repository: `rpi-groove-ir-emitter`.
- Linked worktree:
  `~/.herdr/worktrees/rpi-groove-ir-emitter/github-actions-ci-forgejo-pypi-publishing`.
- Delivery branch: `feature/github-actions-ci-forgejo-pypi-publishing`.
- The user explicitly authorized commit and push for this super-agent run.
- After the push is verified, detach the linked worktree at the delivery commit
  and safely remove only the transferred spec and plan copies from the invoking
  checkout.

## Affected Files

- `.github/workflows/ci.yml`
- `tests/test_github_workflows.py`
- `README.md`
- `specs/SPEC-github-actions-ci-forgejo-pypi-publishing.md`
- `specs/PLAN-github-actions-ci-forgejo-pypi-publishing.md`

No dependency pin, package metadata, runtime code, or publishing workflow change
is part of this correction.

## Implementation Performed

1. Removed the Python-version matrix from the `tests` job.
2. Set both `lint` and `tests` to the literal Python version `3.13`.
3. Updated workflow contract tests to require two Python 3.13 setup steps and
   prohibit Python 3.9 and a matrix.
4. Updated the README CI description and approved spec to describe the final
   hosted-CI contract while retaining `python_requires='>=3.9'`.

Test-first development is not applicable because this is a narrow workflow
configuration correction. The existing workflow contract test is updated with
the implementation and exercised as deterministic validation.

## Validation

Run only the short validation permitted by the super-agent workflow:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_github_workflows`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`
- `git diff --check`

Hosted GitHub Actions, a fresh dependency installation, a package build, and a
live Forgejo publish/install round trip are not run locally. Code-review and QA
phases are skipped by the super-agent workflow. Delivery therefore remains
DRAFT until the updated hosted checks pass.

## Documentation And Delivery Record

`README.md` now states that hosted tests run only on Python 3.13 and do not test
Python 3.9. All affected files, including this approved completed-work record,
will be staged together, committed with a DRAFT fix message, pushed to the
existing delivery branch, and verified before worktree detachment and safe
invoking-checkout artifact cleanup.

## Completion Classification

This is a DRAFT correction because hosted GitHub Actions is not validated in
this run. The repository's default Definition of Done is not fully satisfied
because the super-agent workflow intentionally skips independent code review and
full QA.
