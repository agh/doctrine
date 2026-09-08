#!/usr/bin/env python3
"""Verify that vendored third-party files still match their upstream payloads.

Vendored material under reference/ is stored byte-for-byte as published
upstream. A formatter run (commit b6f870a) once rewrote list markers inside the
Google style guides and silently corrupted them. This script guards against a
repeat by checking every file listed in reference/UPSTREAM.json against its
recorded sha256.

Usage:
    python3 scripts/check_vendored.py            # verify checksums, exit 1 on drift
    python3 scripts/check_vendored.py --refresh  # re-download and update manifest
"""
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_FILE = PROJECT_ROOT / "reference/UPSTREAM.json"
COMMITS_API = "https://api.github.com/repos/{repo}/commits"
NETWORK_TIMEOUT = 30


def load_manifest(path: Path) -> Dict[str, Any]:
    """Read the provenance manifest, or exit with a clear error."""
    if not path.exists():
        print(f"Error: manifest not found at {path}")
        sys.exit(1)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: {path} is not valid JSON: {exc}")
        sys.exit(1)


def sha256_of(path: Path) -> str:
    """Return the sha256 of a file, read in binary so no newline translation occurs."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str) -> bytes:
    """Fetch a URL, returning raw bytes."""
    request = urllib.request.Request(url, headers={"User-Agent": "doctrine-check-vendored"})
    with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT) as response:
        return response.read()


def repo_slug(entry: Dict[str, Any]) -> Optional[str]:
    """Extract owner/repo from an entry's upstream_repo URL."""
    url = entry.get("upstream_repo", "")
    if "github.com/" not in url:
        return None
    return url.split("github.com/")[-1].rstrip("/").removesuffix(".git")


def latest_commit(entry: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return (sha, YYYY-MM-DD) of the newest upstream commit touching this path."""
    slug = repo_slug(entry)
    upstream_path = entry.get("upstream_path")
    if not slug or not upstream_path:
        return None, None
    url = (
        f"{COMMITS_API.format(repo=slug)}"
        f"?sha={entry.get('upstream_ref', 'HEAD')}&path={upstream_path}&per_page=1"
    )
    try:
        commits = json.loads(fetch(url))
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        print(f"  warning: could not read commit metadata for {upstream_path}: {exc}")
        return None, None
    if not commits:
        return None, None
    commit = commits[0]
    committed = commit.get("commit", {}).get("committer", {}).get("date", "")
    day = committed[:10] if committed else None
    return commit.get("sha"), day


def verify(entries: List[Dict[str, Any]]) -> int:
    """Check each entry's sha256. Returns the number of failures."""
    failures = 0
    for entry in entries:
        path = PROJECT_ROOT / entry["path"]
        expected = entry.get("sha256", "")
        if not path.exists():
            print(f"MISSING  {entry['path']}")
            failures += 1
            continue
        actual = sha256_of(path)
        if actual != expected:
            print(f"MODIFIED {entry['path']}")
            print(f"           expected sha256 {expected}")
            print(f"           actual   sha256 {actual}")
            failures += 1
            continue
        print(f"OK       {entry['path']}")
    return failures


def refresh(entries: List[Dict[str, Any]]) -> int:
    """Re-download every entry, rewrite the file, and update the manifest in place."""
    today = datetime.now(timezone.utc).date().isoformat()
    failures = 0
    for entry in entries:
        path = PROJECT_ROOT / entry["path"]
        print(f"Fetching {entry['upstream_url']}")
        try:
            payload = fetch(entry["upstream_url"])
        except (urllib.error.URLError, OSError) as exc:
            print(f"  ERROR: download failed: {exc}")
            failures += 1
            continue

        old_sha = entry.get("sha256", "")
        new_sha = hashlib.sha256(payload).hexdigest()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entry["sha256"] = new_sha
        entry["retrieved"] = today

        commit_sha, commit_date = latest_commit(entry)
        if commit_sha:
            entry["upstream_commit"] = commit_sha
        if commit_date:
            entry["upstream_commit_date"] = commit_date

        status = "unchanged" if old_sha == new_sha else f"updated ({old_sha[:12]} -> {new_sha[:12]})"
        print(f"  {entry['path']}: {status}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-download every vendored file and update reference/UPSTREAM.json",
    )
    args = parser.parse_args()

    manifest = load_manifest(MANIFEST_FILE)
    entries = manifest.get("files", [])
    if not entries:
        print(f"Error: {MANIFEST_FILE} lists no files")
        return 1

    if args.refresh:
        failures = refresh(entries)
        MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"\nManifest written: {MANIFEST_FILE.relative_to(PROJECT_ROOT)}")
        if failures:
            print(f"{failures} file(s) failed to download")
            return 1
        return 0

    print(f"Verifying {len(entries)} vendored file(s) against {MANIFEST_FILE.relative_to(PROJECT_ROOT)}\n")
    failures = verify(entries)
    print()
    if failures:
        print(f"{failures} of {len(entries)} vendored file(s) do not match their recorded checksum.")
        print("Vendored material MUST stay byte-for-byte identical to upstream.")
        print("If this is a deliberate vendor update, run: python3 scripts/check_vendored.py --refresh")
        return 1
    print(f"All {len(entries)} vendored file(s) match their recorded checksums.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
