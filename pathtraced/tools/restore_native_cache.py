"""Restore the exact packaged triangle cache. Standard library only; no network."""
from pathlib import Path
import gzip, hashlib, json, os, tempfile
ROOT = Path(__file__).resolve().parents[1]
def digest(data): return hashlib.sha256(data).hexdigest()
def main():
    spec = json.loads((ROOT / "assets/native-cache-parts.json").read_text())
    dest = ROOT / spec["target"]
    if dest.exists():
        if dest.stat().st_size != spec["bytes"] or digest(dest.read_bytes()) != spec["sha256"]:
            raise SystemExit("Refusing to overwrite a different existing native cache.")
        print("Native cache already matches:", dest)
        return
    chunks = []
    for part in spec["parts"]:
        data = (ROOT / part["path"]).read_bytes()
        if len(data) != part["bytes"] or digest(data) != part["sha256"]:
            raise SystemExit("Corrupt or incomplete cache part: " + part["path"])
        chunks.append(data)
    compressed = b"".join(chunks)
    if len(compressed) != spec["gzip_bytes"] or digest(compressed) != spec["gzip_sha256"]:
        raise SystemExit("Compressed cache hash mismatch.")
    data = gzip.decompress(compressed)
    if len(data) != spec["bytes"] or digest(data) != spec["sha256"]:
        raise SystemExit("Restored cache hash mismatch.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".native-cache-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as f: f.write(data)
        os.link(tmp, dest)  # Exclusive publication: never overwrite another file.
    finally:
        os.unlink(tmp)
    print("Restored exact native cache:", dest)
if __name__ == "__main__": main()
