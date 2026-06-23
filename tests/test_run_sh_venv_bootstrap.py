import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestRunShVenvBootstrap(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self._tmp_roots: list[str] = []

    def tearDown(self) -> None:
        for tmp_root in self._tmp_roots:
            shutil.rmtree(tmp_root, ignore_errors=True)
        self._tmp_roots = []

    def _copy_repo(self) -> Path:
        workdir = Path(tempfile.mkdtemp())
        self._tmp_roots.append(str(workdir))
        copy_target = workdir / "repo"
        shutil.copytree(
            self.repo_root,
            copy_target,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return copy_target

    def _write_executable(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def _install_fake_module_entrypoint(self, repo_root: Path) -> None:
        fake_main = repo_root / "ir_emitter" / "__main__.py"
        self._write_executable(
            fake_main,
            "#!/usr/bin/python3\n"
            "import sys\n"
            'if __name__ == "__main__":\n'
            '    print("fake ir_emitter module executed", file=sys.stderr)\n',
        )

    def _read_calls(self, calls_log: Path) -> list[str]:
        if not calls_log.exists():
            return []
        calls = calls_log.read_text(encoding="utf-8").strip().splitlines()
        return [line.strip() for line in calls if line.strip()]

    def _run_run_sh(self, repo_root: Path, args: list[str], calls_log: Path, extra_env: dict[str, str] | None = None):
        env = os.environ.copy()
        env["RUNSH_TEST_CALLS"] = str(calls_log)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [str(repo_root / "run.sh"), *args],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
        )

    def _write_venv_python_stub(self, venv_python: Path, calls_log: Path) -> None:
        script = (
            "#!/bin/sh\n"
            'echo "$0 $@" >> "$RUNSH_TEST_CALLS"\n'
            "exit 0\n"
        )
        self._write_executable(venv_python, script)

    def _write_python3_stub(self, stub_dir: Path, calls_log: Path) -> None:
        python3_stub = stub_dir / "python3"
        script = (
            "#!/bin/sh\n"
            'echo "$0 $@" >> "$RUNSH_TEST_CALLS"\n'
            'if [ "$1" = "-m" ] && [ "$2" = "venv" ] && [ "$3" = ".venv" ]; then\n'
            '  mkdir -p .venv/bin\n'
            "  cat > .venv/bin/python <<'PYTHON_STUB'\n"
            "#!/bin/sh\n"
            'echo "$0 $@" >> "$RUNSH_TEST_CALLS"\n'
            "exit 0\n"
            "PYTHON_STUB\n"
            "  chmod +x .venv/bin/python\n"
            "fi\n"
            "exit 0\n"
        )
        self._write_executable(python3_stub, script)

    def test_existing_venv_python_is_used(self) -> None:
        repo = self._copy_repo()
        calls_log = repo / "calls.log"

        self._install_fake_module_entrypoint(repo)
        self._write_venv_python_stub(repo / ".venv" / "bin" / "python", calls_log)
        (repo / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
        input_file = repo / "existing_input.json"
        input_file.write_text("{}", encoding="utf-8")

        result = self._run_run_sh(repo, ["--input", str(input_file)], calls_log)
        calls = self._read_calls(calls_log)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(any("/.venv/bin/python" in line for line in calls))
        self.assertFalse(any("/usr/bin/python3" in line for line in calls))
        self.assertTrue(any(" -m ir_emitter " in line for line in calls))

    def test_missing_venv_triggers_bootstrap_and_install(self) -> None:
        repo = self._copy_repo()
        calls_log = repo / "calls.log"
        stub_dir = repo / "stubbin"
        stub_dir.mkdir()

        self._install_fake_module_entrypoint(repo)
        self._write_python3_stub(stub_dir, calls_log)
        input_file = repo / "bootstrap_input.json"
        input_file.write_text("{}", encoding="utf-8")

        result = self._run_run_sh(
            repo,
            ["--input", str(input_file)],
            calls_log,
            extra_env={"PATH": f"{stub_dir}:{os.environ.get('PATH', '')}"},
        )

        calls = self._read_calls(calls_log)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(any(" -m venv .venv" in line for line in calls), calls)
        self.assertTrue(any(" -m pip install ." in line for line in calls), calls)

    def test_missing_input_flag_exits_before_bootstrap(self) -> None:
        repo = self._copy_repo()
        calls_log = repo / "calls.log"
        stub_dir = repo / "stubbin"
        stub_dir.mkdir()
        self._write_python3_stub(stub_dir, calls_log)

        result = self._run_run_sh(
            repo,
            [],
            calls_log,
            extra_env={"PATH": f"{stub_dir}:{os.environ.get('PATH', '')}"},
        )

        calls = self._read_calls(calls_log)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Input file not specified", result.stdout + result.stderr)
        self.assertEqual(calls, [])

    def test_missing_input_file_exits_before_bootstrap(self) -> None:
        repo = self._copy_repo()
        calls_log = repo / "calls.log"
        stub_dir = repo / "stubbin"
        stub_dir.mkdir()
        self._write_python3_stub(stub_dir, calls_log)

        result = self._run_run_sh(
            repo,
            ["--input", str(repo / "does-not-exist.json")],
            calls_log,
            extra_env={"PATH": f"{stub_dir}:{os.environ.get('PATH', '')}"},
        )

        calls = self._read_calls(calls_log)
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist", result.stdout + result.stderr)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
