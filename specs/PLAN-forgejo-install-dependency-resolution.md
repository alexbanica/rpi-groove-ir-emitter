# Forgejo install dependency resolution plan

Status: Approved

## Spec reference

`specs/SPEC-forgejo-install-dependency-resolution.md`

## Affected files

- `README.md`
- `scripts/publish_forgejo.py`
- `specs/SPEC-forgejo-install-dependency-resolution.md`
- `specs/PLAN-forgejo-install-dependency-resolution.md`

## Implementation performed

1. Added public PyPI to the documented stable and beta installation commands
   while retaining Forgejo as the project package index.
2. Explained the separation between the Forgejo-hosted project and its public
   dependencies.
3. Kept the publisher's existing anonymous artifact and SHA-256 verification.
4. Added an exact-version installation into a temporary target after upload,
   requiring a project wheel, disabling pip's cache, resolving dependencies
   through public PyPI, and using a sanitized credential-free environment.
5. Included temporary install state in the existing cleanup lifecycle.
6. Recorded the delivered behavior in this approved spec and plan.

## Validation run

- Bytecode-free Python compilation for `scripts/publish_forgejo.py`.
- Static inspection of the modified pip command and environment handling.
- `git diff --check`.

## Validation skipped

- Live Forgejo/PyPI installation, hosted Actions, and publication.
- Ruff because it is unavailable in the local Python 3 environment and no
  project virtual environment is present.
- Automated tests because publishing code and documentation are outside the
  repository's deterministic domain-source test boundary.

## QA and code review

QA and code review were skipped as required by `$super-agent`.

## Documentation updates

The README public installation examples, dependency-index explanation, and
publication verification description were updated.

## Staging and delivery status

All accepted in-scope paths are staged, committed on `main`, and pushed to
`origin/main` as explicitly requested for this invocation.

## Residual risk

Live index availability, platform dependency compatibility, and hosted release
behavior remain unverified until the corrected installation path runs against
Forgejo and public PyPI.
