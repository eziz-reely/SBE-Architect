# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke test of the IngeTrazo adapter with stand-ins for the IngeTrazo/Qt classes it touches
(this checks OUR calls only; run the plugin inside IngeTrazo for the real thing)."""
import importlib.util, json, os, sys, types

HERE = os.path.dirname(os.path.abspath(__file__))


def stub(name, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


class Vec:
    def __init__(self, x, y, z): self.p = (x, y, z)


class Face:
    def __init__(self, loop, holes): self.loop, self.holes, self.attrs = loop, holes, {}


class Mesh:
    def __init__(self): self.faces = []
    def add_face(self, loop, holes=None):
        f = Face(list(loop), holes); self.faces.append(f); return f


class Group:
    def __init__(self, mesh=None, name=None): self.mesh, self.name, self.ext, self.layer, self.ifc = mesh, name, None, None, None


class Layer:
    def __init__(self, name): self.name = name


def load_plugin():
    stub("PySide6"); stub("PySide6.QtGui", QVector3D=Vec); stub("PySide6.QtWidgets", QFileDialog=object, QInputDialog=object, QMessageBox=object)
    stub("core"); stub("core.bim", tag_group=lambda g, c, n: setattr(g, "ifc", {"class": c, "name": n}))
    sys.modules["core"].bim = sys.modules["core.bim"]
    stub("core.group", Group=Group); stub("core.history", SnapshotImport=object); stub("core.layers", Layer=Layer); stub("core.mesh", Mesh=Mesh)
    d = os.path.join(HERE, "..", "mm_homes", "__init__.py")
    spec = importlib.util.spec_from_file_location("ingetrazo_plugin_mm_homes", d, submodule_search_locations=[os.path.dirname(d)])
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return mod


def test_build_into_and_replace():
    mod = load_plugin()
    scene = types.SimpleNamespace(layers=[], groups=[])
    model = json.load(open(os.path.join(HERE, "data", "gordon_120.json"), encoding="utf-8"))
    counts = mod.build_into(scene, "mm_homes", model)
    n = len(scene.groups)
    assert counts["IfcWall"] > 20 and counts["IfcRoof"] == 2 and counts["IfcWindow"] == 13
    assert all(g.ifc and g.ext == {"mm_homes": {"id": model["id"]}} for g in scene.groups)
    assert len(scene.layers) == 1
    glass = [f for g in scene.groups for f in g.mesh.faces if "opacity" in f.attrs]
    assert glass and all(0 < f.attrs["opacity"] < 1 for f in glass)
    scene.groups.append(Group(Mesh(), "user geometry"))
    mod.build_into(scene, "mm_homes", model, "sarkans")    # replaces only its own groups
    assert len(scene.groups) == n + 1 and sum(g.name == "user geometry" for g in scene.groups) == 1
    assert sum(1 for g in scene.groups if g.ext) == n
