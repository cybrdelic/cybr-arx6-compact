"""Build and check the native renderer with the host C++17 compiler."""
from pathlib import Path
import argparse
import array
import json
import math
import os
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))
from portable_native import find_native_renderer, default_build_dir

def run(args, input_text=None):
    print("+", subprocess.list2cmdline([str(x) for x in args]), flush=True)
    subprocess.run([str(x) for x in args], input=input_text, text=True, check=True)

def smoke(executable, output):
    output = output / 'paths with spaces'
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "assets/frame_inputs/00036.bin"
    data = bytearray(source.read_bytes())
    header = list(struct.unpack("<7i", data[:28]))
    header[1:5] = [160, 90, 1, 2]
    data[:28] = struct.pack("<7i", *header)
    inp, raw = output / "smoke-frame.bin", output / "smoke.f32"
    inp.write_bytes(data)
    run([executable, ROOT / "assets/native.bin", "--stream-lines", "unused", "2"], f'{inp}\n{raw}\n')
    payload = raw.read_bytes()
    assert struct.unpack("<4i", payload[:16]) == (160, 90, 12, 1)
    values = array.array("f")
    values.frombytes(payload[16:])
    if sys.byteorder != "little":
        values.byteswap()
    rgb = [values[i + channel] for i in range(0, len(values), 12) for channel in range(3)]
    assert len(values) == 160 * 90 * 12 and all(math.isfinite(v) and v >= 0 for v in rgb)
    assert max(rgb) > 0, "Blank renderer output"
    report = {"resolution": [160, 90], "requested_spp": 1, "max_depth": 2,
              "finite_nonnegative_rgb": True, "max_linear_rgb": max(rgb), "stream_paths_with_spaces": True,
              "scope": "Bounded native rendering smoke; not a full film or transport certification."}
    (output / "smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=default_build_dir())
    parser.add_argument("--serial", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not shutil.which("cmake"):
        raise SystemExit("CMake is required. Install a C++17 toolchain and CMake, then retry.")
    run([sys.executable, ROOT / "tools/restore_native_cache.py"])
    run(["cmake", "-S", ROOT, "-B", args.build_dir, "-DCMAKE_BUILD_TYPE=Release",
         "-DARX_ENABLE_OPENMP=" + ("OFF" if args.serial else "ON")])
    run(["cmake", "--build", args.build_dir, "--config", "Release", "--parallel", "2"])
    if args.check:
        run(["ctest", "--test-dir", args.build_dir, "-C", "Release", "--output-on-failure"])
    executable = find_native_renderer(args.build_dir)
    if args.smoke:
        smoke(executable, args.build_dir / "smoke")
    print("Renderer:", executable)

if __name__ == "__main__":
    main()
