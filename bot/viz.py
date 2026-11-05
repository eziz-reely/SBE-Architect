"""MM Homes: fotoreālas vizualizācijas ar Gemini (Google API) no references bildes.

Lietošana (no mapes modelu-bots):
    python viz.py MM-30-01              -> viz/V1_peleks.png, pēc tam no tā V1_sarkans.png, V1_koks.png (pilns automāts)
    python viz.py MM-30-01 --pamats     -> tikai V1_peleks.png
    python viz.py MM-30-01 --toni       -> tikai V1_sarkans.png, V1_koks.png no esošā V1_peleks.png (tas pats kadrs, cits tonis)
    python viz.py MM-30-01 --tonis koks -> tikai viens tonis

Vajag:
    GEMINI_API_KEY vides mainīgais (mākoņa vidē) vai MM System/.env ar rindu GEMINI_API_KEY=...
    viz/ref_<tonis>.png (uztaisa ref.py; bots to dara pats)
Neobligāti .env: GEMINI_IMAGE_MODEL=... (noklusējums zemāk), ja Google maina modeļa nosaukumu.
Tikai Python standarta bibliotēka, nekas nav jāinstalē.
"""
import base64, glob, json, os, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # MM System
CFG = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
DEFAULT_MODEL = 'gemini-3-pro-image'

# ---- viena konstante visiem skatiem un toņiem: apkārtne, gaisma, kamera ----
# ---- kamera un stils: viena konstante visiem modeļiem; apkārtne + gaisma: modeļa atmosfēra (mm-config.json "atmosferas") ----
CAMERA = ("Camera: eye-level photograph from 1.6 m above the ground, 3:2 frame, vertical lines perfectly straight "
          "(architectural shift lens), the whole house together with its whole terrace is fully visible inside the frame with comfortable margins on all sides "
          "(house and terrace fill about three quarters of the frame width), horizon in the lower third. "
          "Style: photorealistic architectural photography, real materials, sharp detail, natural lens, no illustration look, no CGI look.")
ATMOS = list(CFG['atmosferas'])


def atmosphere(m):
    """Modeļa atmosfēra: model.json projekts.atmosfera, citādi pēc modeļa numura (MM-30-01 -> 1., MM-30-02 -> 2., ...)."""
    k = (m.get('projekts') or {}).get('atmosfera')
    if k not in CFG['atmosferas']:
        try:
            n = int(m['id'].rsplit('-', 1)[1])
        except Exception:
            n = 1
        k = ATMOS[(n - 1) % len(ATMOS)]
    return k, CFG['atmosferas'][k]['en']


FORBID = ("Do not add: any other terrace, deck, patio or steps than the one shown in the reference, railings, furniture, people, animals, cars, fences, "
          "lamps, signs, text, logos, plants or bushes against the walls, extra buildings.")
KEEP = ("DO NOT CHANGE (the reference image is exact): camera position and angle, house outline and proportions, roof shape "
        "and pitch (no roof overhang), position, width, height and number of every window and door. "
        "Do not add, remove, merge, enlarge or divide any opening. Window and door frames keep the colour shown.")


def openings(m):
    """Atveru skaits redzamajās fasādēs (dienvidu ieejas garsiena un austrumu gals), lai Gemini neizdomā papildu logus."""
    if not m:
        return ''
    from ref import wside
    ns = sum(1 for w in m['windows'] if wside(m, w) == 'south')
    ne = sum(1 for w in m['windows'] if wside(m, w) == 'east')
    ng = sum(1 for g in m.get('gableWins', []) if g['side'] == 'east')
    south = 'the entrance door and ' + (f'exactly {ns} window(s)' if ns else 'NO windows at all') 
    return (f" OPENING COUNT (from the reference image, exact): the long entrance facade has {south}, nothing else, the rest of that wall is plain cladding. "
            f"The east gable end has exactly {ne} large glazing and {ng} sloped pentagon (house-shaped) window above it: vertical sides and a pointed top whose two upper edges run parallel to the roof slopes, as drawn in the reference image. It must be clearly pentagonal, NOT a rectangle and NOT a thin strip. Nothing else, the wall areas beside the glazing are plain cladding. "
            "Do not invent any additional window, door, vent or shutter anywhere.")


def materials(tk, m=None):
    t = CFG['toni'][tk]
    ck = ((m or {}).get('projekts') or {}).get('cokols') or 'RAL 9005'
    plinth = 'anthracite grey metal plinth RAL 7016' if ck == 'RAL 7016' else 'black metal plinth RAL 9005'
    wall = {'peleks': 'painted graphite grey (close to RGB %s)' % t['sw'],
            'sarkans': 'painted traditional Norwegian red (close to RGB %s)' % t['sw'],
            'koks': 'natural oiled timber, warm honey-brown (close to RGB %s)' % t['sw'],
            'zals': 'painted dark forest green, deep and muted, matte Scandinavian paint (close to RGB %s)' % t['sw'],
            'balts': 'painted soft light grey-white, matte Scandinavian paint, clean and bright but not pure white (close to RGB %s)' % t['sw']}[tk]
    from ref import slab_mode
    if m and slab_mode(m):
        foundation = ("The house stands directly on the ground. NO concrete, NO foundation, NO plinth, NO posts and NO slab edge are visible anywhere: "
                      "only a wooden terrace (single step, 25 cm above the ground) touches the ground and the house. The vertical cladding boards of the house walls "
                      "go down to the terrace deck surface and stop there. The terrace edge (a dark anthracite grey RAL 7016 deck-board fascia, about 25 cm high) meets the grass directly, "
                      "with a thin shadow gap and NO concrete strip under or beside it. "
                      "The terrace is made of horizontal anthracite grey (RAL 7016) wooden deck boards laid along the long side of the house, thin gaps between boards. "
                      "It runs 1.1 m deep along the whole entrance wall (the long wall with the entrance door) and continues 3 m beyond the glazed gable end, "
                      "exactly as in the reference image (L-shaped terrace, no railing, no furniture on it). The entrance door opens onto the terrace.")
    else:
        foundation = (f"The house stands on a hidden post foundation: a {plinth} about 30 cm high, "
                      "with a thin shadow gap above the ground.")
    frames = {'RAL 9016': 'white (RAL 9016)', 'RAL 9005': 'black (RAL 9005)'}.get(t.get('logi'), 'anthracite grey (RAL 7016)')
    s = (f"Materials: walls are vertical cladding boards {wall}. Roof: dark anthracite standing seam steel RAL 7016, no overhang, "
         f"thin anthracite gutter along the eave and a round anthracite downpipe ending 5 cm above the ground. "
         f"Windows and the entrance door: {frames} frames, set back (recessed) into the wall about 15 cm, NOT flush with the cladding: the reference image shows the visible reveal sides of every opening, keep that depth. "
         f"The window reveals (jambs and heads of each opening) are clad in the same colour and material as the facade walls. "
         f"The entrance door leaf is flat in the frame colour, with one narrow vertical glass strip (about 16 cm wide, almost full door height) along the hinge side "
         f"and a long vertical stainless steel bar handle (about 110 cm) on the opening side, exactly as in the reference image. "
         f"Every window has a thin projecting metal window sill (drip sill) in the frame colour at its bottom edge. "
         f"The flat casing boards (about 10 cm wide trim around every window and the entrance door on the facade) are in the same colour as the frames: {frames}. "
         f"Glass reflects the overcast sky. "
         f"{foundation}")
    if t.get('vejmala') == 'balta':
        s += " Roof verge (sloping fascia board along the gable roof edge): white painted timber verge boards (classic Norwegian detail)."
    else:
        s += " Roof verge (sloping fascia along the gable roof edge): only a slim anthracite RAL 7016 metal verge flashing, no timber boards, no white."
    if t.get('sturi'):
        s += f" White corner trims {t['sturi']} mm wide on every corner of the house (classic Norwegian detail)."
    return s


def env():
    for p in (os.path.join(ROOT, '.env'), os.path.join(HERE, '.env')):
        if os.path.exists(p):
            for ln in open(p, encoding='utf-8'):
                if '=' in ln and not ln.lstrip().startswith('#'):
                    k, v = ln.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise SystemExit('Nav GEMINI_API_KEY (vides mainīgais vai MM System\\.env).')
    return key, os.environ.get('GEMINI_IMAGE_MODEL', DEFAULT_MODEL)


def gemini(key, model, text, images):
    parts = [{'text': text}] + [{'inline_data': {'mime_type': 'image/png', 'data': base64.b64encode(open(p, 'rb').read()).decode()}} for p in images]
    body = {'contents': [{'parts': parts}],
            'generationConfig': {'responseModalities': ['TEXT', 'IMAGE'], 'imageConfig': {'aspectRatio': '3:2'}}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                 data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        raise SystemExit(f'Gemini kļūda {e.code}: {e.read().decode()[:600]}')
    for c in r.get('candidates', []):
        for p in c.get('content', {}).get('parts', []):
            d = p.get('inlineData') or p.get('inline_data')
            if d and d.get('data'):
                return base64.b64decode(d['data'])
    raise SystemExit('Gemini neatdeva bildi: ' + json.dumps(r)[:600])


def model_dir(mid):
    hits = glob.glob(os.path.join(ROOT, 'MĀJAS', '*', mid, 'model.json'))
    if not hits:
        raise SystemExit(f'Nav atrasts MĀJAS/*/{mid}/model.json')
    return os.path.dirname(hits[0])


def make_base(mid, viz, key, model):
    base = os.path.join(viz, 'V1_peleks.png')
    ref = os.path.join(viz, 'ref_peleks.png')
    if not os.path.exists(ref):
        raise SystemExit('Nav viz/ref_peleks.png. Palaid: python ref.py <model.json>')
    m = json.load(open(os.path.join(os.path.dirname(viz), 'model.json'), encoding='utf-8'))
    ak, scene = atmosphere(m)
    print('atmosfēra:', ak, '-', CFG['atmosferas'][ak]['lv'])
    text = ("Turn this technical reference image of a small modular house into a photorealistic photograph. " + KEEP + " " +
            materials('peleks', m) + openings(m) + " " + scene + " Realistic Scandinavian colours. " + CAMERA + " " + FORBID)
    open(base, 'wb').write(gemini(key, model, text, [ref]))
    open(base.replace('.png', '_prompt.txt'), 'w', encoding='utf-8').write(text)
    return base


def make_tones(mid, viz, key, model, tones):
    base, outs = os.path.join(viz, 'V1_peleks.png'), []
    if not os.path.exists(base):
        raise SystemExit('Vispirms uztaisi V1_peleks.png (python viz.py %s)' % mid)
    m = json.load(open(os.path.join(os.path.dirname(viz), 'model.json'), encoding='utf-8'))
    for tk in tones:
        text = ("Edit the FIRST image, a photograph. Change ONLY the colours, trims and roof verge of the house so they match the SECOND image "
                "(a technical reference with the target colours and the exact opening layout). " + materials(tk, m) + " "
                "Keep everything else identical to the first image: camera, framing, sky, light, the whole landscape, path, "
                "roof, plinth, gutters and every opening. " + KEEP + openings(m))
        out = os.path.join(viz, f'V1_{tk}.png')
        open(out, 'wb').write(gemini(key, model, text, [base, os.path.join(viz, f'ref_{tk}.png')]))
        open(out.replace('.png', '_prompt.txt'), 'w', encoding='utf-8').write(text)
        outs.append(out)
    return outs


def run(mid, mode='viss', tones=None):
    """mode: 'viss' = pelēkais + visi toņi (botam pilnā automātā), 'pamats' = tikai pelēkais, 'toni' = tikai toņi."""
    viz = os.path.join(model_dir(mid), 'viz')
    key, model = env()
    # visi toņi (sarkans, koks, zaļš, balts) pēc noklusējuma; ar --tonis var norādīt konkrētus
    tones = tones or [t for t in CFG['toni'] if t != 'peleks']
    outs = []
    if mode in ('viss', 'pamats'):
        outs.append(make_base(mid, viz, key, model))
    if mode in ('viss', 'toni'):
        outs += make_tones(mid, viz, key, model, tones)
    return outs


def main():
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if '--tonis' in a:
        outs = run(a[0], 'toni', a[a.index('--tonis') + 1:])
    elif '--toni' in a:
        outs = run(a[0], 'toni')
    elif '--pamats' in a:
        outs = run(a[0], 'pamats')
    else:
        outs = run(a[0], 'viss')
    for o in outs:
        print(o)


if __name__ == '__main__':
    main()
