import json, os, math, sys
sys.path.insert(0, '/home/user/SBE-Architect/bot')
import planner as P
W, D = 16054.0, 12339.0
DB = 8619.0; WW = 6819.0
T, t = 283.5, 195
PITCH = 30
H = 5300
r1 = lambda x: round(x, 1)
# ---- telpas ----
wL = 3561.0
y6 = (283.5, 2005.5)
y7 = (2200.5, 2200.5 + 10.05e6 / wL); y8 = (y7[1] + t, y7[1] + t + 10.05e6 / wL); y9 = (y8[1] + t, 12055.5)
def R(x, y, w, h): return [r1(x), r1(y), r1(w), r1(h)]
rooms = [
 ('Priekštelpa', 'Entrance hall', [R(4995, 283.5, 2805, 1829)]),
 ('Gaitenis', 'Corridor', [R(4039.5, 2200.5, 850, 9855), R(4889.5, 2307.5, 2910.5, 900)]),
 ('Garderobe', 'Wardrobe room', [R(7995, 283.5, 1450, 2710)]),
 ('Pieliekamais', 'Pantry', [R(9640, 283.5, 1247, 2710)]),
 ('Dzīvojamā istaba ar virtuves zonu', 'Living room with kitchen', [R(7995, 3188.5, 7775.5, 5147), R(11082, 283.5, 4688.5, 2905), R(7315.5, 6749.5, 679.5, 1586)]),
 ('Tehniskā telpa', 'Technical room', [R(283.5, 283.5, 4516.5, 1722)]),
 ('Guļamistaba', 'Bedroom', [R(283.5, y7[0], wL, y7[1] - y7[0])]),
 ('Guļamistaba', 'Bedroom', [R(283.5, y8[0], wL, y8[1] - y8[0])]),
 ('Guļamistaba', 'Bedroom', [R(283.5, y9[0], wL, y9[1] - y9[0])]),
 ('Sanitārais mezgls', 'Bathroom', [R(5084.5, 8530.5, 1451, 3525)]),
 ('Palīgtelpa', 'Utility room', [R(5084.5, 6749.5, 2036, 1586)]),
 ('Sanitārais mezgls', 'Bathroom', [R(5084.5, 3402.5, 2715.5, 3152)]),
]
rooms = [{'n': n, 'en': e, 'r': r} for n, e, r in rooms]
def door(x, y, o, hinge, side, w=800, th=t, **k):
    d = {'x': r1(x), 'y': r1(y), 'o': o, 'hinge': hinge, 'side': side, 'w': w, 'th': th}; d.update(k); return d
doors = [
 door(6600, 0, 'h', 's', -1, 1000, T, entry=True),
 door(4045, 2005.5, 'h', 's', 1),                     # tehniskā -> gaitenis
 door(3844.5, 4300, 'v', 's', -1),                    # gulamistaba 7
 door(3844.5, 7200, 'v', 's', -1),                    # gulamistaba 8
 door(3844.5, 11000, 'v', 's', -1),                   # gulamistaba 9
 door(5300, 3207.5, 'h', 's', 1),                     # sanitārais 12
 door(4889.5, 7000, 'v', 's', 1),                     # palīgtelpa
 door(4889.5, 10300, 'v', 's', 1),                     # san.mezgls
 door(8300, 2993.5, 'h', 's', -1),                    # garderobe
 door(9760, 2993.5, 'h', 's', -1),                    # pieliekamais
 door(5500, 2112.5, 'h', 's', 1),                     # priekštelpa -> gaitenis
]
openings = [{'x': 7800, 'y': 2357.5, 'o': 'v', 'w': 800, 'th': 195}]
def win(x, y, ln, o, sill, head, kind, side, **k):
    w = {'len': ln, 'sill': sill, 'head': head, 'kind': kind, 'x': x, 'y': y, 'o': o, 'side': side}; w.update(k); return w
def two(ln): return {'parts': [{'len': ln / 2, 'kind': 'tilt', 'hinge': 'l'}, {'len': ln / 2, 'kind': 'fixed', 'hinge': 'l'}], 'tilt': True}
X1 = W - T
windows = [
 win(1500, 0, 1200, 'h', 900, 2100, 'tilt', 'north'),                 # tehniskā
 win(12400, 0, 1800, 'h', 900, 2100, 'casement2', 'north'),           # virtuve
 win(0, 3100, 1400, 'v', 1200, 2100, 'hopper', 'west', out=-1),       # g7
 win(0, 6200, 1400, 'v', 1200, 2100, 'hopper', 'west', out=-1),       # g8
 win(0, 9900, 1200, 'v', 1200, 2100, 'hopper', 'west', out=-1),       # g9
 win(800, 12055.5, 1400, 'h', 1200, 2100, 'tilt', 'south'),           # g9
 win(5500, 12055.5, 600, 'h', 1400, 2100, 'tilt', 'south'),           # san.mezgls
 win(8600, 8335.5, 2000, 'h', 0, 2400, 'fixed', 'south'),
 win(11000, 8335.5, 1800, 'h', 0, 2400, 'parts', 'south', **two(1800)),
 win(13400, 8335.5, 2000, 'h', 0, 2400, 'fixed', 'south'),
 win(X1, 1500, 1400, 'v', 900, 2100, 'tilt', 'east', out=1),
 win(X1, 3600, 1400, 'v', 0, 2400, 'fixed', 'east', out=1),
 win(X1, 5400, 1400, 'v', 0, 2400, 'fixed', 'east', out=1),
 win(X1, 7000, 800, 'v', 900, 2100, 'tilt', 'east', out=1),
]
# ---- mebeles ----
F = []
def A(*f): F.append(list(f))
# guļamistabas
for (ya, yb), nn in ((y7, 1), (y8, 2)):
    by = (ya + yb) / 2 - 800
    A('bed', 283.5, r1(by), 2000, 1600, 'w'); A('nightstand', 283.5, r1(by - 450)); A('nightstand', 283.5, r1(by + 1630))
    A('wardrobe', 2400, r1(ya), 1400, 600, 's')
by = (y9[0] + y9[1]) / 2 - 900
A('bed', 283.5, r1(by), 2000, 1800, 'w'); A('nightstand', 283.5, r1(by - 450)); A('nightstand', 283.5, r1(by + 1830))
A('wardrobe', 2400, r1(y9[0]), 1400, 600, 's')
# tehniskā
A('washer', 300, 300)
# sanitārais 10 (dienvidu spārns)
A('toilet', 5810, 12055.5, -1); A('basin', 6085.5, 10000, 450, 500, 'e'); A('shower', 5084.5, 8530.5, 900, ['e', 's'])
# sanitārais 12
A('toilet', 5084.5, 4600, 1, 'w'); A('basin', 5084.5, 5300, 450, 500, 'w')
A('R', 5700, 5774, 1700, 780, {'rx': 380}); A('washer', 7200, 3500)
# garderobe / pieliekamais plaukti
A('R', 7995, 283.5, 1450, 350); A('R', 9640, 283.5, 1247, 350)
# virtuve gar ziemeļu sienu + sala
it = P.kitchen_items(11200, 283.5, 3800, 'n')
for c in it.cmds: A(*c)
A('R', 11800, 1700, 2600, 900, {'rx': 20})
for cx in (12300, 12900, 13500): A('stool', cx, 2750)
# atpūtas zona un galds
A('sofa', 8300, 4200, 900, 2400, 'w')
A('R', 9600, 4800, 1200, 600, {'rx': 20})
A('galds', 13300, 4300, 790, 1800)
for cy in (4500, 5300): A('chair', 13050, cy, 'e'); A('chair', 14390, cy, 'w')
STAMPS = {4: (10800, 7000), 6: (2900, 3600), 7: (2900, 6300), 8: (2900, 10000), 9: (5650, 9700)}
# ---- jumts, terase, lievenis ----
eave = round(H - 295 / math.cos(math.radians(PITCH)) - (DB / 2) * math.tan(math.radians(PITCH)))
terrace = {'name': 'Terase', 'poly': [[6819, 8619], [16054, 8619], [16054, 11319], [6819, 11319]], 'posts': [[6819, 11169, 150], [10900, 11169, 150], [15904, 11169, 150], [15904, 8619, 150]]}
lievenis = {'name': 'Lievenis', 'poly': [[5113, -1210], [7872, -1210], [7872, 0], [5113, 0]], 'posts': [[5113, -1210, 150], [7722, -1210, 150]]}
m = {'id': 'MM-165-01', 'nosaukums': 'MM 165-01', 'platiba_grupa': '165m2',
 'ievade': {'garums': W, 'platums': D, 'augstums': H, 'augstums_0': H}, 'W': W, 'D': D,
 'poly': [[0, 0], [W, 0], [W, DB], [WW, DB], [WW, D], [0, D]],
 'recess': {'south': [[WW, W, 3720]], 'east': [[DB, D, W - WW]]},
 'jumts': {'forma': 'divslipju', 'pitch': PITCH, 'ov': 0, 'eave': eave},
 'rooms': rooms, 'doors': doors, 'openings': openings, 'windows': windows, 'furniture': F,
 'porch': [terrace, lievenis],
 'axes': {'x': [[0, '1'], [WW, '2'], [W, '3']], 'y': [[0, 'C'], [DB, 'B'], [D, 'A']]},
 'stampAt': {}, 'stampScale': {}, 'levelAt': [6000, 1700],
 'innerDims': [['x', 1000], ['y', 1000]],
 'wallTags': [], 'sections': [], 'entryInChain': True, 'gableWins': [],
 'ceiling': 2600, 'ceilingNote': 'Griestu augstums 2600 mm.', 'planNotes': [],
 'projekts': {'faze': 'klients', 'revizija': '00', 'adrese': [], 'modela_nosaukums': 'Nordika', 'tonis': 'peleks', 'pamati': 'platne', 'griesti': 0, 'piragi': 'ne', 'terase': 'ne'}}
# zīmju pozīcijas telpu centrā (lielākā taisnstūra centrs)
for i, r in enumerate(rooms):
    b = max(r['r'], key=lambda q: q[2] * q[3]); m['stampAt'][str(i)] = [round(b[0] + b[2] / 2), round(b[1] + b[3] / 2)]; m['stampScale'][str(i)] = 0.5
    if i in STAMPS: m['stampAt'][str(i)] = list(STAMPS[i])
out = '/home/user/SBE-Architect/MĀJAS/165m2/MM-165-01'
os.makedirs(out, exist_ok=True)
json.dump(m, open(out + '/model.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in rooms: print(r['n'], round(sum(q[2] * q[3] for q in r['r']) / 1e6, 2))
