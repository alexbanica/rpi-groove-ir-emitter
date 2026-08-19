# Remove infrastructure tests

Status: Approved

## Purpose

Remove the repository's remaining automated tests outside deterministic domain
source logic so the tracked test suite conforms to the domain-only test policy.

## Requested behavior

Delete all tracked automated tests for packaging, release publishing, and the
repository launcher. Remove their stale CI and publisher consumers so active
quality gates do not reference an absent `tests/` directory. Do not change
packaging, release, launcher, runtime, or domain behavior.

## Scope

- Remove `tests/test_packaging_metadata.py`.
- Remove `tests/test_publish_forgejo_package.py`.
- Remove `tests/test_run_sh_venv_bootstrap.py`.
- Remove the CI test job and the deleted test path from CI linting.
- Remove unittest discovery and the deleted test path from publisher linting.
- Align README CI and release-quality documentation.
- Record the delivered removal in approved completed-work artifacts.

## Out of scope

- Adding replacement tests.
- Removing or changing future deterministic domain-source tests.
- Changing packaging, release, launcher, runtime, or domain behavior.
- Retagging or rerunning release `1.0.1`.

## Definitions

For this change, infrastructure tests are automated tests for packaging
metadata, Forgejo publication tooling, and launcher/virtual-environment
orchestration. These are outside the repository's deterministic domain-source
test boundary.

## Inputs and constraints

- The root `AGENTS.md` domain-only test policy is authoritative.
- This spec's no-test CI and publisher behavior supersedes test-related
  requirements in `SPEC-github-actions-ci-forgejo-pypi-publishing.md` while no
  tracked deterministic domain tests exist.
- Preserve production code and unrelated user changes.
- Use the invoking checkout without a linked worktree.
- Stage the complete accepted change set but do not commit or push without
  explicit authorization.

## Deterministic behavior delivered

The three tracked non-domain test files are deleted, and no tracked test file
remains under `tests/`. CI now has only its Python 3.13 lint job and lints only
existing source/tooling paths. The release publisher runs the same lint target
without invoking unittest discovery. Future deterministic domain tests may use
`tests/`, but adding them requires an explicit CI and publisher-gate decision.

## Assumptions and impact

The deleted tests are the complete tracked infrastructure-test set because
`git ls-files tests` listed only those three paths before deletion. Removing
their consumers resolves CI run `32260694514`, where Ruff and unittest failed
because `tests/` did not exist, and publish run `32260782997`, where the
publisher's unittest quality gate failed before build or upload.

## Validation performed

- Inspected the tracked test inventory before deletion.
- Verified no tracked test path remains under `tests/` after deletion.
- Parsed `.github/workflows/ci.yml` as YAML.
- Compiled `scripts/publish_forgejo.py` with the local Python 3 interpreter
  without writing bytecode.
- Verified active CI, publisher, and README commands contain no stale test
  directory or unittest-discovery reference.
- Ran `git diff --check` over the complete change.
- Inspected the staged path list and staged diff.

## Validation skipped

- Automated tests because this change removes non-domain tests and the policy
  prohibits maintaining replacements for them.
- Hosted GitHub Actions and release publication.
- Ruff because it is unavailable in the local Python 3 environment and no
  project virtual environment is present.
- QA and independent code review, as required by `$super-agent`.

## Documentation changes

This approved completed-work spec and its matching plan document the removal.
README now documents the lint-only CI and publisher quality gate.
