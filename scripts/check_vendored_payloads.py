#!/usr/bin/env python3
"""Guard the verbatim third-party payloads under reference/.

Vendored payloads are upstream documents. They are not Doctrine prose and MUST
NOT be reformatted by markdownlint, prettier or any other auto-fixer: commit
b6f870a stripped the whitespace after 474 list markers in the Google guides,
which stopped them rendering as lists at all.

Two checks run:

1. Checksum: every payload must match reference/CHECKSUMS.sha256. Any edit,
   including a deliberate erratum or a vendor resync, must regenerate the file
   with --update so the change is visible in review.
2. Rendering: no Markdown payload may contain an ordered-list marker with no
   space after it (``1.Foo``), the exact signature of the b6f870a damage.
   Bullet damage (``*Foo``) is not pattern-matched because emphasis at the
   start of a line is indistinguishable from it; the checksum covers that case.

Usage:
    python3 scripts/check_vendored_payloads.py
    python3 scripts/check_vendored_payloads.py --update
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE_DIR = PROJECT_ROOT / "reference"
CHECKSUM_FILE = REFERENCE_DIR / "CHECKSUMS.sha256"

# Upstream families vendored verbatim. reference/security holds Doctrine-built
# data files and is checked by .github/workflows/check-security-refs.yml.
VENDOR_DIRS = (
    "airbnb",
    "google",
    "holywell",
    "ietf",
    "rubocop",
    "rust",
    "shopify",
    "uber",
)

# Doctrine-owned files that live beside the payloads.
EXCLUDED_NAMES = {".markdownlint.json"}

BROKEN_ORDERED_MARKER = re.compile(r"^ {0,3}\d+[.)][^\s\d]")
FENCE = ("```", "~~~")


def payloads() -> list[Path]:
    """Return every vendored payload path, sorted by repository-relative path."""
    found = []
    for vendor in VENDOR_DIRS:
        for path in sorted((REFERENCE_DIR / vendor).rglob("*")):
            if path.is_file() and path.name not in EXCLUDED_NAMES:
                found.append(path)
    return sorted(found, key=lambda p: p.relative_to(PROJECT_ROOT).as_posix())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checksums() -> None:
    lines = [
        "# SHA-256 of every verbatim vendored payload under reference/.",
        "# Regenerate with: python3 scripts/check_vendored_payloads.py --update",
        "# Local corrections to upstream text are recorded in reference/ERRATA.md.",
    ]
    for path in payloads():
        lines.append(f"{digest(path)}  {path.relative_to(PROJECT_ROOT).as_posix()}")
    CHECKSUM_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_checksums() -> dict[str, str]:
    recorded = {}
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        checksum, _, name = line.partition("  ")
        recorded[name] = checksum
    return recorded


def check_checksums() -> list[str]:
    if not CHECKSUM_FILE.exists():
        return [f"{CHECKSUM_FILE.relative_to(PROJECT_ROOT)} is missing"]

    recorded = read_checksums()
    current = {
        path.relative_to(PROJECT_ROOT).as_posix(): digest(path) for path in payloads()
    }

    problems = []
    for name in sorted(set(recorded) - set(current)):
        problems.append(f"{name}: recorded but no longer present")
    for name in sorted(set(current) - set(recorded)):
        problems.append(f"{name}: present but not recorded")
    for name in sorted(set(current) & set(recorded)):
        if current[name] != recorded[name]:
            problems.append(
                f"{name}: content changed "
                f"(recorded {recorded[name][:12]}, found {current[name][:12]})"
            )
    return problems


def check_list_markers() -> list[str]:
    problems = []
    for path in payloads():
        if path.suffix != ".md":
            continue
        in_fence = False
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.lstrip().startswith(FENCE):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if BROKEN_ORDERED_MARKER.match(line):
                name = path.relative_to(PROJECT_ROOT).as_posix()
                problems.append(
                    f"{name}:{number}: ordered-list marker with no space: {line[:60]!r}"
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite reference/CHECKSUMS.sha256 from the working tree",
    )
    args = parser.parse_args()

    if args.update:
        write_checksums()
        print(f"Wrote {CHECKSUM_FILE.relative_to(PROJECT_ROOT)}")
        return 0

    problems = check_checksums() + check_list_markers()
    if problems:
        print("Vendored payload check failed:")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nVendored payloads are verbatim upstream documents. Do not run "
            "formatters over reference/.\nRecord deliberate corrections in "
            "reference/ERRATA.md and rerun with --update."
        )
        return 1

    print(f"Vendored payload check passed: {len(payloads())} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
