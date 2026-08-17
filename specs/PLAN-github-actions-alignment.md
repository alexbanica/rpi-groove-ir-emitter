# GitHub Actions Alignment Implementation Plan

Status: Approved

## Specification

- `specs/SPEC-github-actions-alignment.md`

## Affected Files

- `.github/dependabot.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/publish.yml`
- `README.md`
- `tests/test_github_workflows.py`
- `specs/SPEC-github-actions-alignment.md`
- `specs/PLAN-github-actions-alignment.md`

## Implementation Performed

1. Standardized workflow names, concurrency, immutable pins, checkout handling,
   pip caching, step names, and formatting.
2. Added the missing beta-tag trigger already accepted by the publisher.
3. Updated focused workflow assertions and README guidance.
4. Added grouped weekly Dependabot updates.
5. Added this completed-work spec and plan.

## Validation Run

- YAML parsing and shared structural assertions.
- `python3 -m unittest tests.test_github_workflows`: 10 passed.
- `git diff --check`.

## Validation Skipped

- Full tests, hosted Actions, and live Forgejo publication/download were skipped
  because they exceed the `super-agent` validation boundary or require external
  runtime state.

## Review And QA

- Formal QA and independent review were skipped as required by `super-agent`.

## Documentation

- README and completed-work artifacts document the delivered conventions.

## Delivery State

- All accepted files are staged after final reconciliation, committed together,
  and pushed to `origin/main` as explicitly requested.
- No linked worktree or artifact cleanup applies.

## Residual Risk

- Hosted execution and live Forgejo behavior remain unverified.
