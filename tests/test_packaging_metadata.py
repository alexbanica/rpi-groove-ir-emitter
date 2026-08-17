import subprocess
import sys
from pathlib import Path
import shutil
import tempfile
import unittest


class TestPackagingMetadata(unittest.TestCase):
    def _run_egg_info_for_version(self, version: str) -> str:
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_root = Path(tmpdir)
            shutil.copy2(repo_root / "setup.py", fixture_root / "setup.py")
            package_dir = fixture_root / "ir_emitter"
            package_dir.mkdir()
            egg_base = fixture_root / "egg-info"
            egg_base.mkdir()
            init_source = (repo_root / "ir_emitter" / "__init__.py").read_text(encoding="utf-8")
            (package_dir / "__init__.py").write_text(
                init_source.replace('__version__ = "1.0.0"', f'__version__ = "{version}"'),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(fixture_root / "setup.py"),
                    "egg_info",
                    "--egg-base",
                    str(egg_base),
                ],
                cwd=fixture_root,
                text=True,
                capture_output=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"setup.py egg_info failed: {result.stdout}{result.stderr}",
            )
            metadata = fixture_root / "egg-info" / "rpi_groove_ir_emitter.egg-info" / "PKG-INFO"
            self.assertTrue(metadata.exists(), "expected PKG-INFO to be generated")
            version_line = next(
                line for line in metadata.read_text(encoding="utf-8").splitlines()
                if line.startswith("Version: ")
            )
            return version_line.removeprefix("Version: ")

    def test_setup_metadata_reads_version_from_import_package(self) -> None:
        self.assertEqual(self._run_egg_info_for_version("2.4.6"), "2.4.6")

    def test_stable_and_beta_versions_are_normalized_in_metadata(self) -> None:
        fixtures = {
            "2.4.6": "2.4.6",
            "2.4.6b3": "2.4.6b3",
        }
        for source_version, expected_version in fixtures.items():
            with self.subTest(source_version=source_version):
                self.assertEqual(self._run_egg_info_for_version(source_version), expected_version)

    def test_metadata_preserves_required_package_identity(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_root = Path(tmpdir)
            shutil.copy2(repo_root / "setup.py", fixture_root / "setup.py")
            shutil.copytree(repo_root / "ir_emitter", fixture_root / "ir_emitter")
            egg_base = fixture_root / "egg-info"
            egg_base.mkdir()
            result = subprocess.run(
                [sys.executable, str(fixture_root / "setup.py"), "egg_info", "--egg-base", str(egg_base)],
                cwd=fixture_root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            metadata = (fixture_root / "egg-info" / "rpi_groove_ir_emitter.egg-info" / "PKG-INFO").read_text(encoding="utf-8")
            self.assertIn("Name: rpi-groove-ir-emitter\n", metadata)
            self.assertIn("Requires-Python: >=3.9\n", metadata)

    def test_egg_info_includes_ir_emitter_package(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        egg_info_dir = "rpi_groove_ir_emitter.egg-info"

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                sys.executable,
                str(repo_root / "setup.py"),
                "egg_info",
                "--egg-base",
                tmpdir,
            ]
            result = subprocess.run(
                cmd,
                cwd=repo_root,
                text=True,
                capture_output=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"setup.py egg_info failed: {result.stdout}{result.stderr}",
            )
            self.assertNotIn("not a valid package name", result.stderr)

            top_level_file = Path(tmpdir) / egg_info_dir / "top_level.txt"
            self.assertTrue(top_level_file.exists(), "expected top_level metadata file to be generated")
            top_level = top_level_file.read_text(encoding="utf-8").splitlines()

            self.assertIn("ir_emitter", top_level)
            self.assertNotIn("rpi-groove-ir-emitter", top_level)
            self.assertTrue(all(name for name in top_level), "top-level package names must not be empty")


if __name__ == "__main__":
    unittest.main()
