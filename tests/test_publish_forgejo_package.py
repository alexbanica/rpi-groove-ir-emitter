import hashlib
import io
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from scripts import publish_forgejo


def _write_minimal_repo(root: Path, version: str = "1.0.0") -> None:
    """Create the source files required by the release build in a temp repo."""
    (root / "setup.py").write_text("from setuptools import setup\n", encoding="utf-8")
    (root / "MANIFEST.in").write_text("include README.md\n", encoding="utf-8")
    (root / "README.md").write_text("readme\n", encoding="utf-8")
    (root / "LICENSE").write_text("license\n", encoding="utf-8")
    runtime = root / "ir_emitter"
    runtime.mkdir()
    (runtime / "__init__.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )


def _write_valid_artifacts(
    root: Path,
    *,
    include_setup: bool = True,
    include_wheel_metadata: bool = True,
    sdist_directory_required_name: Optional[str] = None,
    extra_sdist_member: Optional[str] = None,
    extra_sdist_type: int = tarfile.REGTYPE,
) -> tuple[Path, Path]:
    """Create the smallest pair that satisfies the publisher's archive contract."""
    version = "1.2.3"
    prefix = f"rpi_groove_ir_emitter-{version}"
    # setuptools normalizes the distribution name in the generated sdist root.
    archive_prefix = f"rpi_groove_ir_emitter-{version}"
    sdist = root / f"{prefix}.tar.gz"
    sdist_directories = [
        f"{archive_prefix}/",
        f"{archive_prefix}/ir_emitter/",
    ]
    sdist_members = [
        (f"{archive_prefix}/ir_emitter/__init__.py", b'__version__ = "1.2.3"\n'),
        (f"{archive_prefix}/PKG-INFO", b"Metadata-Version: 2.1\nName: rpi-groove-ir-emitter\nVersion: 1.2.3\n"),
        (f"{archive_prefix}/README.md", b"readme\n"),
        (f"{archive_prefix}/LICENSE", b"license\n"),
    ]
    if include_setup:
        sdist_members.append((f"{archive_prefix}/setup.py", b"from setuptools import setup\n"))
    with tarfile.open(sdist, "w:gz") as archive:
        for name in sdist_directories:
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            archive.addfile(info)
        for name, data in sdist_members:
            if name == f"{archive_prefix}/{sdist_directory_required_name}":
                info = tarfile.TarInfo(name)
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
                continue
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if extra_sdist_member is not None:
            info = tarfile.TarInfo(extra_sdist_member)
            info.type = extra_sdist_type
            if extra_sdist_type in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                info.linkname = f"{archive_prefix}/README.md"
            else:
                info.size = len(b"unexpected")
            archive.addfile(info, io.BytesIO(b"unexpected") if info.isfile() else None)

    wheel = root / f"{prefix}-py3-none-any.whl"
    dist_info = f"{prefix}.dist-info"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("ir_emitter/__init__.py", b'__version__ = "1.2.3"\n')
        archive.writestr(
            f"{dist_info}/METADATA",
            b"Metadata-Version: 2.1\nName: rpi-groove-ir-emitter\nVersion: 1.2.3\n",
        )
        if include_wheel_metadata:
            archive.writestr(f"{dist_info}/WHEEL", b"Wheel-Version: 1.0\nTag: py3-none-any\n")
    return sdist, wheel


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def read(self, *_args):
        return super().read(*_args)


class PublishForgejoContractTests(unittest.TestCase):
    def test_exact_release_tag_grammar_and_beta_mapping(self):
        self.assertEqual(publish_forgejo.parse_release_tag("1.2.3"), "1.2.3")
        self.assertEqual(publish_forgejo.parse_release_tag("1.2.3-beta1"), "1.2.3b1")
        self.assertEqual(publish_forgejo.parse_release_tag("10.20.30-beta42"), "10.20.30b42")
        for tag in ("v1.2.3", " 1.2.3", "01.2.3", "1.2.3-beta0", "1.2.3-beta.1", "1.2.3+build"):
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    publish_forgejo.parse_release_tag(tag)

    def test_required_inputs_are_checked_before_commands(self):
        for missing in ("RELEASE_TAG", "FORGEJO_PACKAGE_USERNAME", "FORGEJO_PACKAGE_TOKEN"):
            env = {
                "RELEASE_TAG": "1.2.3",
                "FORGEJO_PACKAGE_USERNAME": "publisher",
                "FORGEJO_PACKAGE_TOKEN": "secret",
            }
            env.pop(missing)
            with self.subTest(missing=missing), patch.object(publish_forgejo, "run_command") as run:
                with self.assertRaises((KeyError, ValueError, SystemExit)):
                    publish_forgejo.publish(env=env)
                run.assert_not_called()

    def test_version_rewrite_requires_exactly_one_literal_assignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            version_file = Path(tmp) / "__init__.py"
            version_file.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
            self.assertEqual(publish_forgejo.rewrite_version(version_file, "1.2.3b1"), 1)
            self.assertIn('__version__ = "1.2.3b1"', version_file.read_text(encoding="utf-8"))
            version_file.write_text('__version__ = "1"\n__version__ = "2"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                publish_forgejo.rewrite_version(version_file, "1.2.3")

    def test_sensitive_environment_is_removed_from_non_upload_commands(self):
        env = {
            "PATH": "/bin",
            "TWINE_USERNAME": "old-user",
            "TWINE_PASSWORD": "old-secret",
            "TWINE_REPOSITORY_URL": "bad-url",
            "TWINE_NON_INTERACTIVE": "0",
            "PYPIRC_PATH": "/tmp/pypirc",
            "FORGEJO_PACKAGE_USERNAME": "user",
            "FORGEJO_PACKAGE_TOKEN": "token",
        }
        sanitized = publish_forgejo.sanitize_environment(env)
        self.assertEqual(sanitized, {"PATH": "/bin"})
        self.assertNotIn("token", repr(sanitized))

    def test_artifact_selection_requires_exact_sdist_and_wheel_allowlist(self):
        paths = [
            Path("rpi_groove_ir_emitter-1.2.3.tar.gz"),
            Path("rpi_groove_ir_emitter-1.2.3-py3-none-any.whl"),
        ]
        selected = publish_forgejo.select_artifacts(paths, "1.2.3")
        self.assertEqual(tuple(selected), tuple(paths))
        for bad in (
            paths + [Path("rpi_groove_ir_emitter-1.2.3.zip")],
            paths + [Path("rpi_groove_ir_emitter-1.2.3-py3-none-any.whl")],
            [Path("other-1.2.3.tar.gz"), paths[1]],
        ):
            with self.subTest(paths=bad):
                with self.assertRaises(ValueError):
                    publish_forgejo.select_artifacts(bad, "1.2.3")

        matching_other_distribution = [
            Path("other-package-1.2.3.tar.gz"),
            Path("other-package-1.2.3-py3-none-any.whl"),
        ]
        with self.assertRaises(ValueError):
            publish_forgejo.select_artifacts(matching_other_distribution, "1.2.3")

    def test_archive_validation_accepts_minimal_sdist_and_wheel_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = _write_valid_artifacts(Path(tmp))
            self.assertIsNone(publish_forgejo.validate_artifacts(list(artifacts), "1.2.3"))

    def test_archive_validation_rejects_required_content_present_only_as_directory(self):
        required_names = (
            "setup.py",
            "ir_emitter/__init__.py",
            "README.md",
            "LICENSE",
        )
        for required_name in required_names:
            with self.subTest(required_name=required_name), tempfile.TemporaryDirectory() as tmp:
                artifacts = _write_valid_artifacts(
                    Path(tmp), sdist_directory_required_name=required_name
                )
                with self.assertRaises((ValueError, publish_forgejo.PublishError)):
                    publish_forgejo.validate_artifacts(list(artifacts), "1.2.3")

    def test_archive_validation_requires_setup_metadata_and_both_artifacts(self):
        for options in ({"include_setup": False}, {"include_wheel_metadata": False}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as tmp:
                artifacts = _write_valid_artifacts(Path(tmp), **options)
                with self.assertRaises((ValueError, publish_forgejo.PublishError)):
                    publish_forgejo.validate_artifacts(list(artifacts), "1.2.3")

    def test_archive_validation_rejects_forbidden_regular_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = _write_valid_artifacts(
                Path(tmp), extra_sdist_member="rpi_groove_ir_emitter-1.2.3/.github/workflows/ci.yml"
            )
            with self.assertRaises((ValueError, publish_forgejo.PublishError)):
                publish_forgejo.validate_artifacts(list(artifacts), "1.2.3")

    def test_archive_validation_rejects_out_of_root_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = _write_valid_artifacts(
                Path(tmp),
                extra_sdist_member="../outside/",
                extra_sdist_type=tarfile.DIRTYPE,
            )
            with self.assertRaises((ValueError, publish_forgejo.PublishError)):
                publish_forgejo.validate_artifacts(list(artifacts), "1.2.3")

    def test_archive_validation_rejects_every_non_regular_tar_member(self):
        for member_type, label in (
            (tarfile.SYMTYPE, "symlink"),
            (tarfile.LNKTYPE, "hardlink"),
            (tarfile.CHRTYPE, "char-device"),
            (tarfile.BLKTYPE, "block-device"),
            (tarfile.FIFOTYPE, "fifo"),
        ):
            with self.subTest(member_type=label), tempfile.TemporaryDirectory() as tmp:
                artifacts = _write_valid_artifacts(
                    Path(tmp),
                    extra_sdist_member=f"rpi_groove_ir_emitter-1.2.3/{label}",
                    extra_sdist_type=member_type,
                )
                with self.assertRaises((ValueError, publish_forgejo.PublishError)):
                    publish_forgejo.validate_artifacts(list(artifacts), "1.2.3")

    def test_publish_command_order_credentials_and_single_upload(self):
        commands = []

        def run(command, **kwargs):
            commands.append((command, kwargs))
            if "egg_info" in command:
                target = Path(command[-1])
                info_dir = target / "rpi_groove_ir_emitter-1.2.3.egg-info"
                info_dir.mkdir(parents=True)
                (info_dir / "PKG-INFO").write_text(
                    "Name: rpi-groove-ir-emitter\nVersion: 1.2.3\n", encoding="utf-8"
                )
            elif "build" in command:
                _write_valid_artifacts(Path(command[-1]))
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(publish_forgejo, "run_command", side_effect=run),
            patch.object(publish_forgejo, "verify_public_artifacts", side_effect=lambda *_args: None),
        ):
            root = Path(tmp)
            _write_minimal_repo(root)
            publish_forgejo.publish(env=env, repo_root=root)
        self.assertGreaterEqual(len(commands), 5)
        command_text = [" ".join(command) for command, _ in commands]
        test_index = next(index for index, text in enumerate(command_text) if "-m unittest" in text)
        build_index = next(index for index, text in enumerate(command_text) if "-m build" in text)
        self.assertLess(test_index, build_index)
        upload = [(command, kwargs) for command, kwargs in commands if "twine" in command]
        self.assertEqual(len(upload), 1)
        self.assertEqual(upload[0][1]["env"]["TWINE_USERNAME"], "publisher")
        self.assertEqual(upload[0][1]["env"]["TWINE_PASSWORD"], "secret")
        non_upload = [(command, kwargs) for command, kwargs in commands if "twine" not in command]
        self.assertNotIn("secret", repr([kwargs for _command, kwargs in non_upload]))

        egg_info_command = next(command for command, _kwargs in non_upload if "egg_info" in command)
        publisher_temp_root = Path(egg_info_command[-1]).parent
        for _command, kwargs in non_upload:
            command_env = kwargs["env"]
            self.assertEqual(command_env["PYTHONDONTWRITEBYTECODE"], "1")
            ruff_cache_dir = Path(command_env["RUFF_CACHE_DIR"])
            self.assertTrue(ruff_cache_dir.is_absolute())
            self.assertTrue(ruff_cache_dir.is_relative_to(publisher_temp_root))
            self.assertFalse(ruff_cache_dir == root or root in ruff_cache_dir.parents)

    def test_build_release_uses_clean_temporary_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            out_dir = Path(tmp) / "release" / "dist"
            root.mkdir()
            out_dir.mkdir(parents=True)
            (root / "setup.py").write_text("from setuptools import setup\n", encoding="utf-8")
            (root / "MANIFEST.in").write_text("include README.md\n", encoding="utf-8")
            (root / "README.md").write_text("readme\n", encoding="utf-8")
            (root / "LICENSE").write_text("license\n", encoding="utf-8")
            runtime = root / "ir_emitter"
            runtime.mkdir()
            (runtime / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
            (runtime / "player.py").write_text("runtime\n", encoding="utf-8")
            for directory in ("tests", "specs", "scripts", ".github"):
                (root / directory).mkdir()
                (root / directory / "must-not-copy.txt").write_text("excluded\n", encoding="utf-8")

            observed = {}

            def run(command, **kwargs):
                workspace = Path(kwargs["cwd"])
                observed["command"] = list(command)
                observed["cwd"] = workspace
                observed["env"] = kwargs["env"]
                observed["names"] = sorted(path.name for path in workspace.iterdir())
                observed["runtime_names"] = sorted(path.name for path in (workspace / "ir_emitter").iterdir())
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            env = {"PATH": "/bin"}
            with patch.object(publish_forgejo, "run_command", side_effect=run):
                publish_forgejo._build_release(root, out_dir, env)

            workspace = observed["cwd"]
            self.assertIsNot(workspace, root)
            self.assertEqual(workspace.parent, out_dir.parent)
            self.assertEqual(
                observed["command"],
                ["python", "-m", "build", "--no-isolation", "--outdir", str(out_dir)],
            )
            self.assertEqual(observed["env"], env)
            self.assertEqual(
                observed["names"], ["LICENSE", "MANIFEST.in", "README.md", "ir_emitter", "setup.py"]
            )
            self.assertEqual(observed["runtime_names"], ["__init__.py", "player.py"])

    def test_stubbed_boundaries_preserve_release_sequencing_and_real_validation(self):
        commands = []
        verification = []
        validation = []
        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_minimal_repo(root)
            version_file = root / "ir_emitter" / "__init__.py"
            observed_versions = []

            def run(command, **kwargs):
                commands.append((list(command), kwargs))
                observed_versions.append(version_file.read_text(encoding="utf-8"))
                if "egg_info" in command:
                    target = Path(command[-1])
                    info_dir = target / "rpi_groove_ir_emitter-1.2.3.egg-info"
                    info_dir.mkdir(parents=True)
                    (info_dir / "PKG-INFO").write_text(
                        "Name: rpi-groove-ir-emitter\nVersion: 1.2.3\n", encoding="utf-8"
                    )
                elif "build" in command:
                    _write_valid_artifacts(Path(command[-1]))
                return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            def validate(paths, version):
                validation.append((list(paths), version, [path.stat().st_size for path in paths]))
                return publish_forgejo.validate_artifacts(paths, version)

            def verify(paths, version):
                verification.append((list(paths), version))

            with (
                patch.object(publish_forgejo, "run_command", side_effect=run),
                patch.object(publish_forgejo, "validate_artifacts", side_effect=validate),
                patch.object(publish_forgejo, "verify_public_artifacts", side_effect=verify),
            ):
                publish_forgejo.publish(env=env, repo_root=root)

            self.assertEqual(version_file.read_text(encoding="utf-8"), '__version__ = "1.0.0"\n')
            self.assertTrue(observed_versions)
            self.assertEqual(observed_versions[0], '__version__ = "1.2.3"\n')
            self.assertEqual(len(validation), 1)
            self.assertEqual(validation[0][1], "1.2.3")
            self.assertEqual(len(verification), 1)
            self.assertTrue(all(size > 0 for size in validation[0][2]))

    def test_public_verification_is_unauthenticated_and_checks_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = [
                Path(tmp) / "rpi_groove_ir_emitter-1.2.3.tar.gz",
                Path(tmp) / "rpi_groove_ir_emitter-1.2.3-py3-none-any.whl",
            ]
            artifacts[0].write_bytes(b"sdist")
            artifacts[1].write_bytes(b"wheel")
            digests = [hashlib.sha256(artifact.read_bytes()).hexdigest() for artifact in artifacts]
            html = (
                '<a href="rpi_groove_ir_emitter-1.2.3.tar.gz#sha256='
                + digests[0]
                + '">sdist</a>'
                '<a href="rpi_groove_ir_emitter-1.2.3-py3-none-any.whl#sha256='
                + digests[1]
                + '">wheel</a>'
            )
            calls = []
            remote_payload = {artifacts[0].name: b"sdist", artifacts[1].name: b"wheel"}

            def opener(request):
                calls.append(request)
                url = request.full_url
                if url == publish_forgejo.SIMPLE_INDEX_URL:
                    return _Response(html.encode())
                if url.endswith(artifacts[0].name):
                    return _Response(remote_payload[artifacts[0].name])
                if url.endswith(artifacts[1].name):
                    return _Response(remote_payload[artifacts[1].name])
                raise AssertionError(f"unexpected verification URL: {url}")

            publish_forgejo.verify_public_artifacts(artifacts, "1.2.3", opener=opener)
            self.assertEqual(
                [request.full_url for request in calls],
                [
                    publish_forgejo.SIMPLE_INDEX_URL,
                    publish_forgejo.SIMPLE_INDEX_URL + artifacts[0].name,
                    publish_forgejo.SIMPLE_INDEX_URL + artifacts[1].name,
                ],
            )
            for request in calls:
                self.assertFalse(request.header_items())

            remote_payload[artifacts[1].name] = b"tampered-remote"
            with self.assertRaises(ValueError):
                publish_forgejo.verify_public_artifacts(artifacts, "1.2.3", opener=opener)

    def test_cleanup_runs_after_failure_and_original_error_propagates(self):
        cleanup = []
        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ir_emitter").mkdir()
            (root / "ir_emitter" / "__init__.py").write_text(
                '__version__ = "1.0.0"\n', encoding="utf-8"
            )
            with patch.object(publish_forgejo, "run_command", side_effect=RuntimeError("build failed")):
                with patch.object(publish_forgejo, "cleanup", side_effect=lambda: cleanup.append(True)):
                    with self.assertRaisesRegex(RuntimeError, "build failed"):
                        publish_forgejo.publish(env=env, repo_root=root)
        self.assertEqual(cleanup, [True])

    def test_cleanup_runs_when_version_rewrite_fails_before_commands(self):
        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "ir_emitter" / "__init__.py"
            version_file.parent.mkdir()
            version_file.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
            with (
                patch.object(publish_forgejo, "_rewrite_version_file", side_effect=ValueError("rewrite failed")),
                patch.object(publish_forgejo, "cleanup") as cleanup,
                patch.object(subprocess, "run") as command,
            ):
                with self.assertRaisesRegex(ValueError, "rewrite failed"):
                    publish_forgejo.publish(env=env, repo_root=root)
            cleanup.assert_called_once_with()
            command.assert_not_called()

    def test_cleanup_failure_does_not_replace_release_command_failure(self):
        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }
        release_error = RuntimeError("release command failed")
        cleanup_error = OSError("cleanup failed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ir_emitter").mkdir()
            (root / "ir_emitter" / "__init__.py").write_text(
                '__version__ = "1.0.0"\n', encoding="utf-8"
            )
            with (
                patch.object(publish_forgejo, "run_command", side_effect=release_error),
                patch.object(publish_forgejo, "cleanup", side_effect=cleanup_error),
            ):
                with self.assertRaises(RuntimeError) as raised:
                    publish_forgejo.publish(env=env, repo_root=root)
        self.assertIs(raised.exception, release_error)

    def test_restore_failure_does_not_replace_active_release_error(self):
        env = {
            "RELEASE_TAG": "1.2.3",
            "FORGEJO_PACKAGE_USERNAME": "publisher",
            "FORGEJO_PACKAGE_TOKEN": "secret",
        }
        release_error = RuntimeError("release command failed")
        restore_error = OSError("version restore failed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version_file = root / "ir_emitter" / "__init__.py"
            version_file.parent.mkdir()
            version_file.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
            with (
                patch.object(publish_forgejo, "_rewrite_version_file", return_value='__version__ = "1.0.0"\n'),
                patch.object(publish_forgejo, "_run_quality_gates", side_effect=release_error),
                patch.object(publish_forgejo, "cleanup"),
                patch.object(Path, "write_text", side_effect=restore_error),
            ):
                with self.assertRaises(RuntimeError) as raised:
                    publish_forgejo.publish(env=env, repo_root=root)
            self.assertIs(raised.exception, release_error)


if __name__ == "__main__":
    unittest.main()
