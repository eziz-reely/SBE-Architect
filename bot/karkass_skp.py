"""Ražošanas karkass uz SketchUp (tikai karkass, bez apvalka).

    python karkass_skp.py <model.json> [izvades mape]

Izvade (mapē `3d/` blakus model.json): <id>_karkass_skp.rb. SketchUp: Extensions > MM Homes > Importēt MM modeli…
(izvēlas .rb) vai Window > Ruby Console: load 'ceļš/<id>_karkass_skp.rb'.

Ko uztaisa (kā karkass_parzimet līgums, sk. SVG_IMPORTS_RASEJUMI.md 2. sadaļu):
- katram panelim (A, B, C, D, S1 …) grupa modeļa augšējā līmenī, nosaukums = paneļa id;
- katra detaļa = komponents ar definīciju VERT.STATNIS / HOR.STATNIS / VERT.SLIPAIS / SLIPAIS / PĀRSEDZE / SPARE,
  zīmēts detaļas asīs (slīpajām pagriezts pa slīpumu), lai bounding box = īstais garums × platums × biezums;
  vienādām detaļām viena definīcija;
- atribūti: karkass_parzimet/loma (parzimet lomas), karkass_generate/loma (SBE loma), karkass_generate/panelis;
- jumta spāres grupā JUMTS.
Tagus, ainas un materiālus NEVEIDO (tos lietotājs liek SketchUp pats). Viss vienā darbībā (Ctrl+Z atceļ visu).
Koordinātas kā skp.py: X uz austrumiem, Y uz ziemeļiem (Y = D − plāna y), Z no ±0,000.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import karkass

# SBE loma -> karkass_parzimet loma (core.rb sarakstā nav opening_plate, cripple, nogging)
ROLE = {'opening_plate': 'header_edge', 'nogging': 'block'}
NAME = {'PĀRSEDZE': 'HOR.STATNIS'}   # sienas pārsedze parzimet līgumā ir HOR.STATNIS (PARSEDZE tikai jumta logam); loma paliek header


def _parz_role(role, pts):
    if role == 'cripple':
        return 'cripple_high' if min(c for _, c in pts) > 1000 else 'cripple_low'
    return ROLE.get(role, role)


def _angle(poly):
    """Garākās malas slīpums (spārei / slīpajam gulsnim = jumta slīpums)."""
    best, a = -1, 0.0
    for (u0, z0), (u1, z1) in zip(poly, poly[1:] + poly[:1]):
        L = math.hypot(u1 - u0, z1 - z0)
        if L > best and abs(u1 - u0) > 1e-6:
            best, a = L, math.atan2(z1 - z0, u1 - u0)
    if a > math.pi / 2:
        a -= math.pi
    elif a < -math.pi / 2:
        a += math.pi
    return a


def _part(o, d, n, poly, depth, ang, Dm):
    """Detaļa: plāna punkts = o + d*u + n*w (w 0..depth), z. Atgriež (lokālie punkti (a, c), sākums, X, Y) SketchUp asīs, mm."""
    dx, dy = d[0], -d[1]                       # plāna vektors -> SketchUp (Y uz ziemeļiem)
    nx, ny = n[0], -n[1]
    ca, sa = math.cos(ang), math.sin(ang)
    X = (dx * ca, dy * ca, sa)
    Zr = (-dx * sa, -dy * sa, ca)
    Y = (-dy, dx, 0.0)                         # Zr × X (labās rokas asis, bez spoguļošanas)
    sig = 1 if Y[0] * nx + Y[1] * ny > 0 else -1
    loc = [(u * ca + z * sa, -u * sa + z * ca) for u, z in poly]
    a0, c0 = min(p[0] for p in loc), min(p[1] for p in loc)
    loc = [(round(a - a0, 1), round(c - c0, 1)) for a, c in loc]
    loc = [q for i, q in enumerate(loc) if q != loc[i - 1]]   # bez dubultiem punktiem (add_face)
    wo = depth if sig < 0 else 0.0             # Y pret n: sākums paneļa otrā pusē
    ox, oy = o[0], Dm - o[1]
    org = (ox + X[0] * a0 + Zr[0] * c0 + nx * wo, oy + X[1] * a0 + Zr[1] * c0 + ny * wo, X[2] * a0 + Zr[2] * c0)
    return loc, org, X, Y


def build(m):
    kd = karkass.frame3d(m)
    Dm = m['D']
    defs, dkey, groups, inst = [], {}, [], []

    def add(gi, name, role, prole, o, d, n, poly, depth, sloped):
        ang = _angle(poly) if sloped else 0.0
        loc, org, X, Y = _part(o, d, n, poly, depth, ang, Dm)
        k = (name, tuple(loc), round(depth, 1))
        if k not in dkey:
            dkey[k] = len(defs)
            defs.append([name, [list(p) for p in loc], round(depth, 1)])
        inst.append([gi, dkey[k], prole, role, [round(v, 2) for v in org], [round(v, 6) for v in X], [round(v, 6) for v in Y]])

    for P in kd['paneli']:
        groups.append(P['id'])
    for pi, role, poly, h, name in kd['det']:
        P = kd['paneli'][pi]
        pts = [tuple(p) for p in poly]
        add(pi, NAME.get(name, name), role, _parz_role(role, pts), P['o'], P['d'], P['n'], pts, h, name == 'SLIPAIS')
    if kd.get('rafs'):
        gi = len(groups)
        groups.append('JUMTS')
        for r in kd['rafs']:
            add(gi, 'SPARE', 'rafter', 'rafter', r['o'], r['d'], r['n'], [tuple(p) for p in r['poly']], kd['B'], True)
    return {'id': kd.get('id') or m.get('id'), 'groups': groups, 'defs': defs, 'inst': inst, 'D': kd['D'], 'DJ': kd['DJ']}


RB = r'''# encoding: UTF-8
# MM Homes ražošanas karkass: __ID__ (SBE Architect, karkass_skp.py). Tikai karkass: tagus, ainas un materiālus neveido.
module MMKarkass__TAG__
  G = __GROUPS__
  DEFS = __DEFS__
  INST = __INST__
  def self.run
    model = Sketchup.active_model
    model.start_operation('MM karkass: __ID__', true)
    begin
      defs = DEFS.map do |nm, pts, dep|
        d = model.definitions.add(nm)
        f = d.entities.add_face(pts.map { |a, c| Geom::Point3d.new(a.mm, 0, c.mm) })
        f.reverse! if f.normal.y < 0
        f.pushpull(dep.mm)
        d
      end
      grs = G.map do |nm|
        g = model.entities.add_group
        g.name = nm
        g.set_attribute('karkass_generate', 'panelis', nm)
        g
      end
      INST.each do |gi, di, prole, role, o, x, y|
        xa = Geom::Vector3d.new(*x)
        ya = Geom::Vector3d.new(*y)
        tr = Geom::Transformation.axes(Geom::Point3d.new(o[0].mm, o[1].mm, o[2].mm), xa, ya, xa * ya)
        i = grs[gi].entities.add_instance(defs[di], tr)
        i.set_attribute('karkass_parzimet', 'loma', prole)
        i.set_attribute('karkass_generate', 'loma', role)
      end
      model.commit_operation
      UI.messagebox("MM karkass __ID__: #{G.size} grupas, #{INST.size} detaļas, #{DEFS.size} definīcijas.\nTagi, ainas un materiāli nav veidoti.")
    rescue StandardError => e
      model.abort_operation
      UI.messagebox("MM karkass neizdevās:\n#{e.message}")
    end
  end
end
MMKarkass__TAG__.run if Sketchup.active_model
'''


def script(m):
    """(Ruby teksts, faila nosaukums, kopsavilkums) no model.json vārdnīcas."""
    k = build(m)
    tag = ''.join(ch if ch.isalnum() else '_' for ch in str(k['id']))
    tag = tag[:1].upper() + tag[1:] if tag else 'X'
    js = lambda v: json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    src = (RB.replace('__TAG__', tag).replace('__ID__', str(k['id']).replace("'", ''))
           .replace('__GROUPS__', js(k['groups'])).replace('__DEFS__', js(k['defs'])).replace('__INST__', js(k['inst'])))
    return src, f"{k['id']}_karkass_skp.rb", f"{len(k['groups'])} grupas, {len(k['inst'])} detaļas, {len(k['defs'])} definīcijas"


def main(model_path, out_dir=None):
    src, nm, info = script(json.load(open(model_path, encoding='utf-8')))
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(model_path)), '3d')
    os.makedirs(out_dir, exist_ok=True)
    fp = os.path.join(out_dir, nm)
    with open(fp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)
    print(f"{fp}: {info}")
    return fp


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('lietošana: python karkass_skp.py <model.json> [izvades mape]')
        sys.exit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
