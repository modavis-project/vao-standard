#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Private, trusted MMIC worker. Only invoked by the distributed validator."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import sys

# -I excludes the current directory and user PYTHONPATH. Restore only this
# installed, locally trusted module directory; incoming files cannot choose code.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mmic  # noqa: E402


def main():
    memory_limit = None
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
        if sys.platform != "darwin":
            resource.setrlimit(
                resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024)
            )
            memory_limit = 512 * 1024 * 1024
    except (ImportError, ValueError, OSError):
        pass
    raw = sys.stdin.buffer.read(64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024:
        raise SystemExit("Worker request exceeds budget")
    request = json.loads(raw)
    assets = {
        key: base64.b64decode(value, validate=True) if isinstance(value, str) else value
        for key, value in request["assets"].items()
    }
    report = mmic.validate_materialized(request["manifest"], assets.get)
    report["worker"] = {
        "isolatedInterpreter": True,
        "wallTimeSeconds": 15,
        "snapshotByteLimit": 32 * 1024 * 1024,
        "memoryLimitBytes": memory_limit,
        "memoryLimitMeaning": "POSIX address-space limit where supported; bounded inputs on macOS",
    }
    print(json.dumps(report))


if __name__ == "__main__":
    main()
