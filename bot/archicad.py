"""ArchiCAD skripts (Tapir) no model.json, KLIENTA PROJEKTS.

    python archicad.py <model.json> [izvades mape]

Izvade: <id>_archicad.py: viens Python skripts ar project.json iekšā, kas palaiž SBE dzinēju (SBE-ARHITEKTS: python -m sbe archicad).
ArchiCAD: atver SBE_skice.tpl, Tapir > Run script > <id>_archicad.py. Favorīti un layouti nāk no veidnes un dzinēja, netiek veidoti otrreiz.
Uzbūvē: stāvu, ārsienas (pa ēkas kontūru), starpsienas (no telpu spraugām), logus, durvis, zonas, divslīpju jumtu.
Ar mansardu (loft.poly + loft.level) veido 2. stāvu, un jumts ceļas pa tā kontūru; jumts.papildu = papildu jumti (ieejas bloks), projekts.siena_mm = ārsienas biezums.
Koordinātas: plāna mm (y uz dienvidiem) → ArchiCAD m, y apgriezts (y_ac = D - y), lai plāns nebūtu spoguļots.
Ko skripts vēl NEdara (atskaitē parādās kā piezīmes): grīdas plātnes, cokols, mansarda logi, mēbeles, layouti.
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


def _floor_data(m, pref="", fl=1):
    """Viena stāva dati: ārsienas pa kontūru, starpsienas, ailas, zonas. pref = sienu id priekšvārds (2. stāvam "L")."""
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
        wid = f"{pref}E{i + 1}"
        walls.append({"id": wid, "a": a, "b": b, "t": T, "outer": True})
        edge_wall[i] = wid
    # ---- starpsienas (tā pati loģika kā geometry.py): spraugas 100..200 mm starp telpām ----
    R = [tuple(r[:4]) for room in (m.get("rooms") or []) for r in room.get("r", [])]   # r[4:] = sienu pielaides (cad.js), ģeometrijai nevajag
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
            walls.append({"id": f"{pref}P{k_}", "a": (x + w / 2, y - a_), "b": (x + w / 2, y + h + b_), "t": w, "outer": False})
        else:
            a_, b_ = reach(x, y + h / 2, -1, 0), reach(x + w, y + h / 2, 1, 0)
            walls.append({"id": f"{pref}P{k_}", "a": (x - a_, y + h / 2), "b": (x + w + b_, y + h / 2), "t": h, "outer": False})
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
                      "ieeja": bool(d.get("entry")), "o": o, "hinge": d.get("hinge"), "side": d.get("side")})
    # ---- telpas (zonas) ----
    zones = []
    for i, room in enumerate(m.get("rooms") or []):
        for j, (rx, ry, rw, rh) in enumerate(tuple(r_[:4]) for r_ in room.get("r", [])):
            zones.append({"nr": f"{fl}.{i + 1:02d}" + (f".{j + 1}" if j else ""), "nosaukums": room.get("n", ""),
                          "poly": [(rx, ry), (rx + rw, ry), (rx + rw, ry + rh), (rx, ry + rh)]})
    return {"c": c, "walls": walls, "opens": opens, "zones": zones, "notes": notes}


def data_of(m):
    """model.json -> vienkārši dati skriptam (mm, plāna koordinātes, y uz dienvidiem). Ar mansardu (m["loft"]) otrs stāvs."""
    f1 = _floor_data(m)
    c, notes = f1["c"], f1["notes"]
    floors = [f1]
    lf = m.get("loft") or {}
    if lf.get("poly") and lf.get("level"):
        m2 = {**m, **lf, "id": str(m.get("id", "")) + " mansards"}
        f2 = _floor_data(m2, "L", 2)
        floors.append(f2)
        notes += f2["notes"]
    top = floors[-1]["c"]
    # ---- jumts: pamats = augšējā stāva ārsienu kontūra (ar mansardu tā ir korpuss bez ieejas bloka, tāpēc kore nav nobīdīta) ----
    x0, y0, x1, y1 = (min(p[0] for p in top.poly), min(p[1] for p in top.poly), max(p[0] for p in top.poly), max(p[1] for p in top.poly))
    roof = None
    J = m.get("jumts") or {}
    if J:
        roof = {"forma": "cetrslipju" if c.tanH else "divslipju", "slipums": c.pitch, "dzega_mm": c.eave, "parkare_mm": c.ov,
                "biezums_mm": float(J.get("biezums_mm") or G.ROOF_TH), "bounds": (x0, y0, x1, y1),
                "papildu": [e for e in (J.get("papildu") or []) if e.get("taisnsturis")]}
        if c.tanH:
            notes.append("Četrslīpju jumts veidots pa ēkas apvalka robežrāmi (ne pa precīzo kontūru)")
    if len(top.poly) > 4:
        notes.append("Ēkas kontūra nav taisnstūris: jumts var neatbilst")
    ridge = c.eave + (min(x1 - x0, y1 - y0) / 2) * c.tan + float(J.get("biezums_mm") or G.ROOF_TH)
    d = {"id": m.get("id", "projekts"), "nosaukums": m.get("nosaukums", m.get("id", "")), "D": c.D, "W": c.W,
         "augstums_mm": c.eave if not roof else ridge, "eave": c.eave, "walls": f1["walls"], "opens": f1["opens"], "zones": f1["zones"],
         "roof": roof, "piezimes": notes, "razotajs": "MM", "projekts": m.get("projekts") or {}}
    if len(floors) > 1:
        d["loft"] = {"level": float(lf["level"]), "walls": floors[1]["walls"], "opens": floors[1]["opens"], "zones": floors[1]["zones"]}
    return d


def _veras(o, wall):
    """Durvju vēršanās (hinge 's' = eņģe ailas sākumā pa plāna asi, side = vēršanās uz +y/+x) -> sbe dzinēja "L+/L-/R+/R-"
    (L = eņģe sienas sākumā, + = sienas normāle (-uy, ux), y uz augšu)."""
    if o.get("hinge") not in ("s", "e", "w", "n") or o.get("side") not in (1, -1):
        return "L+"
    (ax, ay), (bx, by) = wall["a"], wall["b"]
    dx, dy = bx - ax, by - ay                       # plāna koordinātēs (y uz dienvidiem)
    along = dx if o["o"] == "h" else dy             # kustība pa plāna asi (x horizontālām, y vertikālām sienām)
    start_hinge = (o["hinge"] == "s") == (along > 0)
    sv = (0, o["side"]) if o["o"] == "h" else (o["side"], 0)
    n_plan = (dy, -dx)                              # dzinēja normāle (y uz augšu) pārvērsta atpakaļ plāna koordinātēs
    plus = sv[0] * n_plan[0] + sv[1] * n_plan[1] > 0
    return ("L" if start_hinge else "R") + ("+" if plus else "-")


def _stavs(items, D, pre, nr_id, level, height):
    """Viena stāva bloks project.json: sienas, ailas, telpas (y apgriezts uz augšu)."""
    flip = lambda pt: [round(pt[0], 2), round(D - pt[1], 2)]
    wmap = {w["id"]: w for w in items["walls"]}
    sienas = []
    for w in items["walls"]:
        e = {"id": w["id"], "no": flip(w["a"]), "lidz": flip(w["b"])}
        if w["outer"]:
            e["pirags"] = f"{pre}-S04"
        elif abs(w["t"] - 195) < 1:
            e["pirags"] = f"{pre}-SS195"
        else:
            e["biezums"] = round(w["t"], 1)
        sienas.append(e)
    ailas = []
    for a in items["opens"]:
        w = wmap[a["siena"]]
        # dzinējs mēra pozīciju no sienas "no" gala līdz ailas malai; mūsu "poz" = ailas centrs no sienas sākuma
        o = {"siena": a["siena"], "tips": a["tips"], "pozicija_mm": round(a["poz"] - a["platums"] / 2, 1), "platums": a["platums"],
             "augstums": a["augstums"]}
        if a["tips"] == "durvis":
            o["veras"] = _veras(a, w)
        else:
            o["palodze"] = a["palodze"]
            o["veids"] = "casement2" if a.get("daļas", 1) > 1 else str(a.get("kind") or "tilt")
        ailas.append(o)
    telpas = []
    for z in items["zones"]:
        xs, ys = [p[0] for p in z["poly"]], [p[1] for p in z["poly"]]
        telpas.append({"nr": z["nr"], "nosaukums": z["nosaukums"],
                       "taisnsturi": [[round(min(xs), 1), round(D - max(ys), 1), round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)]]})
    return {"id": nr_id, "limenis_mm": level, "augstums_mm": round(height), "sienas": sienas, "telpas": telpas, "ailas": ailas}


def project_json(m, nr="001"):
    """model.json -> project.json priekš SBE dzinēja (SBE-ARHITEKTS: python -m sbe archicad). mm, y uz augšu (plāna y apgriezts).
    Ar mansardu (loft.poly + loft.level) tiek veidots 2. stāvs, un jumts ceļas pa tā ārsienu kontūru."""
    d = data_of(m)
    D = d["D"]
    pre = str((m.get("projekts") or {}).get("pirags_prefikss") or "MM")
    lf = d.get("loft")
    st1 = _stavs(d, D, pre, "1", 0, lf["level"] if lf else d["eave"])
    if not lf:   # vienstāva projektā bloks kā agrāk (bez limeņa un augstuma)
        st1.pop("limenis_mm"); st1.pop("augstums_mm")
    pr = (d.get("projekts") or {})
    p = {"nr": nr, "nosaukums": d["nosaukums"], "razotajs": "mm", "klients": pr.get("klients", ""),
         "revizija": 1, "augstums_mm": lf["level"] if lf else d["eave"], "stavi": [st1],
         "objekts": {"nosaukums": "Dzīvojamā māja " + str(d["nosaukums"]),
                     "adrese": ", ".join(s_.strip() for s_ in (pr.get("adrese") or []) if s_.strip())},
         "noformejums": "skice"}
    r = d["roof"]
    if lf:   # 2. stāva sienas līdz kores augstumam (jumts tās apgriež ar TrimElements)
        p["stavi"].append(_stavs(lf, D, pre, "2", lf["level"], max(d["augstums_mm"] - lf["level"], 1000)))
    if r:
        p["jumts"] = {"forma": r.get("forma", "divslipju"), "slipums": r["slipums"], "parkare_mm": r["parkare_mm"], "dzega_mm": r["dzega_mm"],
                      "biezums_mm": r["biezums_mm"], "kore": "x"}
        if r.get("papildu"):   # papildu jumti (piem. ieejas mezgla plakanais): model.json plāna koordinātēs -> y uz augšu
            p["jumts"]["papildu"] = [{**{k: v for k, v in e.items() if k != "taisnsturis"},
                                      "taisnsturis": [e["taisnsturis"][0], round(D - e["taisnsturis"][3], 2), e["taisnsturis"][2], round(D - e["taisnsturis"][1], 2)]}
                                     for e in r["papildu"]]
    flip = lambda x, y: [round(x, 2), round(D - y, 2)]
    # ---- kāpnes uz mansardu: telpa "Kāpnes" 1. stāvā; augšējais gals = tas, kam blakus gaitenis (citādi dienvidu gals) ----
    if lf:
        rm = [(room, tuple(r_[:4])) for room in (m.get("rooms") or []) for r_ in room.get("r", [])]
        st = next((r_ for room, r_ in rm if str(room.get("n", "")).lower().startswith(("kāpnes", "kapnes"))), None)
        if st:
            x, y, w, h = st
            vert = h >= w
            ga = [r_ for room, r_ in rm if str(room.get("n", "")).lower().startswith("gaiten") and r_ != st]
            near = lambda r_, ex, ey: abs(r_[0] - ex) < 400 and abs(r_[1] - ey) < 400 or (r_[0] <= ex <= r_[0] + r_[2] and r_[1] - 400 <= ey <= r_[1] + r_[3] + 400)
            if vert:
                cx = x + w / 2; ends = [(cx, y), (cx, y + h)]; run = h
            else:
                cy = y + h / 2; ends = [(x, cy), (x + w, cy)]; run = w
            top = 1 if any(near(g, *ends[1]) for g in ga) or not any(near(g, *ends[0]) for g in ga) else 0
            bot, up = ends[1 - top], ends[top]
            n = max(2, round(lf["level"] / 173))
            p["kapnes"] = [{"stavs": 0, "no": flip(*bot), "lidz": flip(*up), "platums": round(w if vert else h, 1), "pakapieni": n,
                            "augstums": lf["level"], "piezime": "ģenerēts no telpas 'Kāpnes' (gājiens uz gaiteni)"}]
    # ---- asis no modeļa (y apgriezts, kā plānā) ----
    ax = m.get("axes") or {}
    if ax.get("x") and ax.get("y") and (len(ax["x"]) > 2 or len(ax["y"]) > 2):   # tikai papildu asis; parastās A-B / 1-2 uzliek dzinējs pats
        p["asis"] = {"x": [[round(v, 1), str(n_)] for v, n_ in ax["x"]], "y": [[round(D - v, 1), str(n_)] for v, n_ in ax["y"]]}
    # ---- ieejas bloka (jumts.papildu) ārsienām cita fasādes virsma, ja norādīta projekts.ieejas_virsma ----
    iv = (m.get("projekts") or {}).get("ieejas_virsma")
    if iv and r and r.get("papildu"):
        ax0, ay0, ax1, ay1 = r["papildu"][0]["taisnsturis"]
        mg = float((m.get("projekts") or {}).get("siena_mm") or 283.5) + 50   # sienu ass ir iebīdīta, stūris ar korpusa sienu iznāk līdz T aiz bloka malas
        inb = lambda q: ax0 - mg <= q[0] <= ax1 + mg and ay0 - mg <= q[1] <= ay1 + mg
        ids = [w["id"] for w in d["walls"] if w["outer"] and inb(w["a"]) and inb(w["b"])]
        if ids:
            p["fasades_virsmas"] = [{"virsma": iv, "stavs": 0, "sienas": ids}]
    p["_piezimes_no_model_json"] = d["piezimes"]
    return p


RUNNER = r"""# -*- coding: utf-8 -*-
# __ID__: SBE Architect -> ArchiCAD (Tapir). Ģenerēts no model.json (bot/archicad.py), neko neveido otrreiz:
# tas tikai ieliek project.json un palaiž TAVU esošo SBE dzinēju (favorīti L01-L12, pīrāgi, Layout Book no SBE_skice.tpl).
# Palaišana: atver SBE_skice.tpl (tukšs projekts), Tapir > Run script > šis fails.   Pārbaude bez ArchiCAD: python __FILE__ --dry
import os, sys, io, json, traceback

SBE_DEFAULT = r"__SBE__"
PROJECT = json.loads(r'''__DATA__''')
HERE = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry" in sys.argv


def sbe_root():
    for c in (os.environ.get("SBE_ARHITEKTS"), SBE_DEFAULT, os.path.join(os.path.expanduser("~"), "Desktop", "Projekti", "SBE-ARHITEKTS")):
        if c and os.path.isdir(os.path.join(c, "sbe")):
            return c
    sys.exit("Nav atrasta SBE-ARHITEKTS mape (ar apakšmapi sbe). Norādi vides mainīgo SBE_ARHITEKTS vai labo SBE_DEFAULT šajā failā.")


class Tee(io.StringIO):
    def write(self, s):
        if sys.__stdout__:
            sys.__stdout__.write(s)
        return super().write(s)


SBE = sbe_root()
pdir = os.path.join(HERE, "__ID___projekts")
os.makedirs(pdir, exist_ok=True)
json.dump(PROJECT, open(os.path.join(pdir, "project.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.path.insert(0, SBE)
os.chdir(SBE)
from sbe.__main__ import main
from sbe import tapir

_post0 = tapir._post


def _post(body):
    # ieraksta žurnālā katru Tapir kļūdu (try_cmd tās citādi norij, piem. jumta izveidi)
    r = _post0(body)
    try:
        c = ((body.get("parameters") or {}).get("addOnCommandId") or {}).get("commandName")
        resp = (r.get("result") or {}).get("addOnCommandResponse")
        bad = c and (not r.get("succeeded") or (isinstance(resp, dict) and (resp.get("success") is False or any(
            isinstance(e, dict) and "error" in e for k in resp.values() if isinstance(k, list) for e in k))))
        if bad:
            print("TAPIR KĻŪDA " + c + ": " + json.dumps(r, ensure_ascii=False)[:900])
    except Exception:
        pass
    return r


tapir._post = _post

buf = Tee()
old = sys.stdout
sys.stdout = buf
try:
    args = ["archicad", pdir, "--jauns", "--force"] + (["--dry"] if DRY else [])
    print("rezultāts:", main(args))
except BaseException:
    traceback.print_exc(file=buf)
    print("KĻŪDA:", sys.exc_info()[1])
finally:
    sys.stdout = old
    log = os.path.join(HERE, "__ID___archicad_log.txt")
    open(log, "w", encoding="utf-8").write(buf.getvalue())
    print("\nŽurnāls: " + log)
"""


def sbe_default():
    """Ceļš uz SBE-ARHITEKTS: ~/.sbe-arhivs.json "sbe_arhitekts" vai noklusējums."""
    try:
        c = json.load(open(os.path.join(os.path.expanduser('~'), '.sbe-arhivs.json'), encoding='utf-8'))
        if c.get('sbe_arhitekts'):
            return c['sbe_arhitekts']
    except Exception:
        pass
    return os.path.join(os.path.expanduser('~'), 'Desktop', 'Projekti', 'SBE-ARHITEKTS')


def script(m, filename=None):
    """-> (skripta teksts, faila nosaukums). Skripts ieliek project.json un palaiž SBE dzinēju (SBE-ARHITEKTS)."""
    pj = project_json(m)
    name = filename or f"{m.get('id', 'projekts')}_archicad.py"
    txt = json.dumps(pj, ensure_ascii=False, indent=1)
    assert "'''" not in txt
    out = (RUNNER.replace("__ID__", str(m.get("id", "projekts"))).replace("__FILE__", name)
           .replace("__SBE__", sbe_default()).replace("__DATA__", txt))
    return out, name


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
