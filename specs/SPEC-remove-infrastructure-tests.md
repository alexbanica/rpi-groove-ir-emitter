# Remove infrastructure tests

Status: Approved

## Purpose

Remove the repository's remaining automated tests outside deterministic domain
source logic so the tracked test suite conforms to the domain-only test policy.

## Requested behavior

Delete all tracked automated tests for packaging, release publishing, and the
repository launcher. Do not change production code, workflows, packaging
behavior, or domain behavior.

## Scope

- Remove `tests/test_packaging_metadata.py`.
- Remove `tests/test_publish_forgejo_package.py`.
- Remove `tests/test_run_sh_venv_bootstrap.py`.
- Record the delivered removal in approved completed-work artifacts.

## Out of scope

- Adding replacement tests.
- Removing or changing future deterministic domain-source tests.
- Changing CI or publisher quality-gate commands.
- Changing packaging, release, launcher, runtime, or domain behavior.
- Retagging or rerunning release `1.0.1`.

## Definitions

For this change, infrastructure tests are automated tests for packaging
metadata, Forgejo publication tooling, and launcher/virtual-environment
orchestration. These are outside the repository's deterministic domain-source
test boundary.

## Inputs and constraints

- The root `AGENTS.md` domain-only test policy is authoritative.
- Preserve production code and unrelated user changes.
- Use the invoking checkout without a linked worktree.
- Stage the complete accepted change set but do not commit or push without
  explicit authorization.

## Deterministic behavior delivered

The three tracked non-domain test files are deleted. No tracked test file
remains under `tests/`; future deterministic domain tests may still use that
directory and the existing discovery command.

## Assumptions and impact

The deleted tests are the complete tracked infrastructure-test set because
`git ls-files tests` listed only those three paths before deletion. The
publisher's existing unittest discovery command now completes without running
these prohibited tests, including the packaging fixture that failed after the
release version was rewritten to `1.0.1`.

## Validation performed

- Inspected the tracked test inventory before deletion.
- Verified no tracked test path remains under `tests/` after deletion.
- Ran `git diff --check` over the complete change.
- Inspected the staged path list and staged diff.

## Validation skipped

- Automated tests because this change removes non-domain tests and the policy
  prohibits maintaining replacements for them.
- Hosted GitHub Actions and release publication.
- QA and independent code review, as required by `$super-agent`.

## Documentation changes

This approved completed-work spec and its matching plan document the removal.
No operator or product documentation changes are required.
