# GitHub Actions Alignment

Status: Approved

## Purpose

Align this Python package's automation with the shared workspace conventions
without changing its publisher implementation or package behavior.

## Requested Behavior

- Use `.github/workflows/ci.yml` and `.github/workflows/publish.yml` with the
  common `CI` and `Publish` display names.
- Apply least-privilege permissions, immutable external-action pins,
  non-persisted checkout credentials, dependency caching, and per-workflow/per-ref
  concurrency.
- Trigger for both stable and beta tags supported by the publisher.
- Enable grouped weekly Dependabot updates for GitHub Actions.

## Scope

- GitHub Actions and Dependabot configuration.
- Existing workflow-focused regression assertions.
- README automation and credential documentation.
- Completed-work artifacts.

## Out Of Scope

- Python application, package, release-script, dependency, or runtime behavior.
- Forgejo endpoints, credential names, artifact validation, and public-index
  verification.
- Central cross-repository reusable workflows.

## Deterministic Behavior Delivered

- CI retains separate Python 3.13 lint and test jobs for `main` pull requests and
  pushes, canceling superseded runs for the same workflow/ref.
- Publication runs for supported stable and beta tags and never cancels an
  in-progress release for the same ref.
- Checkout is pinned to `v7.0.1`, setup-python to `v7.0.0`, checkout credentials
  are not persisted, and dependency caches use `requirements-dev.txt`.
- Both workflows have read-only contents permission.
- Dependabot groups GitHub Actions updates weekly.

## Assumptions And Impact

- Exact tag grammar, quality gates, artifact creation, upload, and public-index
  verification remain enforced by `scripts/publish_forgejo.py`.
- GitHub-hosted runners satisfy the Node 24 runner requirement of the selected
  action releases.

## Validation Performed

- Parsed workflows and Dependabot configuration as YAML and ran shared
  structural assertions.
- Ran `python3 -m unittest tests.test_github_workflows`: 10 tests passed.
- Ran `git diff --check`.

## Validation Skipped

- Full tests, hosted GitHub Actions, and live Forgejo publication/download were
  not run.
- Formal QA and independent review were skipped by `super-agent`.

## Documentation Changes

- Updated README beta-trigger, shared-convention, and secret guidance.
