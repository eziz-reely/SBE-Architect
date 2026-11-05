"""MM Homes: 3D references bilde Gemini vizualizācijām (stūra skats, perspektīva ar taisnām vertikālēm).

Lietošana:  python ref.py <model.json> [tonis ...]
Rezultāts:  <modeļa mape>/viz/ref_<tonis>.svg (+ .png, ja ir pieejams Playwright: node sablons/png.mjs)

Ģeometrija nāk no model.json: gabarīti, jumts, logi, durvis, gala logi. Gemini šo bildi lieto kā precīzu formu,
tāpēc logu skaits, vietas un izmēri šeit ir tieši kā rasējumā.
"""
import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
IMG_W, IMG_H = 1536, 1024          # 3:2
EYE = 1600                         # acu augstums virs zemes, mm
YAW = 35                           # galvenā (ieejas) fasāde ~35° no frontāla


def ral(s):
    return {'RAL 7016': '#383E42', 'RAL 9016': '#F1F0EA', 'RAL 9005': '#1d1d1d'}.get(s, '#383E42')


class Cam:
    def __init__(self, m):
        W, D = m['W'], m['D']
        self.ground = -CFG['floor'].get('posts_ground', 600)
        dist = max(W, D) * 2.1
        a = math.radians(YAW)
        # skatītājs dienvidaustrumos: dienvidu (ieejas) fasāde dominē, austrumu gals ar lielo stiklu redzams
        tx, ty = W * .5, D * .5
        self.C = (tx + math.sin(a) * dist, ty + math.cos(a) * dist, self.ground + EYE)
        fx, fy = tx - self.C[0], ty - self.C[1]
        n = math.hypot(fx, fy)
        self.f = (fx / n, fy / n)
        self.r = (-self.f[1], self.f[0])   # plāna y iet uz dienvidiem: skatoties uz ziemeļiem, labā puse ir +x
        self.k, self.ox, self.oy = 1.0, 0.0, 0.0

    def raw(self, p):
        dx, dy, dz = p[0] - self.C[0], p[1] - self.C[1], p[2] - self.C[2]
        depth = dx * self.f[0] + dy * self.f[1]
        return ((dx * self.r[0] + dy * self.r[1]) / depth, -dz / depth)

    def __call__(self, p):
        u, v = self.raw(p)
        return (round(u * self.k + self.ox, 1), round(v * self.k + self.oy, 1))


def poly(cam, pts, **a):
    attrs = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
    return f'<polygon points="{" ".join(f"{x},{y}" for x, y in map(cam, pts))}" {attrs}/>'


def line(cam, p, q, **a):
    (x1, y1), (x2, y2) = cam(p), cam(q)
    attrs = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items())
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {attrs}/>'


def render(m, tone_key):
    tone = CFG['toni'][tone_key]
    plinth = ral((m.get('projekts') or {}).get('cokols') or 'RAL 9005')
    W, D = m['W'], m['D']
    pitch = m['jumts']['pitch']
    eave = m['jumts']['eave']
    ridge = m['ievade']['augstums']
    floorT = sum(l[1] for l in CFG['layers']['G1']['layers'])
    cam = Cam(m)
    g0 = cam.ground
    clad, frame = tone['sw'], ral(tone.get('logi', 'RAL 7016'))
    cb = tone.get('sturi', 0)
    tan = math.tan(math.radians(pitch))

    # kadrs: māja ~2/3 platuma, horizonts apakšējā trešdaļā
    pts = [(x, y, z) for x in (0, W) for y in (0, D) for z in (g0, ridge)]
    us = [cam.raw(p)[0] for p in pts]
    cam.k = IMG_W * .66 / (max(us) - min(us))
    cam.ox = IMG_W / 2 - cam.k * (max(us) + min(us)) / 2
    cam.oy = IMG_H * .64

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{IMG_W}" height="{IMG_H}" viewBox="0 0 {IMG_W} {IMG_H}">',
         f'<rect width="{IMG_W}" height="{IMG_H}" fill="#dfe3e6"/>',
         f'<rect y="{cam.oy}" width="{IMG_W}" height="{IMG_H - cam.oy}" fill="#9aa58c"/>']

    def wall(face, u0, u1, z0, z1):
        """punkts uz fasādes: south u=x (y=D), east u=y (x=W)."""
        if face == 'south':
            return [(u0, D, z0), (u1, D, z0), (u1, D, z1), (u0, D, z1)]
        return [(W, u0, z0), (W, u1, z0), (W, u1, z1), (W, u0, z1)]

    def boards(face, u0, u1, ztop):
        out = []
        for u in range(int(u0) + 120, int(u1), 120):
            zt = ztop(u) if callable(ztop) else ztop
            p = (u, D, -floorT) if face == 'south' else (W, u, -floorT)
            q = (u, D, zt) if face == 'south' else (W, u, zt)
            out.append(line(cam, p, q, stroke='rgba(0,0,0,.28)', stroke_width=1))
        return out

    def at(face, u, d, z):
        """punkts uz fasādes ar dziļumu d (mm) sienā: south u=x (y=D-d), east u=y (x=W-d)."""
        return (u, D - d, z) if face == 'south' else (W - d, u, z)

    def shade(hexc, k):
        c = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
        return '#%02x%02x%02x' % tuple(max(0, min(255, int(v * k))) for v in c)

    def seen(face, p, n):
        """virsma redzama, ja tās normāle (fasādes u/d/z asīs) vērsta pret kameru."""
        nx = (n[0], -n[1], n[2]) if face == 'south' else (-n[1], n[0], n[2])   # (u, d, z) -> (x, y, z)
        return sum(a * (c - b) for a, b, c in zip(nx, p, cam.C)) > 0

    def opening(face, u0, u1, z0, z1, door=False, glass_left=True):
        """logs vai durvis iedziļināti R = 150 mm: rāmis ailas dziļumā, ailas sāni un augša fasādes tonī un materiālā
        (redzamās virsmas ēnotas), metāla palodze loga tonī izvirzīta no sienas plaknes."""
        R = 150
        Q = lambda uu0, uu1, zz0, zz1, d=R: [at(face, uu0, d, zz0), at(face, uu1, d, zz0), at(face, uu1, d, zz1), at(face, uu0, d, zz1)]
        o = [poly(cam, Q(u0, u1, z0, z1), fill=shade(clad, .55), stroke='#111', stroke_width=1)]   # ailas aizmugure (ēna)
        f0, f1, fz0, fz1 = u0, u1, z0, z1
        o.append(poly(cam, Q(f0, f1, fz0, fz1), fill=frame, stroke='#111', stroke_width=1))
        o.append(poly(cam, Q(f0 + 60, f1 - 60, fz0 + (0 if door else 60), fz1 - 60), fill=frame if door else '#8fa3ad', stroke='#111', stroke_width=1))
        if not door and u1 - u0 > 1500:
            mid = (u0 + u1) / 2
            o.append(poly(cam, Q(mid - 35, mid + 35, z0 + 60, z1 - 60), fill=frame))
        if door:
            gx = u0 + 120 if glass_left else u1 - 280
            hx = u1 - 260 if glass_left else u0 + 220
            o.append(poly(cam, Q(gx, gx + 160, 150, 1950), fill='#8fa3ad', stroke='#111', stroke_width=1))
            o.append(poly(cam, Q(hx, hx + 40, 500, 1600, R - 40), fill='#b9bcbe', stroke='#555', stroke_width=.6))
        # ailas virsmas (tikai redzamās): sāni, augša, apakša (durvīm slieksnis)
        rev = [([at(face, u0, 0, z0), at(face, u0, R, z0), at(face, u0, R, z1), at(face, u0, 0, z1)], (1, 0, 0), 1.45),
               ([at(face, u1, 0, z0), at(face, u1, R, z0), at(face, u1, R, z1), at(face, u1, 0, z1)], (-1, 0, 0), 1.45),
               ([at(face, u0, 0, z1), at(face, u1, 0, z1), at(face, u1, R, z1), at(face, u0, R, z1)], (0, 0, -1), .5),
               ([at(face, u0, 0, z0), at(face, u1, 0, z0), at(face, u1, R, z0), at(face, u0, R, z0)], (0, 0, 1), 1.6)]
        for pts, n, k in rev:
            if seen(face, pts[0], n):
                o.append(poly(cam, pts, fill=shade(clad, k), stroke='#111', stroke_width=.8))
        if not door and z0 > 0:
            # metāla palodze loga tonī: no rāmja līdz 40 mm ārpus sienas, augšējā virsma + priekšmala
            o.append(poly(cam, [at(face, u0 - 30, -40, z0), at(face, u1 + 30, -40, z0), at(face, u1, R, z0), at(face, u0, R, z0)], fill=shade(frame, 1.25), stroke='#111', stroke_width=.8))
            o.append(poly(cam, Q(u0 - 30, u1 + 30, z0 - 45, z0, -40), fill=frame, stroke='#111', stroke_width=1))
        return o

    gable_top = lambda y: eave + min(y, D - y) * tan
    # austrumu gala fasāde (aiz dienvidu stūra)
    east = [(W, 0, -floorT), (W, D, -floorT), (W, D, eave), (W, D / 2, ridge), (W, 0, eave)]
    s.append(poly(cam, east, fill=clad, stroke='#111', stroke_width=1.5))
    s += boards('east', 0, D, gable_top)
    for w in m['windows']:
        if w['side'] == 'east':
            s += opening('east', w['y'], w['y'] + w['len'], w['sill'], w['head'])
    for gw in m.get('gableWins', []):
        if gw['side'] == 'east':
            u0, u1 = D - gw['u1'], D - gw['u0']
            z1 = min(gable_top(u0), gable_top(u1)) - 450
            s += opening('east', u0, u1, gw['z0'], z1)
    # dienvidu (ieejas) fasāde
    s.append(poly(cam, wall('south', 0, W, -floorT, eave), fill=clad, stroke='#111', stroke_width=1.5))
    s += boards('south', 0, W, eave)
    for w in m['windows']:
        if w['side'] == 'south':
            s += opening('south', w['x'], w['x'] + w['len'], w['sill'], w['head'])
    for d in m['doors']:
        if d.get('entry'):
            s += opening('south', d['x'], d['x'] + d['w'], 0, 2100, door=True)
    # stūru apdare (sarkanajam tonim)
    if cb:
        s.append(poly(cam, wall('south', W - cb, W, -floorT, eave), fill='#F2F0EA', stroke='#111', stroke_width=1))
        s.append(poly(cam, wall('south', 0, cb, -floorT, eave), fill='#F2F0EA', stroke='#111', stroke_width=1))
        s.append(poly(cam, [(W, D - cb, -floorT), (W, D, -floorT), (W, D, eave), (W, D - cb, eave)], fill='#F2F0EA', stroke='#111', stroke_width=1))
    # metāla cokols (stabveida pamati), tonis projekts.cokols, noklusējums RAL 9005
    s.append(poly(cam, wall('south', 0, W, g0 + 40, -floorT), fill=plinth))
    s.append(poly(cam, [(W, 0, g0 + 40), (W, D, g0 + 40), (W, D, -floorT), (W, 0, -floorT)], fill=plinth))
    # jumts: dienvidu slīpne ar valcprofila šuvēm, austrumu vējmala
    rz = ridge
    roof = [(0, D, eave), (W, D, eave), (W, D / 2, rz), (0, D / 2, rz)]
    s.append(poly(cam, roof, fill='#40464b', stroke='#111', stroke_width=1.5))
    for x in range(265, int(W), 530):
        s.append(line(cam, (x, D, eave), (x, D / 2, rz), stroke='#2a2f33', stroke_width=1.5))
    # vējmala: sarkanajam balti koka dēļi (~200 mm), pārējiem tieva metāla vējmalas skārda RAL 7016
    vb, vh = ('#F2F0EA', 220) if tone.get('vejmala') == 'balta' else ('#30363a', 90)
    s.append(poly(cam, [(W, D, eave), (W, D / 2, rz), (W, D / 2, rz - vh), (W, D, eave - vh)], fill=vb, stroke='#111', stroke_width=1))
    s.append(poly(cam, [(W, 0, eave), (W, D / 2, rz), (W, D / 2, rz - vh), (W, 0, eave - vh)], fill=vb, stroke='#111', stroke_width=1))
    # notekas: gar dienvidu dzegu, caurule pie austrumu stūra līdz 50 mm virs zemes
    s.append(poly(cam, [(0, D + 120, eave - 60), (W, D + 120, eave - 60), (W, D + 120, eave - 180), (0, D + 120, eave - 180)], fill='#2f3438'))
    s.append(poly(cam, [(W - 230, D + 120, g0 + 50), (W - 130, D + 120, g0 + 50), (W - 130, D + 120, eave - 180), (W - 230, D + 120, eave - 180)], fill='#2f3438'))
    s.append('</svg>')
    return '\n'.join(s)


def main(model_path, tones):
    m = json.load(open(model_path, encoding='utf-8'))
    out = os.path.join(os.path.dirname(os.path.abspath(model_path)), 'viz')
    os.makedirs(out, exist_ok=True)
    files = []
    for tk in tones:
        p = os.path.join(out, f'ref_{tk}.svg')
        open(p, 'w', encoding='utf-8').write(render(m, tk))
        files.append(p)
    try:
        subprocess.run(['node', os.path.join(HERE, 'sablons', 'png.mjs'), *files], check=True)
    except Exception as e:
        print('PNG netika uztaisīts (vajag node + Playwright):', e)
    return files


if __name__ == '__main__':
    a = sys.argv[1:]
    for f in main(a[0], a[1:] or list(CFG['toni'])):
        print(f)
