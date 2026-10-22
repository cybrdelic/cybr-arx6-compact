"""Locate a locally built renderer; never run an archived binary."""
import os
import hashlib
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def default_build_dir():
    # Keep CMake compiler probes below legacy Windows path-length limits.
    if os.name == "nt":
        key = hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]
        return Path(tempfile.gettempdir()) / "arx-native" / key
    return ROOT / ".build/native"

def find_native_renderer(build_dir=None):
    configured = os.environ.get("ARX_PATHTRACER")
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("ARX_PATHTRACER does not name a file: " + str(path))
        return path
    suffix = ".exe" if os.name == "nt" else ""
    build = Path(build_dir) if build_dir else default_build_dir()
    candidates = [build / "bin/Release" / ("pathtrace" + suffix),
                  build / "bin" / ("pathtrace" + suffix),
                  ROOT / "source" / ("pathtrace" + suffix)]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError("Build the native renderer with: python pathtraced/tools/build_native.py --check")
