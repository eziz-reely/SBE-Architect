"""SketchUp 3D modelis no model.json (KLIENTA PROJEKTS).

    python skp.py <model.json> [izvades mape]

Izvade (mapē `3d/` blakus model.json): TIKAI <id>_skp.rb, SketchUp Ruby skripts
(Window > Ruby Console: load 'ceļš/<id>_skp.rb'), uztaisa grupas ar materiāliem. [MM] .dae un .obj netaisa
(funkcijas write_dae / write_obj paliek kodā, bet netiek izsauktas).

Ko modelis satur: grīdas panelis uz stabiem, cokols, ārsienas ar logu un durvju caurumiem, iekšsienas (iegūtas kā
iekšējā laukuma un telpu starpība), mansarda grīda, divslīpju jumts, logi (rāmis, apmale, stikls), ārdurvis,
mansarda logi (arī piecstūra). Mēbeles netiek modelētas. Koordinātas mm, X uz austrumiem, Y uz ziemeļiem, Z uz augšu,
±0,000 = grīdas pīrāga augšas.
"""
import json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
T = sum(l[1] for l in CFG['layers']['S1']['layers'])      # ārsiena 283,5
FT = sum(l[1] for l in CFG['layers']['G1']['layers'])     # grīdas pīrāgs 275,5
ROOF_T = sum(l[1] for l in CFG['layers']['J1']['layers'])
PITCH = CFG['roof']['pitch']
P1 = sum(l[1] for l in CFG['layers'].get('P1', {'layers': [['', 164.5]]})['layers'])
GROUND = -CFG['floor'].get('posts_ground', 600)
RAL = {'RAL 9016': '#F1F0EA', 'RAL 7016': '#383E42', 'RAL 9005': '#1D1D1D'}


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------- ģeometrija: visi ķermeņi = trijstūri (SketchUp ass: Y uz ziemeļiem) ----------
class Mesh:
    def __init__(self, D):
        self.D = D
        self.tris = defaultdict(list)     # materiāls -> [(p, q, r)]

    def box(self, mat, x0, y0, z0, x1, y1, z1):
        """Kaste PLĀNA koordinātēs (Y uz leju lapā), pārvērsta uz SketchUp (Y uz ziemeļiem)."""
        ya, yb = self.D - y1, self.D - y0
        if x1 - x0 < 0.01 or yb - ya < 0.01 or z1 - z0 < 0.01:
            return
        P = [(x0, ya, z0), (x1, ya, z0), (x1, yb, z0), (x0, yb, z0), (x0, ya, z1), (x1, ya, z1), (x1, yb, z1), (x0, yb, z1)]
        for a, b, c, d in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            self.tris[mat] += [(P[a], P[b], P[c]), (P[a], P[c], P[d])]

    def prism_x(self, mat, x0, x1, profile):
        """Ķermenis, izvilkts pa X no izliekta profila (y_plāna, z) punktiem pretēji pulksteņrādītājam skatā no +X."""
        pr = [(self.D - y, z) for y, z in profile]            # uz SketchUp Y
        # profila orientācija: nodrošina CCW (Y,Z) skatā no +X
        area = sum(pr[i][0] * pr[(i + 1) % len(pr)][1] - pr[(i + 1) % len(pr)][0] * pr[i][1] for i in range(len(pr)))
        if area < 0:
            pr = pr[::-1]
        for i in range(1, len(pr) - 1):
            self.tris[mat].append(((x1, *pr[0]), (x1, *pr[i]), (x1, *pr[i + 1])))
            self.tris[mat].append(((x0, *pr[0]), (x0, *pr[i + 1]), (x0, *pr[i])))
        for i in range(len(pr)):
            a, b = pr[i], pr[(i + 1) % len(pr)]
            self.tris[mat] += [((x0, *a), (x1, *a), (x1, *b)), ((x0, *a), (x1, *b), (x0, *b))]


def sub(b, c):
    """Kaste b mīnus kaste c (abas (x0,y0,z0,x1,y1,z1)); atgriež kastu sarakstu."""
    if any(min(b[i + 3], c[i + 3]) - max(b[i], c[i]) <= 0.01 for i in range(3)):
        return [b]
    out = []
    cur = list(b)
    for ax in range(3):
        lo, hi = max(b[ax], c[ax]), min(b[ax + 3], c[ax + 3])
        if cur[ax] < lo - 0.01:
            p = list(cur); p[ax + 3] = lo; out.append(tuple(p))
            cur[ax] = lo
        if cur[ax + 3] > hi + 0.01:
            p = list(cur); p[ax] = hi; out.append(tuple(p))
            cur[ax + 3] = hi
    return out


def carve(b, cuts):
    pieces = [b]
    for c in cuts:
        pieces = [q for p in pieces for q in sub(p, c)]
    return pieces


def build(m):
    W, D = m['W'], m['D']
    pr = m.get('projekts') or {}
    tone = CFG['toni'][pr.get('tonis', 'peleks')]
    cok = RAL.get(pr.get('cokols') or 'RAL 9005', '#1D1D1D')
    logi = RAL.get(tone.get('logi', 'RAL 7016'), '#383E42')
    tan = math.tan(math.radians(PITCH))
    eave = m['jumts']['eave']
    thV = ROOF_T / math.cos(math.radians(PITCH))
    ridgeU = eave + (D / 2) * tan
    ceil = float(m.get('ceiling', 2200))
    mats = {'kladums': tone['sw'], 'jumts': RAL['RAL 7016'], 'cokols': cok, 'logi': logi, 'stikls': '#8FA3AD',
            'grida': '#CDBFA8', 'starpsienas': '#ECEAE4', 'zeme': '#9A9A96', 'sturi': '#F2F0EA'}
    M = Mesh(D)
    # zeme, cokols, grīdas panelis
    M.box('zeme', -1500, -1500, GROUND - 40, W + 1500, D + 1500, GROUND)
    M.box('cokols', 0, 0, GROUND + 40, W, D, -FT)
    M.box('kladums', 0, 0, -FT, W, D, 0)
    M.box('grida', T, T, 0, W - T, D - T, 10)

    # caurumi ārsienās: logi un ārdurvis; interjera durvis
    def wall_range(o, x, y, th):
        return None
    ext_cuts, int_cuts, trims = [], [], []
    for w in m['windows']:
        z0, z1 = w['sill'], w['head']
        if w['o'] == 'h':
            yy = (0, T) if w['y'] < D / 2 else (D - T, D)
            c = (w['x'], yy[0] - 1, z0, w['x'] + w['len'], yy[1] + 1, z1)
            face = ('h', yy[0] if w['y'] < D / 2 else yy[1], w['x'], w['x'] + w['len'], z0, z1, -1 if w['y'] < D / 2 else 1, yy)
        else:
            xx = (0, T) if w['x'] < W / 2 else (W - T, W)
            c = (xx[0] - 1, w['y'], z0, xx[1] + 1, w['y'] + w['len'], z1)
            face = ('v', xx[0] if w['x'] < W / 2 else xx[1], w['y'], w['y'] + w['len'], z0, z1, -1 if w['x'] < W / 2 else 1, xx)
        ext_cuts.append(c)
        trims.append(face)
    doors_leaf = []
    for d in m['doors']:
        if d['o'] == 'h':
            c = (d['x'], d['y'] - 1, 0, d['x'] + d['w'], d['y'] + d['th'] + 1, 2100)
        else:
            c = (d['x'] - 1, d['y'], 0, d['x'] + d['th'] + 1, d['y'] + d['w'], 2100)
        (ext_cuts if d.get('entry') else int_cuts).append(c)
        if d.get('entry'):
            doors_leaf.append(d)

    # ārsienas
    for b in [(T, 0, 0, W - T, T, eave), (T, D - T, 0, W - T, D, eave), (0, 0, 0, T, D, eave), (W - T, 0, 0, W, D, eave)]:
        for p in carve(b, ext_cuts):
            M.box('kladums', *p)
    for x0, x1 in ((0, T), (W - T, W)):
        M.prism_x('kladums', x0, x1, [(0, eave), (D, eave), (D / 2, ridgeU)])
    # stūru dēļi (sarkanajam tonim)
    if tone.get('sturi'):
        s = tone['sturi']
        for cx in (-15, W - s + 15):
            for cy in (-15, D - s + 15):
                M.box('sturi', cx, cy, -FT, cx + s, cy + s, eave)

    # iekšsienas = iekšējais laukums − telpas
    rooms = [tuple(r) for rm in m['rooms'] for r in rm['r']]
    xs = sorted({T, W - T, *[r[0] for r in rooms], *[r[0] + r[2] for r in rooms]})
    ys = sorted({T, D - T, *[r[1] for r in rooms], *[r[1] + r[3] for r in rooms]})
    cells = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if not any(r[0] <= cx <= r[0] + r[2] and r[1] <= cy <= r[1] + r[3] for r in rooms):
                cells.append([xs[i], ys[j], xs[i + 1], ys[j + 1]])
    merged = True
    while merged:                      # saplūdina blakus šūnas ar vienādu malu
        merged = False
        for a in cells:
            for b in cells:
                if a is b:
                    continue
                if a[1] == b[1] and a[3] == b[3] and abs(a[2] - b[0]) < .01:
                    a[2] = b[2]; cells.remove(b); merged = True; break
                if a[0] == b[0] and a[2] == b[2] and abs(a[3] - b[1]) < .01:
                    a[3] = b[3]; cells.remove(b); merged = True; break
            if merged:
                break
    for c in cells:
        for p in carve((c[0], c[1], 0, c[2], c[3], ceil), int_cuts):
            M.box('starpsienas', *p)

    # mansarda grīda
    lf = m.get('loft')
    if lf:
        lv = lf['level']
        for rm in lf['rooms']:
            if rm.get('void'):
                continue
            for r in rm['r']:
                M.box('grida', r[0], r[1], lv - P1, r[0] + r[2], r[1] + r[3], lv)

    # jumts (divslīpju, bez pārkares)
    for sgn in (1, -1):
        y0 = 0 if sgn == 1 else D
        q = [(y0, eave), (D / 2, ridgeU), (D / 2, ridgeU + thV), (y0, eave + thV)]
        # divi trijstūri kā prizma pa X: izlietojam prism_x ar izliektu četrstūri
        M.prism_x('jumts', 0, W, q)

    # logu rāmji, apmales, stikls (1. stāva logi — caurumos)
    cas = (CFG.get('win') or {}).get('casing', 100)
    fr = 70
    for kind, pos, a0, a1, z0, z1, out, rng in trims:
        for rect in _frame_boxes(kind, pos, a0, a1, z0, z1, out, rng, cas, fr):
            M.box(rect[0], *rect[1:])
    for d in doors_leaf:
        yy = (d['y'], d['y'] + d['th'])
        ymid = (yy[0] + yy[1]) / 2
        M.box('logi', d['x'], ymid - 30, 0, d['x'] + d['w'], ymid + 30, 2100)
        for rect in _frame_boxes('h', yy[1], d['x'], d['x'] + d['w'], 0, 2100, 1, yy, cas, 0):
            if rect[0] != 'stikls':
                M.box(rect[0], *rect[1:])
    # mansarda logi uz zīmējuma virsmas (virs sienas, zem kores)
    if lf:
        for w in lf['windows']:
            west = w['x'] < W / 2
            xo = 0 if west else W
            sgn = -1 if west else 1
            u0, u1 = w['y'], w['y'] + w['len']
            z0 = w['sill']
            if w.get('shape') == 'gable':
                off = 200
                zt = lambda u: eave + min(u, D - u) * tan - off
                prof = [(u0, z0), (u1, z0), (u1, zt(u1)), (D / 2, zt(D / 2)), (u0, zt(u0))]
            else:
                prof = [(u0, z0), (u1, z0), (u1, w['head']), (u0, w['head'])]
            xa, xb = (xo - 25, xo) if west else (xo, xo + 25)
            M.prism_x('logi', xa, xb, _grow(prof, 70))
            M.prism_x('stikls', xa - sgn * 0 + (-5 if west else 5), xb + (-5 if west else 5), prof)
    return M, mats


def _grow(poly, g):
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    out = []
    for u, z in poly:
        du, dz = u - cx, z - cz
        n = math.hypot(du, dz) or 1
        out.append((u + du / n * g, z + dz / n * g))
    return out


def _frame_boxes(kind, pos, a0, a1, z0, z1, out, rng, cas, fr):
    """Stikls + rāmis (vidū sienā) + apmale (ārpusē, tikai augšā un sānos, apakšā virs palodzes)."""
    res = []
    lo, hi = rng
    mid = (lo + hi) / 2
    g = 12
    if kind == 'h':
        res.append(('stikls', a0, mid - g / 2, z0, a1, mid + g / 2, z1))
        if fr:
            res += [('logi', a0, mid - 35, z0, a0 + fr, mid + 35, z1), ('logi', a1 - fr, mid - 35, z0, a1, mid + 35, z1),
                    ('logi', a0, mid - 35, z1 - fr, a1, mid + 35, z1), ('logi', a0, mid - 35, z0, a1, mid + 35, z0 + fr)]
        ya, yb = (pos - 30, pos) if out < 0 else (pos, pos + 30)
        if out < 0:
            ya, yb = pos - 30, pos
        res += [('logi', a0 - cas, ya, z0, a0, yb, z1 + cas), ('logi', a1, ya, z0, a1 + cas, yb, z1 + cas),
                ('logi', a0, ya, z1, a1, yb, z1 + cas)]
        if z0 > 0:
            res.append(('logi', a0, ya, z0 - cas, a1, yb, z0))
    else:
        res.append(('stikls', mid - g / 2, a0, z0, mid + g / 2, a1, z1))
        if fr:
            res += [('logi', mid - 35, a0, z0, mid + 35, a0 + fr, z1), ('logi', mid - 35, a1 - fr, z0, mid + 35, a1, z1),
                    ('logi', mid - 35, a0, z1 - fr, mid + 35, a1, z1), ('logi', mid - 35, a0, z0, mid + 35, a1, z0 + fr)]
        xa, xb = (pos - 30, pos) if out < 0 else (pos, pos + 30)
        res += [('logi', xa, a0 - cas, z0, xb, a0, z1 + cas), ('logi', xa, a1, z0, xb, a1 + cas, z1 + cas),
                ('logi', xa, a0, z1, xb, a1, z1 + cas)]
        if z0 > 0:
            res.append(('logi', xa, a0, z0 - cas, xb, a1, z0))
    return res


# ---------- izvade ----------
def write_obj(path, M, mats):
    lines, vi = ['# MM modelis, mm', 'mtllib %s' % os.path.basename(path).replace('.obj', '.mtl')], 1
    mtl = []
    for k, h in mats.items():
        r, g, b = hex2rgb(h)
        mtl.append(f'newmtl {k}\nKd {r:.3f} {g:.3f} {b:.3f}\n' + ('d 0.45\n' if k == 'stikls' else ''))
    for mat, tris in M.tris.items():
        lines.append('usemtl ' + mat)
        for t in tris:
            for p in t:
                lines.append('v %.2f %.2f %.2f' % p)
            lines.append('f %d %d %d' % (vi, vi + 1, vi + 2))
            vi += 3
    open(path, 'w').write('\n'.join(lines) + '\n')
    open(path.replace('.obj', '.mtl'), 'w').write('\n'.join(mtl))


def write_dae(path, M, mats, name):
    geoms, inst, effects, mat_x = [], [], [], []
    for k, h in mats.items():
        r, g, b = hex2rgb(h)
        a = 0.45 if k == 'stikls' else 1
        effects.append(f'<effect id="{k}-fx"><profile_COMMON><technique sid="c"><lambert><diffuse><color>{r:.3f} {g:.3f} {b:.3f} {a}</color></diffuse>'
                       f'{"<transparency><float>%.2f</float></transparency>" % a if a < 1 else ""}</lambert></technique></profile_COMMON></effect>')
        mat_x.append(f'<material id="{k}" name="{k}"><instance_effect url="#{k}-fx"/></material>')
    for mat, tris in M.tris.items():
        pts = ' '.join('%.2f %.2f %.2f' % p for t in tris for p in t)
        n = len(tris) * 3
        idx = ' '.join(str(i) for i in range(n))
        geoms.append(f'<geometry id="{mat}-g" name="{mat}"><mesh><source id="{mat}-p"><float_array id="{mat}-pa" count="{n * 3}">{pts}</float_array>'
                     f'<technique_common><accessor source="#{mat}-pa" count="{n}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>'
                     f'<vertices id="{mat}-v"><input semantic="POSITION" source="#{mat}-p"/></vertices>'
                     f'<triangles material="m" count="{len(tris)}"><input semantic="VERTEX" source="#{mat}-v" offset="0"/><p>{idx}</p></triangles></mesh></geometry>')
        inst.append(f'<node id="{mat}-n" name="{mat}"><instance_geometry url="#{mat}-g"><bind_material><technique_common>'
                    f'<instance_material symbol="m" target="#{mat}"/></technique_common></bind_material></instance_geometry></node>')
    xml = ('<?xml version="1.0" encoding="utf-8"?><COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">'
           '<asset><unit meter="0.001" name="millimeter"/><up_axis>Z_UP</up_axis></asset>'
           f'<library_effects>{"".join(effects)}</library_effects><library_materials>{"".join(mat_x)}</library_materials>'
           f'<library_geometries>{"".join(geoms)}</library_geometries>'
           f'<library_visual_scenes><visual_scene id="s" name="{name}">{"".join(inst)}</visual_scene></library_visual_scenes>'
           '<scene><instance_visual_scene url="#s"/></scene></COLLADA>')
    open(path, 'w', encoding='utf-8').write(xml)


def write_rb(path, M, mats, name):
    out = ["# MM modelis %s. KĀ PALAIST SketchUp: 1) File > New, mērvienības milimetri (Millimeters);" % name,
           "# 2) Extensions > Developer > Ruby Console (vecākās versijās Window > Ruby Console);",
           "# 3) ieraksti: load 'C:/ceļš/%s' (slīpsvītras uz priekšu /) un Enter; modelis parādīsies, tad Camera > Zoom Extents." % os.path.basename(path),
           "# Neko citu nevajag. Ja ceļā ir mīkstinājuma zīmes (ā, ē ...), nokopē failu uz C:/temp/ un ielādē no turienes.",
           'model = Sketchup.active_model', 'model.start_operation("MM %s", true)' % name, 'ents = model.active_entities', 'mats = {}']
    for k, h in mats.items():
        r, g, b = (int(x * 255) for x in hex2rgb(h))
        out.append(f'mats["{k}"] = model.materials.add("{k}"); mats["{k}"].color = Sketchup::Color.new({r}, {g}, {b})' +
                   ('; mats["%s"].alpha = 0.45' % k if k == 'stikls' else ''))
    for mat, tris in M.tris.items():
        out.append(f'g = ents.add_group; g.name = "{mat}"; mesh = Geom::PolygonMesh.new')
        out.append('[')
        out.append(',\n'.join('[' + ','.join('%.1f' % c for p in t for c in p) + ']' for t in tris))
        out.append('].each { |t| i = [0, 3, 6].map { |o| mesh.add_point(Geom::Point3d.new(t[o].mm, t[o + 1].mm, t[o + 2].mm)) }; mesh.add_polygon(i) }')
        out.append(f'g.entities.add_faces_from_mesh(mesh, 0, mats["{mat}"], mats["{mat}"])')
    out += ['model.commit_operation', 'Sketchup.active_model.active_view.zoom_extents']
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')


def main(model_path, out_dir=None):
    m = json.load(open(model_path, encoding='utf-8'))
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(model_path)), '3d')
    os.makedirs(out_dir, exist_ok=True)
    M, mats = build(m)
    mid = m['id']
    outs = []
    write_rb(os.path.join(out_dir, mid + '_skp.rb'), M, mats, mid); outs.append(mid + '_skp.rb')   # [MM] SKP pieprasījumam tiek taisīts tikai .rb
    return [os.path.join(out_dir, o) for o in outs]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for o in main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None):
        print(o)
