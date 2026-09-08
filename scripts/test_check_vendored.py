#!/usr/bin/env python3
"""Unit tests for scripts/check_vendored.py.

Run with:
    python3 -m unittest discover scripts
    python3 -m unittest scripts.test_check_vendored
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_vendored as cv  # noqa: E402


class ChapterLinkTests(unittest.TestCase):
    def rewrite(self, text: str) -> str:
        return cv.rewrite_mdbook_chapter_links(text.encode()).decode()

    def test_rewrites_inline_link(self):
        self.assertEqual(self.rewrite("[Naming](naming.html)"), "[Naming](naming.md)")

    def test_rewrites_reference_definition_with_fragment(self):
        self.assertEqual(
            self.rewrite("[C-CASE]: naming.html#c-case"),
            "[C-CASE]: naming.md#c-case",
        )

    def test_rewrites_hyphenated_chapter(self):
        self.assertEqual(
            self.rewrite("[C-SEALED]: future-proofing.html#c-sealed"),
            "[C-SEALED]: future-proofing.md#c-sealed",
        )

    def test_leaves_rustdoc_illustrations_alone(self):
        for target in (
            "[`Deserialize`]: trait.Deserialize.html",
            "[`Value`]: ../enum.Value.html",
            "[`DeserializeOwned`]: de/trait.DeserializeOwned.html",
        ):
            with self.subTest(target=target):
                self.assertEqual(self.rewrite(target), target)

    def test_leaves_absolute_urls_alone(self):
        target = "[Elegant APIs](https://deterministic.space/elegant-apis-in-rust.html)"
        self.assertEqual(self.rewrite(target), target)

    def test_is_idempotent(self):
        once = self.rewrite("[C-CASE]: naming.html#c-case")
        self.assertEqual(self.rewrite(once), once)


class StdRelocationTests(unittest.TestCase):
    def test_atomicbool_page_moved_to_the_generic_struct(self):
        old = (
            "[`AtomicBool`]: "
            "https://doc.rust-lang.org/std/sync/atomic/struct.AtomicBool.html#method.into_inner"
        )
        self.assertEqual(
            cv.rewrite_std_doc_relocations(old.encode()).decode(),
            "[`AtomicBool`]: "
            "https://doc.rust-lang.org/std/sync/atomic/struct.Atomic.html#method.into_inner",
        )

    def test_is_idempotent(self):
        once = cv.rewrite_std_doc_relocations(
            b"https://doc.rust-lang.org/std/sync/atomic/struct.AtomicBool.html"
        )
        self.assertEqual(cv.rewrite_std_doc_relocations(once), once)


class TransformSpecTests(unittest.TestCase):
    def test_missing_transform_means_byte_for_byte(self):
        self.assertEqual(cv.transform_names({}), [])

    def test_a_string_is_accepted(self):
        self.assertEqual(
            cv.transform_names({"transform": "mdbook-chapter-links"}),
            ["mdbook-chapter-links"],
        )

    def test_a_list_is_applied_in_order(self):
        names = ["mdbook-chapter-links", "rustdoc-std-relocations"]
        self.assertEqual(cv.transform_names({"transform": names}), names)
        payload = (
            b"[C-CASE]: naming.html#c-case\n"
            b"https://doc.rust-lang.org/std/sync/atomic/struct.AtomicBool.html\n"
        )
        self.assertEqual(
            cv.apply_transforms(payload, names),
            b"[C-CASE]: naming.md#c-case\n"
            b"https://doc.rust-lang.org/std/sync/atomic/struct.Atomic.html\n",
        )

    def test_unknown_transform_raises(self):
        with self.assertRaises(KeyError):
            cv.apply_transforms(b"x", ["no-such-transform"])


class ManifestTests(unittest.TestCase):
    """The shipped manifest must stay self-consistent."""

    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(cv.MANIFEST_FILE.read_text(encoding="utf-8"))["files"]

    def test_every_declared_transform_exists(self):
        for entry in self.entries:
            for name in cv.transform_names(entry):
                with self.subTest(path=entry["path"], transform=name):
                    self.assertIn(name, cv.TRANSFORMS)

    def test_transformed_entries_record_the_untouched_upstream_digest(self):
        for entry in self.entries:
            if cv.transform_names(entry):
                with self.subTest(path=entry["path"]):
                    self.assertIn("upstream_sha256", entry)

    def test_every_entry_records_a_licence(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                self.assertTrue(entry.get("license"))
                self.assertTrue(entry.get("upstream_commit"))
                self.assertTrue(entry.get("retrieved"))


if __name__ == "__main__":
    unittest.main()
