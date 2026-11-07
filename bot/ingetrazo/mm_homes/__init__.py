# SPDX-License-Identifier: GPL-3.0-or-later
"""MM Homes for IngeTrazo: build a house from an SBE-Architect model.json.

Extensions > MM Homes > Load model.json...   builds the house as BIM-tagged groups
(IfcWall, IfcWindow, IfcDoor, IfcSlab, IfcRoof, IfcStair) in ONE undo step.
Loading again replaces the previous MM house (groups carry group.ext["mm_homes"]).

Install: copy this whole folder (mm_homes) into IngeTrazo's plugins folder
(Extensions > Open plugins folder) and restart IngeTrazo.
"""
from __future__ import annotations

import json
import os

from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from core import bim
from core.group import Group
from core.history import SnapshotImport
from core.layers import Layer
from core.mesh import Mesh

from . import geometry

LAYER = "MM Homes"
TONE_LABELS = [("peleks", "Pelēks (grafīts)"), ("sarkans", "Norvēģu sarkans"), ("koks", "Dabīgs koks"),
               ("zals", "Tumši zaļš"), ("balts", "Gaiši pelēks (balts)")]


def _vec(p):
    return QVector3D(p[0], p[1], p[2])


def make_group(part, key, model_id):
    """One Group per part: faces with colour (and opacity for glass), BIM tag on the group."""
    g = Group(Mesh(), name=part["name"])
    base = geometry.rgb(part["color"])
    for loop, holes, color, opacity in part["faces"]:
        f = g.mesh.add_face([_vec(p) for p in loop], [[_vec(p) for p in h] for h in holes] or None)
        f.attrs["color"] = tuple(color) if color else base
        if opacity is not None:
            f.attrs["opacity"] = opacity
        f.attrs["layer"] = LAYER
    g.layer = LAYER
    g.ext = {key: {"id": model_id}}
    bim.tag_group(g, part["ifc"], part["name"])
    return g


def build_into(scene, key, model, tone=None):
    """Replace this plugin's groups in `scene` by the house of `model`; returns the IFC counts."""
    parts = geometry.build(model, tone)
    if not any(ly.name == LAYER for ly in scene.layers):
        scene.layers.append(Layer(LAYER))
    scene.groups[:] = [g for g in scene.groups if key not in (getattr(g, "ext", None) or {})]
    for part in parts:
        scene.groups.append(make_group(part, key, model.get("id", "MM")))
    return geometry.summary(parts)


def setup(app):
    state = {"path": None, "tone": None}

    def build(path, tone=None):
        try:
            with open(path, encoding="utf-8") as f:
                model = json.load(f)
            counts = {}

            def mutate(scene):
                counts.update(build_into(scene, app.key, model, tone))

            app.viewport.history.execute(SnapshotImport(mutate))
            app.viewport.notify_scene_changed()
            try:
                app.window._on_zoom_extents()
            except Exception:
                pass
            state["path"] = path
            names = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
            app.viewport.flash_status(f"MM Homes {model.get('id', '')}: {names}. Ctrl+Z atceļ.", 6000)
        except Exception as exc:   # a bad file must never break the app
            QMessageBox.warning(app.window, "MM Homes", f"Neizdevās uzbūvēt modeli:\n{exc}")

    def load():
        path, _ = QFileDialog.getOpenFileName(app.window, "SBE-Architect model.json", state["path"] or "", "model.json (*.json)")
        if path:
            build(path, state["tone"])

    def reload():
        if state["path"] and os.path.exists(state["path"]):
            build(state["path"], state["tone"])
        else:
            load()

    def pick_tone():
        labels = [l for _, l in TONE_LABELS]
        label, ok = QInputDialog.getItem(app.window, "MM Homes", "Fasādes tonis:", labels, 0, False)
        if ok:
            state["tone"] = TONE_LABELS[labels.index(label)][0]
            reload()

    menu = app.add_menu("MM Homes")
    if menu is not None:
        menu.addAction("Ielādēt model.json…", load)
        menu.addAction("Pārbūvēt no šī paša faila", reload)
        menu.addAction("Mainīt fasādes toni…", pick_tone)
