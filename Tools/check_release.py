#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the complete local release gate without publishing anything."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def check_python_sources() -> None:
    print("\n== compile reference tools and tests ==", flush=True)
    # Compile in memory so a Git-free export is checked without generated files.
    for directory in (ROOT / "Tools", ROOT / "tests"):
        for source in sorted(directory.rglob("*.py")):
            compile(source.read_bytes(), str(source), "exec", dont_inherit=True)


def run(label: str, arguments: list[str]) -> None:
    print(f"\n== {label} ==", flush=True)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # An unpacked source inside another checkout must not inherit that repository.
    environment["GIT_CEILING_DIRECTORIES"] = str(ROOT.parent)
    completed = subprocess.run(arguments, cwd=ROOT, env=environment, check=False)
    if completed.returncode:
        raise SystemExit(f"FAILED ({completed.returncode}): {label}")


def main() -> int:
    python = sys.executable
    formatted_sources = [
        "Tools/build_release.py",
        "Tools/build_site.py",
        "Tools/check_release.py",
        "Tools/check_site.py",
        "Tools/check_wheel.py",
        "Tools/generate_schema_reference.py",
        "Tools/update_release_bundle.py",
        "Tools/vao04.py",
        "Tools/vao04_interop.py",
        "Tools/vao04_rdf.py",
        "Tools/vao04_runtime.py",
        "Tools/vao05.py",
        "Tools/vao05_interop.py",
        "Tools/vao05_rdf.py",
        "Tools/vao05_runtime.py",
        "Tools/vao_resources.py",
        "Tools/vao06.py",
        "Tools/vao06_runtime.py",
        "Tools/vao06_rdf.py",
        "Tools/vao06_interop.py",
        "Tools/vao.py",
        "Tools/mmic.py",
        "Tools/mmic_rdf.py",
        "Tools/mmic_worker.py",
        "Tools/migrate_vao05.py",
        "Tools/build_mmic_schema.py",
        "Tools/build_mmic_resources.py",
        "Tools/build_mmic_fixtures.py",
        "Tools/update_release_bundle06.py",
        "Tools/generate_schema_reference06.py",
        "tests",
    ]
    check_python_sources()
    run(
        "undefined names and unused imports",
        [
            python,
            "-m",
            "ruff",
            "check",
            "--no-cache",
            "--select",
            "F",
            "Tools",
            "tests",
        ],
    )
    run(
        "reference-code formatting",
        [python, "-m", "ruff", "format", "--no-cache", "--check", *formatted_sources],
    )
    run(
        "REUSE 3.3 licensing compliance",
        [python, "-m", "reuse", "--root", str(ROOT), "lint"],
    )
    run(
        "generated schema reference",
        [python, "Tools/generate_schema_reference.py", "--check"],
    )
    run(
        "normative specification bundle fixity",
        [python, "Tools/update_release_bundle.py", "--check"],
    )
    run(
        "current generated schema reference",
        [python, "Tools/generate_schema_reference06.py", "--check"],
    )
    run(
        "current normative bundle fixity",
        [python, "Tools/update_release_bundle06.py", "--check"],
    )
    run("MMIC generated schema", [python, "Tools/build_mmic_schema.py", "--check"])
    run(
        "MMIC local catalog and vocabulary",
        [python, "Tools/build_mmic_resources.py", "--check"],
    )
    run(
        "MMIC deterministic fixtures",
        [python, "Tools/build_mmic_fixtures.py", "--check"],
    )
    run(
        "deterministic publication site",
        [python, "Tools/check_site.py"],
    )
    run(
        "installable wheel and bundled-schema smoke test",
        [python, "Tools/check_wheel.py"],
    )
    run(
        "unit, conformance, security, RDF, metadata, and reproducibility tests",
        [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
    )
    fixture_sets = (
        ("descriptor", sorted((ROOT / "Fixtures/VAO04/descriptors").glob("*.json"))),
        ("workspace", sorted((ROOT / "Fixtures/VAO04/workspaces").iterdir())),
        ("carrier", sorted((ROOT / "Fixtures/VAO04/carriers").glob("*.vao"))),
    )
    for fixture_kind, paths in fixture_sets:
        if not paths:
            raise SystemExit(f"No VAO 0.4 {fixture_kind} fixtures found.")
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            run(
                f"{fixture_kind} CLI: {path.name}",
                [python, "Tools/vao04.py", "validate", relative],
            )
    fixture_sets_05 = (
        ("descriptor", sorted((ROOT / "Fixtures/VAO05/descriptors").glob("*.json"))),
        ("workspace", sorted((ROOT / "Fixtures/VAO05/workspaces").iterdir())),
        ("carrier", sorted((ROOT / "Fixtures/VAO05/carriers").glob("*.vao"))),
    )
    for fixture_kind, paths in fixture_sets_05:
        if not paths:
            raise SystemExit(f"No VAO 0.5 {fixture_kind} fixtures found.")
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            run(
                f"0.5 {fixture_kind} CLI: {path.name}",
                [python, "Tools/vao05.py", "validate", relative],
            )
    companion_directory = ROOT / "Fixtures/VAO04/companions"
    companion_sets = {
        "release": sorted(companion_directory.glob("release*.json")),
        "pack": sorted(companion_directory.glob("pack-manifest*.json")),
        "receipt": sorted(companion_directory.glob("materialization-receipt*.json")),
        "zenodo-metadata": sorted(companion_directory.glob("zenodo-metadata*.json")),
    }
    enumerated = {path for paths in companion_sets.values() for path in paths}
    actual = set(companion_directory.glob("*.json"))
    if not actual or enumerated != actual:
        raise SystemExit(
            "Every VAO 0.4 companion fixture must match exactly one release-gate kind."
        )
    for kind, paths in companion_sets.items():
        if not paths:
            raise SystemExit(f"No VAO 0.4 {kind} companion fixture found.")
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            run(
                f"{kind} companion CLI: {path.name}",
                [
                    python,
                    "Tools/vao04.py",
                    "validate-descriptor",
                    kind,
                    relative,
                ],
            )
    run(
        "legacy Zenodo publication-set cross-validation",
        [
            python,
            "Tools/vao04.py",
            "validate-publication",
            "Fixtures/VAO04/companions/release.example.json",
            "Fixtures/VAO04/companions/zenodo-metadata-legacy.example.json",
        ],
    )
    exact_manifest = "Fixtures/VAO04/workspaces/minimal/vao-manifest.json"
    run(
        "release-to-manifest exact cross-validation",
        [
            python,
            "Tools/vao04.py",
            "validate-release",
            "Fixtures/VAO04/companions/release.example.json",
            exact_manifest,
        ],
    )
    run(
        "pack-to-manifest exact cross-validation",
        [
            python,
            "Tools/vao04.py",
            "validate-pack",
            "Fixtures/VAO04/companions/pack-manifest.example.json",
            exact_manifest,
        ],
    )
    run(
        "receipt-to-manifest-and-carrier exact cross-validation",
        [
            python,
            "Tools/vao04.py",
            "validate-receipt",
            "Fixtures/VAO04/companions/materialization-receipt-minimal.example.json",
            exact_manifest,
            "Fixtures/VAO04/carriers/minimal.vao",
        ],
    )
    companion_directory_05 = ROOT / "Fixtures/VAO05/companions"
    for kind, pattern in {
        "release": "release*.json",
        "pack": "pack-manifest*.json",
        "receipt": "materialization-receipt*.json",
        "zenodo-metadata": "zenodo-metadata*.json",
    }.items():
        for path in sorted(companion_directory_05.glob(pattern)):
            run(
                f"0.5 {kind} companion CLI: {path.name}",
                [
                    python,
                    "Tools/vao05.py",
                    "validate-descriptor",
                    kind,
                    path.relative_to(ROOT).as_posix(),
                ],
            )
    exact_manifest_05 = "Fixtures/VAO05/workspaces/minimal/vao-manifest.json"
    run(
        "0.5 release-to-manifest exact cross-validation",
        [
            python,
            "Tools/vao05.py",
            "validate-release",
            "Fixtures/VAO05/companions/release.example.json",
            exact_manifest_05,
        ],
    )
    run(
        "0.5 release-to-carrier exact cross-validation",
        [
            python,
            "Tools/vao05.py",
            "validate-release-carriers",
            "Fixtures/VAO05/companions/release.example.json",
            exact_manifest_05,
            "Fixtures/VAO05/carriers/minimal.vao",
        ],
    )
    run(
        "0.5 receipt-to-manifest-and-carrier exact cross-validation",
        [
            python,
            "Tools/vao05.py",
            "validate-receipt",
            "Fixtures/VAO05/companions/materialization-receipt-minimal.example.json",
            exact_manifest_05,
            "Fixtures/VAO05/carriers/minimal.vao",
        ],
    )
    print(
        "\nRELEASE GATE PASSED: VAO 0.6.0/MMIC 1.0.0 and retained VAO 0.4/0.5 content are internally consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
