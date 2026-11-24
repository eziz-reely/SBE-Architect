"""Karkass ražošanai: model.json -> sienu paneļi (statņi, gulšņi, pārsedzes, ailas), spāres, detaļu saraksti.

    python karkass.py <model.json>          # dati un kopsavilkums konsolē
    python karkass_lapas.py <model.json>    # A3 ražošanas lapas (1. lapa = skice)

Sinhronizēts ar projektu: kontūra (arī L un robi), logi un durvis, starpsienas, jumts (arī L jumts ar ieleju) un pīrāgu slāņi
(projekts.piragi_layers: karkasa biezums C24 45x145 vai 45x195, slāņi ārpus karkasa nosaka karkasa atkāpi no fasādes).
Mērvienības mm. Panelis: u = garums gar sienu no kreisā gala, skatoties no ārpuses; z = augstums no grīdas virsas (±0,000).
Pieņēmumi ir PIE sarakstā (redzami lapās). Prototips no projekta failiem karkass/kods/karkass.py.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import archicad  # noqa: E402  sienu asis, starpsienas, ailas no model.json
import kontura as KT  # noqa: E402

B = 45.0                 # dēļa biezums
CC, CLEAR_MAX = 600.0, 555.0
HDR_BOT = 2130.0         # pārsedzes apakša (durvīm un logiem, kuru augša tuvu)
SPARE_CC = 600.0

PIE = [
    "Karkasa ārmala = fasādes ārmala mīnus slāņi ārpus karkasa (pīrāgs S-04). Ārsienas karkass C24 45×{D:.0f}, statņi c/c 600 (tīrā atstarpe ≤ 555).",
    "Stūri: garenvirziena (garāko) sienu paneļi iet cauri līdz ārmalai, šķērssienas pieiet pie to iekšējās šķautnes; iekšējā stūrī caurejošais panelis ir garāks par karkasa biezumu.",
    "Ārsienu augšmala seko jumta apakšai fasādes līnijā (frontonos slīpi). Divi augšgulšņi un divi apakšgulšņi.",
    "Aila = loga vai durvju izmērs no projekta; ja ailas augša tuvāk par 150 mm no 2130, pārsedzes apakša = 2130. Pārsedze 45 plakaniski + 45×{D:.0f} uz šķautnes.",
    "Starpsienas no plāna (karkass = sienas biezums mīnus apšuvums), augstums = griesti; gali līdz ārsienas karkasa iekšmalai.",
    "Spāres C24 45×{DJ:.0f} c/c 600 pa jumta plaknēm ar pārkari; L jumtam ielejas spāres saīsinātas pēc ielejas līnijas.",
]


# ---------------------------------------------------------------- pīrāgi
def layers_of(m):
    """Projekta pīrāgi: mm-config.json slāņi + projekts.piragi_layers (redaktorā labotie)."""
    cfg = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
    L = {k: {'name': v['name'], 'layers': [list(l) for l in v['layers']]} for k, v in cfg['layers'].items()}
    pr = m.get('projekts') or {}
    for k, v in (pr.get('piragi_layers') or {}).items():
        L.setdefault(k, {'name': k, 'layers': []})['layers'] = [list(l) for l in v]
    for k, v in (pr.get('piragi_names') or {}).items():
        if k in L and v:
            L[k]['name'] = v
    return L


def frame_of(layers, default=145.0):
    """(karkasa biezums, slāņu biezums ārpus karkasa) no pīrāga: karkass = pirmais slānis ar tipu 'i' (vai nosaukumā C24)."""
    off = 0.0
    for l in layers:
        t = float(l[1] or 0)
        kind = l[2] if len(l) > 2 else ''
        if kind == 'i' or str(l[0]).upper().startswith('C24') and t >= 95:
            return t, off
        if kind != 'n':
            off += t
    return default, off


# ---------------------------------------------------------------- jumts
def _poly_area(P):
    return abs(sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))) / 2


def roof_geom(m):
    """Jumta ģeometrija: z(x, y) jumta apakša, plaknes [(nosaukums, punkti3d, tan)], spāres [(plakne, garums)], ielejas garumi.
    Divslīpju taisnstūris (kore gar x) vai L jumts (tā pati loģika kā sablons/mm-roofl.js)."""
    J = m.get('jumts') or {}
    pr = m.get('projekts') or {}
    W, D = float(m['W']), float(m['D'])
    pitch = float(J.get('pitch') or 30)
    tan = math.tan(math.radians(pitch))
    eave = float(J.get('eave') or 2600)
    ov = float(J.get('ov') or 0)
    OS = pr.get('ov_side') or {}
    od = lambda q: float(OS[q]) if OS.get(q) is not None else ov
    notes = []
    if float(J.get('hip') or 0) or str(J.get('forma', '')).startswith(('cetr', 'četr')):
        notes.append('Četrslīpju jumts: spāres rēķinātas kā divslīpju jumtam (pārbaudīt)')
    if str(J.get('forma', '')) in ('vienslipa', 'parapets'):
        notes.append('Vienslīpu vai plakans jumts: spāres rēķinātas aptuveni kā divslīpju jumtam (pārbaudīt)')
    K = m.get('kontura') or {}
    poly = KT.P_full(K) if (K.get('bloki') and len(K['bloki']) > 1) else (m.get('poly') or [[0, 0], [W, 0], [W, D], [0, D]])
    Lon = J.get('L') is not False and (J.get('L') or len(K.get('bloki') or []) == 2) and len(poly) == 6 and not float(J.get('hip') or 0)
    if Lon:
        g = _roofL(poly, W, D, tan, eave, od, J)
        if g:
            g['notes'] = notes
            return g
    # divslīpju: kore gar x vidū
    oN, oS, oW, oE = od('north'), od('south'), od('west'), od('east')
    z = lambda x, y: eave + tan * min(y, D - y)
    hr = eave + tan * D / 2
    planes = [('Ziemeļu slīpne', [(-oW, -oN, eave - oN * tan), (W + oE, -oN, eave - oN * tan), (W + oE, D / 2, hr), (-oW, D / 2, hr)], tan),
              ('Dienvidu slīpne', [(-oW, D + oS, eave - oS * tan), (W + oE, D + oS, eave - oS * tan), (W + oE, D / 2, hr), (-oW, D / 2, hr)], tan)]
    cos = math.cos(math.atan(tan))
    n = math.ceil((W + oW + oE - B) / SPARE_CC) + 1
    sp = [(planes[0][0], (D / 2 + oN) / cos)] * n + [(planes[1][0], (D / 2 + oS) / cos)] * n
    return {'z': z, 'planes': planes, 'spares': sp, 'ielejas': [], 'kore': [W + oW + oE], 'poly': poly, 'notes': notes, 'ridge': hr}


def _roofL(poly, W, D, tan, eave, od, J):
    r = next((p for p in poly if 1 < p[0] < W - 1 and 1 < p[1] < D - 1), None)
    has = lambda x, y: any(abs(p[0] - x) < 1 and abs(p[1] - y) < 1 for p in poly)
    c = next((q for q in [(0, 0), (W, 0), (W, D), (0, D)] if not has(*q)), None)
    if not r or not c:
        return None
    cw, cd = abs(r[0] - c[0]), abs(r[1] - c[1])
    A = 0 if (W - cw) <= (D - cd) else 1
    U, cu, cv, nu, nv, V = (D, c[1], c[0], cd, cw, W) if A else (W, c[0], c[1], cw, cd, D)
    a = nu if cu == 0 else 0
    b = U if cu == 0 else U - nu
    s = 1 if cv == 0 else -1
    v0 = nv if cv == 0 else V - nv
    dm, dw, hw, wc = V - nv, nv, (b - a) / 2, (a + b) / 2
    tMax = (dm / 2) * tan / hw
    tanW = tMax if J.get('kore_kopiga') else (math.tan(math.radians(float(J['pitch_sparns']))) if J.get('pitch_sparns') else tan)
    tanW = min(tanW if tanW > 0 else tan, tMax)
    if A:
        sd = {'u0': 'north', 'u1': 'south', 'far': 'east' if s > 0 else 'west', 'wg': 'west' if s > 0 else 'east'}
    else:
        sd = {'u0': 'west', 'u1': 'east', 'far': 'south' if s > 0 else 'north', 'wg': 'north' if s > 0 else 'south'}
    h = lambda d: eave + d * tan
    hW = lambda d: eave + d * tanW
    hr, hg = h(dm / 2), hW(hw)
    oN, oF = od(sd['wg']), od(sd['far'])
    oG, oNw, vR = oN, oN * tan / tanW, (hg - eave) / tan
    o0 = oNw if a == 0 else od(sd['u0'])
    o1 = oNw if b == U else od(sd['u1'])
    w3 = lambda u, v, zz: ((v0 + s * v, u, zz) if A else (u, v0 + s * v, zz))

    def z(x, y):
        u, q = (y, x) if A else (x, y)
        v = (q - v0) * s
        if v < 0:
            return hW(min(u - a, b - u))
        zm = h(min(v, dm - v))
        return max(zm, hW(min(u - a, b - u))) if (a < u < b and v <= dm / 2) else zm
    near = [(-o0, -oN, h(-oN)), (a - oNw, -oN, h(-oN)), (wc, vR, hg), (b + oNw, -oN, h(-oN)), (U + o1, -oN, h(-oN)), (U + o1, dm / 2, hr), (-o0, dm / 2, hr)]
    P = [('Galvenā tālā slīpne', [(-o0, dm + oF, h(-oF)), (U + o1, dm + oF, h(-oF)), (U + o1, dm / 2, hr), (-o0, dm / 2, hr)], tan),
         ('Galvenā slīpne ar ieleju', near, tan),
         ('Spārna slīpne 1', [(a - oNw, -dw - oG, h(-oN)), (a - oNw, -oN, h(-oN)), (wc, vR, hg), (wc, -dw - oG, hg)], tanW),
         ('Spārna slīpne 2', [(b + oNw, -dw - oG, h(-oN)), (b + oNw, -oN, h(-oN)), (wc, vR, hg), (wc, -dw - oG, hg)], tanW)]
    planes = [(n_, [w3(*p) for p in pts], t_) for n_, pts, t_ in P]
    cosM, cosW = math.cos(math.atan(tan)), math.cos(math.atan(tanW))
    sp = []
    # galvenā tālā slīpne: pilnas spāres
    n = math.ceil((U + o0 + o1 - B) / SPARE_CC) + 1
    sp += [(P[0][0], (dm / 2 + oF) / cosM)] * n
    # galvenā slīpne ar ieleju: spārna platumā spāres no ielejas līdz korei
    ua, ub = a - oNw, b + oNw
    vval = lambda u: -oN + (vR + oN) * (1 - abs(u - wc) / (wc - ua))
    for i in range(n):
        u = -o0 + B / 2 + i * (U + o0 + o1 - B) / (n - 1)
        run = (dm / 2 - vval(u)) if ua < u < ub else (dm / 2 + oN)
        if run > 50:
            sp.append((P[1][0], run / cosM))
    # spārna slīpnes: spāres perpendikulāri spārna korei, ielejas zonā līdz ielejai
    span_v = vR + dw + oG
    nw = math.ceil((span_v - B) / SPARE_CC) + 1
    for side in (P[2][0], P[3][0]):
        for i in range(nw):
            v = -dw - oG + B / 2 + i * (span_v - B) / (nw - 1)
            run = (wc - ua) if v <= -oN else (wc - ua) * (1 - (v + oN) / (vR + oN))
            if run > 50:
                sp.append((side, run / cosW))
    vl = math.sqrt((wc - ua) ** 2 + (vR + oN) ** 2 + (hg - h(-oN)) ** 2)
    return {'z': z, 'planes': planes, 'spares': sp, 'ielejas': [vl, vl], 'kore': [U + o0 + o1, vR + dw + oG], 'poly': poly, 'ridge': max(hr, hg),
            'tanW': tanW}


def roof_area(g):
    """Jumta plakņu laukums pa slīpumu, m²."""
    return sum(_poly_area([(p[0], p[1]) for p in pts]) / math.cos(math.atan(t)) for _, pts, t in g['planes']) / 1e6


# ---------------------------------------------------------------- paneļi
def _r(v):
    return round(v, 1)


class Panel:
    def __init__(self, pid, kind, L, top, D, note=''):
        self.id, self.kind, self.L, self.top, self.D, self.note = pid, kind, L, top, D, note   # top: [(u, z)] augšgulšņa augšmala
        self.m, self.opens, self.warn = [], [], []

    def top_at(self, u):
        T = self.top
        if u <= T[0][0]:
            return T[0][1]
        for (u0, z0), (u1, z1) in zip(T, T[1:]):
            if u <= u1:
                return z0 + (z1 - z0) * (u - u0) / ((u1 - u0) or 1)
        return T[-1][1]

    def slope_at(self, u):
        T = self.top
        for (u0, z0), (u1, z1) in zip(T, T[1:]):
            if u0 - 1e-6 <= u <= u1 + 1e-6 and u1 > u0:
                return (z1 - z0) / (u1 - u0)
        return 0.0

    def add(self, name, role, u0, u1, z0, z1, length=None, w=None, cut=None):
        self.m.append({'nos': name, 'loma': role, 'u0': _r(u0), 'u1': _r(u1), 'z0': _r(z0), 'z1': _r(z1), 'b': B, 'h': w or self.D,
                       'garums': _r(length if length is not None else max(u1 - u0, z1 - z0)), 'cut': cut})
        return self.m[-1]

    def area(self):
        """(bruto, neto bez ailām) m²."""
        T = self.top
        gross = sum((u1 - u0) * (z0 + z1) / 2 for (u0, z0), (u1, z1) in zip(T, T[1:])) / 1e6
        net = gross - sum((o['u1'] - o['u0']) * (o['head'] - o['sill']) for o in self.opens) / 1e6
        return gross, net


def _simplify(pts, tol=0.6):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        zc = a[1] + (c[1] - a[1]) * (b[0] - a[0]) / ((c[0] - a[0]) or 1)
        if abs(zc - b[1]) > tol:
            out.append(b)
    out.append(pts[-1])
    res = [out[0]]   # bez sīkiem posmiem (< 60 mm): no tuviem punktiem paliek augstākais (kore)
    for q in out[1:-1]:
        if len(res) > 1 and q[0] - res[-1][0] < 60:
            if q[1] > res[-1][1]:
                res[-1] = q
        else:
            res.append(q)
    if len(res) > 1 and out[-1][0] - res[-1][0] < 60:
        res.pop()
    out = res + [out[-1]]
    return [(_r(u), _r(z)) for u, z in out]


def _fill(a, b, mk):
    """Statņi c/c 600 tīrajā atstarpē [a, b], neviena atstarpe > 555."""
    g = b - a
    if g <= CLEAR_MAX + 1e-6:
        return
    k = math.ceil((g - CLEAR_MAX) / CC - 1e-9)
    pos = [a + CLEAR_MAX + CC * i for i in range(k)]
    if g - (CLEAR_MAX + CC * (k - 1) + B) < 20:
        gap = (g - B * k) / (k + 1)
        pos = [a + gap * (i + 1) + B * i for i in range(k)]
    for p in pos:
        mk(p)


def build_panel(P, opens, junctions, rot_ends):
    """Detaļas panelim P. opens: [{u0,u1,sill,head,tips}]; junctions: starpsienu asis u; rot_ends: (sākumā, beigās) pagriezts statnis stūrim."""
    L, D = P.L, P.D
    sl = lambda u: math.sqrt(1 + P.slope_at(u) ** 2)
    # apakšgulšņi (pārtraukti durvju ailās)
    cuts = sorted((o['u0'], o['u1']) for o in opens if o['sill'] <= 0)
    segs, cur = [], 0.0
    for c0, c1 in cuts:
        if c0 > cur:
            segs.append((cur, c0))
        cur = max(cur, c1)
    if cur < L:
        segs.append((cur, L))
    for i in range(2):
        for s0, s1 in segs:
            P.add('HOR.STATNIS', 'bottom_plate', s0, s1, i * B, (i + 1) * B)
    # augšgulšņi pa augšmalas posmiem
    for (u0, z0), (u1, z1) in zip(P.top, P.top[1:]):
        k = (z1 - z0) / ((u1 - u0) or 1)
        for i in range(2):
            dz = (i + 1) * B * math.sqrt(1 + k * k)
            if abs(k) < 1e-4:
                P.add('HOR.STATNIS', 'top_plate', u0, u1, z0 - dz, z0 - dz + B)
            else:
                P.add('SLIPAIS', 'top_plate', u0, u1, min(z0, z1) - dz, max(z0, z1) - dz + B, length=math.hypot(u1 - u0, z1 - z0), cut='slīps griezums gar jumtu')
    zb = 2 * B

    def stud(u0, role, w=B, z0=None, z1=None, depth=None):
        u1 = u0 + w
        a = zb if z0 is None else z0
        if z1 is None:
            t0, t1 = P.top_at(u0), P.top_at(u1)
            pl = 2 * B * max(sl(u0), sl(u1))
            lo, hi = min(t0, t1) - pl, max(t0, t1) - pl
            if hi - lo > 2:
                return P.add('VERT.SLIPAIS', role, u0, u1, a, hi, length=hi - a, w=depth, cut='slīps augšgals')
            return P.add('VERT.STATNIS', role, u0, u1, a, lo, length=lo - a, w=depth)
        return P.add('VERT.STATNIS', role, u0, u1, a, z1, length=z1 - a, w=depth)

    fixed = []
    stud(0, 'stud')
    fixed.append((0, B))
    if rot_ends[0]:
        stud(B, 'junction_rot', w=D)
        fixed[-1] = (0, B + D)
    stud(L - B, 'stud')
    fixed.append((L - B, L))
    if rot_ends[1]:
        stud(L - B - D, 'junction_rot', w=D)
        fixed[-1] = (L - B - D, L)
    end_l, end_r = fixed[0][1], fixed[1][0]
    for c in sorted(junctions):
        u0 = c - D / 2
        if u0 - B < end_l or u0 + D + B > end_r:
            P.warn.append(f'starpsienas pieslēgums u={_r(c)} pie gala bloka, pārbaudīt')
            continue
        if any(o['u0'] - B <= c <= o['u1'] + B for o in opens):
            P.warn.append(f'starpsienas pieslēgums u={_r(c)} ailā, pārbaudīt')
            continue
        stud(u0 - B, 'junction')
        stud(u0, 'junction_rot', w=D)
        stud(u0 + D, 'junction')
        fixed.append((u0 - B, u0 + D + B))
    ops = sorted(opens, key=lambda o: o['u0'])
    for i, o in enumerate(ops):
        a0, a1, hb = o['u0'], o['u1'], o['head']
        room = min(P.top_at(a0 - B), P.top_at(a1 + B)) - 2 * B * max(sl(a0), sl(a1))
        if hb + B + D > room + 1:
            P.warn.append(f"aila {o['u1'] - o['u0']:.0f}×{hb - o['sill']:.0f}: pārsedze {B + D:.0f} mm neietilpst zem augšgulšņiem ({room:.0f}); vajag citu pārsedzi vai zemāku ailu")
        share_l = i > 0 and a0 - ops[i - 1]['u1'] <= 180
        share_r = i + 1 < len(ops) and ops[i + 1]['u0'] - a1 <= 180
        for side, lo, shared in (('l', a0 - B, share_l), ('r', a1, share_r)):
            stud(lo, 'jack', z0=zb, z1=hb)
            if not shared:
                stud(lo - B if side == 'l' else a1 + B, 'king')
        fixed.append((a0 - B - (0 if share_l else B), a1 + B + (0 if share_r else B)))
        P.add('PĀRSEDZE', 'header', a0 - B, a1 + B, hb, hb + B, w=D)
        P.add('PĀRSEDZE', 'header', a0 - B, a1 + B, hb + B, hb + B + D, w=D)
        top_hdr = hb + B + D
        if a1 - a0 + 2 * B > CLEAR_MAX:
            _fill(a0 - B, a1 + B, lambda u, t=top_hdr: stud(u, 'cripple', z0=t) if P.top_at(u) - t > 2 * B + 60 else None)
        if o['sill'] > 0:
            P.add('HOR.STATNIS', 'sill', a0, a1, o['sill'] - B, o['sill'])
            _fill(a0, a1, lambda u, o=o: stud(u, 'cripple', z0=zb, z1=o['sill'] - B))
    merged = []
    for a, b in sorted(fixed):
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    for (a0, a1), (b0, b1) in zip(merged, merged[1:]):
        if any(o['u0'] - B <= a1 and b0 <= o['u1'] + B for o in opens):
            continue
        _fill(a1, b0, lambda u: stud(u, 'stud'))
    # horizontālais šķērsis (nogging) pusaugstumā starp statņiem, kur nav ailu
    vs = sorted((q['u0'], q['u1']) for q in P.m if q['nos'].startswith('VERT') and q['z0'] <= zb + 1 and q['z1'] > 1400)
    for (p0, p1), (q0, q1) in zip(vs, vs[1:]):
        if q0 - p1 > 100 and not any(o['u0'] - B < (p1 + q0) / 2 < o['u1'] + B for o in opens):
            P.add('HOR.STATNIS', 'nogging', p1, q0, 1200, 1200 + B)
    P.opens = [{'u0': _r(o['u0']), 'u1': _r(o['u1']), 'sill': o['sill'], 'head': o['head'], 'tips': o['tips']} for o in opens]
    return P


def generate(m):
    """model.json -> {'paneli': [Panel], 'jumts': roof_geom, 'D': ..., 'piezimes': [...]}"""
    LY = layers_of(m)
    D, off = frame_of(LY['S1']['layers'])
    DJ, _ = frame_of(LY['J1']['layers'], 195.0)
    d = archicad.data_of(m)
    roof = roof_geom(m)
    z = roof['z']
    W, Dd = float(m['W']), float(m['D'])
    poly = [tuple(map(float, p)) for p in (m.get('poly') or [[0, 0], [W, 0], [W, Dd], [0, Dd]])]
    n = len(poly)
    warn = list(roof.get('notes') or [])
    ceil = float(m.get('ceiling') or 2600)
    walls = {w['id']: w for w in d['walls']}
    ext = [w for w in d['walls'] if w['outer']]
    part = [w for w in d['walls'] if not w['outer']]
    # orientācija, kura iet cauri: garākās malas virziens
    edges = [(poly[i], poly[(i + 1) % n]) for i in range(n)]
    elen = lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1])
    longest = max(edges, key=elen)
    through_h = abs(longest[0][1] - longest[1][1]) < 1
    area2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    cwise = area2 > 0          # plāna koordinātēs (y uz leju) pozitīvs = pulksteņrādītāja virzienā ekrānā

    def convex(i):   # virsotne i (starp malu i-1 un i)
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        return (cr > 0) == cwise

    def outward(e):   # ārējā normāle
        (x0, y0), (x1, y1) = e
        dx, dy = (x1 - x0) / elen(e), (y1 - y0) / elen(e)
        return (-dy, dx) if cwise else (dy, -dx)

    def wall_of(e):   # archicad siena, kas atbilst malai (paralēla, ass T/2 iekšpusē)
        best, bd = None, 1e9
        hz = abs(e[0][1] - e[1][1]) < 1
        for w in ext:
            whz = abs(w['a'][1] - w['b'][1]) < 1
            if whz != hz:
                continue
            dist = abs(w['a'][1] - e[0][1]) if hz else abs(w['a'][0] - e[0][0])
            lo, hi = sorted((e[0][0], e[1][0]) if hz else (e[0][1], e[1][1]))
            wl, wh = sorted((w['a'][0], w['b'][0]) if hz else (w['a'][1], w['b'][1]))
            if wh < lo - 1 or wl > hi + 1:
                continue
            if dist < bd:
                best, bd = w, dist
        return best

    panels = []
    letters = 'ABCDEFGHIJKLMNOPRSTUVZ'
    # sāk ar ziemeļu fasādes kreiso (rietumu) malu un iet pretēji pulksteņrādītājam (skatoties no ārpuses u iet no kreisās uz labo)
    order = list(range(n))
    start = min(order, key=lambda i: (round(min(edges[i][0][1], edges[i][1][1])), -round(max(edges[i][0][0], edges[i][1][0]))) if abs(edges[i][0][1] - edges[i][1][1]) < 1 else (1e9, 0))
    order = [(start - k) % n for k in range(n)] if cwise else [(start + k) % n for k in range(n)]
    for k, i in enumerate(order):
        e = edges[i]
        hz = abs(e[0][1] - e[1][1]) < 1
        through = hz == through_h
        nx, ny = outward(e)
        # skatoties no ārpuses: kreisais gals = e[1] (cwise), labais = e[0]
        pL, pR = (e[1], e[0]) if cwise else (e[0], e[1])
        iL, iR = ((i + 1) % n, i) if cwise else (i, (i + 1) % n)
        dirx, diry = (pR[0] - pL[0]) / elen(e), (pR[1] - pL[1]) / elen(e)
        # karkasa ārmalas līnija (atkāpe off iekšup); gali pie stūriem
        cvL, cvR = convex(iL), convex(iR)
        def short(cv):   # cik panelis īsāks (+) vai garāks (-) par fasādes malu šajā galā
            if through:
                return off if cv else -(off + D)          # izliektā stūrī līdz karkasa ārmalai, iekšējā stūrī pāri šķērssienai
            return off + D if cv else -off
        ext_l, ext_r = short(cvL), short(cvR)
        Lp = elen(e) - ext_l - ext_r
        ox, oy = pL[0] - nx * off + dirx * ext_l, pL[1] - ny * off + diry * ext_l   # paneļa sākuma punkts (ārmala)
        at = lambda u: (ox + dirx * u, oy + diry * u)
        # augšmala: jumta apakša fasādes līnijā
        el_ = elen(e)
        fx = lambda u: (pL[0] + dirx * min(max(ext_l + u, 0), el_), pL[1] + diry * min(max(ext_l + u, 0), el_))   # pagarinājums aiz stūra: augstums kā stūrī
        N = max(2, int(Lp / 10))
        top = _simplify([(Lp * j / N, z(*fx(Lp * j / N))) for j in range(N + 1)])
        P = Panel(letters[k] if k < len(letters) else f'E{k + 1}', 'arsiena', Lp, top, D, '(caurejošā)' if through else '(šķērssiena)')
        w = wall_of(e)
        ops = []
        if w:
            wd = (w['b'][0] - w['a'][0], w['b'][1] - w['a'][1])
            wl_ = math.hypot(*wd)
            for o in d['opens']:
                if o['siena'] != w['id']:
                    continue
                cx, cy = w['a'][0] + wd[0] / wl_ * o['poz'], w['a'][1] + wd[1] / wl_ * o['poz']
                cu = (cx - ox) * dirx + (cy - oy) * diry
                head = o['palodze'] + o['augstums'] if o['tips'] != 'durvis' else 2100
                if o['tips'] == 'durvis' or head > HDR_BOT or abs(head - HDR_BOT) <= 150:
                    head = HDR_BOT if head <= HDR_BOT + 150 else head
                ops.append({'u0': cu - o['platums'] / 2, 'u1': cu + o['platums'] / 2, 'sill': 0 if o['tips'] == 'durvis' else o['palodze'], 'head': head,
                            'tips': o['tips']})
        junc = []
        for p in part:
            for pt in (p['a'], p['b']):
                dn = (pt[0] - ox) * (-nx) + (pt[1] - oy) * (-ny)     # attālums iekšup no karkasa ārmalas
                if 0 < dn < D + 300:
                    cu = (pt[0] - ox) * dirx + (pt[1] - oy) * diry
                    if 0 < cu < Lp:
                        junc.append(cu)
        build_panel(P, ops, junc, (through and cvL, through and cvR))
        P.edge, P.side = e, ('north' if ny < -.5 else 'south' if ny > .5 else 'west' if nx < -.5 else 'east')
        P.o, P.dir = (ox, oy), (dirx, diry)
        panels.append(P)
    # starpsienas
    S2 = LY['S2']['layers']
    for j, p in enumerate(part):
        t = float(p['t'])
        dpart = max(45.0, round(t - (sum(float(l[1] or 0) for l in S2 if (len(l) < 3 or l[2] != 'i')) if abs(t - sum(float(l[1] or 0) for l in S2)) < 2 else 50)))
        hz = abs(p['a'][1] - p['b'][1]) < 1
        a_, b_ = (p['a'][0], p['b'][0]) if hz else (p['a'][1], p['b'][1])
        lo, hi = min(a_, b_), max(a_, b_)
        fixed_c = p['a'][1] if hz else p['a'][0]
        # gali līdz ārsienas karkasa iekšmalai, ja tuvu
        for P0 in [q for q in panels if q.kind == 'arsiena']:
            (ex0, ey0), (ex1, ey1) = P0.edge
            ehz = abs(ey0 - ey1) < 1
            if ehz == hz:
                continue
            line = ex0 if hz else ey0          # ārsienas fasādes līnija
            inner = line - (off + D) * (1 if (P0.side in ('east', 'south')) else -1)
            span = sorted((ey0, ey1) if hz else (ex0, ex1))
            if not (span[0] - 1 <= fixed_c <= span[1] + 1):
                continue
            if abs(lo - inner) < 130:
                lo = inner
            if abs(hi - inner) < 130:
                hi = inner
        Lp = hi - lo
        if Lp < 200:
            continue
        P = Panel(f'S{j + 1}', 'starpsiena', Lp, [(0, ceil), (Lp, ceil)], dpart, '(starpsiena)')
        ops = []
        for o in d['opens']:
            if o['siena'] != p['id']:
                continue
            wd = (p['b'][0] - p['a'][0], p['b'][1] - p['a'][1])
            wl_ = math.hypot(*wd)
            c_ = (p['a'][0] + wd[0] / wl_ * o['poz']) if hz else (p['a'][1] + wd[1] / wl_ * o['poz'])
            cu = c_ - lo
            ops.append({'u0': cu - o['platums'] / 2, 'u1': cu + o['platums'] / 2, 'sill': 0 if o['tips'] == 'durvis' else o['palodze'],
                        'head': HDR_BOT if o['tips'] == 'durvis' else o['palodze'] + o['augstums'], 'tips': o['tips']})
        build_panel(P, ops, [], (False, False))
        P.axis = (hz, fixed_c, lo, hi)
        panels.append(P)
    pie = [s.format(D=D, DJ=DJ) for s in PIE]
    return {'id': m.get('id'), 'paneli': panels, 'jumts': roof, 'D': D, 'DJ': DJ, 'off': off, 'piezimes': pie + warn, 'slani': LY}


def cutlist(panels):
    rows = {}
    for P in panels:
        for q in P.m:
            k = (q['nos'], int(round(q['h'])), int(round(q['b'])), int(round(q['garums'])))
            rows[k] = rows.get(k, 0) + 1
    return sorted(((n, h, b, g, c) for (n, h, b, g), c in rows.items()), key=lambda r: (r[0], -r[3]))


def spare_list(roof, DJ):
    rows = {}
    for n, g in roof['spares']:
        k = ('SPARE', int(round(DJ)), 45, int(round(g / 10) * 10))
        rows[k] = rows.get(k, 0) + 1
    for g in roof['ielejas']:
        k = ('IELEJAS SPARE', int(round(DJ)), 45, int(round(g / 10) * 10))
        rows[k] = rows.get(k, 0) + 1
    return sorted(((n, h, b, g, c) for (n, h, b, g), c in rows.items()), key=lambda r: (r[0], -r[3]))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('lietošana: python karkass.py <model.json>')
        sys.exit(2)
    mdl = json.load(open(sys.argv[1], encoding='utf-8'))
    res = generate(mdl)
    print(f"Karkass {res['id']}: C24 45x{res['D']:.0f}, atkāpe {res['off']:.0f} mm, spāres 45x{res['DJ']:.0f}")
    for P in res['paneli']:
        g, nn = P.area()
        print(f"  {P.id:4} {P.kind:10} L={P.L:7.0f}  detaļas={len(P.m):3}  {g:5.1f} m² (neto {nn:5.1f})  {'; '.join(P.warn)}")
    print(f"  jumts: {roof_area(res['jumts']):.1f} m², spāres {len(res['jumts']['spares'])} gab.")
