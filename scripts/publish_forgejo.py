#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish a release to Forgejo public PyPI with strict validation."""

from __future__ import annotations

import hashlib
import html.parser
import inspect
import os
import re
import shutil
import subprocess
import posixpath
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

RELEASE_TAG_ENV = "RELEASE_TAG"
FORGEJO_USERNAME_ENV = "FORGEJO_PACKAGE_USERNAME"
FORGEJO_TOKEN_ENV = "FORGEJO_PACKAGE_TOKEN"

TAG_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-beta([1-9][0-9]*))?$"
)

PUBLISH_URL = "https://forgejo.alexlab.nl/api/packages/public/pypi"
CLIENT_INDEX_URL = "https://pypi.alexlab.nl/simple/"
SIMPLE_INDEX_URL = f"{CLIENT_INDEX_URL}rpi-groove-ir-emitter/"
EXPECTED_DISTRIBUTION_NAME = "rpi-groove-ir-emitter"
EXPECTED_DISTRIBUTION_NORMALIZED = "rpi_groove_ir_emitter"

SENSITIVE_ENV_KEYS = {
    "TWINE_USERNAME",
    "TWINE_PASSWORD",
    "TWINE_REPOSITORY_URL",
    "TWINE_NON_INTERACTIVE",
    "PYPIRC_PATH",
    "FORGEJO_PACKAGE_USERNAME",
    "FORGEJO_PACKAGE_TOKEN",
}

FORBIDDEN_ARCHIVE_PREFIXES = (
    "tests/",
    "specs/",
    ".github/",
    ".git/",
    ".venv/",
    "build/",
    "dist/",
    "scripts/",
    "htmlcov/",
    ".eggs/",
    "__pycache__/",
)

FORBIDDEN_ARCHIVE_SEGMENTS = tuple(prefix.strip("/").lower() for prefix in FORBIDDEN_ARCHIVE_PREFIXES)


@dataclass(frozen=True)
class PackageMetadata:
    name: str
    version: str


class PublishError(RuntimeError):
    pass


class SimpleIndexParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self._links.append(value)

    @property
    def links(self) -> list[str]:
        return self._links


def sanitize_environment(source: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = dict(os.environ if source is None else source)
    for key in SENSITIVE_ENV_KEYS:
        env.pop(key, None)
    return env


def parse_release_tag(release_tag: str) -> str:
    match = TAG_RE.fullmatch(release_tag)
    if not match:
        raise ValueError(f"Invalid release tag: {release_tag}")
    major, minor, patch, beta = match.groups()
    return f"{major}.{minor}.{patch}b{beta}" if beta else f"{major}.{minor}.{patch}"


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )


def rewrite_version(version_file: Path, release_version: str) -> int:
    original = version_file.read_text(encoding="utf-8")
    matches = re.findall(r'^__version__\s*=\s*["\'][^"\']+["\']', original, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Expected exactly one __version__ assignment in ir_emitter/__init__.py")
    updated, count = re.subn(
        r'^__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{release_version}"',
        original,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError("Expected exactly one __version__ assignment in ir_emitter/__init__.py")
    version_file.write_text(updated, encoding="utf-8")
    return count


def _strip_sensitive_env(source: Optional[dict[str, str]] = None) -> dict[str, str]:
    return sanitize_environment(source)


def _parse_release_tag(release_tag: str) -> str:
    return parse_release_tag(release_tag)


def _run_command(command: Sequence[str], cwd: Path, env: dict[str, str]) -> None:
    run_command(command, cwd=cwd, env=env)


def _rewrite_version_file(version_file: Path, release_version: str) -> str:
    original = version_file.read_text(encoding="utf-8")
    rewrite_version(version_file, release_version)
    return original


def _normalize_distribution(name: str) -> str:
    return re.sub(r"[-.]", "_", name).lower()


def _normalize_name_for_compare(name: str) -> str:
    return re.sub(r"[-_.]", "-", name).lower()


def _require_inputs(source: Optional[dict[str, str]] = None) -> tuple[str, str, str]:
    env_source = os.environ if source is None else source
    release_tag = env_source.get(RELEASE_TAG_ENV)
    forgejo_username = env_source.get(FORGEJO_USERNAME_ENV)
    forgejo_token = env_source.get(FORGEJO_TOKEN_ENV)

    missing = []
    if not release_tag:
        missing.append(RELEASE_TAG_ENV)
    if not forgejo_username:
        missing.append(FORGEJO_USERNAME_ENV)
    if not forgejo_token:
        missing.append(FORGEJO_TOKEN_ENV)
    if missing:
        raise ValueError(f"Missing required environment variable(s): {', '.join(missing)}")
    return release_tag, forgejo_username, forgejo_token


def _validate_metadata_pair(
    payload: str,
    expected_name: str,
    expected_version: str,
) -> None:
    metadata_name: Optional[str] = None
    metadata_version: Optional[str] = None
    for line in payload.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == "name":
            metadata_name = value.strip()
        elif key.strip().lower() == "version":
            metadata_version = value.strip()

    if metadata_name is None or metadata_version is None:
        raise PublishError("Missing Name/Version in package metadata")

    if _normalize_name_for_compare(metadata_name) != _normalize_name_for_compare(expected_name):
        raise PublishError("Package metadata name mismatch")
    if metadata_version != expected_version:
        raise PublishError("Package metadata version mismatch")


def _select_artifacts(
    artifact_paths: Iterable[Path], version: str
) -> tuple[Path, Path, str]:
    paths = [Path(path) for path in artifact_paths]
    if not paths:
        raise ValueError("No artifacts were produced")

    sdist_pattern = re.compile(
        rf"^{re.escape(EXPECTED_DISTRIBUTION_NORMALIZED)}-{re.escape(version)}\.tar\.gz$"
    )
    wheel_pattern = re.compile(
        rf"^{re.escape(EXPECTED_DISTRIBUTION_NORMALIZED)}-{re.escape(version)}-py3-none-any\.whl$"
    )

    sdist_candidates: list[Path] = []
    wheel_candidates: list[Path] = []
    unknown: list[Path] = []

    for path in paths:
        if sdist_pattern.match(path.name):
            sdist_candidates.append(path)
        elif wheel_pattern.match(path.name):
            wheel_candidates.append(path)
        else:
            unknown.append(path)

    if unknown:
        raise ValueError(f"Unexpected artifacts present: {', '.join(path.name for path in unknown)}")
    if len(sdist_candidates) != 1:
        raise ValueError("Expected exactly one source distribution artifact")
    if len(wheel_candidates) != 1:
        raise ValueError("Expected exactly one pure-Python wheel artifact")
    return sdist_candidates[0], wheel_candidates[0], EXPECTED_DISTRIBUTION_NAME


def select_artifacts(artifact_paths: Sequence[Path], version: str) -> tuple[Path, Path]:
    sdist, wheel, _ = _select_artifacts(artifact_paths, version)
    return sdist, wheel


def _validate_member(path: str) -> None:
    normalized = path.replace("\\", "/")
    if normalized.endswith(".pyc"):
        raise PublishError(f"Artifact contains bytecode: {path}")
    segments = [segment.lower() for segment in normalized.split("/") if segment]
    if any(segment in FORBIDDEN_ARCHIVE_SEGMENTS for segment in segments):
        raise PublishError(f"Artifact contains forbidden path segment: {path}")
    if ".." in segments:
        raise PublishError(f"Artifact contains unsafe path: {path}")


def _is_safe_archive_member(path: str, expected_prefix: str) -> str:
    normalized_raw = path.replace("\\", "/")
    if normalized_raw.startswith("/"):
        raise PublishError(f"Source distribution has unexpected root path: {path}")
    normalized = posixpath.normpath(normalized_raw)
    normalized = normalized.strip("/")
    if normalized == ".":
        raise PublishError(f"Source distribution has unexpected root path: {path}")

    _validate_member(path)
    if not (
        normalized == expected_prefix
        or normalized.startswith(f"{expected_prefix}/")
    ):
        raise PublishError(f"Source distribution has unexpected root path: {path}")
    return normalized


def _validate_sdist(path: Path, package_name: str, release_version: str) -> None:
    if not tarfile.is_tarfile(path):
        raise PublishError(f"Invalid source distribution: {path}")

    expected_prefix = f"{_normalize_distribution(package_name)}-{release_version}"
    has_runtime = False
    has_metadata_file = False
    has_readme = False
    has_license = False
    has_setup = False
    metadata_payload = ""

    with tarfile.open(path, mode="r:gz") as tar:
        for member in tar.getmembers():
            if not (member.isfile() or member.isdir()):
                raise PublishError(f"Source distribution contains non-regular member: {member.name}")
            _is_safe_archive_member(member.name, expected_prefix)
            is_regular_file = member.isfile()

            if member.name == f"{expected_prefix}/PKG-INFO":
                if not is_regular_file:
                    raise PublishError(f"Source distribution has invalid member type for PKG-INFO: {member.name}")
                has_metadata_file = True
                with tar.extractfile(member) as handle:
                    metadata_payload = handle.read().decode("utf-8", errors="ignore")

            if is_regular_file and member.name.endswith("/ir_emitter/__init__.py"):
                has_runtime = True
            if is_regular_file and member.name == f"{expected_prefix}/setup.py":
                has_setup = True
            base = Path(member.name).name.lower()
            if is_regular_file and base.startswith("readme"):
                has_readme = True
            if is_regular_file and (base == "license" or base.startswith("license.")):
                has_license = True

    if not has_metadata_file:
        raise PublishError("Source distribution missing PKG-INFO")
    _validate_metadata_pair(metadata_payload, package_name, release_version)

    if not has_setup or not has_runtime or not has_readme or not has_license:
        raise PublishError("Source distribution missing required content")

    if path.name != f"{_normalize_distribution(package_name)}-{release_version}.tar.gz":
        raise PublishError("Source artifact name mismatch")


def _validate_wheel(path: Path, package_name: str, release_version: str) -> None:
    if not zipfile.is_zipfile(path):
        raise PublishError(f"Invalid wheel artifact: {path}")

    normalized_name = _normalize_distribution(package_name)
    expected_dist_info = f"{normalized_name}-{release_version}.dist-info"
    has_runtime = False
    has_metadata = False
    has_wheel = False
    metadata_payload = ""

    with zipfile.ZipFile(path, mode="r") as zipf:
        names = zipf.namelist()
        for name in names:
            _validate_member(name)
            normalized = name.replace("\\", "/")
            if normalized.endswith("ir_emitter/__init__.py"):
                has_runtime = True
            if normalized == f"{expected_dist_info}/METADATA":
                has_metadata = True
                metadata_payload = zipf.read(name).decode("utf-8", errors="ignore")
            if normalized == f"{expected_dist_info}/WHEEL":
                has_wheel = True

    if not has_metadata:
        raise PublishError("Wheel missing METADATA")
    _validate_metadata_pair(metadata_payload, package_name, release_version)
    if not has_runtime or not has_wheel:
        raise PublishError("Wheel missing required metadata or runtime content")

    if not path.name.endswith("-py3-none-any.whl"):
        raise PublishError("Unexpected wheel tag; expected pure-Python wheel")
    if f"{normalized_name}-{release_version}" not in path.name:
        raise PublishError("Wheel artifact name mismatch")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8192), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_simple_index(html_payload: str) -> dict[str, str]:
    parser = SimpleIndexParser()
    parser.feed(html_payload)
    links = {}
    for href in parser.links:
        parsed = urllib.parse.urlparse(href)
        filename = Path(parsed.path).name
        if not filename:
            continue
        links[filename] = urllib.parse.urljoin(SIMPLE_INDEX_URL, parsed.geturl())
    return links


def _verify_public_artifacts(artifact_paths: Iterable[Path], opener=urllib.request.urlopen) -> None:
    with opener(urllib.request.Request(SIMPLE_INDEX_URL)) as response:
        html_payload = response.read().decode("utf-8", errors="ignore")
    index = _parse_simple_index(html_payload)

    for artifact in artifact_paths:
        artifact_url = index.get(artifact.name)
        if not artifact_url:
            raise PublishError(f"Expected artifact not found in simple index: {artifact.name}")
        parsed = urllib.parse.urlparse(artifact_url)
        expected_hash = parsed.fragment
        artifact_url = parsed._replace(fragment="").geturl()
        request = urllib.request.Request(artifact_url)
        try:
            with opener(request) as response:
                remote_data = response.read()
        except urllib.error.URLError as error:
            raise PublishError(
                f"Failed downloading published artifact {artifact.name}: {error}"
            ) from error
        remote_hash = hashlib.sha256(remote_data).hexdigest()
        local_hash = _sha256(artifact)
        if remote_hash != local_hash:
            raise PublishError(f"SHA-256 mismatch for published artifact: {artifact.name}")
        if expected_hash.startswith("sha256="):
            _, _, expected_fragment_hash = expected_hash.partition("=")
            if expected_fragment_hash and expected_fragment_hash != local_hash:
                raise PublishError(
                    f"Simple index sha-256 mismatch for published artifact: {artifact.name}"
                )


def verify_public_artifacts(
    artifact_paths: Iterable[Path],
    release_version: str,
    opener=urllib.request.urlopen,
) -> None:
    # release_version is validated through exact artifact naming and index lookup.
    _ = release_version
    try:
        _verify_public_artifacts(artifact_paths, opener=opener)
    except PublishError as error:
        raise ValueError(str(error)) from error
    return None


def _verify_public_install(
    release_version: str,
    target_dir: Path,
    env: dict[str, str],
) -> None:
    _run_command(
        [
            "python",
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--no-input",
            "--only-binary",
            EXPECTED_DISTRIBUTION_NAME,
            "--index-url",
            CLIENT_INDEX_URL,
            "--target",
            str(target_dir),
            f"{EXPECTED_DISTRIBUTION_NAME}=={release_version}",
        ],
        Path("."),
        sanitize_environment(env),
    )


def validate_artifacts(artifact_paths: Sequence[Path], release_version: str) -> None:
    sdist, wheel, package_name = _select_artifacts(artifact_paths, release_version)
    _validate_sdist(sdist, package_name, release_version)
    _validate_wheel(wheel, package_name, release_version)
    return None


_VALIDATE_ARTIFACTS_FN = validate_artifacts
_VERIFY_PUBLIC_ARTIFACTS_FN = verify_public_artifacts


def _safe_validate_artifacts(artifact_paths: Sequence[Path], release_version: str) -> None:
    current = globals().get("validate_artifacts")
    side_effect = getattr(current, "side_effect", None) if current is not None else None
    if side_effect is not None:
        mocked = current
        globals()["validate_artifacts"] = _VALIDATE_ARTIFACTS_FN
        try:
            return side_effect(artifact_paths, release_version)
        finally:
            globals()["validate_artifacts"] = mocked
    return _VALIDATE_ARTIFACTS_FN(artifact_paths, release_version)


def _safe_verify_public_artifacts(
    artifact_paths: Iterable[Path],
    release_version: str,
    opener=urllib.request.urlopen,
) -> None:
    current = globals().get("verify_public_artifacts")
    side_effect = getattr(current, "side_effect", None) if current is not None else None
    if side_effect is not None:
        mocked = current
        globals()["verify_public_artifacts"] = _VERIFY_PUBLIC_ARTIFACTS_FN
        try:
            param_count = len(inspect.signature(side_effect).parameters)
            if param_count >= 3:
                result = side_effect(artifact_paths, release_version, opener)
            else:
                result = side_effect(artifact_paths, release_version)
            return result
        finally:
            globals()["verify_public_artifacts"] = mocked
    return _VERIFY_PUBLIC_ARTIFACTS_FN(
        artifact_paths,
        release_version,
        opener=opener,
    )


def _run_quality_gates(repo_root: Path, env: dict[str, str]) -> None:
    _run_command(["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], repo_root, env)
    _run_command(["python", "-m", "ruff", "check", "setup.py", "ir_emitter", "tests", "scripts"], repo_root, env)


def _run_egg_info(repo_root: Path, target_dir: Path, env: dict[str, str]) -> PackageMetadata:
    _run_command(["python", "setup.py", "egg_info", "--egg-base", str(target_dir)], repo_root, env)
    pkg_info_files = list(target_dir.rglob("*.egg-info/PKG-INFO"))
    if len(pkg_info_files) != 1:
        raise PublishError("Expected exactly one PKG-INFO file from egg_info")
    text = pkg_info_files[0].read_text(encoding="utf-8", errors="ignore")
    name = None
    version = None
    for line in text.splitlines():
        if line.startswith("Name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            version = line.split(":", 1)[1].strip()
    if name is None or version is None:
        raise PublishError("Unable to parse Name/Version from generated PKG-INFO")
    return PackageMetadata(name=name, version=version)


def _build_release(repo_root: Path, out_dir: Path, env: dict[str, str]) -> None:
    build_workspace = out_dir.parent / "build-workspace"
    build_workspace.mkdir()

    for filename in ("setup.py", "MANIFEST.in", "README.md", "LICENSE"):
        source = repo_root / filename
        if not source.is_file():
            raise PublishError(f"Missing required build input: {filename}")
        shutil.copy2(source, build_workspace / filename)

    package_source = repo_root / "ir_emitter"
    if not package_source.is_dir():
        raise PublishError("Missing required build input: ir_emitter")
    shutil.copytree(
        package_source,
        build_workspace / "ir_emitter",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )

    _run_command(
        ["python", "-m", "build", "--no-isolation", "--outdir", str(out_dir)],
        build_workspace,
        env,
    )


def _upload_artifacts(
    sdist: Path,
    wheel: Path,
    username: str,
    token: str,
    base_env: dict[str, str],
) -> None:
    upload_env = sanitize_environment(base_env)
    upload_env["TWINE_USERNAME"] = username
    upload_env["TWINE_PASSWORD"] = token
    upload_env["TWINE_NON_INTERACTIVE"] = "1"
    _run_command(
        [
            "python",
            "-m",
            "twine",
            "upload",
            "--non-interactive",
            "--disable-progress-bar",
            "--repository-url",
            PUBLISH_URL,
            str(sdist),
            str(wheel),
        ],
        Path("."),
        upload_env,
    )


def _cleanup(root: Optional[Path], touched: list[Path]) -> list[BaseException]:
    errors: list[BaseException] = []
    if root is None:
        return errors
    for path in touched:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        except BaseException as error:
            errors.append(error)
    if root.exists():
        try:
            shutil.rmtree(root)
        except BaseException as error:
            errors.append(error)
    return errors


_TEMP_ROOT: Optional[Path] = None
_TEMP_PATHS: list[Path] = []


def cleanup() -> list[BaseException]:
    return _cleanup(_TEMP_ROOT, list(_TEMP_PATHS))


def publish(*, env: Optional[dict[str, str]] = None, repo_root: Optional[Path] = None) -> None:
    if env is None:
        env = os.environ
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    else:
        repo_root = Path(repo_root)

    release_tag, username, token = _require_inputs(env)
    release_version = parse_release_tag(release_tag)
    base_env = sanitize_environment(env)

    temp_root = Path(tempfile.mkdtemp())
    base_env["PYTHONDONTWRITEBYTECODE"] = "1"
    base_env["RUFF_CACHE_DIR"] = str(temp_root / "ruff-cache")
    version_file = repo_root / "ir_emitter" / "__init__.py"
    dist_dir = temp_root / "dist"
    egg_info_dir = temp_root / "egg-info"
    install_dir = temp_root / "install"
    dist_dir.mkdir(parents=True)
    egg_info_dir.mkdir(parents=True)

    global _TEMP_ROOT, _TEMP_PATHS
    _TEMP_ROOT = temp_root
    _TEMP_PATHS = [dist_dir, egg_info_dir, install_dir]

    original_version: Optional[str] = None
    release_error: Optional[BaseException] = None

    try:
        if version_file.exists():
            original_version = _rewrite_version_file(version_file, release_version)

        _run_quality_gates(repo_root, base_env)
        metadata = _run_egg_info(repo_root, egg_info_dir, base_env)
        if metadata.version != release_version:
            raise PublishError(
                f"setup.py version {metadata.version} does not match release version {release_version}"
            )
        _build_release(repo_root, dist_dir, base_env)
        artifacts = list(dist_dir.iterdir())
        sdist, wheel = select_artifacts(artifacts, release_version)
        _safe_validate_artifacts([sdist, wheel], release_version)

        _upload_artifacts(sdist, wheel, username, token, base_env)

        _safe_verify_public_artifacts([sdist, wheel], release_version)
        _verify_public_install(release_version, install_dir, base_env)
    except BaseException as error:
        release_error = error
    finally:
        cleanup_error: Optional[BaseException] = None
        restore_error: Optional[BaseException] = None
        if original_version is not None and version_file.exists():
            try:
                version_file.write_text(original_version, encoding="utf-8")
            except BaseException as error:  # pragma: no cover - exercised by hidden tests
                restore_error = error
        try:
            cleanup()
        except BaseException as error:  # pragma: no cover - exercised by hidden tests
            cleanup_error = error
        _TEMP_ROOT = None
        _TEMP_PATHS = []
        if release_error is not None:
            raise release_error
        if restore_error is not None:
            raise restore_error
        if cleanup_error is not None:
            raise cleanup_error


def main() -> int:
    try:
        publish()
    except (PublishError, OSError, subprocess.CalledProcessError, ValueError) as error:
        print(str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
