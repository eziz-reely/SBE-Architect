"""Mājas kontūra no taisnstūriem: bloki (galvenais, spārni) mīnus robi (ieejas padziļinājumi).

model.json:
    "kontura": {
      "bloki": [{"r": [x, y, w, h], "loma": "galvenais"}, {"r": [...], "loma": "sparns"}],
      "robi":  [{"puse": "south", "plat": 3000, "dzil": 1500, "nob": 2000,
                 "stabi": true, "pakapiens": true}]
    }
No tā rodas `poly` (taisnleņķa kontūra pulksteņrādītāja virzienā, y uz leju) un `recess` (fasāžu ieliekumi).
Bloku var būt cik vajag (L = 2, nākotnē 3 bloku māja ar izvirzījumiem); robu arī.

Roba nobīde `nob` ir no fasādes kreisā stūra, skatoties uz fasādi no ārpuses (tāpat kā `recess` u).
Roba dziļums skaitās no tās fasādes malas, kas šajā vietā ir visvairāk ārā.

Tā pati loģika JS pusē ir redaktorā (lapa.html: konturaPoly, robRect, recessOf), tām jāsakrīt.

    python kontura.py                # pašpārbaude (taisnstūris, L, robs, 3 bloki)
"""
import sys

SIDES = ('north', 'south', 'west', 'east')


def _grid(rects_on, rects_off):
    xs = sorted({v for r in rects_on + rects_off for v in (r[0], r[0] + r[2])})
    ys = sorted({v for r in rects_on + rects_off for v in (r[1], r[1] + r[3])})
    inr = lambda r, x, y: r[0] < x < r[0] + r[2] and r[1] < y < r[1] + r[3]
    C = [[any(inr(r, (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2) for r in rects_on) and
          not any(inr(r, (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2) for r in rects_off)
          for i in range(len(xs) - 1)] for j in range(len(ys) - 1)]
    return xs, ys, C


def _trace(xs, ys, C):
    """Šūnu režģa robeža → viena kontūra vai None (tukšs, vairāki gabali, caurums, stūru saskare)."""
    ny, nx = len(C), len(C[0]) if C else 0
    on = lambda i, j: 0 <= i < nx and 0 <= j < ny and C[j][i]
    cells = [(i, j) for j in range(ny) for i in range(nx) if C[j][i]]
    if not cells:
        return None
    seen, st = {cells[0]}, [cells[0]]
    while st:
        i, j = st.pop()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if on(i + a, j + b) and (i + a, j + b) not in seen:
                seen.add((i + a, j + b)); st.append((i + a, j + b))
    if len(seen) != len(cells):
        return None
    E = {}
    for i, j in cells:
        x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
        if not on(i, j - 1): E[(x0, y0)] = (x1, y0)
        if not on(i + 1, j): E[(x1, y0)] = (x1, y1)
        if not on(i, j + 1): E[(x1, y1)] = (x0, y1)
        if not on(i - 1, j): E[(x0, y1)] = (x0, y0)
    start = next(iter(E)); out, k = [], start
    for _ in range(len(E) + 1):
        out.append(list(k)); k = E.get(k)
        if k is None:
            return None
        if k == start:
            break
    if len(out) != len(E):
        return None
    n = len(out)
    o2 = [q for i, q in enumerate(out) if not ((out[i - 1][0] == q[0] == out[(i + 1) % n][0]) or (out[i - 1][1] == q[1] == out[(i + 1) % n][1]))]
    i0 = min(range(len(o2)), key=lambda i: (o2[i][1], o2[i][0]))
    return o2[i0:] + o2[:i0]


def bbox(P):
    xs, ys = [p[0] for p in P], [p[1] for p in P]
    return min(xs), min(ys), max(xs), max(ys)


def rob_rect(P, rob):
    """Roba taisnstūris [x, y, w, h] kontūrā P (pirms izgriešanas)."""
    x0, y0, x1, y1 = bbox(P)
    side, w, d, off = rob['puse'], float(rob['plat']), float(rob['dzil']), float(rob.get('nob', 0))
    hz = side in ('north', 'south')
    L = (x1 - x0) if hz else (y1 - y0)
    flip = side in ('north', 'east')
    a0 = (x0 if hz else y0) + (L - off - w if flip else off)
    a1 = a0 + w
    # visvairāk ārā esošā mala šajā fasādes posmā
    edges = [(P[i], P[(i + 1) % len(P)]) for i in range(len(P))]
    k = 1 if hz else 0
    cand = [a[k] for a, b in edges if abs(a[k] - b[k]) < .5 and min(a[1 - k], b[1 - k]) < a1 - .5 and max(a[1 - k], b[1 - k]) > a0 + .5]
    if not cand:
        return None
    face = max(cand) if side in ('south', 'east') else min(cand)
    if hz:
        return [a0, face - d, w, d] if side == 'south' else [a0, face, w, d]
    return [face - d, a0, d, w] if side == 'east' else [face, a0, d, w]


def poly_of(K):
    """kontura → (poly, robu taisnstūri) vai (None, kļūda)."""
    bl = [b['r'] for b in K.get('bloki', [])]
    if not bl:
        return None, 'nav bloku'
    xs, ys, C = _grid(bl, [])
    P = _trace(xs, ys, C)
    if not P:
        return None, 'bloki nesaskaras vai veido caurumu'
    cuts = []
    for rb in K.get('robi', []):
        R = rob_rect(P, rb)
        if not R:
            return None, f"robs {rb.get('puse')} neatrodas uz fasādes"
        cuts.append(R)
    if cuts:
        xs, ys, C = _grid(bl, cuts)
        P2 = _trace(xs, ys, C)
        if not P2:
            return None, 'robs sadala māju vai nogriež visu malu'
        if bbox(P2) != bbox(P):
            return None, 'robs nogriež visu mājas malu'
        P = P2
    return [[round(v, 1) for v in q] for q in P], cuts


def recess_of(P):
    """Fasāžu ieliekumi: katrai pusei [[u0, u1, dziļums]], u no fasādes kreisās malas (kā redaktora recessOf)."""
    x0, y0, x1, y1 = bbox(P)
    W, D = x1 - x0, y1 - y0
    E = [(P[i], P[(i + 1) % len(P)]) for i in range(len(P))]
    out = {}
    for sd, vert in (('south', 0), ('north', 0), ('west', 1), ('east', 1)):
        ed = [((min(a[1], b[1]) - y0, max(a[1], b[1]) - y0, a[0] - x0) if vert else (min(a[0], b[0]) - x0, max(a[0], b[0]) - x0, a[1] - y0))
              for a, b in E if (abs(a[0] - b[0]) < .5 if vert else abs(a[1] - b[1]) < .5)]
        cs = sorted({v for e in ed for v in e[:2]})
        S, L = (W, D) if vert else (D, W)
        far, flip = sd in ('south', 'east'), sd in ('north', 'east')
        r = []
        for i in range(len(cs) - 1):
            mid = (cs[i] + cs[i + 1]) / 2
            hit = [(S - e[2]) if far else e[2] for e in ed if e[0] < mid < e[1]]
            if not hit:
                continue
            dep = min(hit)
            if dep > .5:
                u0, u1 = (L - cs[i + 1], L - cs[i]) if flip else (cs[i], cs[i + 1])
                last = r[-1] if r else None
                if last and abs(last[2] - dep) < .5 and abs((last[0] - u1) if flip else (last[1] - u0)) < .5:
                    if flip: last[0] = u0
                    else: last[1] = u1
                else:
                    r.append([u0, u1, dep])
        if r:
            out[sd] = sorted(r)
    return out


def apply(m):
    """Ieraksta modelī poly, recess, W, D no m['kontura']. Atgriež kļūdas tekstu vai None."""
    K = m.get('kontura')
    if not K:
        return None
    P, cuts = poly_of(K)
    if P is None:
        return cuts
    x0, y0, x1, y1 = bbox(P)
    if x0 or y0:
        return 'kontūrai jāsākas no 0,0'
    m['W'], m['D'] = x1, y1
    m['poly'] = P if len(P) > 4 else None
    if not m['poly']:
        m.pop('poly')
    m['recess'] = recess_of(P)
    return None


def L_kontura(A_len, A_w, B_len, B_w, sparns='sw', robi=()):
    """L māja no diviem spārniem: galvenais (garums A_len gar x, platums A_w), otrs spārns (B_len no galvenā malas, platums B_w).
    sparns: kurā galvenā spārna stūrī un uz kuru pusi iet otrais spārns: 'sw', 'se' (uz dienvidiem), 'nw', 'ne' (uz ziemeļiem)."""
    south = sparns[0] == 's'
    west = sparns[1] == 'w'
    bx = 0 if west else A_len - B_w
    if south:
        bl = [{'r': [0, 0, A_len, A_w], 'loma': 'galvenais'}, {'r': [bx, A_w, B_w, B_len], 'loma': 'sparns'}]
    else:
        bl = [{'r': [0, B_len, A_len, A_w], 'loma': 'galvenais'}, {'r': [bx, 0, B_w, B_len], 'loma': 'sparns'}]
    return {'bloki': bl, 'robi': list(robi)}


def _selftest():
    ok = True

    def eq(name, a, b):
        nonlocal ok
        if a != b:
            ok = False
            print('KĻŪDA', name, a, '!=', b)
    P, _ = poly_of({'bloki': [{'r': [0, 0, 10000, 6000]}]})
    eq('taisnstūris', P, [[0, 0], [10000, 0], [10000, 6000], [0, 6000]])
    K = L_kontura(15000, 7000, 5000, 6000, 'sw')
    P, _ = poly_of(K)
    eq('L', P, [[0, 0], [15000, 0], [15000, 7000], [6000, 7000], [6000, 12000], [0, 12000]])
    eq('L recess', recess_of(P), {'south': [[6000, 15000, 5000]], 'east': [[0, 5000, 9000]]})
    # robs uz taisnstūra dienvidu fasādes, 2000 no kreisā (rietumu) stūra
    P, c = poly_of({'bloki': [{'r': [0, 0, 10000, 6000]}], 'robi': [{'puse': 'south', 'plat': 3000, 'dzil': 1500, 'nob': 2000}]})
    eq('robs D', c, [[2000.0, 4500.0, 3000.0, 1500.0]])
    eq('robs D poly', P, [[0, 0], [10000, 0], [10000, 6000], [5000, 6000], [5000, 4500], [2000, 4500], [2000, 6000], [0, 6000]])
    # ziemeļu fasādē kreisais stūris ir austrumos
    _, c = poly_of({'bloki': [{'r': [0, 0, 10000, 6000]}], 'robi': [{'puse': 'north', 'plat': 3000, 'dzil': 1500, 'nob': 2000}]})
    eq('robs Z', c, [[5000.0, 0, 3000.0, 1500.0]])
    # robs L mājas spārnā (dienvidu fasāde, spārna gals)
    K = L_kontura(15000, 7000, 5000, 6000, 'sw', [{'puse': 'south', 'plat': 2000, 'dzil': 1200, 'nob': 2000}])
    P, c = poly_of(K)
    eq('robs L', c, [[2000.0, 10800.0, 2000.0, 1200.0]])
    # robs, kas nogriež visu malu
    P, e = poly_of({'bloki': [{'r': [0, 0, 10000, 6000]}], 'robi': [{'puse': 'south', 'plat': 10000, 'dzil': 1500, 'nob': 0}]})
    eq('robs visa mala', P, None)
    # 3 bloki (T/izvirzījumi) — arhitektūra atvērta
    P, _ = poly_of({'bloki': [{'r': [0, 0, 12000, 6000]}, {'r': [4000, 6000, 4000, 3000]}, {'r': [0, -2000, 3000, 2000]}]})
    eq('3 bloki', len(P), 10)
    print('OK' if ok else 'KĻŪDAS')
    return ok


if __name__ == '__main__':
    sys.exit(0 if _selftest() else 1)
