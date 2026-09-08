#!/usr/bin/env python3
"""Unit tests for scripts/validate_versions.py.

Run with:
    python3 -m unittest discover scripts
    python3 -m unittest scripts.test_validate_versions
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_versions as vv  # noqa: E402


class NormaliseRepoTests(unittest.TestCase):
    def test_https_url(self):
        self.assertEqual(
            vv.normalise_repo("https://github.com/astral-sh/ruff-pre-commit"),
            "astral-sh/ruff-pre-commit",
        )

    def test_https_url_with_git_suffix(self):
        self.assertEqual(vv.normalise_repo("https://github.com/psf/black.git"), "psf/black")

    def test_trailing_slash(self):
        self.assertEqual(vv.normalise_repo("https://github.com/psf/black/"), "psf/black")

    def test_scp_style_ssh_keeps_owner(self):
        # The previous implementation returned "tool", losing the owner.
        self.assertEqual(vv.normalise_repo("git@github.com:owner/tool.git"), "owner/tool")

    def test_ssh_protocol_url(self):
        self.assertEqual(vv.normalise_repo("ssh://git@github.com/owner/tool.git"), "owner/tool")

    def test_non_github_host(self):
        self.assertEqual(vv.normalise_repo("https://gitlab.com/group/project"), "group/project")

    def test_quoted_url(self):
        self.assertEqual(vv.normalise_repo('"https://github.com/psf/black"'), "psf/black")

    def test_bare_owner_repo(self):
        self.assertEqual(vv.normalise_repo("psf/black"), "psf/black")

    def test_two_owners_are_distinct(self):
        # Suffix matching used to conflate these; owner-preserving keys do not.
        self.assertNotEqual(
            vv.normalise_repo("https://github.com/dnephin/pre-commit-golang"),
            vv.normalise_repo("https://github.com/TekWizely/pre-commit-golang"),
        )


class ParseCanonicalTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        tmp = Path(self.tmpdir.name) / ".pre-commit-config.yaml"
        tmp.write_text(text, encoding="utf-8")
        return tmp

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_reads_active_entries(self):
        path = self._write(
            "repos:\n"
            "  - repo: https://github.com/psf/black\n"
            "    rev: 24.1.0\n"
            "    hooks:\n"
            "      - id: black\n"
        )
        self.assertEqual(vv.parse_canonical(path), {"psf/black": "24.1.0"})

    def test_reads_commented_entries(self):
        path = self._write(
            "repos:\n"
            "  # - repo: https://github.com/psf/black\n"
            "  #   rev: 24.1.0\n"
            "  #   hooks:\n"
            "  #     - id: black\n"
        )
        self.assertEqual(vv.parse_canonical(path), {"psf/black": "24.1.0"})

    def test_quoted_rev_is_unquoted(self):
        path = self._write("  - repo: https://github.com/psf/black\n    rev: \"24.1.0\"\n")
        self.assertEqual(vv.parse_canonical(path), {"psf/black": "24.1.0"})

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            vv.parse_canonical(Path(self.tmpdir.name) / "absent.yaml")

    def test_repo_without_rev_is_ignored(self):
        path = self._write("  - repo: local\n    hooks:\n      - id: something\n")
        self.assertEqual(vv.parse_canonical(path), {})


class CollectReferencesTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.root = Path(self.tmpdir.name)

    def _guide(self, relative: str, body: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_finds_pair_in_fenced_block(self):
        self._guide(
            "guides/languages/python.md",
            "# Python\n\n```yaml\nrepos:\n"
            "  - repo: https://github.com/psf/black\n    rev: 24.1.0\n```\n",
        )
        refs = vv.collect_references(self.root)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].repo, "psf/black")
        self.assertEqual(refs[0].rev, "24.1.0")

    def test_scans_agents_and_configs(self):
        self._guide(
            "agents/code/reviewer.md",
            "- repo: https://github.com/psf/black\n  rev: 24.1.0\n",
        )
        self._guide(
            "configs/editorconfig/README.md",
            "- repo: https://github.com/psf/isort\n  rev: 5.13.2\n",
        )
        repos = {r.repo for r in vv.collect_references(self.root)}
        self.assertEqual(repos, {"psf/black", "psf/isort"})

    def test_skips_reference_tree(self):
        self._guide(
            "guides/reference/vendored.md",
            "- repo: https://github.com/psf/black\n  rev: 0.0.0\n",
        )
        self.assertEqual(vv.collect_references(self.root), [])

    def test_tolerates_intervening_key(self):
        self._guide(
            "guides/x.md",
            "- repo: https://github.com/psf/black\n  # comment key\n  rev: 24.1.0\n",
        )
        refs = vv.collect_references(self.root)
        self.assertEqual([r.rev for r in refs], ["24.1.0"])

    def test_records_line_number(self):
        self._guide("guides/x.md", "intro\n\n- repo: https://github.com/psf/black\n  rev: 24.1.0\n")
        self.assertEqual(vv.collect_references(self.root)[0].line, 3)

    def test_non_markdown_yaml_is_scanned(self):
        self._guide(
            "configs/ansible/extra.yaml",
            "- repo: https://github.com/psf/black\n  rev: 24.1.0\n",
        )
        self.assertEqual(len(vv.collect_references(self.root)), 1)

    def test_unrelated_extension_is_ignored(self):
        self._guide("configs/thing.json", "- repo: https://github.com/psf/black\n  rev: 24.1.0\n")
        self.assertEqual(vv.collect_references(self.root), [])


class EvaluateTests(unittest.TestCase):
    def _ref(self, repo: str, rev: str) -> vv.Reference:
        return vv.Reference(path=Path("guides/x.md"), line=1, repo=repo, rev=rev)

    def test_matching_version_is_clean(self):
        refs = [self._ref("psf/black", "24.1.0")]
        mismatches, unknown = vv.evaluate(refs, {"psf/black": "24.1.0"})
        self.assertEqual(mismatches, [])
        self.assertEqual(unknown, [])

    def test_mismatch_is_reported(self):
        refs = [self._ref("psf/black", "23.0.0")]
        mismatches, unknown = vv.evaluate(refs, {"psf/black": "24.1.0"})
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["found"], "23.0.0")
        self.assertEqual(mismatches[0]["expected"], "24.1.0")
        self.assertEqual(unknown, [])

    def test_undocumented_unknown_tool(self):
        _, unknown = vv.evaluate([self._ref("who/what", "1.0")], {"psf/black": "24.1.0"})
        self.assertEqual(len(unknown), 1)
        self.assertFalse(unknown[0]["documented"])

    def test_documented_unknown_tool(self):
        repo = next(iter(vv.KNOWN_UNPINNED))
        _, unknown = vv.evaluate([self._ref(repo, "1.0")], {"psf/black": "24.1.0"})
        self.assertTrue(unknown[0]["documented"])


class MainExitCodeTests(unittest.TestCase):
    @staticmethod
    def _run(argv: list[str]) -> tuple[int, str]:
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = vv.main(argv)
        return code, buffer.getvalue()

    def test_repository_passes_without_strict(self):
        code, _ = self._run([])
        self.assertEqual(code, 0)

    def test_repository_passes_with_strict(self):
        code, _ = self._run(["--strict"])
        self.assertEqual(code, 0)

    def test_json_output_is_parseable(self):
        import json

        _, output = self._run(["--json"])
        payload = json.loads(output)
        self.assertIn("mismatches", payload)
        self.assertIn("unknown", payload)
        self.assertGreater(payload["canonical_count"], 0)

    def test_strict_fails_on_undocumented_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guide = root / "guides" / "x.md"
            guide.parent.mkdir(parents=True)
            guide.write_text(
                "- repo: https://github.com/nobody/nothing\n  rev: 9.9.9\n",
                encoding="utf-8",
            )
            self.assertEqual(self._run(["--strict", "--root", str(root)])[0], 1)
            self.assertEqual(self._run(["--root", str(root)])[0], 0)

    def test_mismatch_fails_without_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guide = root / "guides" / "x.md"
            guide.parent.mkdir(parents=True)
            canonical = vv.parse_canonical(vv.CONFIG_FILE)
            repo, rev = next(iter(canonical.items()))
            self.assertNotEqual(rev, "0.0.0-not-a-real-version")
            guide.write_text(
                f"- repo: https://github.com/{repo}\n  rev: 0.0.0-not-a-real-version\n",
                encoding="utf-8",
            )
            code, output = self._run(["--root", str(root)])
            self.assertEqual(code, 1)
            self.assertIn("MISMATCH", output)


if __name__ == "__main__":
    unittest.main()
