# SPEC: GitHub Actions CI and public Forgejo PyPI publishing

Status: Approved

## Iteration: Python 3.13-only hosted CI (2026-08-17)

The initial approved contract added a Python 3.9 and 3.13 test matrix. The
implemented workflow installs the complete pinned release toolchain in every
test job, but `build==1.5.0` requires Python 3.10 or newer. The Python 3.9 job
therefore fails during dependency installation before unit tests run.

This iteration removes Python 3.9 from GitHub Actions and makes the hosted test
job Python 3.13-only. It preserves the separate lint and test outcomes, pinned
release tooling, release workflow, runtime behavior, and the existing package
metadata declaration `python_requires='>=3.9'`. Hosted CI no longer claims or
validates Python 3.9 compatibility.

## Purpose

Add deterministic GitHub Actions quality gates for contributions and `main`,
and publish tagged Python package releases to the public Forgejo PyPI registry.

## Problem Statement

The repository has no GitHub Actions workflows, no defined Python lint command,
and no automated package release path. Pull requests and changes merged to
`main` therefore have no hosted lint or unit-test gate. Pushing a release tag
does not build, validate, publish, or verify the `rpi-groove-ir-emitter` Python
package.

The related `homebridge-simple-ir-fan` repository already provides a hardened
Forgejo npm release model: a tag-only workflow passes an exact tag and one
package token to a tested publisher; the publisher validates the tag, aligns
the package version, runs quality gates, inspects the packed payload, publishes
once, verifies the public package, and cleans temporary release state. This
project needs the same release guarantees expressed through Python packaging
tools and Python version semantics rather than npm behavior.

## Scope

- Add GitHub Actions CI for pull requests targeting `main` and pushes to
  `main`.
- Define and run deterministic Python lint and unit-test gates.
- Add a separate GitHub Actions workflow for pushed numeric release tags.
- Add a tested Python release publisher for the public Forgejo PyPI registry.
- Derive release package metadata from the accepted Git tag in the release
  checkout.
- Build and inspect one source distribution and one pure-Python wheel.
- Publish validated artifacts with Twine using narrowly scoped Forgejo
  credentials.
- Verify the published package through the unauthenticated public Forgejo PyPI
  index.
- Document CI, release tags, credentials, package installation, and remaining
  operator-owned validation.

## Out Of Scope

- Creating, moving, deleting, or force-updating Git tags.
- Creating or changing the Forgejo `public` organization, its membership, or
  its visibility.
- Creating the Forgejo access token or configuring GitHub repository variables,
  secrets, rulesets, or branch protection through automation.
- Publishing to pypi.org or any registry other than the literal public Forgejo
  PyPI owner endpoint.
- Publishing containers, npm packages, or generic artifacts.
- Deleting, overwriting, replacing, or deprecating an existing Forgejo package
  version.
- Adding npm concepts such as scopes, dist-tags, `package-lock.json`, `.npmrc`,
  or npm tarball naming.
- Changing IR emission, GPIO, CLI, JSON, launcher, or runtime dependency
  behavior.
- Changing the package's existing `python_requires='>=3.9'` metadata; this
  iteration changes hosted CI coverage only.
- Creating the first real tag or performing the first live publication during
  implementation.

## Definitions

- **Stable tag:** `MAJOR.MINOR.PATCH`, where each component is zero or a
  positive integer without leading zeroes.
- **Beta tag:** `MAJOR.MINOR.PATCH-betaN`, where `N` is a positive integer
  without leading zeroes, beginning with `beta1`.
- **Coarse tag filter:** the GitHub Actions push filter
  `[0-9]*.[0-9]*.[0-9]*`; it selects numeric-looking tags, while the publisher
  owns exact validation.
- **Release tag:** the unchanged `github.ref_name` supplied to the publisher as
  `RELEASE_TAG`.
- **Python release version:** the PEP 440 canonical package version derived from
  a valid release tag. A stable tag remains `MAJOR.MINOR.PATCH`; a beta tag
  `MAJOR.MINOR.PATCH-betaN` becomes `MAJOR.MINOR.PATCHbN` in Python package
  metadata and artifact filenames.
- **Public Forgejo PyPI publish endpoint:**
  `https://forgejo.alexlab.nl/api/packages/public/pypi`.
- **Public Forgejo PyPI simple index:**
  `https://forgejo.alexlab.nl/api/packages/public/pypi/simple`.
- **Package identity:** the Python distribution `rpi-groove-ir-emitter` and
  import package `ir_emitter`.

## Inputs And Constraints

- The integration branch is the existing `main` branch; no `master` branch is
  introduced.
- Pull-request CI runs only for pull requests whose base branch is `main`.
- Merge CI is represented by the resulting push to `main`.
- Both hosted CI outcomes run on Python 3.13. The test job is a single job and
  does not use a Python-version matrix.
- Exact tag validation accepts only the stable and beta forms above.
- Leading `v`, whitespace, leading-zero components, `beta0`, dotted
  prereleases, arbitrary suffixes, and build metadata are rejected before any
  build or registry operation.
- The repository's documented unit-test command remains:
  `python -m unittest discover -s tests -p 'test_*.py'`.
- Ruff is the canonical Python linter and treats every diagnostic as a CI
  failure. It covers tracked Python production code, tests, packaging code, and
  release scripts while excluding generated build output and virtual
  environments.
- Python release tooling uses module invocation through the selected Python
  interpreter. Python dependencies are installed from the normal public Python
  package source without Forgejo credentials.
- The Forgejo owner is the literal public organization `public`; it is not
  supplied by tags, pull requests, or mutable workflow input.
- `FORGEJO_PACKAGE_USERNAME` is a non-secret GitHub repository variable naming
  the Forgejo account used by Twine.
- `FORGEJO_PACKAGE_TOKEN` is the only GitHub repository secret used for release
  publication. It belongs to the named account, has `write:package`, is limited
  to public resources, and that account has package write access in the
  Forgejo `public` organization.
- GitHub workflow permissions are read-only for repository contents. The
  external Forgejo credential, not `GITHUB_TOKEN`, authorizes publication.
- Standard public TLS and hostname verification remain enabled. No custom CA,
  insecure URL, disabled verification, or equivalent bypass is permitted.
- Third-party GitHub Actions must be pinned immutably; mutable pull-request
  content cannot select action versions, registry endpoints, owners, commands,
  or credentials.

## Deterministic Behavior

### Pull-request and main-branch CI

1. A pull request targeting `main` starts CI.
2. A push to `main`, including the push produced by merging a pull request,
   starts CI.
3. CI checks out the triggering revision with read-only contents permission.
4. The lint gate installs the declared lint tooling and runs the canonical Ruff
   check. Any diagnostic or tool failure fails the gate.
5. The test gate runs once on Python 3.13 and executes the repository unit-test
   command. Any failed test, test discovery error, dependency installation
   error, or command failure fails the gate.
6. Lint and tests are visible as distinct required outcomes so branch
   protection can require both checks.
7. CI never receives, references, or exposes Forgejo publication credentials.

### Release trigger and validation

1. A pushed tag matching the coarse numeric tag filter starts the release
   workflow.
2. Pull requests, branch pushes, schedules, and manual dispatch do not start the
   release workflow.
3. The release job is a single publication attempt for the pushed tag; it does
   not use a matrix and concurrent runs for the same tag are serialized without
   cancelling an in-progress publication.
4. The workflow checks out the exact pushed tag and passes its unchanged name as
   `RELEASE_TAG` only to the publisher step.
5. The publisher requires `RELEASE_TAG`, `FORGEJO_PACKAGE_USERNAME`, and
   `FORGEJO_PACKAGE_TOKEN` before release work begins.
6. The publisher performs exact tag validation before changing package metadata,
   building artifacts, contacting Forgejo, or invoking Twine.
7. A stable tag maps to the identical Python release version. A beta tag maps to
   the canonical PEP 440 beta version defined above.

### Quality gates and release metadata

1. The publisher runs the same canonical unit-test and Ruff lint gates required
   by CI before building or publishing.
2. The publisher aligns both distribution metadata and
   `ir_emitter.__version__` to the derived Python release version in the release
   checkout.
3. Release-time metadata changes are never committed, tagged, or pushed by the
   workflow or publisher.
4. Any tag, lint, test, metadata, build, inspection, authentication, publication,
   or verification failure stops the release and returns a non-zero result.

### Build and artifact integrity

1. The publisher builds exactly one source distribution and one pure-Python
   wheel for `rpi-groove-ir-emitter` using the derived Python release version.
2. Before publication, the publisher validates machine-readable artifact
   metadata and archive contents rather than selecting files through an
   unrestricted wildcard.
3. Exactly one source distribution and one wheel must match the expected
   normalized distribution name and Python release version.
4. Both artifacts must contain the `ir_emitter` runtime package and appropriate
   Python packaging metadata. The source distribution must also contain the
   required build metadata, README, and license.
5. Release credentials, CI files, repository metadata, local virtual
   environments, caches, generated bytecode, and unrelated development files
   must not be present in published artifacts.
6. Unexpected, missing, duplicate, malformed, or mismatched artifact content
   fails before Twine is invoked.

### Authentication and publication

1. The Forgejo username and token are exposed only to the Twine upload
   subprocess. Lint, tests, dependency installation, build, artifact inspection,
   and public verification run with known Twine and Forgejo credential variables
   removed.
2. Twine uploads only the two explicitly validated artifact paths to the fixed
   public Forgejo PyPI publish endpoint.
3. The publisher performs one upload attempt and propagates registry failures.
   It does not retry, skip an existing version, delete a version, or request an
   overwrite.
4. Publishing an already existing package name and version fails closed and
   leaves the existing Forgejo package unchanged.
5. The workflow and publisher never run Git commit, tag, push, or force-update
   commands.

### Public post-publish verification and cleanup

1. After Twine succeeds, the publisher removes Forgejo credentials and queries
   the public simple index without authentication.
2. Verification proves that the expected distribution and canonical Python
   release version are anonymously readable and that the expected wheel and
   source distribution can be resolved from the fixed public index.
3. Missing, private-only, malformed, wrong-name, wrong-version, or unexpected
   artifact results fail the release even when upload returned success.
4. Temporary authentication configuration, downloaded verification files, and
   locally built artifacts are removed after success and after failure.
5. Cleanup is best-effort and must not replace or hide the original release
   failure.

## Assumptions

- `betaN` means a positive beta sequence number and maps intentionally to
  Python's canonical `bN` spelling.
- The Forgejo `public` organization exists, is publicly visible, and permits
  anonymous package reads.
- The configured Forgejo account is a member of `public` with sufficient
  package-write access.
- GitHub-hosted runners can resolve and reach `forgejo.alexlab.nl` over HTTPS
  with normal public trust roots.
- Repository branch protection will be configured by an operator to require
  the distinct lint and test outcomes; workflow files alone cannot enforce the
  repository setting.
- The first real tag, hosted workflow run, Forgejo upload, anonymous download,
  and package installation remain operator-owned runtime validation.

## Impact And Regression Considerations

- CI adds mandatory quality feedback but does not change runtime code behavior.
- Hosted CI validates Python 3.13 only. The unchanged `python_requires='>=3.9'`
  metadata is not a claim that Python 3.9 remains covered by GitHub Actions.
- Release builds temporarily override the tracked `1.0.0` metadata with the tag
  version; incorrect alignment could publish misleading package metadata, so
  both distribution and import-package versions require deterministic tests.
- Python normalizes beta tag spelling from `-betaN` to `bN`; documentation and
  verification must not claim the npm-style tag is the literal PyPI version.
- Publishing is irreversible through this workflow. A mistaken valid tag can
  create an immutable public package version, so tag protection is an operator
  requirement.
- Pull requests from forks are untrusted and must never gain access to Forgejo
  credentials.
- Package build changes must preserve the existing distribution name, import
  path, Python requirement, runtime dependency selection, CLI defaults, JSON
  compatibility, playback semantics, and pigpio failure exit status.

## Validation Plan

- Run the full repository unit suite:
  `python3 -m unittest discover -s tests -p 'test_*.py'`.
- Run the canonical Ruff lint command against production, test, packaging, and
  release Python files.
- Add deterministic publisher tests using temporary fixtures and stubbed
  subprocess/network boundaries. Cover stable and beta tags, malformed tags,
  PEP 440 normalization, metadata alignment, gate ordering, explicit artifact
  selection, artifact allowlisting, credential isolation, immutable duplicate
  failure, public verification, cleanup, and failure propagation.
- Add structural workflow tests for branch/tag triggers, read-only permissions,
  exact tag checkout, Python 3.13-only lint and test jobs, absence of Python 3.9
  and a test matrix, no publish matrix, serialized same-tag runs, credential
  placement, fixed endpoints, and prohibited insecure or mutating behavior.
- Build a source distribution and wheel locally without publishing and inspect
  their metadata and contents.
- Run `git diff --check`.
- Treat delivery as DRAFT until an operator creates an accepted tag and confirms
  the hosted workflow, authenticated Forgejo upload, anonymous exact-version
  download, and clean installation from the public index.

## Super-agent Delivery Record (2026-08-17)

- Delivered the Python 3.13-only hosted CI behavior described by this iteration.
- Validation performed: focused workflow structural tests, the repository unit
  suite, and `git diff --check`.
- Validation skipped: hosted GitHub Actions execution and all live Forgejo
  publication checks.
- QA and independent code review were skipped by the requested `super-agent`
  workflow.
- Documentation was updated to state that hosted CI does not test Python 3.9.

## Documentation Requirements

- Document the `main` pull-request and push quality gates and the exact local
  lint/test commands.
- Document that both hosted quality outcomes use Python 3.13 and that hosted CI
  does not test Python 3.9.
- Document accepted stable and beta tag forms and rejected leading-`v` tags.
- Explain the Python-specific beta mapping from `X.Y.Z-betaN` tags to
  `X.Y.ZbN` package versions.
- Document the fixed public Forgejo publish and simple-index URLs.
- Document the non-secret `FORGEJO_PACKAGE_USERNAME` repository variable and
  secret `FORGEJO_PACKAGE_TOKEN`, including public-only `write:package` access
  and `public` organization membership.
- Provide stable and beta package installation examples that use the public
  Forgejo simple index without embedding credentials.
- Document immutable duplicate-version failure, normal TLS requirements, tag
  protection, and the operator-owned first release round trip.
