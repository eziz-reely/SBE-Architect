"""MM Homes modeļu bots, 1. solis: model.json -> A3 lapa (plāns ar mēbelēm + 4 fasādes), HTML LV un EN.

Lietošana:  python build_model.py MAJAS/30m2/MM-30-01/model.json
Rezultāts:  <modeļa mape>/rasejumi/<id>_LV.html un <id>_EN.html

Noformējums nāk no SBE šablona (sablons/sbe = kopija no SBE-ARHITEKTS/sablons/arhitekts).
Šablona failus nemaina: rev. bloks, sienu biezumi un lapas izkārtojums tiek ielikti, būvējot.
"""
import base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SBE = os.path.join(HERE, 'sablons', 'sbe')
REV = 100  # iekšējs datu konteiners, lapā netiek rādīts


def js(o):
    return json.dumps(o, ensure_ascii=False)


def rev_block(m, rev=REV):
    keys = ['level', 'W', 'D', 'rooms', 'doors', 'windows', 'axes', 'stampAt', 'stampScale', 'levelAt', 'innerDims',
            'wallTags', 'sections', 'gableWins', 'ceiling', 'ceilingNote', 'planNotes', 'winOk']
    rv = {'id': 'A', 'rev': rev, 'short': m['nosaukums'], 'marks': True, 'openRooms': [], 'fixtures': [], 'openings': [],
          'poly': m.get('poly') or [[0, 0], [m['W'], 0], [m['W'], m['D']], [0, m['D']]], 'recess': m.get('recess', {})}
    rv.update({k: m[k] for k in keys if k in m})
    calls = []
    for f in m.get('furniture', []):
        name, args = f[0], f[1:]
        calls.append(f"    {name}({', '.join(js(a) for a in args)});")
    return ('  // ---------- MM modelis: %s ----------\n  {\n    const rv = %s;\n%s\n    rv.furn = F.splice(0);\n    V.push(rv);\n  }\n'
            % (m['id'], js(rv), '\n'.join(calls)))


def build(model_path, langs=None):
    m = json.load(open(model_path, encoding='utf-8'))
    cfg = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
    j = m.get('jumts', {})
    cfg['roof'].update({k: j[k] for k in ('pitch', 'ov', 'eave') if k in j})
    cfg['tb']['object'] = [m['nosaukums']]
    import datetime
    pr = {**cfg.get('projekts', {}), **m.get('projekts', {})}
    if not pr.get('datums'):
        pr['datums'] = datetime.date.today().strftime('%d.%m.%Y')
    pr['modelis'] = 'MM ' + m.get('platiba_grupa', '').replace('m2', '')   # rakstlaukumā tikai MM un m²
    pr.update(nosaukums=m['nosaukums'], ievade=m.get('ievade', {}), pitch=cfg['roof']['pitch'])
    # projekta piezīmes no izvēlēm: pamati (+ cokols), griestu augstums, papildu teksts
    pam = cfg['pamati'][pr.get('pamati', 'stabveida')]
    g = int(pr.get('griesti', 2200) or 0)
    extra = pr.get('piezimes') or []
    ck = pr.get('cokols') or 'RAL 9005'   # stabveida pamatu metāla cokola tonis
    pr['cokols'], pr['cokols_hex'] = ck, {'RAL 9005': '#1d1d1d', 'RAL 7016': '#383E42'}.get(ck, '#1d1d1d')
    pam = {k: [l.replace('RAL 9005', ck) for l in v] for k, v in pam.items()}
    lf = bool(m.get('loft'))   # bez mansarda: vienkārši griestu augstums
    pr['piezimes'] = pam['lv'] + ([f'Griestu augstums zem mansarda {g} mm.' if lf else f'Griestu augstums {g} mm.'] if g else []) + extra
    pr['piezimes_en'] = pam['en'] + ([f'Ceiling height under the loft {g} mm.' if lf else f'Ceiling height {g} mm.'] if g else []) + (pr.get('piezimes_en') or extra)
    # grīdas pīrāgs fasādēs: stabveida pamatiem apdare līdz grīdas apakšai (−G1), metāla cokols līdz 40 mm virs zemes
    if pr.get('pamati', 'stabveida') == 'stabveida':
        cfg['floor'] = {'foundation': 'stabi', 'above': cfg['floor'].get('posts_ground', 600)}
    tone = cfg['toni'][pr.get('tonis', 'peleks')]
    pr['tonis_lv'], pr['tonis_en'], pr['tonis_sw'] = tone['lv'], tone['en'], tone['sw']
    pr['sturi'] = tone.get('sturi', 0)   # sarkanajam tonim: balti 90 mm stūru dēļi (norvēģu standarts)
    cfg['projekts'] = pr
    T = sum(l[1] for l in cfg['layers']['S1']['layers'])
    t = sum(l[1] for l in cfg['layers']['S2']['layers'])

    cad = open(os.path.join(SBE, 'plani', 'cad.js'), encoding='utf-8').read()
    ar = open(os.path.join(SBE, 'plani', 'ar.js'), encoding='utf-8').read()
    sheet = open(os.path.join(HERE, 'sablons', 'mm-sheet.js'), encoding='utf-8').read()
    anchor = '  // ---------- Rev. 8:'
    assert anchor in cad, 'SBE cad.js: nav atrasts Rev. 8 bloks'
    blocks = rev_block(m)
    if m.get('loft'):   # mansards: tās pašas ārsienas, savas telpas, logi un mēbeles
        blocks += rev_block({**m, **m['loft'], 'id': m['id'] + ' mansards'}, REV + 1)
    cad = cad.replace(anchor, blocks + anchor, 1)
    # MM labojumi SBE plānam: īsākas asis (axOff), plāns bez izmēriem (noDims), telpa bez zīmes (void)
    for a, b in [('el("line", { x1: x, y1: -3150, x2: x, y2: v.D + 3150, ...dash }, ag);\n      bub(x, -3450, n); bub(x, v.D + 3450, n);',
                  'const AO = opt.axOff || 3150; el("line", { x1: x, y1: -AO, x2: x, y2: v.D + AO, ...dash }, ag);\n      bub(x, -AO - 300, n); bub(x, v.D + AO + 300, n);'),
                 ('el("line", { x1: -3150, y1: y, x2: v.W + (longPlan ? 1600 : 3150), y2: y, ...dash }, ag);\n      bub(-3450, y, n); bub(v.W + (longPlan ? 1900 : 3450), y, n);',
                  'const AO = opt.axOff || 3150; el("line", { x1: -AO, y1: y, x2: v.W + (longPlan ? 1600 : AO), y2: y, ...dash }, ag);\n      bub(-AO - 300, y, n); bub(v.W + (longPlan ? 1900 : AO + 300), y, n);'),
                 ('lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(0)', 'lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(v.level || 0)'),
                 ('  const dg = el("g", {}, g);', '  const dg = el("g", opt.noDims ? { display: "none" } : {}, g);'),
                 ('    stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,', '    if (!rm.void) stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,'),
                 # stabveida pamati: metāla cokols RAL 9005 no grīdas apakšas līdz 40 mm virs zemes, ēnas sprauga zem tā
                 ('  } else el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "#9b9c98", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  } else if ((window.AR && AR.projekts && AR.projekts.pamati) === "platne") el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "#9b9c98", stroke: C.ink, "stroke-width": 14 }, g);\n  else { el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "rgba(0,0,0,.25)" }, g); el("rect", { x: -20, y: 0, width: span + 40, height: ROOF.plinth - 40, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g); el("line", { x1: -20, y1: 22, x2: span + 20, y2: 22, stroke: "rgba(255,255,255,.18)", "stroke-width": 8 }, g); }'),
                 # stūru dēļi (sarkanais tonis): balti, 90 mm, no grīdas apakšas līdz dzegai
                 ('  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);\n  { const CB = (window.AR && AR.projekts && AR.projekts.sturi) || 0, top = gable ? ROOF.eave : eEdge; if (CB) [0, span - CB].forEach(u => { el("rect", { x: u, y: -top, width: CB, height: top + fT, fill: "#F2F0EA", stroke: C.ink, "stroke-width": 6 }, g); el("line", { x1: u + (u ? 12 : CB - 12), y1: -top + 10, x2: u + (u ? 12 : CB - 12), y2: fT - 10, stroke: "rgba(0,0,0,.18)", "stroke-width": 6 }, g); }); }'),
                 # stabveida pamatu cokols RAL 9005
                 ('    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: "#3a3f43", stroke: C.ink, "stroke-width": 10 }, g);',
                  '    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g);'),
                 # logu (palodzes, augšas) augstuma atzīmes visās fasādēs; gala fasādēm arī ±0,000
                 ('    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }',
                  '    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }\n  { const top = gable ? ROOF.eave : eEdge, zs = [];\n    (v.windows || []).filter(w => w.side === side).forEach(w => { if (w.sill > 0) zs.push(w.sill); zs.push(w.head); });\n    (v.doors || []).filter(d => d.entry && side === "south").forEach(() => zs.push(2100));\n    if (!opt.levels) lvl(0, lv(0));\n    let last = 0; [...new Set(zs)].sort((a, b) => a - b).forEach(z => { if (z - last >= 300 && top - z >= 300) { lvl(z, lv(z)); last = z; } }); }'),
                 # zemes līnija: īsāka garām mājām (opt.ground), lai garā fasāde neuzbrauc gala fasādes atzīmēm
                 ('for (let x = -1400; x < span + 1400 - 260; x += 200)', 'const GX = opt.ground || 1600; for (let x = -(GX - 200); x < span + GX - 200 - 260; x += 200)'),
                 ('el("line", { x1: -1600, y1: ROOF.plinth, x2: span + 1600, y2: ROOF.plinth,', 'el("line", { x1: -(opt.ground || 1600), y1: ROOF.plinth, x2: span + (opt.ground || 1600), y2: ROOF.plinth,'),
                 # klienta lapā grīdas apakšas atzīmi nerāda (uzbrauc ±0,000)
                 ('    if (fT) lvl(-fT, lv(-fT), 1);\n', ''),
                 # bez jumta pārkares nav ēnas zem dzegas
                 ('  if (!gable) el("rect", { x: 0, y: -eEdge, width: span, height: 420, fill: "url(#eaveShadow)" }, g);\n  else el(',
                  '  if (ROOF.ov > 0 && !gable) el("rect", { x: 0, y: -eEdge, width: span, height: 420, fill: "url(#eaveShadow)" }, g);\n  else if (ROOF.ov > 0) el('),
                 # notekcaurule garajā fasādē: taisns gals 300 mm virs zemes (izplūde pret skatītāju), bez līkuma
                 ('      el("rect", { x: u - 40, y: -(eEdge + thV - 240), width: 80, height: eEdge + thV - 240 + 150, fill: GUT, stroke: C.ink, "stroke-width": 9 }, g);\n      el("path", { d: `M ${u - 50} ${150} q 0 110 110 110 h 60 v -100 h -70 z`, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);',
                  '      el("rect", { x: u - 50, y: -(eEdge + thV - 240), width: 100, height: eEdge + thV - 240 + ROOF.plinth - 50, fill: GUT, stroke: C.ink, "stroke-width": 9 }, g);\n      el("line", { x1: u - 22, y1: -(eEdge + thV - 260), x2: u - 22, y2: ROOF.plinth - 70, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);'),
                 # notekcaurule gala fasādē: Ø100 caurule ar kontūru, taisns gals 300 mm virs zemes
                 ('      const d = `M ${uc} ${-(zt - 40)} L ${uc} ${-(zt - 260)} L ${uw} ${-(zt - 700)} L ${uw} ${150}`;\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 98, "stroke-linejoin": "round" }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 80, "stroke-linejoin": "round" }, g);',
                  '      const zEnd = 50 - ROOF.plinth, d = `M ${uc} ${-(zt - 40)} L ${uc} ${-zEnd}`;\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);')]:
        assert a in cad, 'SBE cad.js: nav atrasts ' + a[:40]
        cad = cad.replace(a, b, 1)
    old = 'const sheetsOut = ARC ? arSheets(pv)'
    assert old in cad, 'SBE cad.js: nav atrasta drukas rinda'
    cad = cad.replace(old, 'const sheetsOut = window.MODEL_SHEET ? [modelSheet(pv)] : ARC ? arSheets(pv)', 1)
    sc = 'T_(g, -ROOF.ov + ttl.length * 262 + 350, 2450, "M 1:100"'
    assert sc in cad, 'SBE cad.js: nav atrasts fasādes mērogs'
    cad = cad.replace(sc, 'if (!opt.noScale) ' + sc, 1)
    cad = cad.replace('/*AR*/', ar + '\n' + sheet, 1)
    # fasādes tonis: SBE apdares tekstūru aizstāj ar izvēlēto (sablons/tex)
    import re
    tex = base64.b64encode(open(os.path.join(HERE, 'sablons', tone['tex']), 'rb').read()).decode()
    cad, n = re.subn(r'const CLAD_TEX = "data:image/jpeg;base64,[^"]*";', lambda _: f'const CLAD_TEX = "data:image/jpeg;base64,{tex}";', cad, count=1)
    assert n == 1, 'SBE cad.js: nav atrasta CLAD_TEX tekstūra'

    h = open(os.path.join(SBE, 'plani', 'planojuma-varianti.html'), encoding='utf-8').read()
    mk = '<!-- cad-mode -->'
    h = h[:h.index(mk)].rstrip() + '\n' + mk + '\n<script>\n' + cad + '</script>\n'
    tt = 'const T = 310, t = 170;'
    assert tt in h, 'SBE html: nav atrasti sienu biezumi'
    h = h.replace(tt, f'const T = {T:g}, t = {t:g};', 1)
    h = h.replace('<link rel="stylesheet" href="https://fonts.googleapis.com', '<link rel="x-disabled" href="https://fonts.googleapis.com', 1).replace('"Sora", "IBM Plex Sans"', '"Barlow"')

    d = os.path.join(SBE, 'fonts', 'dl')
    font = '<style>' + ''.join(
        f"@font-face{{font-family:'Barlow';font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(open(os.path.join(d, fn), 'rb').read()).decode()}) format('woff2');unicode-range:{ur};}}"
        for fn, w, ur in json.load(open(os.path.join(d, 'barlow.json')))) + '</style><script>window.HUMANIZED=true;</script>'
    logo = ''
    for lp in (os.path.join(HERE, 'LOGO.png'), os.path.join(HERE, 'sablons', 'LOGO.png'), os.path.join(os.path.dirname(HERE), 'LOGO.png')):
        if os.path.exists(lp):
            logo = 'data:image/png;base64,' + base64.b64encode(open(lp, 'rb').read()).decode()
            break
    css = '<style>@page{size:297mm 420mm;margin:0} svg.a3{width:297mm!important;height:420mm!important}</style>'
    out_dir = os.path.join(os.path.dirname(os.path.abspath(model_path)), 'rasejumi')
    os.makedirs(out_dir, exist_ok=True)
    outs = []
    for lang in (langs or ['LV', 'EN']):
        pre = f"window.PRINT_MODE=true;window.PRINT_REV={REV};window.MODEL_SHEET=true;window.MM_LANG='{lang.lower()}';window.MM_LOGO={js(logo)};window.AR={js(cfg)};"
        page = (f'<!doctype html><html lang="{lang.lower()}"><head><meta charset="utf-8"><title>{m["nosaukums"]}</title>{font}</head>'
                f'<body><script>{pre}</script>{h}{css}</body></html>')
        p = os.path.join(out_dir, f"{m['id']}_{lang}.html")
        open(p, 'w', encoding='utf-8').write(page)
        outs.append(p)
    return outs


if __name__ == '__main__':
    for p in build(sys.argv[1]):
        print(p)
