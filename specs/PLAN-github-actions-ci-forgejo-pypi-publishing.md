# PLAN: GitHub Actions CI and public Forgejo PyPI publishing

Status: Approved

Approved spec:
`specs/SPEC-github-actions-ci-forgejo-pypi-publishing.md`

## Delivery Branch And Base

- Repository: `rpi-groove-ir-emitter`.
- Expected base branch: `main`.
- Expected base commit: `88de1ec37c291ca6e66146db7afc69bdb1722bca`.
- Delivery branch:
  `feature/github-actions-ci-forgejo-pypi-publishing`.
- The delivery branch must not exist locally, in another registered worktree, or
  on `origin` when implementation begins. A conflicting branch requires the
  implementation to stop for user direction.

## Implementation Worktree

Implementation uses an isolated linked worktree.

- Task slug: `github-actions-ci-forgejo-pypi-publishing`.
- Standard path:
  `~/.herdr/worktrees/rpi-groove-ir-emitter/github-actions-ci-forgejo-pypi-publishing`.
- The main implementation agent creates
  `~/.herdr/worktrees/rpi-groove-ir-emitter` when absent, verifies the literal
  repository directory and task slug, and creates or reuses the task worktree in
  detached-HEAD state at the expected base commit.
- If the path is registered to another repository, is dirty with unrelated
  changes, is attached to a branch, or resolves to a different commit, stop
  rather than replacing or cleaning it.
- Copy the approved spec and this approved plan from the invoking checkout into
  the isolated worktree before implementation so both accepted artifacts are
  included in delivery.
- Do not create the delivery branch before development. After the worktree has
  reached either verified DRAFT delivery or the Definition of Done, create the
  exact delivery branch there, reconcile all changes, commit, and push it to
  `origin`.
- Workers must not create, switch, delete, or otherwise manage branches or
  worktrees.

## Approved Technical Decisions

### Toolchain and lint baseline

- Add `requirements-dev.txt` with exact direct pins:
  - `build==1.5.0`
  - `ruff==0.16.0`
  - `setuptools==83.0.0`
  - `twine==6.2.0`
  - `wheel==0.47.0`
- Add `ruff.toml` with `target-version = "py39"`, generated-directory
  exclusions, and the narrow lint selection `E4`, `E7`, `E9`, and `F`.
- Use the canonical command:
  `python -m ruff check setup.py ir_emitter tests scripts`.
- The measured pre-change baseline under that exact selection contains only two
  `F841` diagnostics: unused exception aliases in `ir_emitter/IREmitter.py` and
  `ir_emitter/__main__.py`. Remove only those unused aliases; preserve the
  exception handling and user-visible messages.

### Package version and contents

- Make `ir_emitter.__version__` the single tracked version source.
- Update `setup.py` to read the literal version from
  `ir_emitter/__init__.py` without importing the package or hardware
  dependencies.
- Preserve the default tracked version `1.0.0`, distribution name, import path,
  dependency selection, and all runtime invariants.
- Add `MANIFEST.in` to include the license, README, setup metadata, and runtime
  Python package while pruning tests, specs, workflows, scripts, local caches,
  virtual environments, and development-only files from the source
  distribution.
- Build releases with
  `python -m build --no-isolation --outdir <temporary-dist-directory>` after the
  pinned toolchain is installed.

### Python publisher

- Add `scripts/publish_forgejo.py` as a standard-library orchestrator around
  Python module subprocesses and HTTPS reads.
- Use the exact tag grammar
  `^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-beta([1-9][0-9]*))?$`.
- Map a beta tag `X.Y.Z-betaN` to the PEP 440 version `X.Y.ZbN`; stable tags
  remain unchanged.
- Require `RELEASE_TAG`, `FORGEJO_PACKAGE_USERNAME`, and
  `FORGEJO_PACKAGE_TOKEN` before release work.
- Rewrite only the literal `__version__` assignment in the release checkout and
  fail unless exactly one expected assignment is replaced. Confirm `setup.py
  egg_info` resolves the same normalized version before continuing.
- Strip `TWINE_USERNAME`, `TWINE_PASSWORD`, `TWINE_REPOSITORY_URL`,
  `TWINE_NON_INTERACTIVE`, `PYPIRC_PATH`, `FORGEJO_PACKAGE_USERNAME`, and
  `FORGEJO_PACKAGE_TOKEN` from the base subprocess environment.
- Run unit tests, Ruff, metadata validation, and the no-isolation build without
  Forgejo or Twine credentials.
- Inspect the source distribution with `tarfile`, the wheel with `zipfile`, and
  the embedded package metadata with standard-library metadata parsers. Select
  the exact normalized distribution/version artifacts and reject duplicates,
  unexpected file types, missing runtime/build/docs/license content, and
  repository/development/credential content.
- Invoke Twine once with explicit source-distribution and wheel paths and the
  literal repository URL
  `https://forgejo.alexlab.nl/api/packages/public/pypi`. Supply the repository
  variable as `TWINE_USERNAME` and the secret as `TWINE_PASSWORD` only to that
  subprocess; set non-interactive mode and disable progress output.
- Do not use `--skip-existing`, retry, overwrite, delete, deprecate, or any Git
  mutation.
- Query
  `https://forgejo.alexlab.nl/api/packages/public/pypi/simple/rpi-groove-ir-emitter/`
  without credentials, parse its artifact links, download the exact expected
  source distribution and wheel, and compare their SHA-256 digests with the
  uploaded local artifacts.
- Use temporary directories outside the repository for builds, public
  verification downloads, and any transient configuration. Remove them in
  `finally` paths without hiding the original failure.

### Workflows

- Add `.github/workflows/ci.yml`:
  - triggers only for `pull_request` targeting `main` and `push` to `main`;
  - has `contents: read` permission;
  - uses `ubuntu-latest`;
  - exposes a distinct `lint` job on Python 3.13;
  - exposes a `tests` matrix for Python 3.9 and 3.13;
  - installs the exact pinned development requirements from the normal public
    Python index;
  - runs the canonical Ruff and unittest commands;
  - contains no Forgejo credential or publication reference.
- Add `.github/workflows/publish.yml`:
  - triggers only for pushed tags matching `[0-9]*.[0-9]*.[0-9]*`;
  - has `contents: read` permission and no manual, scheduled, PR, or branch
    trigger;
  - serializes `publish-forgejo-${{ github.ref }}` with
    `cancel-in-progress: false`;
  - uses one `ubuntu-latest`, Python 3.13 publication job without a matrix;
  - checks out `${{ github.ref }}`;
  - installs the pinned development requirements from the normal public Python
    index;
  - passes `github.ref_name`, `vars.FORGEJO_PACKAGE_USERNAME`, and
    `secrets.FORGEJO_PACKAGE_TOKEN` only to the publisher step.
- Pin official actions to these verified immutable commits with readable version
  comments:
  - `actions/checkout` v7.0.1:
    `3d3c42e5aac5ba805825da76410c181273ba90b1`.
  - `actions/setup-python` v6.3.0:
    `ece7cb06caefa5fff74198d8649806c4678c61a1`.

## Affected Files And Ownership Boundary

Expected in-scope files:

- `.github/workflows/ci.yml` (new)
- `.github/workflows/publish.yml` (new)
- `MANIFEST.in` (new)
- `README.md`
- `requirements-dev.txt` (new)
- `ruff.toml` (new)
- `setup.py`
- `ir_emitter/__init__.py`
- `ir_emitter/IREmitter.py`
- `ir_emitter/__main__.py`
- `scripts/publish_forgejo.py` (new)
- `tests/test_packaging_metadata.py`
- `tests/test_publish_forgejo_package.py` (new)
- `tests/test_github_workflows.py` (new)
- `specs/SPEC-github-actions-ci-forgejo-pypi-publishing.md`
- `specs/PLAN-github-actions-ci-forgejo-pypi-publishing.md`

Do not change IR playback services, controllers, DTOs, interfaces,
infrastructure adapters, JSON examples, `run.sh`, `.gitignore`, or unrelated
specs. If implementation requires another production or workflow file, stop for
a plan amendment.

## Dependency-Aware Execution Graph

Every subagent assignment is limited to at most five minutes of active work.
The main agent supervises elapsed time, interrupts a unit at five minutes,
records completed work, partial work, changed files, validation, blockers, and
remaining work, then splits any remainder before reassignment.

### Test-first units

| ID | Type | Boundary and owned files | Dependencies | Acceptance and validation | Assignment |
| --- | --- | --- | --- | --- | --- |
| T1 | Test | Version-source and packaging metadata tests; owns `tests/test_packaging_metadata.py` only. | Approved artifacts copied into worktree. | Tests fail before production changes and cover setup metadata reading `ir_emitter.__version__`, stable/beta normalized metadata fixtures, and required package identity. Run the focused unittest module. | One clean-context test-writer, max 5 minutes. |
| T2 | Test | Publisher contract tests; owns new `tests/test_publish_forgejo_package.py` only. | Approved artifacts copied into worktree. | Standard-library fixtures and stub subprocess/HTTPS boundaries cover required inputs, tag grammar, beta mapping, command order, version rewrite cardinality, artifact selection/allowlist, credential isolation, one-shot Twine upload, public hash verification, cleanup, and all failure paths. Tests fail because the publisher does not exist. | One clean-context test-writer, max 5 minutes. |
| T3 | Test | Workflow structure tests; owns new `tests/test_github_workflows.py` only. | Approved artifacts copied into worktree. | Text-based tests cover exact branch/tag triggers, action SHAs, permissions, matrices, fixed commands/endpoints, credential placement, concurrency, and prohibited insecure/mutating behavior. Tests fail because workflows do not exist. | One clean-context test-writer, max 5 minutes. |

T1, T2, and T3 may run concurrently. Maximum test-writer concurrency is 3.

### Development units

| ID | Type | Boundary and owned files | Dependencies | Acceptance and validation | Assignment |
| --- | --- | --- | --- | --- | --- |
| D0 | Development | Pinned tooling and measured lint-baseline cleanup; owns `requirements-dev.txt`, `ruff.toml`, `ir_emitter/IREmitter.py`, and `ir_emitter/__main__.py`. | Approved artifacts copied into worktree. Test-first is not applicable because changes are dependency metadata, lint configuration, and removal of unused exception aliases without behavioral change. | Exact pins/config are present; only the two aliases change in runtime files; focused Ruff check passes for owned files and existing unit tests remain green. | One clean-context developer, max 5 minutes. |
| D1 | Development | Single version source and source-distribution policy; owns `setup.py`, `ir_emitter/__init__.py`, and new `MANIFEST.in`. | T1 complete. | T1 passes; `setup.py egg_info` reports `rpi-groove-ir-emitter` and the version from `ir_emitter.__version__`; runtime dependencies and defaults are unchanged. | One clean-context developer, max 5 minutes. |
| D2 | Development | Python publisher; owns new `scripts/publish_forgejo.py`. | T2, D0, and D1 complete. | T2 passes; publisher implements the approved sequencing, artifact checks, one-shot Twine credentials, unauthenticated hash verification, and cleanup without real network or publish in tests. | One clean-context developer, max 5 minutes. |
| D3 | Development | CI workflow; owns new `.github/workflows/ci.yml`. | T3 and D0 complete. | Applicable T3 assertions pass; lint and Python 3.9/3.13 test jobs use exact pins and contain no Forgejo data. | One clean-context developer, max 5 minutes. |
| D4 | Development | Release workflow; owns new `.github/workflows/publish.yml`. | T3 and D2 complete. | Applicable T3 assertions pass; only coarse numeric tags trigger; exact tag checkout, action SHAs, single job, concurrency, and publisher-step-only variables/secret match the plan. | One clean-context developer, max 5 minutes. |
| D5 | Development | Operator and developer documentation; owns `README.md`. | D1, D2, D3, and D4 complete. Test-first is not applicable because this is documentation-only. | README states exact local commands, triggers, tag-to-PEP-440 mapping, fixed endpoints, variable/secret setup, public install examples, immutable versions, TLS/tag protection, and first-release DRAFT boundary. | One clean-context developer, max 5 minutes. |

D0 and D1 become ready independently after their own prerequisites. D3 may run
in parallel with D2 after D0 completes. D4 follows D2. D5 follows the final
interfaces. Maximum developer concurrency is 3.

### Shared-file and integration constraints

- Only D0 edits lint configuration and pinned dependencies; D2-D4 consume them
  without modification.
- Only D1 edits version metadata and package-manifest files; D2 consumes that
  contract without editing those files.
- T3 owns the single workflow test file while D3 and D4 own disjoint workflow
  files. The main agent runs the combined workflow test after both complete.
- The main agent, not a worker, copies approved artifacts, integrates completed
  units, classifies unexpected files, resolves any ownership conflict, and owns
  all staging, commit, push, and worktree/branch operations.

## Review Units

After all development units pass focused validation, run two independent
clean-context code-review agents concurrently. Reviewers do not edit files.
Maximum review concurrency is 2.

| ID | Review boundary | Acceptance | Assignment |
| --- | --- | --- | --- |
| R1 | Approved spec/plan against `setup.py`, `MANIFEST.in`, version files, publisher, publisher tests, and packaging tests. | Report spec/plan mismatches, unsafe subprocess or archive handling, credential leakage, incorrect PEP 440/artifact semantics, missing failure coverage, and runtime regressions. | One code-reviewer, max 5 minutes. |
| R2 | Approved spec/plan against both workflows, workflow tests, tool pins/lint configuration, baseline edits, and README. | Report trigger/permission/secret/action-pin errors, missing required checks, insecure TLS/mutation behavior, documentation mismatches, and untested workflow constraints. | One code-reviewer, max 5 minutes. |

Route each accepted review or QA fix to a new clean-context developer with the
specific finding and the smallest file ownership boundary. Do not let reviewers
implement fixes. Re-run the affected focused checks after each fix.

## Main-Agent QA

The main agent owns final QA after all review findings are resolved:

1. Create a temporary validation virtual environment outside the repository.
2. Install `requirements-dev.txt` from the normal public Python index and record
   exact resolved direct-tool versions.
3. Run:
   `python -m ruff check setup.py ir_emitter tests scripts`.
4. Run:
   `python -m unittest discover -s tests -p 'test_*.py'`.
5. Run focused publisher tests with only stubbed subprocess and HTTPS boundaries;
   confirm no real Forgejo mutation occurs.
6. Build with pinned tools and no isolation into a temporary directory:
   `python -m build --no-isolation --outdir <temporary-dist-directory>`.
7. Inspect the built source distribution and wheel with the publisher's
   validation path without supplying credentials or publishing.
8. Verify package metadata name/version, archive allowlists, and that
   `ir_emitter` remains importable without loading hardware adapters.
9. Run `git diff --check`.
10. Inspect the complete diff and verify no runtime invariant changed.

Do not create a real tag, run the hosted workflows, upload to Forgejo, or delete
an existing package during implementation QA. Delivery remains DRAFT until an
operator completes the first hosted tag-to-public-install round trip.

## Documentation

Update `README.md` only. Include:

- local Ruff and unittest commands;
- CI triggers and distinct required check names;
- accepted `X.Y.Z` and `X.Y.Z-betaN` tags and rejection of leading `v`;
- the `X.Y.Z-betaN` to `X.Y.ZbN` Python version mapping;
- public Forgejo publish/simple-index endpoints;
- `FORGEJO_PACKAGE_USERNAME` GitHub repository variable;
- `FORGEJO_PACKAGE_TOKEN` secret, public-only `write:package` scope, and
  `public` organization access;
- credential-free stable and beta install commands using `--index-url`;
- immutable duplicate-version behavior, normal TLS verification, trusted tag
  creation, and first-release DRAFT limitations.

## Commit And Push

- After QA reaches verified DRAFT delivery, reconcile `git status --short`,
  classify every modified, added, deleted, renamed, and untracked path, and
  preserve unrelated user changes.
- Stage every accepted in-scope file, including the approved spec and plan.
- Inspect `git diff --cached --check`, the staged path list, and the full staged
  diff before committing.
- Create the exact delivery branch from the detached worktree.
- Because hosted GitHub Actions and a live Forgejo publish/install round trip are
  intentionally unvalidated, use commit message:
  `feature: DRAFT add GitHub CI and Forgejo PyPI publishing`.
- Push the branch to `origin` and configure its upstream.
- Verify the local branch is not ahead of its upstream and that no accepted
  in-scope change remains unstaged or uncommitted. Report any unrelated path in
  both the implementation worktree and invoking checkout.

## No-Research Constraint

Implementation must not perform product, architecture, scope, or plan research.
It may inspect only applicable instructions, the approved spec and plan, the
files listed in this plan, minimal local patterns required by an owned file, and
validation output needed to execute the approved units. If an approved technical
decision proves incorrect, ambiguous, unavailable, or materially different,
stop for a spec or plan amendment instead of choosing new behavior.

## Completion Classification

Final delivery is DRAFT unless all deterministic implementation checks pass and
the operator later confirms:

- a real accepted tag triggers the hosted release workflow;
- lint and tests pass on GitHub-hosted runners;
- Twine authenticates and publishes both artifacts to the fixed Forgejo owner;
- the public simple index exposes both exact artifacts without credentials;
- stable or beta installation succeeds from the public index.

The implementation completion report must state review findings and resolutions,
validation run and skipped, documentation changes, commit/push status, remaining
runtime risks, Definition-of-Done gaps, and final main-agent acceptance.
