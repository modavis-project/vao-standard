#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Refresh the W3ID note in a site built from the VAO 0.6.0 tag."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from build_site import DEFAULT_BASE_PATH, DEFAULT_BASE_URL, artifacts_page


ARTIFACTS_PAGE = "artifacts/index.html"
PREVIOUS_NOTE = (
    "  <p>Version 0.6.0 resolver routing is pending. The release includes all "
    "normative resources and an offline dependency catalog.</p>\n"
)


def update(site: Path) -> None:
    page = site / ARTIFACTS_PAGE
    original = page.read_bytes().decode("utf-8")
    prefix, previous_note, suffix = original.partition(PREVIOUS_NOTE)
    if not previous_note or PREVIOUS_NOTE in suffix:
        raise ValueError("Expected one routing note from the VAO 0.6.0 site")

    current = artifacts_page(DEFAULT_BASE_URL, DEFAULT_BASE_PATH)
    note = current.removeprefix(prefix).removesuffix(suffix)
    if (
        current != prefix + note + suffix
        or not note.startswith("  <p>")
        or not note.endswith("</p>\n")
        or note.count("\n") != 1
        or "https://w3id.org/modavis/vao/profile/mmic/1.0.0" not in note
    ):
        raise ValueError("Expected the artifacts page to differ only in its W3ID note")

    manifest_path = site / "release-site-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    (entry,) = (item for item in manifest["files"] if item["path"] == ARTIFACTS_PAGE)
    payload = current.encode("utf-8")
    entry.update(sha256=sha256(payload).hexdigest(), size=len(payload))
    page.write_bytes(payload)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    update(parser.parse_args().site)
