# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools"))

import vao03  # noqa: E402
import vao04  # noqa: E402


class ArchiveSecurityTests(unittest.TestCase):
    workspace = ROOT / "Fixtures/VAO04/workspaces/minimal"

    def make_archive(
        self, output: Path, additions: list[tuple[zipfile.ZipInfo, bytes]]
    ) -> None:
        with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
            archive.writestr(
                vao03.zip_info("mimetype"), (self.workspace / "mimetype").read_bytes()
            )
            archive.writestr(
                vao03.zip_info(vao04.MANIFEST_NAME),
                (self.workspace / vao04.MANIFEST_NAME).read_bytes(),
            )
            archive.writestr(
                vao03.zip_info(vao04.CARRIER_NAME),
                (self.workspace / vao04.CARRIER_NAME).read_bytes(),
            )
            archive.writestr(
                vao03.zip_info("payload/evidence/source.txt"),
                (self.workspace / "payload/evidence/source.txt").read_bytes(),
            )
            for info, data in additions:
                archive.writestr(info, data)

    def assert_rejected(
        self, additions: list[tuple[zipfile.ZipInfo, bytes]], expected: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "attack.vao"
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="Duplicate name:.*", category=UserWarning
                )
                self.make_archive(path, additions)
            report = vao04.validate_archive(path)
            self.assertFalse(report["valid"])
            self.assertIn(expected, "\n".join(report["errors"]))

    def test_path_traversal_rejected(self) -> None:
        self.assert_rejected(
            [(vao03.zip_info("../outside"), b"x")], "Unsafe archive path"
        )

    def test_control_character_path_rejected(self) -> None:
        self.assert_rejected(
            [(vao03.zip_info("payload/log\ninjection.txt"), b"x")],
            "Unsafe archive path",
        )

    def test_unknown_root_rejected(self) -> None:
        self.assert_rejected(
            [(vao03.zip_info("unexpected.txt"), b"x")], "Unknown carrier entry"
        )

    def test_duplicate_raw_name_rejected(self) -> None:
        self.assert_rejected(
            [
                (vao03.zip_info("payload/duplicate"), b"a"),
                (vao03.zip_info("payload/duplicate"), b"b"),
            ],
            "duplicate paths",
        )

    def test_nfc_collision_rejected(self) -> None:
        self.assert_rejected(
            [
                (vao03.zip_info("payload/e\u0301.txt"), b"a"),
                (vao03.zip_info("payload/\u00e9.txt"), b"b"),
            ],
            "NFC normalization",
        )

    def test_case_fold_collision_rejected(self) -> None:
        self.assert_rejected(
            [
                (vao03.zip_info("payload/Case.txt"), b"a"),
                (vao03.zip_info("payload/case.txt"), b"b"),
            ],
            "case-fold normalization",
        )

    def test_symbolic_link_rejected(self) -> None:
        info = vao03.zip_info("payload/link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.assert_rejected([(info, b"target")], "symbolic link")

    def test_special_file_rejected(self) -> None:
        info = vao03.zip_info("payload/fifo")
        info.external_attr = (stat.S_IFIFO | 0o644) << 16
        self.assert_rejected([(info, b"")], "special file")

    def test_encrypted_flag_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "encrypted.vao"
            self.make_archive(path, [])
            data = bytearray(path.read_bytes())
            local = data.find(b"PK\x03\x04")
            central = data.find(b"PK\x01\x02")
            self.assertGreaterEqual(local, 0)
            self.assertGreaterEqual(central, 0)
            data[local + 6] |= 0x01
            data[central + 8] |= 0x01
            path.write_bytes(data)
            report = vao04.validate_archive(path)
            self.assertFalse(report["valid"])
            self.assertIn("Encrypted entry", "\n".join(report["errors"]))

    def test_extreme_deflate_ratio_rejected_before_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ratio.vao"
            with zipfile.ZipFile(path, "w", allowZip64=True) as archive:
                archive.writestr(
                    vao03.zip_info("mimetype"),
                    (self.workspace / "mimetype").read_bytes(),
                )
                archive.writestr(
                    vao03.zip_info(vao04.MANIFEST_NAME),
                    (self.workspace / vao04.MANIFEST_NAME).read_bytes(),
                )
                archive.writestr(
                    vao03.zip_info(vao04.CARRIER_NAME),
                    (self.workspace / vao04.CARRIER_NAME).read_bytes(),
                )
                archive.writestr(
                    vao03.zip_info("payload/evidence/source.txt"),
                    (self.workspace / "payload/evidence/source.txt").read_bytes(),
                )
                info = vao03.zip_info("payload/high-ratio.bin")
                info.compress_type = zipfile.ZIP_DEFLATED
                with archive.open(info, "w", force_zip64=True) as stream:
                    block = b"\0" * (1024 * 1024)
                    for _ in range(64):
                        stream.write(block)
            report = vao04.validate_archive(path)
            self.assertFalse(report["valid"])
            self.assertIn("compression-ratio limit", "\n".join(report["errors"]))

    def test_mimetype_declared_size_rejected_before_structural_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad-mimetype.vao"
            with zipfile.ZipFile(path, "w", allowZip64=True) as archive:
                archive.writestr(vao03.zip_info("mimetype"), b"x" * 1024)
                archive.writestr(
                    vao03.zip_info(vao04.MANIFEST_NAME),
                    (self.workspace / vao04.MANIFEST_NAME).read_bytes(),
                )
                archive.writestr(
                    vao03.zip_info(vao04.CARRIER_NAME),
                    (self.workspace / vao04.CARRIER_NAME).read_bytes(),
                )
                archive.writestr(
                    vao03.zip_info("payload/evidence/source.txt"),
                    (self.workspace / "payload/evidence/source.txt").read_bytes(),
                )
            report = vao04.validate_archive(path)
            self.assertFalse(report["valid"])
            self.assertIn("impossible declared size", "\n".join(report["errors"]))

    def test_workspace_symbolic_link_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            (workspace / "payload/link").symlink_to("evidence/source.txt")
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("symbolic link", "\n".join(report["errors"]))

    def test_workspace_hard_link_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            source = workspace / "payload/evidence/source.txt"
            os.link(source, workspace / "payload/evidence/alias.txt")
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("hard link", "\n".join(report["errors"]))

    def test_structural_size_limits_apply_before_workspace_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            with (workspace / vao04.MANIFEST_NAME).open("r+b") as stream:
                stream.truncate(vao04.MAX_MANIFEST_BYTES + 1)
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("Manifest exceeds", "\n".join(report["errors"]))

    def test_standalone_manifest_size_limit_applies_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            descriptor = Path(temporary) / "oversized.json"
            with descriptor.open("wb") as stream:
                stream.truncate(vao04.MAX_MANIFEST_BYTES + 1)
            report = vao04.validate(descriptor)
            self.assertFalse(report["valid"])
            self.assertIn("Manifest exceeds", "\n".join(report["errors"]))

    def test_workspace_path_depth_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            deep = workspace / "payload"
            for _ in range(vao04.MAX_PATH_SEGMENTS):
                deep /= "d"
            deep.mkdir(parents=True)
            (deep / "file").write_bytes(b"x")
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("segment-depth limit", "\n".join(report["errors"]))

    def test_bootstrap_must_embed_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            carrier_path = workspace / vao04.CARRIER_NAME
            carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
            carrier["carrierMode"] = "bootstrap"
            carrier["embeddedRealizations"] = []
            carrier["completeGroupIds"] = []
            shutil.rmtree(workspace / "payload")
            carrier_path.write_bytes(vao04.json_bytes(carrier))
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("bootstrap carrier must embed", "\n".join(report["errors"]))

    def test_preservation_closure_must_mark_all_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            carrier_path = workspace / vao04.CARRIER_NAME
            carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
            carrier["carrierMode"] = "preservation-closure"
            carrier["completeGroupIds"] = []
            carrier_path.write_bytes(vao04.json_bytes(carrier))
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn(
                "mark every asset group complete", "\n".join(report["errors"])
            )

    def test_payload_corruption_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(self.workspace, workspace)
            (workspace / "payload/evidence/source.txt").write_bytes(b"corrupt")
            report = vao04.validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertIn("fails exact byte verification", "\n".join(report["errors"]))

    def test_stream_hash_rejects_growth_beyond_declared_size(self) -> None:
        self.assertEqual(
            (hashlib.sha256(b"abc").hexdigest(), 3),
            vao04.sha256_stream_bounded(io.BytesIO(b"abc"), 3),
        )
        with self.assertRaisesRegex(vao04.VAO04Error, "permitted bound"):
            vao04.sha256_stream_bounded(io.BytesIO(b"abcd"), 3)

    def test_writer_refuses_and_preserves_broken_output_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output.vao"
            output.symlink_to("missing-target")
            with self.assertRaises(vao04.VAO04Error):
                vao04.pack_workspace(self.workspace, output)
            self.assertTrue(output.is_symlink())

    def test_migrator_rejects_source_symlink(self) -> None:
        source_fixture = ROOT / "Fixtures/VAO03/valid/embedded-private"
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "destination"
            shutil.copytree(source_fixture, source)
            (source / "payload/link").symlink_to("evidence/source.txt")
            with self.assertRaisesRegex(vao04.VAO04Error, "symbolic link"):
                vao04.migrate_03_workspace(source, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
