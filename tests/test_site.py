# SPDX-License-Identifier: Apache-2.0
"""Publication-surface regression tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))

from build_site import DEFAULT_BASE_PATH, DEFAULT_BASE_URL, build  # noqa: E402
from check_site import inventory, verify_site  # noqa: E402


class PublicationSiteTests(unittest.TestCase):
    def test_published_site_is_complete_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first_name:
            with tempfile.TemporaryDirectory() as second_name:
                first = Path(first_name)
                second = Path(second_name)
                for output in (first, second):
                    build(
                        output,
                        base_url=DEFAULT_BASE_URL,
                        base_path=DEFAULT_BASE_PATH,
                        publication_state="published",
                    )
                    verify_site(output)
                self.assertEqual(inventory(first), inventory(second))

    def test_prepared_site_is_explicitly_marked(self) -> None:
        with tempfile.TemporaryDirectory() as output_name:
            output = Path(output_name)
            build(
                output,
                base_url=DEFAULT_BASE_URL,
                base_path=DEFAULT_BASE_PATH,
                publication_state="prepared",
            )
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Review build.", index)

    def test_published_site_omits_review_notice(self) -> None:
        with tempfile.TemporaryDirectory() as output_name:
            output = Path(output_name)
            build(
                output,
                base_url=DEFAULT_BASE_URL,
                base_path=DEFAULT_BASE_PATH,
                publication_state="published",
            )
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("Review build.", index)


if __name__ == "__main__":
    unittest.main()
