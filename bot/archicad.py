"""ArchiCAD skripts (Tapir) no model.json, KLIENTA PROJEKTS.

    python archicad.py <model.json> [izvades mape]

Izvade: <id>_archicad.py, viens pašpietiekams Python skripts (tikai standarta bibliotēka). Dati ir ierakstīti tajā.
ArchiCAD: File > New, Tapir > Run script > izvēlas <id>_archicad.py. Bez ArchiCAD pārbauda `--dry`.
Uzbūvē: stāvu, ārsienas (pa ēkas kontūru), starpsienas (no telpu spraugām), logus, durvis, zonas, divslīpju jumtu.
Koordinātas: plāna mm (y uz dienvidiem) → ArchiCAD m, y apgriezts (y_ac = D - y), lai plāns nebūtu spoguļots.
Ko skripts vēl NEdara (atskaitē parādās kā piezīmes): grīdas plātnes, cokols, četrslīpju jumts, mansarda logi, mēbeles, layouti.
Ģeometrijas loģika ir kopīga ar IngeTrazo spraudni (ingetrazo/mm_homes/geometry.py, klase Ctx).
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'ingetrazo', 'mm_homes'))   # tikai geometry.py (bez IngeTrazo/Qt __init__)
import geometry as G          # noqa: E402

M = 0.001


def _line_int(p, d, q, e):
    """Divu taišņu krustpunkts (p + t d), (q + s e)."""
    det = d[0] * (-e[1]) - d[1] * (-e[0])
    if abs(det) < 1e-9:
        return None
    t = ((q[0] - p[0]) * (-e[1]) - (q[1] - p[1]) * (-e[0])) / det
    return (p[0] + d[0] * t, p[1] + d[1] * t)


def data_of(m):
    """model.json -> vienkārši dati skriptam (mm, plāna koordinātes, y uz dienvidiem)."""
    c = G.Ctx(m)
    T = c.T
    notes = []
    walls = []      # {id, a, b, t, outer}
    # ---- ārsienas: kontūras mala nobīdīta iekšup par T/2, stūri = blakus nobīdīto taišņu krustpunkti ----
    n_e = len(c.edges)
    offs = []
    for e in c.edges:
        p = (e["a"][0] + e["n"][0] * T / 2, e["a"][1] + e["n"][1] * T / 2)
        offs.append((p, e["d"]))
    pts = []
    for i in range(n_e):
        q = _line_int(offs[i - 1][0], offs[i - 1][1], offs[i][0], offs[i][1])
        pts.append(q or offs[i][0])
    edge_wall = {}
    for i, e in enumerate(c.edges):
        a, b = pts[i], pts[(i + 1) % n_e]
        wid = f"E{i + 1}"
        walls.append({"id": wid, "a": a, "b": b, "t": T, "outer": True})
        edge_wall[i] = wid
    # ---- starpsienas (tā pati loģika kā geometry.py): spraugas 100..200 mm starp telpām ----
    R = [r for room in (m.get("rooms") or []) for r in room.get("r", [])]
    in_room = lambda px, py: any(rx < px < rx + rw and ry < py < ry + rh for rx, ry, rw, rh in R)
    inside = lambda px, py: c.in_poly(px, py) and all(G._seg_d(px, py, e["a"], e["b"]) > T - 1 for e in c.edges)

    def reach(px, py, dx, dy):
        k = 0
        while k <= 260:
            if in_room(px + dx * (k + 2.5), py + dy * (k + 2.5)) or not inside(px + dx * (k + 2.5), py + dy * (k + 2.5)):
                return k
            k += 5
        return 0

    raw, seen = [], set()
    for a in R:
        for b in R:
            if a is b:
                continue
            gx, gy = b[0] - (a[0] + a[2]), b[1] - (a[1] + a[3])
            if 100 <= gx <= 200:
                y0, y1 = max(a[1], b[1]), min(a[1] + a[3], b[1] + b[3])
                if y1 - y0 > 50:
                    raw.append([a[0] + a[2], y0, gx, y1 - y0, "v"])
            if 100 <= gy <= 200:
                x0, x1 = max(a[0], b[0]), min(a[0] + a[2], b[0] + b[2])
                if x1 - x0 > 50:
                    raw.append([x0, a[1] + a[3], x1 - x0, gy, "h"])
    k_ = 0
    for x, y, w, h, o in raw:
        key = tuple(round(v, 1) if not isinstance(v, str) else v for v in (x, y, w, h, o))
        if key in seen:
            continue
        seen.add(key)
        k_ += 1
        if o == "v":
            a_, b_ = reach(x + w / 2, y, 0, -1), reach(x + w / 2, y + h, 0, 1)
            walls.append({"id": f"P{k_}", "a": (x + w / 2, y - a_), "b": (x + w / 2, y + h + b_), "t": w, "outer": False})
        else:
            a_, b_ = reach(x, y + h / 2, -1, 0), reach(x + w, y + h / 2, 1, 0)
            walls.append({"id": f"P{k_}", "a": (x - a_, y + h / 2), "b": (x + w + b_, y + h / 2), "t": h, "outer": False})
    # ---- ailas ----
    def host(o, s, p0, p1, outer_only=False):
        """Siena, uz kuras guļ aila: ārsienai pēc ārējās malas (on_edge), starpsienai pēc ass."""
        e = c.on_edge(o, s, p0, p1)
        if e is not None:
            return edge_wall[c.edges.index(e)]
        if outer_only:
            return None
        for w in walls:
            if w["outer"]:
                continue
            ax, ay, bx, by = w["a"][0], w["a"][1], w["b"][0], w["b"][1]
            if o == "v" and abs(ax - bx) < 1 and abs(ax - s) < w["t"] / 2 + 30 and min(ay, by) - 30 <= (p0 + p1) / 2 <= max(ay, by) + 30:
                return w["id"]
            if o == "h" and abs(ay - by) < 1 and abs(ay - s) < w["t"] / 2 + 30 and min(ax, bx) - 30 <= (p0 + p1) / 2 <= max(ax, bx) + 30:
                return w["id"]
        return None

    wmap = {w["id"]: w for w in walls}

    def offset_on(wid, cx, cy):
        w = wmap[wid]
        dx, dy = w["b"][0] - w["a"][0], w["b"][1] - w["a"][1]
        L = math.hypot(dx, dy) or 1.0
        return ((cx - w["a"][0]) * dx + (cy - w["a"][1]) * dy) / L

    opens = []
    for w in m.get("windows") or []:
        if w.get("shape"):
            notes.append("Loga ar formu (shape) izlaists")
            continue
        o = w["o"]
        u = w["x"] if o == "h" else w["y"]
        s = w["y"] if o == "h" else w["x"]
        wid = host(o, s, u, u + w["len"], outer_only=True)
        if not wid:
            notes.append(f"Logs ({w['x']},{w['y']}) nav uz sienas, izlaists")
            continue
        cx, cy = (u + w["len"] / 2, wmap[wid]["a"][1]) if o == "h" else (wmap[wid]["a"][0], u + w["len"] / 2)
        opens.append({"tips": "logs", "siena": wid, "poz": offset_on(wid, cx, cy), "platums": w["len"], "augstums": w["head"] - w["sill"],
                      "palodze": w["sill"], "kind": w.get("kind"), "daļas": (len(w["parts"]) if isinstance(w.get("parts"), list) else int(w.get("parts") or 1))})
    for d in m.get("doors") or []:
        o = d["o"]
        u = d["x"] if o == "h" else d["y"]
        s = d["y"] if o == "h" else d["x"]
        wid = host(o, s, u, u + d["w"])
        if not wid:
            notes.append(f"Durvis ({d['x']},{d['y']}) nav uz sienas, izlaistas")
            continue
        cx, cy = (u + d["w"] / 2, wmap[wid]["a"][1]) if o == "h" else (wmap[wid]["a"][0], u + d["w"] / 2)
        opens.append({"tips": "durvis", "siena": wid, "poz": offset_on(wid, cx, cy), "platums": d["w"], "augstums": 2100, "palodze": 0,
                      "ieeja": bool(d.get("entry"))})
    # ---- telpas (zonas) ----
    zones = []
    for i, room in enumerate(m.get("rooms") or []):
        for j, (rx, ry, rw, rh) in enumerate(room.get("r", [])):
            zones.append({"nr": f"1.{i + 1:02d}" + (f".{j + 1}" if j else ""), "nosaukums": room.get("n", ""),
                          "poly": [(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)]})
    # ---- jumts ----
    x0, y0, x1, y1 = (min(p[0] for p in c.poly), min(p[1] for p in c.poly), max(p[0] for p in c.poly), max(p[1] for p in c.poly))
    roof = None
    if m.get("jumts"):
        if c.tanH:
            notes.append("Četrslīpju jumts šajā versijā netiek veidots (tikai divslīpju); jumts izlaists")
        else:
            roof = {"slipums": c.pitch, "dzega_mm": c.eave, "parkare_mm": c.ov, "biezums_mm": G.ROOF_TH, "bounds": (x0, y0, x1, y1)}
    if len(c.poly) > 4:
        notes.append("Ēkas kontūra nav taisnstūris: jumts var neatbilst")
    ridge = c.eave + (min(x1 - x0, y1 - y0) / 2) * c.tan + G.ROOF_TH
    return {"id": m.get("id", "projekts"), "nosaukums": m.get("nosaukums", m.get("id", "")), "D": c.D, "W": c.W,
            "augstums_mm": c.eave if not roof else ridge, "eave": c.eave, "walls": walls, "opens": opens, "zones": zones,
            "roof": roof, "piezimes": notes, "razotajs": "MM"}


TEMPLATE = r'''# -*- coding: utf-8 -*-
"""ArchiCAD (Tapir) skripts: __ID__. Ģenerēts no model.json ar SBE Architect (bot/archicad.py).

Palaišana: ArchiCAD > File > New (tukšs projekts) > Tapir > Run script > šis fails.
Bez ArchiCAD pārbaude:  python __FILE__ --dry
Papildu: --port 19723   --fav "ceļš uz mapi ar logu favorītiem (.xml)"
Vajag: ArchiCAD ar Tapir pievienojumu. Tikai standarta bibliotēka.
"""
import json, sys, urllib.request

DATA = json.loads(r"""__DATA__""")
M = 0.001
DRY = "--dry" in sys.argv
PORT = None
FAV_DIR = sys.argv[sys.argv.index("--fav") + 1] if "--fav" in sys.argv else None


def _post(body):
    req = urllib.request.Request("http://127.0.0.1:%d" % PORT, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def connect():
    global PORT
    if DRY:
        return
    ports = [int(sys.argv[sys.argv.index("--port") + 1])] if "--port" in sys.argv else range(19723, 19744)
    for p in ports:
        PORT = p
        try:
            if _post({"command": "API.IsAlive"}).get("result", {}).get("isAlive"):
                return
        except Exception:
            pass
    sys.exit("Nav atrasts ArchiCAD ar Tapir (porti 19723-19743). Atver ArchiCAD un pārbaudi, ka Tapir ir uzstādīts.")


def cmd(name, params=None, soft=False):
    params = params or {}
    if DRY:
        print("---", name, json.dumps(params, ensure_ascii=False)[:300])
        return _dry(name, params)
    try:
        r = _post({"command": "API.ExecuteAddOnCommand", "parameters": {
            "addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": name}, "addOnCommandParameters": params}})
    except Exception as ex:
        if soft:
            return None
        sys.exit("%s neizdevās: %s" % (name, ex))
    if not r.get("succeeded"):
        if soft:
            return None
        sys.exit("%s neizdevās: %s" % (name, r.get("error")))
    return r["result"]["addOnCommandResponse"]


def _dry(name, p):
    for k in p:
        if isinstance(p[k], list) and name.startswith("Create"):
            return {"elements": [{"elementId": {"guid": "dry-%s-%d" % (name, i)}} for i in range(len(p[k]))]}
    return {}


def ids(res, what):
    out = []
    for i, e in enumerate((res or {}).get("elements", [])):
        if "elementId" not in e:
            sys.exit("%s #%d neizveidojās: %s" % (what, i, e.get("error", e)))
        out.append(e["elementId"])
    return out


def xy(p):
    """plāna mm (y uz dienvidiem) -> ArchiCAD m (y uz ziemeļiem)"""
    return {"x": p[0] * M, "y": (DATA["D"] - p[1]) * M}


def favs(kind):
    if DRY:
        return []
    return (cmd("GetFavoritesByType", {"elementType": kind}, soft=True) or {}).get("favorites", [])


def window_fav(o, wf):
    two = o.get("daļas", 1) > 1 or o["platums"] >= 1200
    fixed = False
    code = ("L06" if fixed else "L07") if two else ("L01" if fixed else "L02")
    if o.get("kind") == "hopper":
        code = "L03" if not two else "L07"
    if o["palodze"] <= 50:
        code = "L10" if two else "L05"
    return next((f for f in wf if f.startswith(code + " ") or f == code), None)


def main():
    d = DATA
    rep = {"sienas": 0, "logi": 0, "durvis": 0, "zonas": 0, "jumts": 0, "piezīmes": list(d["piezimes"])}
    connect()
    cmd("ChangeWindow", {"windowType": "FloorPlan", "storyIndex": 0}, soft=True)
    cmd("SetStories", {"stories": [{"name": "1. stāvs", "level": 0.0, "dispOnSections": True}]})
    if FAV_DIR and not DRY:
        cmd("ImportFavorites", {"path": FAV_DIR, "importFolders": False, "conflictPolicy": "Skip"}, soft=True)
    wf, wallf = favs("Window"), favs("Wall")
    # ---- sienas ----
    h = d["augstums_mm"]
    items = []
    for w in d["walls"]:
        o = {"begCoordinate": xy(w["a"]), "endCoordinate": xy(w["b"]), "floorIndex": 0, "zCoordinate": 0.0,
             "height": (h if w["outer"] else d["eave"] - 300) * M, "referenceLineLocation": "Center"}
        pref = "MM S-04" if w["outer"] else "MM Starpsiena"
        f = next((x for x in wallf if x.startswith(pref)), None)
        if f:
            o["favoriteName"] = f
        else:
            o.update(structureType="Basic", thickness=w["t"] * M)
        items.append(o)
    wid = dict(zip([w["id"] for w in d["walls"]], ids(cmd("CreateWalls", {"wallsData": items}), "Siena")))
    rep["sienas"] = len(items)
    if not any(x.startswith("MM S-04") for x in wallf):
        rep["piezīmes"].append("Nav pīrāga favorītu 'MM S-04 / MM Starpsiena': sienas ir ar Basic biezumu (importē favorītus un palaid vēlreiz)")
    # ---- logi un durvis ----
    win, door = [], []
    for a in d["opens"]:
        x = {"ownerWallId": wid[a["siena"]], "centerOffset": a["poz"] * M, "width": a["platums"] * M,
             "height": a["augstums"] * M, "sillHeight": a["palodze"] * M}
        if a["tips"] == "durvis":
            door.append(x)
        else:
            f = window_fav(a, wf)
            if f:
                x["favoriteName"] = f
            win.append(x)
    if win:
        rep["logi"] = len(ids(cmd("CreateWindows", {"windowsData": win}), "Logs"))
        if not wf:
            rep["piezīmes"].append("Nav logu favorītu L01-L12: logi ar noklusējuma iestatījumiem (pievieno --fav <mape>)")
    if door:
        rep["durvis"] = len(ids(cmd("CreateDoors", {"doorsData": door}), "Durvis"))
        rep["piezīmes"].append("Durvju vēršanās pusi pārbaudi ArchiCAD (plāns apgriezts pa y)")
    # ---- zonas ----
    zs = [{"floorIndex": 0, "name": z["nosaukums"], "numberStr": z["nr"],
           "geometry": {"polygonCoordinates": [xy(p) for p in z["poly"]]}} for z in d["zones"]]
    if zs:
        rep["zonas"] = len(ids(cmd("CreateZones", {"zonesData": zs}), "Zona"))
    # ---- jumts: divas vienslīpes plaknes ----
    r = d["roof"]
    if r:
        import math
        x0, y0, x1, y1 = r["bounds"]
        ov, ym = r["parkare_mm"], (y0 + y1) / 2
        a = math.radians(r["slipums"])
        planes = [((x0 - ov, y0 - ov, x1 + ov, ym), (x0 - ov, y0), (x1 + ov, y0)),
                  ((x0 - ov, ym, x1 + ov, y1 + ov), (x1 + ov, y1), (x0 - ov, y1))]
        rd = []
        for (ax, ay, bx, by), beg, end in planes:
            rd.append({"level": r["dzega_mm"] * M, "floorIndex": 0, "structureType": "Basic", "thickness": r["biezums_mm"] * M,
                       "polygonCoordinates": [xy((ax, ay)), xy((bx, ay)), xy((bx, by)), xy((ax, by))],
                       "pivotLine": {"begCoordinate": xy(beg), "endCoordinate": xy(end)}, "angle": a})
        res = cmd("CreateRoofs", {"roofsData": rd}, soft=True)
        rid = [e["elementId"] for e in (res or {}).get("elements", []) if "elementId" in e]
        rep["jumts"] = len(rid)
        if not rid:
            rep["piezīmes"].append("Jumts neizveidojās (Tapir bez CreateRoofs?)")
        else:
            outer = [wid[w["id"]] for w in d["walls"] if w["outer"]]
            if cmd("TrimElements", {"elements": [{"elementId": e} for e in outer + rid]}, soft=True) is None and not DRY:
                rep["piezīmes"].append("Tapir bez TrimElements: frontonu sienas nav pievilktas jumtam")
    print("\nATSKAITE %s: sienas %d, logi %d, durvis %d, zonas %d, jumta plaknes %d" % (
        d["id"], rep["sienas"], rep["logi"], rep["durvis"], rep["zonas"], rep["jumts"]))
    for n in rep["piezīmes"]:
        print(" - " + n)
    print(" - Nav veidots: grīdas plātnes, cokols, mansarda logi, mēbeles, layouti (skat. SBE_skice.tpl)")


if __name__ == "__main__":
    main()
'''


def script(m, filename=None):
    d = data_of(m)
    name = filename or f"{d['id']}_archicad.py"
    txt = json.dumps(d, ensure_ascii=False, separators=(",", ":"), default=list)
    assert '"""' not in txt
    return TEMPLATE.replace("__ID__", d["id"]).replace("__FILE__", name).replace("__DATA__", txt), name


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    src = argv[1]
    m = G.load(src)
    out = argv[2] if len(argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(src)), "archicad")
    os.makedirs(out, exist_ok=True)
    txt, name = script(m)
    path = os.path.join(out, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
