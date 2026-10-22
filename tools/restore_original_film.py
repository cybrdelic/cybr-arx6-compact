#!/usr/bin/env python3
"""Restore the preserved v1 MP4 from exact byte parts, without transcoding."""
from pathlib import Path
import hashlib
import os

FILM = {'path': 'media/ARX6-P5-Cinematic-v1.mp4', 'bytes': 13128405, 'sha256': 'e8873fec1763941dd100e96727d91d1a1b1f2ec60fc429416c7ee1e06141e11a', 'parts': [{'path': 'media/ARX6-P5-Cinematic-v1.mp4.parts/part-001', 'bytes': 8388608, 'sha256': 'aad7b669c66c79d07450107bd4461b702a4e3a48e2994fd0aee1311a9cbef630'}, {'path': 'media/ARX6-P5-Cinematic-v1.mp4.parts/part-002', 'bytes': 4739797, 'sha256': '501c2735c662f42a4fff408cebbca6095a475902e9df79e15997d0cf6a5f95da'}]}


def matches(data, record):
    return len(data) == record["bytes"] and hashlib.sha256(data).hexdigest() == record["sha256"]


def main():
    root = Path(__file__).resolve().parent.parent
    target = root / FILM["path"]
    if target.exists():
        if not matches(target.read_bytes(), FILM):
            raise SystemExit("Existing film differs; refusing to overwrite it.")
        print("Original v1 film is already restored and verified.")
        return
    chunks = []
    for part in FILM["parts"]:
        data = (root / part["path"]).read_bytes()
        if not matches(data, part):
            raise SystemExit("Film part failed integrity check: " + part["path"])
        chunks.append(data)
    data = b"".join(chunks)
    if not matches(data, FILM):
        raise SystemExit("Reconstructed film failed integrity check.")
    temporary = target.with_suffix(target.suffix + ".restoring")
    with temporary.open("xb") as stream:
        stream.write(data)
    os.replace(temporary, target)
    print("Restored and verified: " + FILM["path"])
    print("SHA-256: " + FILM["sha256"])


if __name__ == "__main__":
    main()
