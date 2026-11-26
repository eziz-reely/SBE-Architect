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
KD = 145.0                   # karkasa statņa dziļums (kastes pagrieztā statņa platums); generate() uzstāda no ārsienas karkasa
MIN_GAP = 40.0               # mazākā atstarpe starp pēdējo statni un bloku; ja mazāka, pēdējo posmu dala uz pusēm
HDR_BOT = 2130.0         # pārsedzes apakša (durvīm un logiem, kuru augša tuvu)
SPARE_CC = 600.0

# Iestatījumi no modeļa (projekts.karkass_iest); generate() tos ielasa. Augšgulsnis vienmēr viens.
NB, NT = 2, 1                 # apakšgulšņu skaits (1 vai 2), augšgulšņu skaits
UZL_W, UZL_H = 0.0, 0.0       # ailas uzlaide platumā un augstumā (kopā, mm)
LOGU_DUBULTI = True           # loga ailas malās divi vertikāli statņi (balsts + pilnais) vai tikai viens pilnais
PASTIPR = True                # loga pārsedze un palodze dubultas (pastiprinātas) vai vienkāršas


SP = 30.0                     # palodzes profils (projekts.palodzes_prof: on, h); specifikācijā tas ir logam klāt, aila no ±0 paliek tāda pati


SEAT = 50.0   # spāres iezāģis pa vertikāli (lietotāja likums); garensienas augšgulsnis ir par SEAT augstāk par spāres apakšu karkasa ārmalā


def apply_settings(m):
    global NB, UZL_W, UZL_H, LOGU_DUBULTI, PASTIPR, SP
    sp = (m.get('projekts') or {}).get('palodzes_prof') or {}
    SP = 0.0 if sp.get('on') is False else (float(sp.get('h')) if float(sp.get('h') or 0) > 0 else 30.0)
    s = (m.get('projekts') or {}).get('karkass_iest') or {}
    NB = 1 if int(s.get('apaksgulsni', 2) or 2) == 1 else 2
    UZL_W = max(0.0, min(100.0, float(s.get('uzlaide_w') or 0)))
    UZL_H = max(0.0, min(100.0, float(s.get('uzlaide_h') or 0)))
    LOGU_DUBULTI = bool(s.get('logu_dubulti', True))
    PASTIPR = bool(s.get('logu_pastiprinajums', True))

PIE = [
    "Karkasa ārmala = fasādes ārmala mīnus slāņi ārpus karkasa (pīrāgs S-04). Ārsienas karkass C24 45×{D:.0f}, statņi c/c 600 (tīrā atstarpe ≤ 555).",
    "Stūri: garenvirziena (garāko) sienu paneļi iet cauri līdz ārmalai, šķērssienas pieiet pie to iekšējās šķautnes; iekšējā stūrī caurejošais panelis ir garāks par karkasa biezumu.",
    "Ārsienu augšmala seko jumta apakšai (frontonos slīpi), bet ne zemāk par augšgulšņa virsu: spāres apakša karkasa ārmalā + 50 mm iezāģis (frontona galā horizontāls posms). Augšgulsnis viens; apakšgulšņi {NB} (iestatījums).",
    "Aila = loga vai durvju izmērs no projekta; ja ailas augša tuvāk par 150 mm no 2130, pārsedzes apakša = 2130. Pārsedze 45 plakaniski + 45×{D:.0f} uz šķautnes.",
    "Starpsienas no plāna (karkass = sienas biezums mīnus apšuvums), augstums = griesti; gali līdz ārsienas karkasa iekšmalai.",
    "Spāres C24 45×{DJ:.0f} c/c 600 pa jumta plaknēm ar iezāģi 50 mm uz augšgulšņa (bez pārkares gals vertikāls karkasa ārmalā); L jumtam ielejas spāres saīsinātas pēc ielejas līnijas.",
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
    rem = g - (CLEAR_MAX + CC * (k - 1) + B)             # atlikusī atstarpe aiz pēdējā statņa
    if rem < MIN_GAP:
        # pēdējā atstarpe < 40 mm: pēdējo statni nevelk, pēdējo posmu līdz atstarpes galam dala ar statni uz pusēm
        start = (pos[k - 2] + B) if k > 1 else a
        span = b - start - B                              # divu vienādu posmu kopējais tīrais platums
        pos = pos[:k - 1] + [start + span / 2]
    for p in pos:
        mk(p)


def build_panel(P, opens, junctions, rot_ends):
    """Detaļas panelim P. opens: [{u0,u1,sill,head,tips}]; junctions: starpsienu asis u; rot_ends: (sākumā, beigās) pagriezts statnis stūrim."""
    L, D = P.L, P.D
    if UZL_W or UZL_H:   # ailu uzlaide (durvīm tikai platumā un augšā)
        opens = [dict(o, u0=o['u0'] - UZL_W / 2, u1=o['u1'] + UZL_W / 2, head=o['head'] + (0 if o.get('fix') else UZL_H / 2),
                      sill=(o['sill'] - UZL_H / 2 if o['sill'] > 0 else 0)) for o in opens]
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
    for i in range(NB):
        for s0, s1 in segs:
            P.add('HOR.STATNIS', 'bottom_plate', s0, s1, i * B, (i + 1) * B)
    # augšgulšņi pa augšmalas posmiem
    for (u0, z0), (u1, z1) in zip(P.top, P.top[1:]):
        k = (z1 - z0) / ((u1 - u0) or 1)
        for i in range(NT):
            dz = (i + 1) * B * math.sqrt(1 + k * k)
            if abs(k) < 1e-4:
                P.add('HOR.STATNIS', 'top_plate', u0, u1, z0 - dz, z0 - dz + B)
            else:
                P.add('SLIPAIS', 'top_plate', u0, u1, min(z0, z1) - dz, max(z0, z1) - dz + B, length=math.hypot(u1 - u0, z1 - z0), cut='slīps griezums gar jumtu')
    zb = NB * B

    def stud(u0, role, w=B, z0=None, z1=None, depth=None, cut=None):
        u1 = u0 + w
        a = zb if z0 is None else z0
        if z1 is None:
            t0, t1 = P.top_at(u0), P.top_at(u1)
            pl = NT * B * max(sl(u0), sl(u1))
            lo, hi = min(t0, t1) - pl, max(t0, t1) - pl
            if hi - lo > 2:
                return P.add('VERT.SLIPAIS', role, u0, u1, a, hi, length=hi - a, w=depth, cut=('slīps augšgals; ' + cut) if cut else 'slīps augšgals')
            return P.add('VERT.STATNIS', role, u0, u1, a, lo, length=lo - a, w=depth, cut=cut)
        return P.add('VERT.STATNIS', role, u0, u1, a, z1, length=z1 - a, w=depth, cut=cut)

    fixed = []
    stud(0, 'stud')
    fixed.append((0, B))
    sd0, sd1 = (rot_ends[0] if isinstance(rot_ends[0], int) and not isinstance(rot_ends[0], bool) else None,
                rot_ends[1] if isinstance(rot_ends[1], int) and not isinstance(rot_ends[1], bool) else None)
    if rot_ends[0]:   # kaste: 3 detaļas (statnis, pagriezts statnis, statnis), saskrūvējamas un piesledzamas frontonam
        r_ = stud(B, 'junction_rot', w=KD)
        if sd0:
            r_['sd'] = sd0
        stud(B + KD, 'stud')
        fixed[-1] = (0, 2 * B + KD)
    stud(L - B, 'stud')
    fixed.append((L - B, L))
    if rot_ends[1]:
        r_ = stud(L - B - KD, 'junction_rot', w=KD)
        if sd1:
            r_['sd'] = sd1
        stud(L - 2 * B - KD, 'stud')
        fixed[-1] = (L - 2 * B - KD, L)
    end_l, end_r = fixed[0][1], fixed[1][0]
    for jn in sorted(junctions, key=lambda t: t[0] if isinstance(t, tuple) else t):
        c, jw, jsd = jn if isinstance(jn, tuple) else (jn, KD, None)
        jw = max(jw, KD)           # kastes pagrieztais statnis vienmēr pilnā karkasa statņa platumā (45×KD), arī ja pieslēgtā siena plānāka
        u0 = c - jw / 2
        if u0 - B < end_l or u0 + jw + B > end_r:
            P.warn.append(f'starpsienas pieslēgums u={_r(c)} pie gala bloka, pārbaudīt')
            continue
        if any(o['u0'] - B <= c <= o['u1'] + B for o in opens):
            P.warn.append(f'starpsienas pieslēgums u={_r(c)} ailā, pārbaudīt')
            continue
        stud(u0 - B, 'junction')
        rot = stud(u0, 'junction_rot', w=jw)
        if jsd:
            rot['sd'] = jsd
        stud(u0 + jw, 'junction')
        fixed.append((u0 - B, u0 + jw + B))
    ops = sorted(opens, key=lambda o: o['u0'])
    for i, o in enumerate(ops):
        a0, a1, hb = o['u0'], o['u1'], o['head']
        room = min(P.top_at(a0 - B), P.top_at(a1 + B)) - NT * B * max(sl(a0), sl(a1))
        hdr_h = B + D                      # augšējais gulsnis (45) + pārsedze (45×D)
        if hb + hdr_h > room + 1:
            P.warn.append(f"aila {o['u1'] - o['u0']:.0f}×{hb - o['sill']:.0f}: pārsedze {hdr_h:.0f} mm neietilpst zem augšgulšņiem ({room:.0f}); vajag citu pārsedzi vai zemāku ailu")
        share_l = i > 0 and a0 - ops[i - 1]['u1'] <= 180
        share_r = i + 1 < len(ops) and ops[i + 1]['u0'] - a1 <= 180
        r = B if PASTIPR else 0            # pastiprinājuma statņi (3 posmos) blakus pilnajam statnim
        hl, hr = a0 - r, a1 + r            # horizontālās daļas piesledzas pilnajam statnim
        top_hdr = hb + hdr_h
        sillz = o['sill']
        for side, edge, shared in (('l', a0, share_l), ('r', a1, share_r)):
            kx = edge - r - B if side == 'l' else edge + r        # pilnais statnis
            stud(kx, 'king')
            if LOGU_DUBULTI and not shared:
                stud(kx - B if side == 'l' else kx + B, 'king')
            if PASTIPR:
                rx = edge - B if side == 'l' else edge
                segs_ = [(zb, sillz - B)] if sillz > 0 else []
                segs_.append((max(sillz, zb), hb))
                segs_.append((hb + B, None))       # virs pārsedzes: statnis iet līdz pārsedzes apakšai (gropē), par pārsedzes biezumu garāks
                for z0_, z1_ in segs_:
                    if z1_ is None:
                        if P.top_at(rx) - top_hdr > NT * B + 60:
                            stud(rx, 'jack', z0=z0_, cut='grope pārsedzei')
                    elif z1_ - z0_ > 20:
                        stud(rx, 'jack', z0=z0_, z1=z1_)
        lo_f = (a0 - r - B) - (B if LOGU_DUBULTI and not share_l else 0)
        hi_f = (a1 + r + B) + (B if LOGU_DUBULTI and not share_r else 0)
        fixed.append((lo_f, hi_f))
        P.add('HOR.STATNIS', 'opening_plate', hl, hr, hb, hb + B, w=D)               # augšējais horizontālais gulsnis
        P.add('PĀRSEDZE', 'header', hl, hr, hb + B, hb + B + D, w=D)                   # pārsedze tādā pašā garumā
        if a1 - a0 + 2 * r > CLEAR_MAX:
            _fill(hl, hr, lambda u, t=top_hdr, zh=hb + B: stud(u, 'cripple', z0=zh, cut='grope pārsedzei') if P.top_at(u) - t > NT * B + 60 else None)
        if sillz > 0:
            P.add('HOR.STATNIS', 'sill', hl, hr, sillz - B, sillz)                     # palodzes horizontālais gulsnis
            _fill(hl, hr, lambda u, z=sillz: stud(u, 'cripple', z0=zb, z1=z - B))
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
    P.opens = [{'u0': _r(o['u0']), 'u1': _r(o['u1']), 'sill': o['sill'], 'head': o['head'], 'tips': o['tips'], 'wh': o.get('wh'), 'sp': o.get('sp', 0)} for o in opens]
    return P


def generate(m):
    """model.json -> {'paneli': [Panel], 'jumts': roof_geom, 'D': ..., 'piezimes': [...]}"""
    apply_settings(m)
    LY = layers_of(m)
    D, off = frame_of(LY['S1']['layers'])
    global KD
    KD = D
    DJ, _ = frame_of(LY['J1']['layers'], 195.0)
    d = archicad.data_of(m)
    roof = roof_geom(m)
    z = roof['z']
    W, Dd = float(m['W']), float(m['D'])
    poly = [tuple(map(float, p)) for p in (m.get('poly') or [[0, 0], [W, 0], [W, Dd], [0, Dd]])]
    n = len(poly)
    ZP = min(z(p[0], p[1]) for p in poly) + off * roof['planes'][0][2] + SEAT   # augšgulšņa virsa: spāres apakša karkasa ārmalā + iezāģis
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
        nx, ny = -dy, dx
        mx, my = (x0 + x1) / 2 + nx * 20, (y0 + y1) / 2 + ny * 20
        c = False
        for i in range(n):          # kontrole: normāle jāvērš ārpus kontūras (neatkarīgi no apgriešanās virziena)
            (ax, ay), (bx, by) = poly[i], poly[i - 1]
            if (ay > my) != (by > my) and mx < (bx - ax) * (my - ay) / (by - ay) + ax:
                c = not c
        return (-nx, -ny) if c else (nx, ny)

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

    S2 = LY['S2']['layers']
    DPART = {}
    for p in part:
        t = float(p['t'])
        DPART[p['id']] = max(45.0, round(t - (sum(float(l[1] or 0) for l in S2 if (len(l) < 3 or l[2] != 'i')) if abs(t - sum(float(l[1] or 0) for l in S2)) < 2 else 50)))
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
        top = _simplify([(Lp * j / N, max(z(*fx(Lp * j / N)), ZP)) for j in range(N + 1)])   # augša = spāres apakša, bet ne zemāk par augšgulsni ZP (iezāģa horizontālā daļa frontona galā)
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
                            'tips': o['tips'], 'fix': head == HDR_BOT, 'wh': float(o.get('augstums') or 2070), 'sp': SP})
        junc = []
        for p in part:
            for pt in (p['a'], p['b']):
                dn = (pt[0] - ox) * (-nx) + (pt[1] - oy) * (-ny)     # attālums iekšup no karkasa ārmalas
                if 0 < dn < D + 300:
                    cu = (pt[0] - ox) * dirx + (pt[1] - oy) * diry
                    if 0 < cu < Lp:
                        junc.append((cu, DPART[p['id']], None))
        build_panel(P, ops, junc, (through and cvL, through and cvR))
        P.edge, P.side = e, ('north' if ny < -.5 else 'south' if ny > .5 else 'west' if nx < -.5 else 'east')
        P.o, P.dir, P.nin = (ox, oy), (dirx, diry), (-nx, -ny)
        panels.append(P)
    # starpsienas
    S2 = LY['S2']['layers']
    PR = []     # starpsienu neapstrādātie gabali (ass, gali, biezums), lai gali saskaras ar blakus sienām
    for j, p in enumerate(part):
        t = float(p['t'])
        dpart = max(45.0, round(t - (sum(float(l[1] or 0) for l in S2 if (len(l) < 3 or l[2] != 'i')) if abs(t - sum(float(l[1] or 0) for l in S2)) < 2 else 50)))
        hz = abs(p['a'][1] - p['b'][1]) < 1
        a_, b_ = (p['a'][0], p['b'][0]) if hz else (p['a'][1], p['b'][1])
        PR.append({'hz': hz, 'c': p['a'][1] if hz else p['a'][0], 'lo': min(a_, b_), 'hi': max(a_, b_), 'dp': dpart, 'walls': [p]})
    # kolineāras starpsienas, ko perpendikulāra siena (T mezgls) sadalījusi, ir viena siena: apvieno vienā panelī
    again = True
    while again:
        again = False
        for ia in range(len(PR)):
            for ib in range(len(PR)):
                a_, b_ = PR[ia], PR[ib]
                if ia == ib or a_['hz'] != b_['hz'] or abs(a_['c'] - b_['c']) > 5 or abs(a_['dp'] - b_['dp']) > 1 or b_['lo'] < a_['lo']:
                    continue
                gap_ = b_['lo'] - a_['hi']
                if not -1 <= gap_ <= 400:
                    continue
                tee_ = any(q['hz'] != a_['hz'] and a_['hi'] - 60 <= q['c'] <= b_['lo'] + 60 and q['lo'] - q['dp'] - 150 <= a_['c'] <= q['hi'] + q['dp'] + 150
                           for q in PR if q is not a_ and q is not b_)
                if gap_ <= 60 or tee_:
                    PR[ia] = {**a_, 'hi': max(a_['hi'], b_['hi']), 'walls': a_['walls'] + b_['walls']}
                    del PR[ib]
                    again = True
                    break
            if again:
                break

    def _snap(j, end):
        """Starpsienas gals j (0 = lo, 1 = hi) uz tuvāko perpendikulāro ārsienas iekšmalu vai starpsienas skaldni (bez spraugām)."""
        me = PR[j]
        cur = me['hi'] if end else me['lo']
        sg = 1 if end else -1                      # virziens no sienas ķermeņa uz galu
        best, bd = None, 1e9
        for P0 in [q for q in panels if q.kind == 'arsiena']:
            (ex0, ey0), (ex1, ey1) = P0.edge
            ehz = abs(ey0 - ey1) < 1
            if ehz == me['hz']:
                continue
            line = ex0 if me['hz'] else ey0
            inner = line - (off + D) * (1 if (P0.side in ('east', 'south')) else -1)
            span = sorted((ey0, ey1) if me['hz'] else (ex0, ex1))
            if span[0] - 1 <= me['c'] <= span[1] + 1 and abs(cur - inner) < 500 and abs(cur - inner) < bd:
                best, bd = inner, abs(cur - inner)
        cand = [q for i, q in enumerate(PR) if i != j and q['hz'] != me['hz'] and abs(cur - q['c']) < q['dp'] / 2 + 300
                and q['lo'] - me['dp'] - 150 <= me['c'] <= q['hi'] + me['dp'] + 150]
        if cand:
            q = min(cand, key=lambda r: abs(cur - r['c']))
            same = [r for r in PR if r['hz'] == q['hz'] and abs(r['c'] - q['c']) < 5]
            lo2, hi2 = min(r['lo'] for r in same), max(r['hi'] for r in same)
            tee = lo2 < me['c'] - q['dp'] / 2 - 60 and hi2 > me['c'] + q['dp'] / 2 + 60       # sieta turpinās abās pusēs
            coll = any(i != j and r['hz'] == me['hz'] and abs(r['c'] - me['c']) < 5 and abs((r['lo'] if end else r['hi']) - cur) < 300 for i, r in enumerate(PR))
            near = q['c'] - sg * q['dp'] / 2        # skaldne, kas pavērsta pret sienas ķermeni
            far = q['c'] + sg * q['dp'] / 2
            pass_through = me['hz'] and not tee and not coll      # L stūrī horizontālā iet cauri līdz tālajai šķautnei
            ends_here = not me['hz'] and (abs(q['lo'] - me['c']) < me['dp'] + 200 or abs(q['hi'] - me['c']) < me['dp'] + 200)
            cont = any(i != j and r['hz'] == me['hz'] and abs(r['c'] - me['c']) < 5 and abs((r['lo'] if end else r['hi']) - (q['c'] + sg * q['dp'] / 2)) < 300 for i, r in enumerate(PR))
            hpair = ends_here and any(r is not q and r['hz'] == q['hz'] and abs(r['c'] - q['c']) < 5 and (abs(r['lo'] - me['c']) < me['dp'] + 200 or abs(r['hi'] - me['c']) < me['dp'] + 200) for r in PR)
            v = far if (pass_through or (ends_here and cont and end) or hpair) else near   # T: starpsiena beidzas pie šīs sienas; augšējā daļa iet cauri, apakšējā pieslēdzas
            if abs(cur - v) < bd or best is None:
                best, bd = v, abs(cur - v)
        return cur if best is None else best

    SN = [(_snap(j, 0), _snap(j, 1)) for j in range(len(PR))]

    def _joins(j):
        """Starpsienas j mezgli ar perpendikulārām starpsienām: T mezgli (kaste vidū) un L stūri (pagriezts statnis galā)."""
        me, (lo, hi) = PR[j], SN[j]
        jun, ends = [], [False, False]
        for i, q in enumerate(PR):
            if i == j or q['hz'] == me['hz']:
                continue
            qlo, qhi = SN[i]
            for e_, o_ in ((qlo, qhi), (qhi, qlo)):
                if abs(e_ - me['c']) > me['dp'] / 2 + 5 or not (lo - 5 <= q['c'] <= hi + 5):
                    continue
                sd = 1 if o_ > me['c'] else -1               # kurā pusē ir pieslēgtās sienas ķermenis
                if q['c'] - lo < max(q['dp'], KD) / 2 + 60:
                    ends[0] = sd
                elif hi - q['c'] < max(q['dp'], KD) / 2 + 60:
                    ends[1] = sd
                elif not any(abs(c0 - (q['c'] - lo)) < 60 for c0, _w, _s in jun):
                    jun.append((q['c'] - lo, q['dp'], sd))
        return jun, tuple(ends)

    for j in range(len(PR)):
        hz, fixed_c, dpart = PR[j]['hz'], PR[j]['c'], PR[j]['dp']
        lo, hi = SN[j]
        Lp = hi - lo
        if Lp < 200:
            continue
        P = Panel(f'S{j + 1}', 'starpsiena', Lp, [(0, ceil), (Lp, ceil)], dpart, '(starpsiena)')
        ops = []
        for o in d['opens']:
            p = next((w_ for w_ in PR[j]['walls'] if w_['id'] == o['siena']), None)
            if p is None:
                continue
            wd = (p['b'][0] - p['a'][0], p['b'][1] - p['a'][1])
            wl_ = math.hypot(*wd)
            c_ = (p['a'][0] + wd[0] / wl_ * o['poz']) if hz else (p['a'][1] + wd[1] / wl_ * o['poz'])
            cu = c_ - lo
            ops.append({'u0': cu - o['platums'] / 2, 'u1': cu + o['platums'] / 2, 'sill': 0 if o['tips'] == 'durvis' else o['palodze'],
                        'head': HDR_BOT if o['tips'] == 'durvis' else o['palodze'] + o['augstums'], 'tips': o['tips'],
                        'fix': o['tips'] == 'durvis', 'wh': float(o.get('augstums') or 2070), 'sp': SP})
        jn_, re_ = _joins(j)
        build_panel(P, ops, jn_, re_)
        P.axis = (hz, fixed_c, lo, hi)
        panels.append(P)
    pie = [s.format(D=D, DJ=DJ, NB=NB) for s in PIE]
    return {'id': m.get('id'), 'zp': ZP, 'paneli': panels, 'jumts': roof, 'D': D, 'DJ': DJ, 'off': off, 'piezimes': pie + warn, 'slani': LY}


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



def frame3d(m):
    """Karkass 3D skatam: paneļu detaļas kā (u, z) daudzstūri ar dziļumu + spāres. Pasaules punkts = o + dir*u + nin*d (plāna x, y), z uz augšu."""
    res = generate(m)
    panels, mem = [], []
    for P in res['paneli']:
        if getattr(P, 'o', None) is not None and hasattr(P, 'dir'):
            o, dr, ni = P.o, P.dir, P.nin
        elif hasattr(P, 'axis'):
            hz, c, lo, hi = P.axis
            o, dr, ni = ((lo, c - P.D / 2), (1, 0), (0, 1)) if hz else ((c - P.D / 2, lo), (0, 1), (1, 0))
        else:
            continue
        pi = len(panels)
        panels.append({'id': P.id, 'kind': P.kind, 'o': [_r(o[0]), _r(o[1])], 'd': [_r(dr[0]), _r(dr[1])], 'n': [_r(ni[0]), _r(ni[1])]})
        for q in P.m:
            u0, u1, z0, z1, role = q['u0'], q['u1'], q['z0'], q['z1'], q['loma']
            if role == 'top_plate' and q.get('cut'):
                k = P.slope_at((u0 + u1) / 2)
                s_ = math.sqrt(1 + k * k)
                zl = z0 if k >= 0 else z0 + abs(k) * (u1 - u0)
                zr = zl + k * (u1 - u0)
                poly = [(u0, zl), (u1, zr), (u1, zr + B * s_), (u0, zl + B * s_)]
            elif q.get('cut') and 'slīps augšgals' in q['cut']:
                pl = NT * B * max(math.sqrt(1 + P.slope_at(u0) ** 2), math.sqrt(1 + P.slope_at(u1) ** 2))
                poly = [(u0, z0), (u1, z0), (u1, P.top_at(u1) - pl), (u0, P.top_at(u0) - pl)]
            else:
                poly = [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
            mem.append([pi, role, [[_r(a), _r(b)] for a, b in poly], _r(q['h'])])
    # spāres: katrai jumta plaknei, soļi SPARE_CC pa horizontāli perpendikulāri kritumam, nogriezti pret plaknes kontūru
    rafters, rafs = [], []
    DJ = res['DJ']
    ZPf, off = res['zp'], res['off']
    zr_ = res['jumts']['z']
    ZE0 = min(zr_(p[0], p[1]) for p in res['jumts']['poly'])   # jumta apakša fasādes līnijā (pie teknes)
    for name, pts, tn in res['jumts']['planes']:
        P3 = [tuple(p) for p in pts]
        if len(P3) < 3:
            continue
        a, b, c = P3[0], P3[1], P3[2]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx_, ny_, nz_ = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        if abs(nz_) < 1e-9:
            continue
        gx, gy = -nx_ / nz_, -ny_ / nz_
        gl = math.hypot(gx, gy)
        if gl < 1e-9:
            continue
        dx, dy = gx / gl, gy / gl             # kritums uz augšu (plānā)
        lx, ly = -dy, dx
        zf = lambda x, y: a[2] + gx * (x - a[0]) + gy * (y - a[1])
        nn = math.sqrt(gx * gx + gy * gy + 1)
        nrm = (-gx / nn, -gy / nn, 1 / nn)
        poly2 = [(p[0], p[1]) for p in P3]
        lats = [p[0] * lx + p[1] * ly for p in poly2]
        l0, l1 = min(lats), max(lats)
        pos, t = [], l0
        while t < l1 - B - 1:
            pos.append(t)
            t += SPARE_CC
        pos.append(l1 - B)
        for t in pos:
            lc = t + B / 2
            xs = []
            for i in range(len(poly2)):
                p, q_ = poly2[i], poly2[(i + 1) % len(poly2)]
                lp, lq = p[0] * lx + p[1] * ly, q_[0] * lx + q_[1] * ly
                if (lp - lc) * (lq - lc) < 0:
                    f = (lc - lp) / (lq - lp)
                    x, y = p[0] + (q_[0] - p[0]) * f, p[1] + (q_[1] - p[1]) * f
                    xs.append(x * dx + y * dy)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                s0, s1 = xs[i], xs[i + 1]
                if s1 - s0 < 50:
                    continue
                p0 = (lc * lx + s0 * dx, lc * ly + s0 * dy)
                p1 = (lc * lx + s1 * dx, lc * ly + s1 * dy)
                rafters.append([[_r(p0[0]), _r(p0[1]), _r(zf(*p0))], [_r(p1[0]), _r(p1[1]), _r(zf(*p1))], [round(v, 4) for v in nrm]])
                # spāres profils vertikālā plaknē (u = s pa kritumu, z): iezāģis 50 uz augšgulšņa, bez pārkares gals vertikāls karkasa ārmalā, korē vertikāls zāģējums
                zb = lambda sv: zf(lc * lx + sv * dx, lc * ly + sv * dy)
                zlow = min(zf(*q_) for q_ in poly2)
                dz = DJ * nn
                ovl = max(0.0, (ZE0 - zb(s0)) / gl) if zb(s0) <= zlow + 1 else 0.0
                sw = s0 + ovl + off
                if zb(s0) <= zlow + 1 and sw + SEAT / gl < s1:
                    sc = SEAT / gl
                    pl = ([(s0, zb(s0)), (sw, zb(sw))] if ovl > 1 else []) + [(sw, ZPf), (sw + sc, ZPf), (s1, zb(s1)), (s1, zb(s1) + dz), (sw if ovl <= 1 else s0, zb(sw if ovl <= 1 else s0) + dz)]
                else:
                    pl = [(s0, zb(s0)), (s1, zb(s1)), (s1, zb(s1) + dz), (s0, zb(s0) + dz)]
                rafs.append({'o': [_r(t * lx), _r(t * ly)], 'd': [round(dx, 5), round(dy, 5)], 'n': [round(lx, 5), round(ly, 5)], 'poly': [[_r(a_), _r(b_)] for a_, b_ in pl]})
    return {'id': res.get('id'), 'D': res['D'], 'DJ': DJ, 'B': B, 'paneli': panels, 'det': mem, 'spares': rafters, 'rafs': rafs, 'B2': B}

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
