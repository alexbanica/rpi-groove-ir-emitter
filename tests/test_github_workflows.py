from pathlib import Path
import re
import unittest


class TestGithubWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow_root = Path(__file__).resolve().parents[1] / ".github" / "workflows"

    def _workflow(self, name: str) -> str:
        path = self.workflow_root / name
        self.assertTrue(path.is_file(), f"missing workflow: {path}")
        return path.read_text(encoding="utf-8")

    def _parse_publish_steps(self, workflow: str):
        step_headers = []
        lines = workflow.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r"^ +-\s+(?:name|uses|run|id|shell|env|with):", line):
                step_indent = len(line) - len(line.lstrip(" "))
                block_start = i
                block_end = i + 1
                while block_end < len(lines):
                    next_line = lines[block_end]
                    if next_line.strip() == "":
                        block_end += 1
                        continue
                    if len(next_line) - len(next_line.lstrip(" ")) <= step_indent:
                        break
                    block_end += 1
                step_headers.append((block_start, block_end))
                i = block_end
                continue
            i += 1

        return [
            self._parse_step_env(
                workflow.splitlines()[start:end],
                start,
                indent,
            )
            for start, end in step_headers
            for indent in [len(workflow.splitlines()[start]) - len(workflow.splitlines()[start].lstrip(" "))]
        ]

    def _parse_step_env(self, step_lines, start_line: int, step_indent: int):
        env = {}
        step_name = None
        for line in step_lines:
            if step_name is None:
                m = re.match(rf"^{' ' * step_indent}-\s+name:\s*(.*)$", line)
                if m:
                    step_name = m.group(1).strip().strip("'\"")
        env_indent = step_indent + 2
        i = 0
        while i < len(step_lines):
            if re.match(rf"^{' ' * env_indent}env:\s*$", step_lines[i]):
                j = i + 1
                while j < len(step_lines):
                    raw = step_lines[j]
                    if raw.strip() == "":
                        j += 1
                        continue
                    indent = len(raw) - len(raw.lstrip(" "))
                    if indent <= env_indent:
                        break
                    m = re.match(rf"^{' ' * (env_indent + 2)}([A-Z_][A-Z0-9_]*)\s*:\s*(.*)$", raw)
                    if m:
                        env[m.group(1)] = m.group(2).strip()
                    j += 1
            i += 1
        return {
            "name": step_name,
            "start": start_line,
            "end": start_line + len(step_lines),
            "env": env,
        }

    def _find_key_occurrences(self, workflow: str, keys: set[str]):
        result = {key: [] for key in keys}
        for idx, line in enumerate(workflow.splitlines()):
            m = re.match(r"^(\s*)([A-Z_][A-Z0-9_]*)\s*:\s*.*$", line)
            if m:
                key = m.group(2)
                if key in keys:
                    result[key].append((idx, line.rstrip("\n")))
        return result

    def _owner_steps(self, workflow: str):
        lines = workflow.splitlines()
        steps = self._parse_publish_steps(workflow)
        owner = {}
        for line_no in range(len(lines)):
            owner[line_no] = None
            for step in steps:
                if step["start"] <= line_no < step["end"]:
                    owner[line_no] = step["name"]
                    break
        return owner, steps

    def test_ci_has_only_main_pull_request_and_push_triggers(self) -> None:
        ci = self._workflow("ci.yml")

        self.assertIn("pull_request:", ci)
        self.assertRegex(ci, r"pull_request:\s*(?:\n\s+)?branches:\s*(?:\[main\]|\n\s+- main)")
        self.assertIn("push:", ci)
        self.assertRegex(ci, r"push:\s*(?:\n\s+)?branches:\s*(?:\[main\]|\n\s+- main)")
        self.assertNotIn("tags:", ci)
        self.assertNotIn("workflow_dispatch:", ci)
        self.assertNotIn("schedule:", ci)

    def test_release_has_only_coarse_numeric_tag_trigger(self) -> None:
        publish = self._workflow("publish.yml")

        self.assertIn("push:", publish)
        self.assertIn("tags:", publish)
        self.assertRegex(publish, r"- ['\"]\[0-9\]\*\.\[0-9\]\*\.\[0-9\]\*['\"]")
        self.assertNotIn("pull_request:", publish)
        self.assertNotIn("branches:", publish)
        self.assertNotIn("workflow_dispatch:", publish)
        self.assertNotIn("schedule:", publish)

    def test_both_workflows_use_read_only_contents_permission(self) -> None:
        for name in ("ci.yml", "publish.yml"):
            workflow = self._workflow(name)
            self.assertIn("permissions:", workflow)
            self.assertIn("contents: read", workflow)
            self.assertNotIn("contents: write", workflow)
            self.assertNotIn("packages: write", workflow)

    def test_actions_are_pinned_to_approved_immutable_shas(self) -> None:
        expected = {
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        }
        for name in ("ci.yml", "publish.yml"):
            workflow = self._workflow(name)
            for action in expected:
                self.assertIn(action, workflow)
            self.assertNotIn("actions/checkout@v", workflow)
            self.assertNotIn("actions/setup-python@v", workflow)

    def test_ci_has_distinct_python_313_jobs_without_a_matrix(self) -> None:
        ci = self._workflow("ci.yml")

        self.assertIn("lint:", ci)
        self.assertIn("tests:", ci)
        self.assertEqual(ci.count('python-version: "3.13"'), 2)
        self.assertNotIn("3.9", ci)
        self.assertNotIn("matrix:", ci)
        self.assertIn("ubuntu-latest", ci)

    def test_ci_uses_pinned_dependencies_and_canonical_quality_commands(self) -> None:
        ci = self._workflow("ci.yml")

        self.assertIn("python -m pip install -r requirements-dev.txt", ci)
        self.assertIn("python -m ruff check setup.py ir_emitter tests scripts", ci)
        self.assertIn("python -m unittest discover -s tests -p 'test_*.py'", ci)
        self.assertNotIn("pip install .", ci)

    def test_ci_never_receives_forgejo_credentials_or_publishing_commands(self) -> None:
        ci = self._workflow("ci.yml")

        for forbidden in (
            "FORGEJO_PACKAGE_USERNAME",
            "FORGEJO_PACKAGE_TOKEN",
            "TWINE_USERNAME",
            "TWINE_PASSWORD",
            "publish_forgejo",
            "api/packages/public/pypi",
        ):
            self.assertNotIn(forbidden, ci)

    def test_release_is_single_serialized_non_matrix_publication_job(self) -> None:
        publish = self._workflow("publish.yml")

        self.assertIn("concurrency:", publish)
        self.assertIn("${{ github.workflow }}-${{ github.ref }}", publish)
        self.assertIn("cancel-in-progress: false", publish)
        self.assertNotIn("matrix:", publish)
        self.assertEqual(publish.count("runs-on: ubuntu-latest"), 1)
        self.assertIn('python-version: "3.13"', publish)

    def test_release_checks_out_exact_tag_and_passes_release_inputs_only_to_publisher(self) -> None:
        publish = self._workflow("publish.yml")

        self.assertIn("ref: ${{ github.ref }}", publish)
        self.assertIn("RELEASE_TAG: ${{ github.ref_name }}", publish)
        self.assertIn("FORGEJO_PACKAGE_USERNAME: ${{ secrets.FORGEJO_PACKAGE_USERNAME }}", publish)
        self.assertIn("FORGEJO_PACKAGE_TOKEN: ${{ secrets.FORGEJO_PACKAGE_TOKEN }}", publish)
        self.assertRegex(publish, r"python (?:-m scripts\.publish_forgejo|scripts/publish_forgejo\.py)")

        owner, steps = self._owner_steps(publish)
        keys = {"RELEASE_TAG", "FORGEJO_PACKAGE_USERNAME", "FORGEJO_PACKAGE_TOKEN"}
        occurrences = self._find_key_occurrences(publish, keys)
        expected_publish_steps = {
            step["name"] for step in steps if "Publish to Forgejo" in (step["name"] or "")
        }
        self.assertEqual(len(expected_publish_steps), 1)
        publish_step_name = next(iter(expected_publish_steps))
        for key in keys:
            self.assertTrue(occurrences[key], f"missing {key} key in workflow")
            for line_no, line in occurrences[key]:
                self.assertEqual(
                    owner[line_no],
                    publish_step_name,
                    f"{key} appears outside publish step: {line}",
                )
                self.assertIn(key, steps[[step["name"] for step in steps].index(publish_step_name)]["env"])

        for step in steps:
            if step["name"] == publish_step_name:
                continue
            for key in keys:
                self.assertNotIn(key, step["env"], f"{key} leaked into step '{step.get('name')}'")

        publisher_step = next(step for step in steps if step["name"] == publish_step_name)
        publisher_match = re.search(r"python (?:-m scripts\.publish_forgejo|scripts/publish_forgejo\.py)", publish)
        assert publisher_match is not None
        lines = publish.splitlines()
        publisher_block = "\n".join(lines[publisher_step["start"] : publisher_step["end"]])
        self.assertIn("RELEASE_TAG", publisher_block)
        self.assertIn("FORGEJO_PACKAGE_USERNAME", publisher_block)
        self.assertIn("FORGEJO_PACKAGE_TOKEN", publisher_block)

    def test_workflows_use_fixed_public_endpoint_and_no_insecure_or_git_mutating_behavior(self) -> None:
        publish = self._workflow("publish.yml")

        self.assertIn("https://forgejo.alexlab.nl/api/packages/public/pypi", publish)
        for forbidden in (
            "http://",
            "--skip-existing",
            "--repository-url ${{",
            "git commit",
            "git tag",
            "git push",
            "git reset",
            "git force",
            "GITHUB_TOKEN",
        ):
            self.assertNotIn(forbidden, publish)


if __name__ == "__main__":
    unittest.main()
