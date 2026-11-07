"""MM Homes: rediģējams rasējums (TESTS).

Lietošana:  python redaktors.py <model.json> [izvade.html]
Rezultāts:  <modeļa mape>/rasejumi/<id>_LV_redaktors.html

Lapa ir tā pati A3 rasējuma lapa (tas pats noformējums, tas pats kods), tikai pārbūvēta pārlūkā no model.json
katru reizi, kad lietotājs pārvelk logu, durvis vai mēbeli. Saglabātais model.json der build_model.py.
"""
import base64, json, os, re, shutil, sys, tempfile

import build_model as bm

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = '/*@@MM_BLOCKS@@*/'


def template(model_path, lang='LV'):
    """Pilnā lapa (LV), kurā modeļa bloku vietā ir MARK."""
    real = bm.rev_block
    bm.rev_block = lambda m, rev=bm.REV: MARK if rev == bm.REV else ''
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, 'model.json')
        shutil.copy(model_path, p)
        out = bm.build(p, [lang])[0]
        return open(out, encoding='utf-8').read()
    finally:
        bm.rev_block = real
        shutil.rmtree(tmp, ignore_errors=True)


def checker():
    """mm-check.mjs noteikumi (tie paši, kas komandrindā), lai lapa pārbauda sevi pēc katra labojuma."""
    s = open(os.path.join(HERE, 'sablons', 'mm-check.mjs'), encoding='utf-8').read()
    consts = s[s.index('const REQ'):s.index('const page')]
    a = s.index('page.evaluate(') + len('page.evaluate(')
    b = s.index(', { REQ, HALL_MAX', a)
    return consts + '\nconst MM_CHECK = ' + s[a:b] + ';\nwindow.MM_RUN_CHECK = () => MM_CHECK({ REQ, HALL_MAX, DOOR_MARGIN, DOOR_BACK, WIN_LOW, WIN_DEPTH, TOL });\n'


def jsstr(o):
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')


def main():
    mp = sys.argv[1]
    m = json.load(open(mp, encoding='utf-8'))
    tpl = template(mp)
    assert MARK in tpl, 'šablonā nav modeļa bloka vietas'
    d = os.path.join(HERE, 'sablons', 'redaktors')
    page = open(os.path.join(d, 'lapa.html'), encoding='utf-8').read()
    frame = open(os.path.join(d, 'iframe.js'), encoding='utf-8').read()
    # fasādes toņi: tekstūra un materiālu teksts katram, lai toni var mainīt lapā
    cfg = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
    tones = {k: dict(t, tex=base64.b64encode(open(os.path.join(HERE, 'sablons', t['tex']), 'rb').read()).decode()) for k, t in cfg['toni'].items()}
    viz3d = open(os.path.join(d, 'viz3d.js'), encoding='utf-8').read().replace('__MM_ATMOS__', jsstr(cfg['atmosferas']))
    three = open(os.path.join(d, 'three.min.js'), encoding='utf-8').read().replace('</script', '<\\/script')
    page = page.replace('/*@@VIZ3D@@*/', viz3d).replace('__MM_THREE__', three)
    for k, v in {'__MM_TONES__': jsstr(tones), '__MM_TEMPLATE__': jsstr(tpl), '__MM_MODEL__': jsstr(m), '__MM_FRAME_JS__': jsstr(checker() + '\n' + frame),
                 '__MM_NAME__': (m.get('projekts') or {}).get('modela_nosaukums') or m['nosaukums'], '__MM_ID__': m['id']}.items():
        page = page.replace(k, v)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(mp)), 'rasejumi', f"{m['id']}_LV_redaktors.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page)
    print(out)


if __name__ == '__main__':
    main()
