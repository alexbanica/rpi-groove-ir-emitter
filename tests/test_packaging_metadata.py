import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


class TestPackagingMetadata(unittest.TestCase):
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
