#!/usr/bin/env python3
"""Check that tool versions quoted in Doctrine match the canonical config.

The canonical source is ``configs/pre-commit/.pre-commit-config.yaml``. Every
``repo:``/``rev:`` pair written into a guide, agent brief or shipped config
MUST agree with it, so a reader who copies a snippet gets the version Doctrine
has actually reviewed.

Scanned surfaces:
    guides/**    the style guides themselves
    agents/**    agent briefs, which also carry copy-and-paste config
    configs/**   shipped configuration, excluding the canonical file itself

Exit codes:
    0   every comparable reference agrees with the canonical config
    1   at least one mismatch, or --strict and at least one undocumented tool
    2   the canonical config is missing or unparseable

Usage:
    python3 scripts/validate_versions.py
    python3 scripts/validate_versions.py --strict
    python3 scripts/validate_versions.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "configs/pre-commit/.pre-commit-config.yaml"

# Every tree that may quote a pinned tool version.
SCAN_DIRS = ("guides", "agents", "configs")

# Directories never scanned: vendored upstream text and generated output.
EXCLUDED_DIRS = {".git", "node_modules", "reference", ".venv", "venv", "dist", "build"}

# Tools whose canonical identity differs from the repository slug.
#   key   -> owner/repo as written in a guide
#   value -> owner/repo as written in the canonical config
ALIASES: dict[str, str] = {}

# Repositories that appear on a scanned surface on purpose but are not pinned
# in the canonical config. Listing them documents the omission instead of
# hiding it, and keeps --strict usable. Remove an entry once the tool is
# adopted canonically.
KNOWN_UNPINNED: dict[str, str] = {
    "ansible/ansible-lint": "Ansible guide only; no canonical Ansible pin yet",
    "adrienverge/yamllint": "Ansible guide only; no canonical YAML pin yet",
    "compilerla/conventional-pre-commit": "commit-message guide illustration",
    "dnephin/pre-commit-golang": "superseded by golangci-lint in the canonical config",
    "jendrikseipp/vulture": "optional Python dead-code hook",
    "returntocorp/semgrep": "security guide illustration (former organisation name)",
    "semgrep/semgrep": "security guide illustration",
    "thibaudcolas/pre-commit-stylelint": "optional CSS hook",
}

# ``  - repo: https://github.com/owner/name``, optionally commented out.
REPO_RE = re.compile(r"^\s*(?:#\s*)?-?\s*repo:\s*(?P<url>\S+)\s*$")
REV_RE = re.compile(r"^\s*(?:#\s*)?rev:\s*(?P<rev>\S+)\s*$")

# A ``repo:``/``rev:`` pair inside prose or a fenced block. pre-commit always
# writes them close together; at most two intervening comment or key lines are
# tolerated.
PAIR_RE = re.compile(
    r"^[ \t]*(?:#[ \t]*)?-?[ \t]*repo:[ \t]*(?P<url>\S+)[ \t]*\n"
    r"(?:^[ \t]*(?:#.*|(?:#[ \t]*)?[a-z_]+:[ \t]*\S*[ \t]*)\n){0,2}?"
    r"^[ \t]*(?:#[ \t]*)?rev:[ \t]*(?P<rev>\S+)[ \t]*$",
    re.MULTILINE,
)

# A bare hostname followed by a path, used to decide whether the leading
# segment of a normalised URL is a host or already the owner.
HOST_RE = re.compile(r"^[\w.-]+\.[\w.-]+/")


def normalise_repo(url: str) -> str:
    """Reduce a repository URL to ``owner/name``.

    Handles HTTPS, SCP-style SSH (``git@github.com:owner/name.git``) and
    ``ssh://`` forms, and keeps the owner. The previous implementation dropped
    it, so ``owner/tool`` collapsed to ``tool`` and could match the wrong
    project by suffix.
    """
    url = url.strip().strip("\"'")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    url = url.rstrip("/")

    scp = re.match(r"^(?:[\w.-]+@)?[\w.-]+:(?P<path>[^/].*)$", url)
    if "://" not in url and scp:
        url = scp.group("path")
    else:
        url = re.sub(r"^[a-z+]+://", "", url)
        url = re.sub(r"^[^/@]+@", "", url)
        if HOST_RE.match(url):
            url = url.split("/", 1)[1]

    parts = [p for p in url.split("/") if p]
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return "/".join(parts)


def canonical_key(repo: str) -> str:
    return ALIASES.get(repo, repo)


@dataclass(frozen=True)
class Reference:
    path: Path
    line: int
    repo: str
    rev: str

    def where(self) -> str:
        try:
            return f"{self.path.resolve().relative_to(PROJECT_ROOT)}:{self.line}"
        except ValueError:
            return f"{self.path}:{self.line}"


def parse_canonical(config_path: Path) -> dict[str, str]:
    """Read ``repo``/``rev`` pairs from the canonical pre-commit config.

    Commented-out entries count: Doctrine keeps optional hooks commented but
    still treats their pins as canonical.
    """
    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    pins: dict[str, str] = {}
    current: str | None = None
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        repo_match = REPO_RE.match(raw)
        if repo_match:
            current = canonical_key(normalise_repo(repo_match.group("url")))
            continue
        if current is None:
            continue
        rev_match = REV_RE.match(raw)
        if rev_match:
            pins[current] = rev_match.group("rev").strip("\"'")
            current = None
    return pins


def iter_files(root: Path, dirs: Sequence[str] = SCAN_DIRS) -> Iterator[Path]:
    """Yield every version-bearing file on the scanned surfaces."""
    for name in dirs:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if EXCLUDED_DIRS.intersection(relative.parts):
                continue
            if path.suffix.lower() in {".md", ".yaml", ".yml", ".template"}:
                yield path


def collect_references(
    root: Path = PROJECT_ROOT, dirs: Sequence[str] = SCAN_DIRS
) -> list[Reference]:
    """Find every ``repo``/``rev`` pair on the scanned surfaces."""
    canonical = CONFIG_FILE.resolve()
    references: list[Reference] = []

    for path in iter_files(root, dirs):
        if path.resolve() == canonical:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in PAIR_RE.finditer(content):
            references.append(
                Reference(
                    path=path,
                    line=content.count("\n", 0, match.start()) + 1,
                    repo=canonical_key(normalise_repo(match.group("url"))),
                    rev=match.group("rev").strip("\"'"),
                )
            )
    return references


def evaluate(
    references: Iterable[Reference], canonical: dict[str, str]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Split references into mismatches and references outside the canonical set."""
    mismatches: list[dict[str, object]] = []
    unknown: list[dict[str, object]] = []

    for ref in references:
        expected = canonical.get(ref.repo)
        if expected is None:
            unknown.append(
                {
                    "location": ref.where(),
                    "repo": ref.repo,
                    "rev": ref.rev,
                    "reason": KNOWN_UNPINNED.get(ref.repo, "not present in the canonical config"),
                    "documented": ref.repo in KNOWN_UNPINNED,
                }
            )
        elif ref.rev != expected:
            mismatches.append(
                {
                    "location": ref.where(),
                    "repo": ref.repo,
                    "found": ref.rev,
                    "expected": expected,
                }
            )

    return mismatches, unknown


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when a scanned surface references a tool absent from the canonical config",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="repository root to scan")
    args = parser.parse_args(argv)

    try:
        canonical = parse_canonical(CONFIG_FILE)
    except FileNotFoundError:
        print(f"ERROR: canonical config not found at {CONFIG_FILE}", file=sys.stderr)
        return 2

    if not canonical:
        print(f"ERROR: no repo/rev pairs parsed from {CONFIG_FILE}", file=sys.stderr)
        return 2

    references = collect_references(args.root)
    mismatches, unknown = evaluate(references, canonical)
    undocumented = [u for u in unknown if not u["documented"]]

    if args.json:
        json.dump(
            {
                "canonical_count": len(canonical),
                "reference_count": len(references),
                "mismatches": mismatches,
                "unknown": unknown,
                "strict": args.strict,
            },
            sys.stdout,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
    else:
        rel = CONFIG_FILE.relative_to(PROJECT_ROOT)
        print(f"Canonical config: {rel} ({len(canonical)} pinned tools)")
        print(f"Scanned {', '.join(SCAN_DIRS)}: {len(references)} repo/rev references")
        print()

        for item in mismatches:
            print(f"MISMATCH {item['location']}")
            print(f"  tool:     {item['repo']}")
            print(f"  found:    {item['found']}")
            print(f"  expected: {item['expected']}")

        for item in unknown:
            level = "UNPINNED" if item["documented"] else "UNKNOWN "
            print(f"{level} {item['location']}  {item['repo']}@{item['rev']} — {item['reason']}")

        print()
        if mismatches:
            print(f"FAILURE: {len(mismatches)} version mismatches.")
        else:
            print("OK: every comparable reference matches the canonical configuration.")
        if unknown:
            print(
                f"{len(unknown)} references are outside the canonical set "
                f"({len(undocumented)} undocumented)."
            )
        if args.strict and undocumented:
            print(
                "FAILURE: --strict rejects undocumented tools. "
                "Pin them, or record them in KNOWN_UNPINNED."
            )

    if mismatches:
        return 1
    if args.strict and undocumented:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
