#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Version-dispatched validation; retained released readers remain unchanged."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

import vao03
import vao04
import vao05
import vao06


def validate(path):
    try:
        if path.is_dir():
            data = vao05._read_bounded_regular(
                path / vao05.MANIFEST_NAME, vao05.MAX_MANIFEST_BYTES, "Manifest"
            )
        elif path.suffix.lower() == ".json":
            data = vao05._read_bounded_regular(
                path, vao05.MAX_MANIFEST_BYTES, "Manifest"
            )
        else:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                if len(names) != len(set(names)) or len(names) > vao05.MAX_ENTRIES:
                    raise ValueError("Duplicate/oversized archive inventory")
                with archive.open(vao05.MANIFEST_NAME) as stream:
                    data = vao05._read_stream_bounded(
                        stream, vao05.MAX_MANIFEST_BYTES, "Manifest"
                    )
        manifest = vao05.strict_json_bytes(data, "Manifest")
        reader = {
            "0.3.3": vao03,
            "0.4.0": vao04,
            "0.5.0": vao05,
            "0.6.0": vao06,
        }.get(manifest.get("formatVersion"))
        if reader is None:
            return {
                "valid": False,
                "status": "unsupported",
                "errors": ["Unknown immutable VAO envelope version"],
                "warnings": [],
            }
        return reader.validate(path)
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        zipfile.BadZipFile,
        vao03.VAO03Error,
    ) as exc:
        return {"valid": False, "errors": [str(exc)], "warnings": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate(args.path)
    vao06.print_report(report, args.json)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
