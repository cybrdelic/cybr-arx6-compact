"""Build representative real design parts without replacing the packaged meshes."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))
from build_meshes import D, build

def has(node, operation):
    return node["op"] == operation or any(has(child, operation) for child in node["children"])

def complexity(node):
    return 1 + sum(complexity(child) for child in node["children"])

def main():
    selected = {min((p for p in D["parts"] if has(p["shape"], op)), key=lambda p: complexity(p['shape']))['id'] for op in ("cut", "helix")}
    records = []
    for part in D["parts"]:
        if part["id"] not in selected:
            continue
        print('Evaluating', part['id'], part['name'], flush=True)
        shape = build(part["shape"])
        vertices, triangles = shape.tessellate(.045, .12)
        assert shape.isValid() and shape.Volume() > 0 and vertices and triangles
        records.append({"id": part["id"], "name": part["name"], "valid": True,
                        "volume_mm3": shape.Volume(), "triangles": len(triangles)})
    print(json.dumps({"scope": "Representative native CSG evaluation, not all-part or hardware qualification.",
                      "parts": records}, indent=2))
if __name__ == "__main__":
    main()
