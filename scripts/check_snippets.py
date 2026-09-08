#!/usr/bin/env python3
"""Syntax-check fenced code blocks in Doctrine's Markdown guides.

Extracts fenced blocks by their info string and hands each to the natural
syntax checker for that language:

    python              py_compile (in-process ``compile``)
    javascript / js     node --check
    typescript / ts     tsc --noEmit
    bash / sh / shell   bash -n
    json                jq (falls back to Python's json module)
    yaml                PyYAML
    go                  go vet, only for complete ``package main`` files

Blocks that are deliberately incomplete are skipped: see SKIP_MARKERS and
``looks_like_fragment``. A checker that is not installed is reported as
"skipped (no toolchain)", never as a pass.

Usage:
    python3 scripts/check_snippets.py                   # fail on any error
    python3 scripts/check_snippets.py --warn            # always exit 0
    python3 scripts/check_snippets.py --summary FILE    # append Markdown report
    python3 scripts/check_snippets.py --lang python     # restrict languages
    python3 scripts/check_snippets.py guides/languages  # restrict paths
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Vendored or generated trees are never Doctrine's to fix.
EXCLUDED_DIRS = {".git", "node_modules", "reference", ".venv", "venv", "dist", "build"}

# Info strings mapped onto a single canonical checker name.
LANGUAGE_ALIASES = {
    "python": "python",
    "python3": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "tsx": "typescript",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "console": None,  # transcript, not a script
    "json": "json",
    "jsonc": None,  # comments are legal here, jq would reject them
    "yaml": "yaml",
    "yml": "yaml",
    "go": "go",
    "golang": "go",
}

# An author can opt a single block out with a trailing marker on the fence,
# e.g. ```python no-check
SKIP_MARKERS = {"no-check", "nocheck", "skip", "fragment", "pseudo", "pseudocode"}

# Template placeholders that are not valid source in any language.
PLACEHOLDER_RE = re.compile(
    r"""
      \{\{ | \}\}                       # mustache/Jinja templating
    | ^\s*\.\.\.\s*$                     # a bare ellipsis line
    | \.\.\.\s*$                         # a trailing ellipsis
    | [\[\{]\s*\.\.\.\s*[\]\}]           # [...] or {...} elision inside data
    | [\s,:]\.\.\.[\s,\]\}]              # ... used as an inline elision
    | <[A-Z_]{3,}>                       # <PLACEHOLDER> tokens
    """,
    re.MULTILINE | re.VERBOSE,
)

# A ``json`` block that carries line comments is really JSONC (tsconfig.json
# and friends). jq would reject it, so it is skipped rather than reported.
JSONC_COMMENT_RE = re.compile(r"^\s*(//|/\*)", re.MULTILINE)

FENCE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n`]*)\n"
    r"(?P<body>.*?)"
    r"^(?P=indent)(?P=fence)[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


@dataclass(frozen=True)
class Snippet:
    """One fenced block, located precisely enough to fix."""

    path: Path
    line: int
    language: str
    code: str

    def where(self) -> str:
        try:
            location = self.path.resolve().relative_to(PROJECT_ROOT)
        except ValueError:
            location = self.path
        return f"{location}:{self.line}"


@dataclass
class Result:
    checked: Counter = field(default_factory=Counter)
    skipped: Counter = field(default_factory=Counter)
    unavailable: Counter = field(default_factory=Counter)
    failures: list[tuple[Snippet, str]] = field(default_factory=list)

    @property
    def total_checked(self) -> int:
        return sum(self.checked.values())


def iter_markdown(paths: Sequence[Path]) -> Iterator[Path]:
    """Yield every Markdown file under ``paths``, excluding vendored trees."""
    for base in paths:
        if base.is_file():
            if base.suffix.lower() == ".md":
                yield base
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
            for name in sorted(filenames):
                if name.lower().endswith(".md"):
                    yield Path(dirpath) / name


def extract(path: Path) -> Iterator[Snippet]:
    """Yield the checkable fenced blocks in ``path``."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    for match in FENCE_RE.finditer(content):
        info = match.group("info").strip()
        if not info:
            continue

        tokens = re.split(r"[\s,]+", info.lower())
        tag = tokens[0].lstrip("{.").rstrip("}")
        if SKIP_MARKERS.intersection(tokens[1:]):
            continue

        language = LANGUAGE_ALIASES.get(tag)
        if language is None:
            continue

        body = match.group("body")
        if not body.strip():
            continue

        line = content.count("\n", 0, match.start()) + 1
        yield Snippet(path=path, line=line, language=language, code=body)


def looks_like_fragment(snippet: Snippet) -> bool:
    """True when a block is illustrative prose-in-code rather than a program."""
    if PLACEHOLDER_RE.search(snippet.code):
        return True
    if snippet.language == "json" and JSONC_COMMENT_RE.search(snippet.code):
        return True
    if snippet.language == "go":
        # go vet needs a whole compilation unit whose imports resolve. A
        # snippet that pulls in a module cannot be vetted offline.
        if not re.search(r"^package\s+main\b", snippet.code, re.MULTILINE):
            return True
        return not _go_imports_are_stdlib(snippet.code)
    return False


GO_IMPORT_BLOCK_RE = re.compile(r"^import\s*\(\s*$(?P<body>.*?)^\)\s*$", re.DOTALL | re.MULTILINE)
GO_IMPORT_LINE_RE = re.compile(r'^\s*(?:[\w.]+\s+)?"(?P<path>[^"]+)"', re.MULTILINE)
GO_SINGLE_IMPORT_RE = re.compile(r'^import\s+(?:[\w.]+\s+)?"(?P<path>[^"]+)"', re.MULTILINE)


def _go_stdlib_packages() -> frozenset[str]:
    """The importable standard-library package paths of the local Go toolchain."""
    cached = getattr(_go_stdlib_packages, "_cache", None)
    if cached is not None:
        return cached
    packages: frozenset[str] = frozenset()
    if shutil.which("go"):
        proc = _run(["go", "list", "std"])
        if proc.returncode == 0:
            packages = frozenset(line.strip() for line in proc.stdout.splitlines() if line.strip())
    _go_stdlib_packages._cache = packages  # type: ignore[attr-defined]
    return packages


def _go_imports_are_stdlib(code: str) -> bool:
    paths: list[str] = []
    for block in GO_IMPORT_BLOCK_RE.finditer(code):
        paths.extend(m.group("path") for m in GO_IMPORT_LINE_RE.finditer(block.group("body")))
    paths.extend(m.group("path") for m in GO_SINGLE_IMPORT_RE.finditer(code))
    if not paths:
        return True
    stdlib = _go_stdlib_packages()
    if not stdlib:
        return False
    return all(path in stdlib for path in paths)


def _run(argv: Sequence[str], *, stdin: str | None = None, cwd: str | None = None):
    return subprocess.run(
        argv,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=120,
        check=False,
    )


# Flags shared by every tsc invocation: parse modern syntax, ignore libraries.
_TSC_BASE_FLAGS = (
    "--skipLibCheck",
    "--target",
    "es2022",
    "--module",
    "esnext",
    "--moduleResolution",
    "bundler",
)


def _tidy(text: str, limit: int = 400) -> str:
    collapsed = " ".join(text.split())
    return collapsed[:limit] + ("…" if len(collapsed) > limit else "")


def check_python(snippet: Snippet) -> str | None:
    # Suppress SyntaxWarning (e.g. invalid escape sequences): they are style
    # signals, not syntax errors, and would otherwise leak onto stderr.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            compile(snippet.code, snippet.where(), "exec")
        except (SyntaxError, ValueError) as exc:
            return _tidy(str(exc))
    return None


def _check_with_tempfile(
    snippet: Snippet, suffix: str, argv: Callable[[str], Sequence[str]]
) -> str | None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / f"snippet{suffix}"
        target.write_text(snippet.code, encoding="utf-8")
        proc = _run(argv(str(target)), cwd=tmp)
        if proc.returncode == 0:
            return None
        noise = (proc.stderr or "") + (proc.stdout or "")
        # Compiler messages carry the throwaway path; the reader only needs
        # the message and the line inside the snippet. Tools report either the
        # given path or its realpath, so both are stripped.
        for literal in (str(target.resolve()), str(target), str(Path(tmp).resolve()), tmp):
            noise = noise.replace(literal, "snippet")
    return _tidy(re.sub(r"(\.\./)+", "", noise))


def check_javascript(snippet: Snippet) -> str | None:
    plain = _check_with_tempfile(snippet, ".mjs", lambda p: ["node", "--check", p])
    if plain is None:
        return None
    # A ```javascript block may well be JSX, which node cannot parse. Retry
    # through the TypeScript parser before calling it a defect.
    tsc = _typescript_binary()
    if tsc is None:
        return plain
    jsx = _check_with_tempfile(
        snippet,
        ".jsx",
        lambda p: [
            *tsc,
            "--noEmit",
            "--noCheck",
            "--allowJs",
            "--jsx",
            "preserve",
            *_TSC_BASE_FLAGS,
            p,
        ],
    )
    return None if jsx is None else plain


def check_typescript(snippet: Snippet) -> str | None:
    tsc = _typescript_binary()
    if tsc is None:
        return None
    # --noCheck parses and reports syntax errors but skips type checking, which
    # a self-contained documentation snippet can never satisfy: its imports and
    # ambient types are not present.
    plain = _check_with_tempfile(
        snippet,
        ".ts",
        lambda p: [*tsc, "--noEmit", "--noCheck", *_TSC_BASE_FLAGS, p],
    )
    if plain is None:
        return None
    jsx = _check_with_tempfile(
        snippet,
        ".tsx",
        lambda p: [*tsc, "--noEmit", "--noCheck", "--jsx", "preserve", *_TSC_BASE_FLAGS, p],
    )
    return None if jsx is None else plain


def check_bash(snippet: Snippet) -> str | None:
    proc = _run(["bash", "-n"], stdin=snippet.code)
    return None if proc.returncode == 0 else _tidy(proc.stderr)


def check_json(snippet: Snippet) -> str | None:
    if shutil.which("jq"):
        proc = _run(["jq", "empty"], stdin=snippet.code)
        return None if proc.returncode == 0 else _tidy(proc.stderr)
    try:
        json.loads(snippet.code)
    except json.JSONDecodeError as exc:
        return _tidy(str(exc))
    return None


def check_yaml(snippet: Snippet) -> str | None:
    import yaml  # imported lazily so the other checkers work without PyYAML

    class TolerantLoader(yaml.SafeLoader):
        """Parses application-specific tags such as ESPHome's ``!secret``."""

    TolerantLoader.add_multi_constructor("", lambda loader, suffix, node: None)

    try:
        list(yaml.load_all(snippet.code, Loader=TolerantLoader))
    except yaml.YAMLError as exc:
        return _tidy(str(exc))
    return None


def check_go(snippet: Snippet) -> str | None:
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "go.mod").write_text("module snippet\n\ngo 1.24\n", encoding="utf-8")
        (Path(tmp) / "main.go").write_text(snippet.code, encoding="utf-8")
        env = dict(os.environ, GOFLAGS="-mod=mod", GOWORK="off", GOPROXY="off")
        proc = subprocess.run(
            ["go", "vet", "./..."],
            capture_output=True,
            text=True,
            cwd=tmp,
            env=env,
            timeout=180,
            check=False,
        )
    return None if proc.returncode == 0 else _tidy(proc.stderr or proc.stdout)


CHECKERS: dict[str, Callable[[Snippet], str | None]] = {
    "python": check_python,
    "javascript": check_javascript,
    "typescript": check_typescript,
    "bash": check_bash,
    "json": check_json,
    "yaml": check_yaml,
    "go": check_go,
}


def _typescript_binary() -> list[str] | None:
    local = PROJECT_ROOT / "node_modules" / ".bin" / "tsc"
    if local.is_file():
        return [str(local)]
    found = shutil.which("tsc")
    return [found] if found else None


def toolchain_available(language: str) -> bool:
    """Whether the checker for ``language`` can actually run here."""
    if language == "python":
        return True
    if language == "javascript":
        return shutil.which("node") is not None
    if language == "typescript":
        return _typescript_binary() is not None
    if language == "bash":
        return shutil.which("bash") is not None
    if language == "json":
        return True
    if language == "go":
        return shutil.which("go") is not None
    if language == "yaml":
        try:
            import yaml  # noqa: F401
        except ImportError:
            return False
        return True
    return False


def check(snippets: Iterable[Snippet], languages: set[str] | None = None) -> Result:
    result = Result()
    availability: dict[str, bool] = {}

    for snippet in snippets:
        if languages and snippet.language not in languages:
            continue
        if looks_like_fragment(snippet):
            result.skipped[snippet.language] += 1
            continue

        if snippet.language not in availability:
            availability[snippet.language] = toolchain_available(snippet.language)
        if not availability[snippet.language]:
            result.unavailable[snippet.language] += 1
            continue

        error = CHECKERS[snippet.language](snippet)
        result.checked[snippet.language] += 1
        if error:
            result.failures.append((snippet, error))

    return result


def render(result: Result) -> str:
    lines = ["## Snippet syntax check", ""]
    if result.total_checked:
        lines.append("| Language | Checked | Failed | Skipped (fragment) |")
        lines.append("| --- | --: | --: | --: |")
        failed_by_lang = Counter(s.language for s, _ in result.failures)
        for language in sorted(set(result.checked) | set(result.skipped)):
            lines.append(
                f"| {language} | {result.checked[language]} | "
                f"{failed_by_lang[language]} | {result.skipped[language]} |"
            )
        lines.append("")
    else:
        lines.append("No checkable snippets found.")
        lines.append("")

    if result.unavailable:
        missing = ", ".join(f"{lang} ({n})" for lang, n in sorted(result.unavailable.items()))
        lines.append(f"Skipped for want of a toolchain: {missing}.")
        lines.append("")

    if result.failures:
        lines.append(f"### {len(result.failures)} failing snippets")
        lines.append("")
        for snippet, error in result.failures:
            lines.append(f"- `{snippet.where()}` ({snippet.language}): {error}")
        lines.append("")
    else:
        lines.append("All checked snippets parse cleanly.")
        lines.append("")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths", nargs="*", type=Path, help="files or directories (default: repository root)"
    )
    parser.add_argument("--warn", action="store_true", help="report failures but exit 0")
    parser.add_argument("--summary", type=Path, help="append a Markdown report to this file")
    parser.add_argument(
        "--lang",
        action="append",
        choices=sorted(CHECKERS),
        help="restrict to one language (repeatable)",
    )
    args = parser.parse_args(argv)

    paths = args.paths or [PROJECT_ROOT]
    snippets = (s for path in iter_markdown(paths) for s in extract(path))
    result = check(snippets, languages=set(args.lang) if args.lang else None)

    report = render(result)
    print(report)

    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(report + "\n")

    if result.failures and not args.warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
