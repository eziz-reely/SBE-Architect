# SPDX-License-Identifier: GPL-3.0-or-later
"""python3 -I -m pytest bot/ingetrazo/tests  (or run this file directly with one or more model.json paths)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mm_homes"))
import geometry as g  # noqa: E402


def key(p):
    return tuple(round(v, 5) for v in p)


def check_part(part):
    """Watertight (every directed edge has its reverse once) and outward (positive volume)."""
    solid_faces = [f for f in part["faces"] if f[2] is None]
    if not solid_faces:
        return []
    errs, edges, vol = [], {}, 0.0
    for loop, holes, _c, _o in solid_faces:
        for lp in (loop, *holes):
            for i, a in enumerate(lp):
                b = lp[(i + 1) % len(lp)]
                k = (key(a), key(b))
                edges[k] = edges.get(k, 0) + 1
        for lp in (loop, *holes):
            n = g.newell(lp)
            vol += g.dot(n, lp[0]) / 6.0
    bad = [k for k, n in edges.items() if n != 1 or (k[1], k[0]) not in edges]
    if bad:
        errs.append(f"{part['name']}: {len(bad)} open/duplicate edges")
    if vol <= 0:
        errs.append(f"{part['name']}: volume {vol:.4f} (inward)")
    return errs


def run(model):
    parts = g.build(model)
    errs = [e for p in parts for e in check_part(p)]
    return parts, errs


def models():
    env = os.environ.get("MM_MODELS")
    return env.split(os.pathsep) if env else glob.glob(os.path.join(HERE, "data", "*.json"))


def test_models_watertight():
    paths = models()
    assert paths, "no test models"
    for path in paths:
        parts, errs = run(json.load(open(path, encoding="utf-8")))
        assert parts and not errs, (path, errs[:5])


if __name__ == "__main__":
    for path in sys.argv[1:] or models():
        parts, errs = run(json.load(open(path, encoding="utf-8")))
        print(os.path.basename(path), g.summary(parts), "faces", sum(len(p["faces"]) for p in parts), "errors", errs[:6])


def test_stairs_and_rotation():
    m = json.load(open(os.path.join(HERE, "data", "mm40_loft.json"), encoding="utf-8"))
    m["furniture"] = [["kapnes", 1000, 1000, 3000, 900, "e"], ["_rot", 90, 2000, 2000, ["kapnesL", 4000, 1000, 2000, 2000, 900, "r", "lauk", 0]]]
    parts, errs = run(m)
    assert sum(1 for p in parts if p["ifc"] == "IfcStair") == 2 and not errs, errs[:5]
