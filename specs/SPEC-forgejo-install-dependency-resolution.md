# Forgejo install dependency resolution

Status: Approved

## Purpose

Ensure the published `rpi-groove-ir-emitter` wheel can be installed
anonymously from Forgejo together with its public Python dependencies.

## Requested behavior

The public installation commands must retrieve `rpi-groove-ir-emitter` from
the Forgejo package index and allow pip to retrieve dependencies unavailable
there from public PyPI. Release verification must exercise that same
dependency-resolving installation path in addition to the existing artifact
and hash checks.

## Scope

- Correct the public Forgejo installation commands in `README.md`.
- Strengthen post-publication verification in `scripts/publish_forgejo.py`.

## Out of scope

- Publishing third-party dependencies to Forgejo.
- Changing package dependencies, versions, runtime behavior, or GPIO platform
  selection.
- Changing Forgejo credentials, visibility, upload behavior, or workflow
  triggers.
- Adding or maintaining automated tests for publishing code, which the
  repository's domain-only test policy forbids.

## Inputs and constraints

- Forgejo remains the package index for `rpi-groove-ir-emitter`.
- Public PyPI is an additional index for dependencies absent from Forgejo.
- Anonymous verification must select the published project wheel, use the
  exact release version, avoid pip's cache, and install into temporary state.
- Existing anonymous simple-index artifact and SHA-256 verification remains
  intact.

## Deterministic behavior delivered

The documented stable and beta commands supply both the Forgejo package index
and public PyPI. After upload and artifact verification, the publisher installs
the exact published version into an isolated temporary target, requires a
wheel for `rpi-groove-ir-emitter`, resolves dependencies, disables pip's cache,
and runs without Forgejo credentials. Temporary install state is removed by the
existing cleanup path after success or failure.

## Assumptions

`rpi-groove-ir-emitter` is published in the configured Forgejo index, while its
third-party dependencies are available from public PyPI. The GitHub-hosted
runner can reach both indexes during release verification.

## Impact

Operators no longer lose public dependency resolution because the Forgejo-only
installation command replaced pip's default public index. A release now fails
verification when its project artifacts are readable but its declared
dependencies cannot be resolved and installed.

## Validation performed

- Compiled `scripts/publish_forgejo.py` with the local Python 3 interpreter
  without writing bytecode.
- Inspected the pip command structure and credential sanitization statically.
- Ran `git diff --check`.

## Validation skipped

- Live installation from Forgejo and public PyPI.
- Hosted GitHub Actions execution and package publication.
- Ruff because it is not installed in the local Python 3 environment and no
  project virtual environment is present.
- Automated tests, code review, and QA.

## Documentation changes

`README.md` documents the dependency index, its purpose, and the strengthened
post-publication installation check.
