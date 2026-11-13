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


# RAL toņi, ko piedāvā redaktors (logu rāmji, aplodas)
RAL = {'RAL 7016': '#383E42', 'RAL 7024': '#474A50', 'RAL 7021': '#2F3234', 'RAL 7035': '#C5C7C4', 'RAL 9005': '#0E0E10',
       'RAL 9010': '#F1ECE1', 'RAL 9016': '#F1F0EA', 'RAL 8017': '#45322E', 'RAL 8019': '#3D3635'}


def rev_block(m, rev=REV):
    keys = ['level', 'W', 'D', 'rooms', 'doors', 'windows', 'axes', 'stampAt', 'stampScale', 'levelAt', 'innerDims', 'userDims',
            'wallTags', 'sections', 'gableWins', 'ceiling', 'ceilingNote', 'planNotes', 'winOk', 'noLeaf', 'decor', 'entryInChain', 'porch', 'terraces', 'axOff', 'posts']
    rv = {'id': 'A', 'rev': rev, 'short': m['nosaukums'], 'marks': True, 'openRooms': [], 'fixtures': [], 'openings': [],
          'poly': m.get('poly') or [[0, 0], [m['W'], 0], [m['W'], m['D']], [0, m['D']]], 'recess': m.get('recess', {})}
    rv.update({k: m[k] for k in keys if k in m})
    rv['wcs'] = [f[1:] for f in m.get('furniture', []) if f[0] == 'toilet']   # tualetes pamatu plāna Ø110 izvadam (mm-pamati.js)
    calls = []
    def call(f):
        if f[0] == '_rot':   # pagriezta mēbele: ["_rot", grādi, cx, cy, [mēbele]] (redaktors)
            return ('{ const i0 = F.length; ' + call(f[4]) + f' for (let i = i0; i < F.length; i++) F[i].tr = "rotate({f[1]:g} {f[2]:g} {f[3]:g})" + (F[i].tr ? " " + F[i].tr : ""); }}')
        return f"{f[0]}({', '.join(js(a) for a in f[1:])});"
    for f in m.get('furniture', []):
        calls.append('    ' + call(f))
    return ('  // ---------- MM modelis: %s ----------\n  {\n    const rv = %s;\n%s\n    rv.furn = F.splice(0);\n    V.push(rv);\n  }\n'
            % (m['id'], js(rv), '\n'.join(calls)))


def _ov_per_edge(cad):
    """[MM] jumta pārkare pa malām: projekts.ov_side = {north, south, east, west} (mm, 0 = fasāde līdz jumtam). Nav norādīts = jumts.ov visām malām (izvade nemainās).
    Fasādes skatā kreisā/labā mala un mala pie sienas tiek ņemtas no šīs malas pārkares, nevis no globālā ROOF.ov."""
    import re
    i = cad.index('function elevation(parent, v, side')
    j = cad.index('\nfunction ', i + 10)
    body = cad[i:j]
    k = body.index('const eEdge = ROOF.eave - ROOF.ov * tan')
    head, rest = body[:k], body[k:]
    ins = ('const _OV = (window.AR && AR.projekts && AR.projekts.ov_side) || {}, _od = q => (_OV[q] != null && !isNaN(+_OV[q])) ? +_OV[q] : ROOF.ov;\n'
           '  const _LR = { south: ["west", "east"], north: ["east", "west"], east: ["south", "north"], west: ["north", "south"] }[side] || ["west", "east"];\n'
           '  const OVL = _od(_LR[0]), OVR = _od(_LR[1]), OVV = endV ? ROOF.ov : _od(side);\n  ')
    rest = rest.replace('const eEdge = ROOF.eave - ROOF.ov * tan', 'const eEdge = ROOF.eave - OVV * tan', 1)
    rest = rest.replace('(v.D / 2 + ROOF.ov) * tan', '(v.D / 2 + OVV) * tan', 1)
    for a, b in [('span + 2 * ROOF.ov', 'span + OVL + OVR'), ('span / 2 + ROOF.ov', 'span / 2 + OVR'), ('span + ROOF.ov', 'span + OVR'),
                 ('(uV + ROOF.ov)', '(uV + OVL)'), ('ROOF.ov + LCX', 'OVL + LCX'), ('ROOF.ov + 1300', 'OVR + 1300'), ('-ROOF.ov', '-OVL')]:
        rest = rest.replace(a, b)
    # gala fasāde: spāru gali kreisajā un labajā pusē var būt dažādā augstumā
    rest = rest.replace('const eT = eEdge + thV, cov', 'const eT = eEdge + thV, eTL = ROOF.eave - OVL * tan + thV, eTR = ROOF.eave - OVR * tan + thV, cov', 1)
    rest = rest.replace('const zA = sd < 0 ? eT : ridgeTop, zB = sd < 0 ? ridgeTop : eT;', 'const zA = sd < 0 ? eTL : ridgeTop, zB = sd < 0 ? ridgeTop : eTR;', 1)
    rest = rest.replace('P(-OVL, eT - vt), P(-OVL, eT), P(span / 2, ridgeTop), P(span + OVR, eT), P(span + OVR, eT - vt)', 'P(-OVL, eTL - vt), P(-OVL, eTL), P(span / 2, ridgeTop), P(span + OVR, eTR), P(span + OVR, eTR - vt)', 1)
    rest = rest.replace('P(-OVL - 20, eT + 5), P(span / 2, ridgeTop + 5), P(span + OVR + 20, eT + 5), P(span + OVR + 20, eT - cov), P(span / 2, ridgeTop - cov), P(-OVL - 20, eT - cov)',
                        'P(-OVL - 20, eTL + 5), P(span / 2, ridgeTop + 5), P(span + OVR + 20, eTR + 5), P(span + OVR + 20, eTR - cov), P(span / 2, ridgeTop - cov), P(-OVL - 20, eTL - cov)', 1)
    rest = rest.replace('if (ROOF.ov > 0 && !FAS) {', 'if ((OVL > 0 || OVR > 0 || _OV[side] > 0) && !FAS) {', 1)
    rest = rest.replace('if (ROOF.ov > 0 && !gable)', 'if (OVV > 0 && !gable)', 1)
    cad = cad[:i] + head + ins + rest + cad[j:]
    return cad


def _mm_extra(cad):
    """[MM] papildinājumi pēc _ov_per_edge: stabu augstums (q.h, nogriežas pie jumta pārkares), fasādes tonis pa pusēm, pārkares tonis."""
    TINT = ('function mmTint(g, hex) {   // [MM] apdares tekstūras pārkrāsošana ar SVG filtru (saglabā dēļu zīmējumu): out = krāsa × (0,55 + 0,45 × gaišums / vidējais)\n'
            '  const id = "tn" + Math.random().toString(36).slice(2, 8), L = Math.max(.05, +((window.AR && AR.projekts && AR.projekts.fasade_lum) || .25)), k = .45 / L;\n'
            '  const c = [1, 3, 5].map(i => parseInt(String(hex).slice(i, i + 2), 16) / 255 || 0);\n'
            '  const f = el("filter", { id, "color-interpolation-filters": "sRGB", x: 0, y: 0, width: 1, height: 1 }, g);\n'
            '  el("feColorMatrix", { type: "matrix", values: c.map(v => [v * k * .299, v * k * .587, v * k * .114, 0, v * .55].map(n => n.toFixed(4)).join(" ")).join(" ") + " 0 0 0 1 0" }, f);\n'
            '  return id;\n}\n'
            'function mmSideHex(side) { const q = ((window.AR && AR.projekts && AR.projekts.fasade_side) || {})[side]; return q ? (q.hex || q) : null; }\n')
    a = 'function cadPlan(parent, v, opt = {}) {'
    assert a in cad, 'SBE cad.js: nav atrasts cadPlan'
    cad = cad.replace(a, TINT + a, 1)
    for a, b in [
        # stabs fasādē: augstums q.h (mm virs ±0,000); virs jumta pārkares apakšas tiek nogriezts pa pārkari (gala fasādē pa slīpumu)
        ('    el("rect", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#c68a58", stroke: C.ink, "stroke-width": 14 }, g);',
         '    const pzc = uu => (gable ? eEdge + (Math.min(uu, span - uu) + (uu < span / 2 ? OVL : OVR)) * tan - 260 : eEdge - 150), ph = pq && +pq.h > 0 ? +pq.h : 0, pzL = ph ? Math.min(ph, pzc(u)) : pzc(u), pzR = ph ? Math.min(ph, pzc(u + s)) : pzc(u + s), pzm = Math.min(pzL, pzR);\n'
         '    if (window.__FDF && window.__FDF[side]) window.__FDF[side].pz = [gable ? 1 : 0, OVL, OVR, tan];\n'
         '    el("polygon", { points: [P(u, -fT), P(u + s, -fT), P(u + s, pzR), P(u, pzL)].join(" "), fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#c68a58", stroke: C.ink, "stroke-width": 14 }, g);'),
        ('el("line", { x1: u + k * 50, y1: -eEdge + 15, x2: u + k * 50, y2: fT - 15, stroke: "#5a3a1e", "stroke-width": 6 }, g);',
         'void 0;'),   # [MM] stabam fasādē nav vektora līniju: tikai tekstūra vai krāsa
        # fasādes tonis tikai vienai pusei (krāsas spainis): projekts.fasade_side[side]
        ('  boards(el("g", { "clip-path": `url(#${wid})` }, g), 0, span,',
         '  boards(el("g", Object.assign({ "clip-path": `url(#${wid})` }, mmSideHex(side) ? { filter: `url(#${mmTint(g, mmSideHex(side))})` } : {}), g), 0, span,'),
        # jumta pārkares tonis (projekts.parkare_hex): gala fasādes pārkare, vēja kaste, garās fasādes spāres gals
        ('      const BC = FAS ? "#F2F0EA" : (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54";\n',
         '      const PKH = (window.AR && AR.projekts && AR.projekts.parkare_hex) || null, BC = PKH || (FAS ? "#F2F0EA" : (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54");\n'),
        ('        if (!FAS) {   // fasādes dēļu tekstūra, pagriezta pa jumta slīpumu (dēļi gar spāri)\n',
         '        if (!FAS || PKH) {   // fasādes dēļu tekstūra, pagriezta pa jumta slīpumu (dēļi gar spāri)\n'),
        ('          const tg = el("g", { transform: `rotate(${th} ${cx} ${cy})` }, el("g", { "clip-path": `url(#${cid})` }, g));\n',
         '          const tg = el("g", { transform: `rotate(${th} ${cx} ${cy})` }, el("g", Object.assign({ "clip-path": `url(#${cid})` }, PKH ? { filter: `url(#${mmTint(g, PKH)})` } : {}), g));\n'),
        ('fill: FAS ? "#F2F0EA" : (AR.projekts.tonis_sw || "#555"), stroke: C.ink, "stroke-width": 12 }, g);',
         'fill: AR.projekts.parkare_hex || (FAS ? "#F2F0EA" : (AR.projekts.tonis_sw || "#555")), stroke: C.ink, "stroke-width": 12 }, g);'),
        ('      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: FAS ? "#F2F0EA" : ((window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54") }, g);\n'
         '      if (!FAS) { el("rect", { x: a, y: top, width: b - a, height: tPV }, el("clipPath", { id: cid }, g));\n'
         '        const tg = el("g", { transform: "rotate(-90)" }, el("g", { "clip-path": `url(#${cid})` }, g));',
         '      const PKH = (window.AR && AR.projekts && AR.projekts.parkare_hex) || null;\n'
         '      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: PKH || (FAS ? "#F2F0EA" : ((window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54")) }, g);\n'
         '      if (!FAS || PKH) { el("rect", { x: a, y: top, width: b - a, height: tPV }, el("clipPath", { id: cid }, g));\n'
         '        const tg = el("g", { transform: "rotate(-90)" }, el("g", Object.assign({ "clip-path": `url(#${cid})` }, PKH ? { filter: `url(#${mmTint(g, PKH)})` } : {}), g));'),
    ]:
        assert a in cad, 'SBE cad.js (mm_extra): nav atrasts ' + a[:60]
        cad = cad.replace(a, b, 1)
    return cad


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
    cp = pr.get('cokols_plate')   # pamatu plātnes cokola tonis (tonēts betons); None = dabīgs betons
    pr['cokols_plate'] = cp if cp in ('RAL 9005', 'RAL 7016') else None
    pr['cokols_plate_hex'] = {'RAL 9005': '#2b2b2d', 'RAL 7016': '#575c60'}.get(pr['cokols_plate'], '#9b9c98')
    pam = {k: [l.replace('RAL 9005', ck) for l in v] for k, v in pam.items()}
    if pr['cokols_plate']:   # pamatu plātne ar tonētu betona cokolu
        pam = {k: [l.replace('Cokols: betons.', 'Cokols: tonēts betons ' + pr['cokols_plate'] + '.').replace('Plinth: concrete.', 'Plinth: tinted concrete ' + pr['cokols_plate'] + '.') for l in v] for k, v in pam.items()}
    lf = bool(m.get('loft'))   # bez mansarda: vienkārši griestu augstums
    pr['piezimes'] = pam['lv'] + ([f'Griestu augstums zem mansarda {g} mm.' if lf else f'Griestu augstums {g} mm.'] if g else []) + extra
    pr['piezimes_en'] = pam['en'] + ([f'Ceiling height under the loft {g} mm.' if lf else f'Ceiling height {g} mm.'] if g else []) + (pr.get('piezimes_en') or extra)
    # grīdas pīrāgs fasādēs: stabveida pamatiem apdare līdz grīdas apakšai (−G1), metāla cokols līdz 40 mm virs zemes
    if pr.get('pamati', 'stabveida') == 'stabveida':
        cfg['floor'] = {'foundation': 'stabi', 'above': pr.get('pamatu_augstums') or cfg['floor'].get('posts_ground', 600)}
    tone = cfg['toni'][pr.get('tonis', 'peleks')]
    pr['tonis_lv'], pr['tonis_en'], pr['tonis_sw'] = tone['lv'], tone['en'], tone['sw']
    if pr.get('fasade_hex'):   # fasādes krāsa pēc izvēles (RAL vai brīva krāsa)
        pr['tonis_sw'] = pr['fasade_hex']
        if pr.get('fasade_ral'):
            pr['tonis_lv'] = pr['tonis_en'] = pr['fasade_ral']
    # [MM] fasādes tonis pa pusēm (projekts.fasade_side) un pārkares tonis (projekts.parkare_hex): apdares tekstūru pārkrāso SVG filtrs,
    # tam vajag tekstūras vidējo gaišumu (toņa "lum" konfigurācijā vai izvēlētās krāsas gaišums)
    _hx = pr.get('fasade_hex') if pr.get('fasade_tex') else None
    pr['fasade_lum'] = (sum(k * int(_hx[i:i + 2], 16) for k, i in ((.299, 1), (.587, 3), (.114, 5))) / 255) if _hx else tone.get('lum', 0.25)
    pr['sturi'] = tone.get('sturi', 0)   # sarkanajam tonim: balti 90 mm stūru dēļi (norvēģu standarts)
    so = pr.get('sturi_opc')   # dekoratīvie stūra dēļi: nav / balts / melns / tonis (bez vējmalas); citādi pēc toņa
    if so:
        pr['sturi'] = 0 if so == 'nav' else 90
        pr['sturi_hex'] = {'balts': '#F2F0EA', 'melns': '#1d1d1d', 'tonis': tone['sw']}.get(so, '#F2F0EA')
    pr['fascia'] = tone.get('vejmala') == 'balta'   # horizontāla balta fascija tikai sarkanajam
    lg = pr.get('logu_tonis') or tone.get('logi', 'RAL 7016')   # logu rāmju tonis: no fasādes toņa vai izvēlēts (projekts.logu_tonis)
    pr['logi'], pr['logi_hex'] = lg, RAL.get(lg, '#383E42')
    if pr.get('logu_hex'):   # brīva rāmju krāsa (krāsas spainis)
        pr['logi_hex'] = pr['logu_hex']
    tc = lambda c: tone['sw'] if c == 'tonis' else c   # 'tonis' = fasādes tonī
    cfg.setdefault('win', {}).update(colorOut=pr['logi'], casingColor=tc(pr.get('aplodas')) or pr['logi'], sillColor=tc(pr.get('palodzes')))   # aplodu tonis var atšķirties (projekts.aplodas)   # logu rāmji un apmales pēc toņa (sarkanajam balti RAL 9016)
    pr['vejkaste'] = m.get('jumts', {}).get('vejkaste', True) is not False   # jumta pārkare ar vēja kasti (slēgta)
    cfg['projekts'] = pr
    for k_, v_ in (pr.get('piragi_layers') or {}).items():   # redaktorā labotie pīrāgu slāņi (projekts.piragi_layers)
        if k_ in cfg['layers']:
            cfg['layers'][k_]['layers'] = v_
        elif k_ == 'P1':   # mansarda grīda
            cfg['layers']['P1'] = {'name': (pr.get('piragi_names') or {}).get('P1') or 'S-02 Mansarda grīda', 'layers': v_}
    for k_, v_ in (pr.get('piragi_names') or {}).items():   # pārdēvētas konstrukcijas (projekts.piragi_names)
        if k_ in cfg['layers'] and v_:
            cfg['layers'][k_]['name'] = v_
    for w_ in pr.get('wall_types') or []:   # redaktorā pievienotie starpsienu veidi (projekts.wall_types) nonāk AR sienu specifikācijā
        if w_.get('id') and w_.get('layers'):
            cfg['layers'][w_['id']] = {'name': w_.get('name') or w_['id'], 'layers': w_['layers']}
    _th = lambda L_: sum(l[1] for l in L_ if not (len(l) > 2 and l[2] == 'n'))   # slāņi "latojumā" (n) neskaitās biezumā, kā redaktorā
    T = _th(cfg['layers']['S1']['layers'])
    t = _th(cfg['layers']['S2']['layers'])

    cad = open(os.path.join(SBE, 'plani', 'cad.js'), encoding='utf-8').read()
    ar = open(os.path.join(SBE, 'plani', 'ar.js'), encoding='utf-8').read()
    sheet = open(os.path.join(HERE, 'sablons', 'mm-sheet.js'), encoding='utf-8').read()
    sheet += '\n' + open(os.path.join(HERE, 'sablons', 'mm-pamati.js'), encoding='utf-8').read()   # [MM] pamatu un komunikāciju plāns
    anchor = '  // ---------- Rev. 8:'
    assert anchor in cad, 'SBE cad.js: nav atrasts Rev. 8 bloks'
    blocks = open(os.path.join(HERE, 'sablons', 'mm-mebeles.js'), encoding='utf-8').read() + rev_block(m)
    if m.get('loft'):   # mansards: tās pašas ārsienas, savas telpas, logi un mēbeles
        blocks += rev_block({**m, **m['loft'], 'id': m['id'] + ' mansards'}, REV + 1)
    cad = cad.replace(anchor, blocks + anchor, 1)
    AXH = 'function axOffs(v, opt) {   // [MM] asu galu attālums katrā pusē: pēc noklusējuma ārpus mērķēdēm un ārtelpām (lieveņa, terases), v.axOff to pārraksta\n  const base = opt.axOff || 3150, pts = [].concat((v.porch ? [v.porch.poly] : []), (v.terraces || []).map(t => t.poly)).flat();\n  const ex = { n: Math.max(0, ...pts.map(q => -q[1])), s: Math.max(0, ...pts.map(q => q[1] - v.D)), w: Math.max(0, ...pts.map(q => -q[0])), e: Math.max(0, ...pts.map(q => q[0] - v.W)) };\n  const r = {}; ["n", "s", "w", "e"].forEach(k => { r[k] = (v.axOff && v.axOff[k] != null) ? v.axOff[k] : base + (ex[k] > 0 ? ex[k] + 400 : 0); });\n  return r;\n}\nfunction terFix(t) {   // [MM] lietotāja terase: kopija ar stūru statņiem (t.corners), ja nav norādīti\n  const xs = t.poly.map(q => q[0]), ys = t.poly.map(q => q[1]), cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2, sz = 300;\n  const posts = t.posts || (t.corners ? t.poly.map(q => [q[0] > cx ? q[0] - sz : q[0], q[1] > cy ? q[1] - sz : q[1], sz]) : []);\n  return Object.assign({}, t, { __ter: 1, posts });\n}\nfunction terPat(g, pc, x0, y0) {   // [MM] terases tekstūra (augšupielādēta), pagriežama: tekstūras platums texW mm\n  const id = "tp" + Math.random().toString(36).slice(2, 7), w = pc.texW || 1000, h = pc.texH || w;\n  const pat = el("pattern", { id, patternUnits: "userSpaceOnUse", width: w, height: h, patternTransform: `rotate(${pc.texRot || 0}) translate(${x0 || 0} ${y0 || 0})` }, g);\n  el("image", { href: pc.tex, width: w, height: h, preserveAspectRatio: "none" }, pat);\n  return id;\n}\nfunction postVisible(v, side, q) {   // [MM] brīvais stabs fasādē redzams tikai, ja māja to neaizsedz (stabi otrā mājas pusē nerādās)\n  const X = side === "west" || side === "east", pos = side === "south" || side === "east", c = X ? q.y + q.d / 2 : q.x + q.w / 2, front = X ? (pos ? q.x + q.w : q.x) : (pos ? q.y + q.d : q.y), P = v.poly;\n  let ext = null;\n  for (let i = 0; i < P.length; i++) { const A = P[i], B = P[(i + 1) % P.length], u0 = X ? A[1] : A[0], u1 = X ? B[1] : B[0], w0 = X ? A[0] : A[1], w1 = X ? B[0] : B[1];\n    if ((u0 - c) * (u1 - c) > 0 || u0 === u1) continue; const w = w0 + (w1 - w0) * (c - u0) / (u1 - u0); ext = ext == null ? w : (pos ? Math.max(ext, w) : Math.min(ext, w)); }\n  return ext == null || (pos ? front >= ext - 50 : front <= ext + 50);\n}\nfunction terEdge(pc, side, v) {   // [MM] terases redzamā mala fasādē: tikai ja iziet aiz fasādes līnijas\n  const xs = pc.poly.map(q => q[0]), ys = pc.poly.map(q => q[1]), a = Math.min(...xs), b = Math.max(...xs), c = Math.min(...ys), d = Math.max(...ys);\n  const bx = b <= 1 || a >= v.W - 1, by = d <= 1 || c >= v.D - 1;   // terase blakus mājai: no sāniem redzama kā dēļu plātne\n  if ((side === "north" || side === "south") && bx) return [[a, c], [b, c]];\n  if ((side === "west" || side === "east") && by) return [[a, c], [b, c]];\n  // [MM] mala redzama tur, kur māja (ieliekumos, nišās) ir tālāk par terases malu: paraugs gar malu pret mājas kontūru\n  const X = side === "west" || side === "east", pos = side === "south" || side === "east", lo = X ? c : a, hi = X ? d : b, edge = side === "south" ? d : side === "north" ? c : side === "east" ? b : a, P = v.poly;\n  let m0 = null, m1 = null;\n  for (let u = lo; u <= hi + 0.5; u += Math.max(20, (hi - lo) / 400)) {\n    let ext = null;\n    for (let i = 0; i < P.length; i++) { const A = P[i], B = P[(i + 1) % P.length], u0 = X ? A[1] : A[0], u1 = X ? B[1] : B[0], w0 = X ? A[0] : A[1], w1 = X ? B[0] : B[1];\n      if ((u0 - u) * (u1 - u) > 0 || u0 === u1) continue; const w = w0 + (w1 - w0) * (u - u0) / (u1 - u0); ext = ext == null ? w : (pos ? Math.max(ext, w) : Math.min(ext, w)); }\n    if (ext == null || (pos ? edge > ext + 50 : edge < ext - 50)) { if (m0 == null) m0 = u; m1 = u; }\n  }\n  if (m0 == null) return [];\n  return X ? [[edge, m0], [edge, m1]] : [[m0, edge], [m1, edge]];\n}\n'
    cad = cad.replace('function cadPlan(parent, v, opt = {}) {', AXH + 'function cadPlan(parent, v, opt = {}) {', 1)
    # [MM] stabu materiāls fasādēs: krāsa vai tekstūra (q.col / q.tex), citādi lamellu koks
    cad = cad.replace('postsU.forEach(([u, s]) => {', 'postsU.forEach(([u, s, pq]) => {', 1)
    # MM labojumi SBE plānam: īsākas asis (axOff), plāns bez izmēriem (noDims), telpa bez zīmes (void)
    for a, b in [('el("line", { x1: x, y1: -3150, x2: x, y2: v.D + 3150, ...dash }, ag);\n      bub(x, -3450, n); bub(x, v.D + 3450, n);',
                  'const AX = axOffs(v, opt); el("line", { x1: x, y1: -AX.n, x2: x, y2: v.D + AX.s, ...dash }, ag);\n      bub(x, -AX.n - 300, n); bub(x, v.D + AX.s + 300, n);'),
                 ('el("line", { x1: -3150, y1: y, x2: v.W + (longPlan ? 1600 : 3150), y2: y, ...dash }, ag);\n      bub(-3450, y, n); bub(v.W + (longPlan ? 1900 : 3450), y, n);',
                  'const AX = axOffs(v, opt); el("line", { x1: -AX.w, y1: y, x2: v.W + (longPlan ? 1600 : AX.e), y2: y, ...dash }, ag);\n      bub(-AX.w - 300, y, n); bub(v.W + (longPlan ? 1900 : AX.e + 300), y, n);'),
                 ('lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(0)', 'lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(v.level || 0)'),
                 ('  const dg = el("g", {}, g);', '  const dg = el("g", opt.noDims ? { display: "none" } : {}, g);'),
                 ('    stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,', '    if (!rm.void) stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,'),
                 # stabveida pamati: metāla cokols RAL 9005 no grīdas apakšas līdz 40 mm virs zemes, ēnas sprauga zem tā
                 ('  } else el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "#9b9c98", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  } else if ((window.AR && AR.projekts && AR.projekts.pamati) === "platne") el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: (AR.projekts.cokols_plate_hex || "#9b9c98"), stroke: C.ink, "stroke-width": 14 }, g);\n  else { el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "rgba(0,0,0,.25)" }, g); el("rect", { x: -20, y: 0, width: span + 40, height: ROOF.plinth - 40, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g); el("line", { x1: -20, y1: 22, x2: span + 20, y2: 22, stroke: "rgba(255,255,255,.18)", "stroke-width": 8 }, g); }'),
                 # stūru dēļi (sarkanais tonis): balti, 90 mm, no grīdas apakšas līdz dzegai
                 ('  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);\n  { const CB = (window.AR && AR.projekts && AR.projekts.sturi) || 0, zt = u => (gable ? roofTopW + (ridgeTop - roofTopW) * Math.min(u, span - u) / (span / 2) : (FAS ? eEdge : eEdge + thV - 20)); if (CB) [0, span - CB].forEach(u => { el("polygon", { points: [P(u, -fT), P(u + CB, -fT), P(u + CB, zt(u + CB)), P(u, zt(u))].join(" "), fill: (AR.projekts.sturi_hex || "#F2F0EA"), stroke: C.ink, "stroke-width": 6 }, g); const lx = u + (u ? 12 : CB - 12); el("line", { x1: lx, y1: -zt(lx) + 10, x2: lx, y2: fT - 10, stroke: "rgba(0,0,0,.18)", "stroke-width": 6 }, g); }); }   // [MM] gala fasādē stūra dēļi līdz vējmalai (pa jumta slīpumu)'),
                 # stabveida pamatu cokols RAL 9005
                 ('    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: "#3a3f43", stroke: C.ink, "stroke-width": 10 }, g);',
                  '    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g);'),
                 # logu (palodzes, augšas) augstuma atzīmes visās fasādēs; gala fasādēm arī ±0,000
                 ('    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }',
                  '    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }\n  { const top = gable ? ROOF.eave : eEdge, zs = [];\n    (v.windows || []).filter(w => w.side === side).forEach(w => { if (w.sill > 0) zs.push(w.sill); zs.push(w.head); });\n    (v.doors || []).filter(d => d.entry && side === "south").forEach(() => zs.push(2100));\n    if (!opt.levels) lvl(0, lv(0));\n    let last = 0; [...new Set(zs)].sort((a, b) => a - b).forEach(z => { if (z - last >= 300 && top - z >= 300) { lvl(z, lv(z)); last = z; } }); }'),
                 # zemes līnija: īsāka garām mājām (opt.ground), lai garā fasāde neuzbrauc gala fasādes atzīmēm
                 ('for (let x = -1400; x < span + 1400 - 260; x += 200)', 'const GX = opt.ground || 1600; for (let x = -(GX - 200) - (opt.gl || 0); x < span + GX - 200 - 260 + (opt.gr || 0); x += 200)'),
                 ('el("line", { x1: -1600, y1: ROOF.plinth, x2: span + 1600, y2: ROOF.plinth,', 'el("line", { x1: -(opt.ground || 1600) - (opt.gl || 0), y1: ROOF.plinth, x2: span + (opt.ground || 1600) + (opt.gr || 0), y2: ROOF.plinth,'),
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
    cad = cad.replace(old, 'const sheetsOut = window.MODEL_SHEET ? mmSheets(pv) : ARC ? arSheets(pv)', 1)
    sc = 'T_(g, -ROOF.ov + ttl.length * 262 + 350, 2450, "M 1:100"'
    assert sc in cad, 'SBE cad.js: nav atrasts fasādes mērogs'
    cad = cad.replace(sc, 'if (!opt.noScale) ' + sc.replace('"M 1:100"', '"M 1:" + (window.MM_SCALE || 100)'), 1)
    cad = cad.replace('T_(svg, 26 + hd.length * 2.75 + 6, 197, "M 1:100"', 'T_(svg, 26 + hd.length * 2.75 + 6, 197, "M 1:" + (window.MM_SCALE || 100)', 1)
    for a, b in [
        # [MM] loga aplodas arī apakšā (w.casingAll); palodze tad zem aplodas
        ('    if (cas) {\n      R(u0 - cas, u1 + cas, z0, z1 + cas, { fill: cc, ...ln });\n      R(u0 - cas + 18, u1 + cas - 18, z0, z1 + cas - 18, { fill: "none", ...thin });',
         '    const CB = window.MM_CASB && cas ? cas : 0; window.MM_CASB = false;\n    if (cas) {\n      R(u0 - cas, u1 + cas, z0 - CB, z1 + cas, { fill: cc, ...ln });   // [MM] bez liekās iekšējās līnijas'),
        # [MM] palodze visiem logiem vienāda: ar aplodām 10 mm aiz ailas (ieiet aplodā), bez aplodām 100 mm aiz rāmja; arī logiem līdz grīdai
        ('    if (z0 > 0) {\n      // sill: plate wider than the casing', '    if (true) {\n      z0 -= CB;\n      // sill: plate wider than the casing'),
        ('      const s0 = u0 - (cas || 0) - 45, s1 = u1 + (cas || 0) + 45;', '      const SO = cas ? 10 : 100, s0 = u0 - SO, s1 = u1 + SO;'),
        # [MM] durvīm plānā 35 mm kārba ailas iekšpusē abos sānos (balta); vērtne un loks no kārbas
        ('  v.doors.forEach(d => {\n    const { x, y, w, th, o, hinge, side } = d, lt = 40;', '  v.doors.forEach(d => {\n    const { th, o, hinge, side } = d, KB = 35, x = o === "h" ? d.x + KB : d.x, y = o === "h" ? d.y : d.y + KB, w = d.w - 2 * KB, lt = 40, frm = (a, b, c, e) => el("rect", { x: a, y: b, width: c, height: e, fill: "#fff", stroke: C.line, "stroke-width": 6 }, g);'),
        ('      gap(x, y - 14, w, th + 28); jamb(x, y, x, y + th); jamb(x + w, y, x + w, y + th);\n      const py', '      gap(x - KB, y - 14, w + 2 * KB, th + 28); jamb(x - KB, y, x - KB, y + th); jamb(x + w + KB, y, x + w + KB, y + th); frm(x - KB, y, KB, th); frm(x + w, y, KB, th);\n      const py'),
        ('      gap(x - 14, y, th + 28, w); jamb(x, y, x + th, y); jamb(x, y + w, x + th, y + w);\n      const px', '      gap(x - 14, y - KB, th + 28, w + 2 * KB); jamb(x, y - KB, x + th, y - KB); jamb(x, y + w + KB, x + th, y + w + KB); frm(x, y - KB, th, KB); frm(x, y + w, th, KB);\n      const px'),
        # [MM] lietotāja pievienotie mēri plānā: [ass, novietojums, no, līdz]
        ('  (v.innerDims || []).forEach(([axis, at], k) => chainCad(dg, cross(axis, at), axis, at, 0, true, k > 0));', '  (v.innerDims || []).forEach(([axis, at], k) => chainCad(dg, cross(axis, at), axis, at, 0, true, k > 0));\n  (v.userDims || []).forEach(([axis, at, a, b]) => chainCad(dg, [a, b], axis, at, 0, true));'),
        # [MM] mansarda logiem arī aplodu varianti (gw.casing, gw.casingAll)
        ('      win(b0, b1, gw.z0, gw.z1, PANES(gw.kind || "hopper", true, false), (window.AR && window.AR.win && window.AR.win.casing) ?? 0);', '      window.MM_CASB = !!gw.casingAll; win(b0, b1, gw.z0, gw.z1, PANES(gw.kind || "hopper", true, false), gw.casing ?? (window.AR && window.AR.win && window.AR.win.casing) ?? 0);'),
        ('k = 1 / Math.cos(ROOF.pitch * Math.PI / 180), cas = (window.AR && window.AR.win && window.AR.win.casing) ?? 0;', 'k = 1 / Math.cos(ROOF.pitch * Math.PI / 180), cas = gw.casing ?? (window.AR && window.AR.win && window.AR.win.casing) ?? 0, CBg = gw.casingAll && cas ? cas : 0;'),
        ('    if (cas) el("polygon", { points: shape(0, cas), fill: (typeof colHex === "function" ? colHex(WINC().cas, "#24282b") : "#24282b"), stroke: "#111", "stroke-width": 8 }, gg);', '    if (cas) el("polygon", { points: shape(0, cas), fill: (typeof colHex === "function" ? colHex(WINC().cas, "#24282b") : "#24282b"), stroke: "#111", "stroke-width": 8 }, gg);\n    if (CBg) el("rect", { x: a0 - cas, y: -z0, width: a1 - a0 + 2 * cas, height: cas, fill: colHex(WINC().cas, "#24282b"), stroke: "#111", "stroke-width": 8 }, gg);'),
        ('    el("rect", { x: a0 - 40 - cas, y: -z0, width: a1 - a0 + 80 + 2 * cas, height: 45, fill: "#2b2f32" }, gg);', '    { const SO = cas ? 10 : 100, s0 = a0 - SO, s1 = a1 + SO, zs = z0, sc = colHex((window.AR && AR.win && AR.win.sillColor) || WINC().cas, "#24282b");   // [MM] palodze kā parastajiem logiem\n      el("polygon", { points: [P(s0, zs - 40), P(s1, zs - 40), P(s1 - 30, zs - 110), P(s0 + 30, zs - 110)].join(" "), fill: "rgba(0,0,0,.35)" }, gg);\n      el("rect", { x: s0, y: -(zs + 10), width: s1 - s0, height: 50, fill: sc, stroke: "#111", "stroke-width": 7 }, gg);\n      el("line", { x1: s0, y1: -(zs - 22), x2: s1, y2: -(zs - 22), stroke: "#111", "stroke-width": 4 }, gg); }'),
        ('    win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w),', '    window.MM_CASB = !!w.casingAll; win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w),'),
        # [MM] ārdurvīm smalka melna kontūra ap stikla joslu un rokturi
        ('width: 40, height: 1100, fill: "#b9bcbe" }, g);', 'width: 40, height: 1100, fill: "#b9bcbe", stroke: "#111", "stroke-width": 4 }, g);'),
        ('width: 160, height: 1800, fill: "url(#glass)" }, g);', 'width: 160, height: 1800, fill: "url(#glass)", stroke: "#111", "stroke-width": 5 }, g);'),
        # [MM] notekas katrā garajā pusē var noņemt (projekts.notekas = {north: false})
        ('  const GUT = "#2f3438";\n  if (!gable) {', '  const GUT = "#2f3438", NOT = s => !(window.AR && AR.projekts && AR.projekts.notekas && AR.projekts.notekas[s] === false);\n  if (!gable && NOT(side)) {'),
        ('  } else {\n    [-1, 1].forEach(sd => {\n      // half-round gutter', '  } else if (gable) {\n    [-1, 1].forEach(sd => {\n      if (!NOT(side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"))) return;\n      // half-round gutter'),
        # [MM] katru noteku un katru notekcauruli var noņemt atsevišķi (projekts.notekas: north/south = noteka, nw/ne/sw/se = caurule stūrī)
        ('  if (!gable && NOT(side)) {\n    const gz = eEdge + thV - 120;\n    el("rect", { x: -ROOF.ov - 40, y: -gz, width: span + 2 * ROOF.ov + 80, height: 120, rx: 40, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);\n    el("line", { x1: -ROOF.ov - 25, y1: -gz + 18, x2: span + ROOF.ov + 25, y2: -gz + 18, stroke: "rgba(255,255,255,.28)", "stroke-width": 7 }, g);\n    [180, span - 180].forEach(u => {',
         '  const PIPE = u => side[0] + (side === "north" ? (u < span / 2 ? "e" : "w") : (u < span / 2 ? "w" : "e"));\n  if (!gable) {\n    const gz = eEdge + thV - 120;\n    if (NOT(side)) {\n    el("rect", { x: -ROOF.ov - 40, y: -gz, width: span + 2 * ROOF.ov + 80, height: 120, rx: 40, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);\n    el("line", { x1: -ROOF.ov - 25, y1: -gz + 18, x2: span + ROOF.ov + 25, y2: -gz + 18, stroke: "rgba(255,255,255,.28)", "stroke-width": 7 }, g);\n      { const ga = -ROOF.ov - 40, gb = span + ROOF.ov + 40, gl = gb - ga, nb = Math.max(1, Math.round(gl / 600));   // [MM] notekas metāla detaļas: ārējā mala, kronšteini, savienojumu šuves, noslēgi\n        el("line", { x1: ga + 30, y1: -gz + 100, x2: gb - 30, y2: -gz + 100, stroke: "rgba(0,0,0,.35)", "stroke-width": 6 }, g);\n        for (let i = 0; i <= nb; i++) { const bx = ga + 60 + (gl - 120) * i / nb; el("rect", { x: bx - 14, y: -gz - 18, width: 28, height: 150, rx: 8, fill: "#1d2124", stroke: C.ink, "stroke-width": 5 }, g); }\n        for (let x = ga + 3000; x < gb - 600; x += 3000) { el("rect", { x: x - 20, y: -gz - 4, width: 40, height: 128, fill: "#3b4247", stroke: C.ink, "stroke-width": 6 }, g); el("line", { x1: x, y1: -gz + 4, x2: x, y2: -gz + 116, stroke: "rgba(255,255,255,.3)", "stroke-width": 4 }, g); }\n        [ga, gb].forEach((x, i) => el("rect", { x: i ? x - 36 : x, y: -gz - 6, width: 36, height: 132, rx: 18, fill: "#3b4247", stroke: C.ink, "stroke-width": 8 }, g)); }\n    }\n    [180, span - 180].forEach(u => {\n      if (!NOT(PIPE(u))) return;'),
        ('      if (!NOT(side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"))) return;',
         '      const LS = side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"), gOn = NOT(LS), pOn = NOT(LS[0] + side[0]);\n      if (!gOn && !pOn) return;'),
        ('      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);\n      el("path", { d: `M ${ue} ${-zt}',
         '      if (pOn) {\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);\n      }\n      if (gOn) el("path", { d: `M ${ue} ${-zt}'),
        # [MM] rietumu terase (v.terrace): klājs plānā kā lievenis, fasādēs kā lieveņa klājs
        ('  if (v.porch) porchPlan(g, v.porch, v.rooms.length + 1);', '  if (v.porch) porchPlan(g, v.porch, v.rooms.length + 1);\n  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));'),
        ('  if (v.porch) {\n    const pc = v.porch, out =', '  for (const pc of [v.porch, ...(v.terraces || []).map(terFix)].filter(Boolean)) {\n    const out ='),
        ("    el(\"rect\", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: \"#4a4f53\", stroke: C.ink, \"stroke-width\": 14 }, g);\n    el(\"line\", { x1: u + s * .35, y1: -eEdge + 20, x2: u + s * .35, y2: fT - 20, stroke: \"rgba(255,255,255,.15)\", \"stroke-width\": 8 }, g);",
         "    el(\"rect\", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || \"#c68a58\", stroke: C.ink, \"stroke-width\": 14 }, g);\n    for (let k = 1; k < Math.round(s / 50) && !(pq && (pq.tex || pq.col)); k++) el(\"line\", { x1: u + k * 50, y1: -eEdge + 15, x2: u + k * 50, y2: fT - 15, stroke: \"#5a3a1e\", \"stroke-width\": 6 }, g);   // [MM] dekoratīvs lamellu statnis"),
        ("  el(\"path\", { d, stroke: \"#b0b0b0\", \"stroke-width\": 4, fill: \"none\", \"clip-path\": `url(#${id})` }, g);\n  el(\"polygon\", { points: pts, fill: \"none\", stroke: C.line, \"stroke-width\": 8 }, g);",
         "  if (pc.tex || pc.col) el(\"polygon\", { points: pts, fill: pc.tex ? `url(#${terPat(g, pc, x0, y0)})` : pc.col }, g); else el(\"path\", { d, stroke: \"#b0b0b0\", \"stroke-width\": 4, fill: \"none\", \"clip-path\": `url(#${id})` }, g);\n  el(\"polygon\", { points: pts, fill: \"none\", stroke: C.line, \"stroke-width\": 8 }, g);"),
        ("        const tg = el(\"g\", { transform: `rotate(-90) scale(${k})` }, el(\"g\", { \"clip-path\": `url(#${id})` }, g));\n        for (let x = Math.floor(-bot / k / 2000) * 2000; x < -top / k + 2000; x += 2000) for (let y = Math.floor(a / k / 2000) * 2000; y < b / k; y += 2000) el(\"use\", { href: \"#cladTex\", x, y }, tg);",
         "        if (pc.tex || pc.col) el(\"rect\", { x: a, y: top, width: b - a, height: bot - top, fill: pc.tex ? `url(#${terPat(g, pc, 0, 0)})` : pc.col }, g); else {\n        const tg = el(\"g\", { transform: `rotate(-90) scale(${k})` }, el(\"g\", { \"clip-path\": `url(#${id})` }, g));\n        for (let x = Math.floor(-bot / k / 2000) * 2000; x < -top / k + 2000; x += 2000) for (let y = Math.floor(a / k / 2000) * 2000; y < b / k; y += 2000) el(\"use\", { href: \"#cladTex\", x, y }, tg); }"),
        ("    const along = q => endV ? q[1] : q[0], edge = pc.poly.filter(out).map(q => map(along(q)));",
         "    const along = q => endV ? q[1] : q[0], edge = (pc.__ter ? terEdge(pc, side, v) : pc.poly.filter(out)).map(q => map(along(q)));"),
        ("      face(u0, u1, fT, ROOF.plinth - 40);   // lievenis cokola augstumā",
         "      face(u0, u1, pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT, ROOF.plinth - 40);   // lievenis cokola augstumā"),
        ("      jamb(w.x, w.y, w.x, w.y + th); jamb(w.x + L, w.y, w.x + L, w.y + th);\n      el(\"rect\", { x: w.x, y: w.y + th * .36",
         "      [[w.x, w.y, w.x, w.y + th], [w.x + L, w.y, w.x + L, w.y + th]].forEach(q => el(\"line\", { x1: q[0], y1: q[1], x2: q[2], y2: q[3], stroke: C.line, \"stroke-width\": 22 }, g));   // [MM] ailas gals ar biezu sienas griezuma līniju\n      el(\"rect\", { x: w.x, y: w.y + th * .36"),
        ("      jamb(w.x, w.y, w.x + th, w.y); jamb(w.x, w.y + L, w.x + th, w.y + L);\n      el(\"rect\", { x: w.x + th * .36",
         "      [[w.x, w.y, w.x + th, w.y], [w.x, w.y + L, w.x + th, w.y + L]].forEach(q => el(\"line\", { x1: q[0], y1: q[1], x2: q[2], y2: q[3], stroke: C.line, \"stroke-width\": 22 }, g));   // [MM] ailas gals ar biezu sienas griezuma līniju\n      el(\"rect\", { x: w.x + th * .36"),
        ("  lvlMark(g, tx, cy + 720, lv(-ROOF.floorT));",
         "  lvlMark(g, tx, cy + 720, lv(-ROOF.floorT + (pc.up || 0)));"),
        ("pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT, ROOF.plinth - 40);",
         "(pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT) - (pc.up || 0), ROOF.plinth - 40);"),
        ("  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));",
         "  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));\n  (v.posts || []).forEach(q => { el(\"rect\", { x: q.x, y: q.y, width: q.w, height: q.d, fill: \"#fff\", stroke: C.ink, \"stroke-width\": 12 }, g); el(\"path\", { d: `M ${q.x} ${q.y} L ${q.x + q.w} ${q.y + q.d} M ${q.x + q.w} ${q.y} L ${q.x} ${q.y + q.d}`, stroke: C.ink, \"stroke-width\": 6 }, g); });   // [MM] brīvie stabi"),
        ("  // openings\n  const reveal =",
         "  (v.posts || []).forEach(q => { if (!postVisible(v, side, q)) return; const a = endV ? q.y : q.x, l = endV ? q.d : q.w; postsU.push([Math.min(map(a), map(a + l)), l, q]); });   // [MM] brīvie stabi fasādēs\n  // openings\n  const reveal ="),
        # [MM] ja apakšā ir aploda, palodze paliek ailas apakšā
        ('    if (true) {\n      z0 -= CB;\n', '    if (true) {\n'),
        # [MM] palodzes tonis var atšķirties no aplodām (AR.win.sillColor)
        ('      R(s0, s1, z0 - 40, z0 + 10, { fill: cc, ...ln });', '      R(s0, s1, z0 - 40, z0 + 10, { fill: colHex((window.AR && AR.win && AR.win.sillColor) || WINC().cas, "#24282b"), ...ln });'),
        # [MM] logu vēršanās loks plānā raustīts
        ('A ${lw} ${lw} 0 0 ${cw} ${tip[0]} ${tip[1]}`, fill: "none", stroke: C.thin, "stroke-width": 5 }, sashG)', 'A ${lw} ${lw} 0 0 ${cw} ${tip[0]} ${tip[1]}`, fill: "none", stroke: C.thin, "stroke-width": 5, ...SWD(1) }, sashG)'),
        # [MM] durvju kārbas paliek sienā: baltais izgriezums tikai brīvajā ailā, sienas līnijas iet pāri kārbām
        ('gap(x - KB, y - 14, w + 2 * KB, th + 28);', 'gap(x, y - 14, w, th + 28);'),
        ('gap(x - 14, y - KB, th + 28, w + 2 * KB);', 'gap(x - 14, y, th + 28, w);'),
        # [MM] jumta pārkare ar vēja kasti: gala fasādēs slēgta kaste no sienas līdz jumta malai, apakša horizontāli fascijas apakšā
        ('    const eT = eEdge + thV, cov = FAS ? 60 : 0;\n',
         '    const eT = eEdge + thV, cov = FAS ? 60 : 0;\n'
         # [MM] pārkare gala fasādē: jumta pīrāgs bez iekšējās apdares (līdz spārei), spāre apšūta ar dēļiem, dēļi pa slīpumu
         '    let tPV = vt;\n'
         '    if (ROOF.ov > 0) {\n'
         '      const RL = (typeof LAYERS === "function" && LAYERS("J1") && LAYERS("J1").layers) || [], ki = RL.findIndex(l => l[2] === "i");\n'
         '      tPV = ((ki >= 0 ? RL.slice(0, ki + 1).reduce((s, l) => s + l[1], 0) : ROOF.th) + 20) / Math.cos(ROOF.pitch * Math.PI / 180);\n'
         '      const BC = FAS ? "#F2F0EA" : (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54";\n'
         '      [[0, -1], [span, 1]].forEach(([u0, sd]) => {\n'
         '        const ue = u0 + sd * ROOF.ov, zA = eT, zB = eT + ROOF.ov * tan;\n'
         '        const pts = [P(ue, zA), P(u0, zB), P(u0, zB - tPV), P(ue, zA - tPV)].join(" "), cid = "ovb-" + side + sd + Math.random().toString(36).slice(2, 6);\n'
         '        el("polygon", { points: pts, fill: BC }, g);\n'
         '        if (!FAS) {   // fasādes dēļu tekstūra, pagriezta pa jumta slīpumu (dēļi gar spāri)\n'
         '          el("polygon", { points: pts }, el("clipPath", { id: cid }, g));\n'
         '          const cx = (ue + u0) / 2, cy = -(zA + zB - tPV) / 2, th = sd < 0 ? 90 - ROOF.pitch : ROOF.pitch - 90;\n'
         '          const tg = el("g", { transform: `rotate(${th} ${cx} ${cy})` }, el("g", { "clip-path": `url(#${cid})` }, g));\n'
         '          for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) el("use", { href: "#cladTex", x: cx - 1000 + i * 2000, y: cy - 1000 + j * 2000 }, tg);\n'
         '        }\n'
         '        el("polygon", { points: pts, fill: "none", stroke: C.ink, "stroke-width": 10 }, g);\n'
         '      });\n'
         '    }\n'
         '    if (ROOF.ov > 0 && window.AR && AR.projekts && AR.projekts.vejkaste) [[0, -1], [span, 1]].forEach(([u0, sd]) => {\n'
         '      const ue = u0 + sd * ROOF.ov, zb = eEdge, zf = eT - tPV, zw = zf + ROOF.ov * tan;\n'
         '      el("polygon", { points: [P(ue, zb), P(ue, zf), P(u0, zw), P(u0, zb)].join(" "), fill: FAS ? "#F2F0EA" : (AR.projekts.tonis_sw || "#555"), stroke: C.ink, "stroke-width": 12 }, g);\n'
         '      el("line", { x1: Math.min(ue, u0), y1: -(zb + 25), x2: Math.max(ue, u0), y2: -(zb + 25), stroke: C.ink, "stroke-width": 5 }, g);\n'
         '    });\n'),
        # [MM] sienas plānā aizlietas ar vienu toni (projekts.sienas_hex), pīrāgu slāņi nav redzami
        ('function drawWalls(g, v, cid) {\n',
         'function drawWalls(g, v, cid) {\n  const SOLID = (window.AR && AR.projekts && AR.projekts.sienas_hex) || ((window.AR && AR.projekts && AR.projekts.wall_style || {}).hatch === 0 ? "#ffffff" : null);   // [MM] sienas aizlietas ar vienu toni vai tīras (bez pīrāgiem)\n'),
        ('  EXT_LAYERS.forEach((l, i) => el("polygon", { points: ps(rings[i]), fill: l.fill || "#fff" }, g));',
         '  EXT_LAYERS.forEach((l, i) => el("polygon", { points: ps(rings[i]), fill: SOLID || l.fill || "#fff" }, g));'),
        ('  EXT_LAYERS.forEach((l, i) => {\n    if (!l.hatch) return;',
         '  EXT_LAYERS.forEach((l, i) => {\n    if (!l.hatch || SOLID) return;'),
        ('  EXT_LAYERS.forEach((l, i) => {\n    if (!l.ins) return;',
         '  EXT_LAYERS.forEach((l, i) => {\n    if (!l.ins || SOLID) return;'),
        ('  rings.forEach((r, i) => el("polygon", { points: ps(r), ...LAYER_LINE,',
         '  rings.forEach((r, i) => (!SOLID || i === rings.length - 1) && el("polygon", { points: ps(r), ...LAYER_LINE,'),
        ('  walls.forEach(([x, y, w, h]) => el("rect", { x, y, width: w, height: h, fill: "#fff" }, g));\n  walls.forEach(wl => {',
         '  walls.forEach(([x, y, w, h]) => el("rect", { x, y, width: w, height: h, fill: SOLID || "#fff" }, g));\n  if (!SOLID) walls.forEach(wl => {'),
        ('  walls.forEach(wl => { const [x, y, w, h] = core(wl); el("rect", { x, y, width: w, height: h, fill: "#fff" }, g); });',
         '  if (!SOLID) walls.forEach(wl => { const [x, y, w, h] = core(wl); el("rect", { x, y, width: w, height: h, fill: "#fff" }, g); });'),
        ('  walls.sort((a, b) => Math.max(a[2], a[3]) - Math.max(b[2], b[3]));\n  walls.forEach(wl => {',
         '  walls.sort((a, b) => Math.max(a[2], a[3]) - Math.max(b[2], b[3]));\n  if (!SOLID) walls.forEach(wl => {'),
        # [MM] durvju kārba tieši starp sienas virsmu līnijām (neizlien ne telpā, ne ārā)
        ('frm(x - KB, y, KB, th); frm(x + w, y, KB, th);',
         '{ const a0 = y <= 1 ? 8 : 16, a1 = y + th >= v.D - 1 ? 8 : 16; frm(x - KB, y + a0, KB, th - a0 - a1); frm(x + w, y + a0, KB, th - a0 - a1); }'),
        ('frm(x, y - KB, th, KB); frm(x, y + w, th, KB);',
         '{ const a0 = x <= 1 ? 8 : 16, a1 = x + th >= v.W - 1 ? 8 : 16; frm(x + a0, y - KB, th - a0 - a1, KB); frm(x + a0, y + w, th - a0 - a1, KB); }'),
        # [MM] notekcaurule ar lauzienu: lielai pārkarei caurule zem pārkares 45° atgriežas pie sienas
        ('      const zEnd = 50 - ROOF.plinth, d = `M ${uc} ${-(zt - 40)} L ${uc} ${-zEnd}`;',
         '      const zEnd = 50 - ROOF.plinth, gn = Math.abs(uc - uw) > 160, zk = Math.min(zt - 260, eEdge - 160), px = gn ? uw : uc;\n'
         '      const d = gn ? `M ${uc} ${-(zt - 40)} L ${uc} ${-zk} L ${uw} ${-(zk - Math.abs(uc - uw))} L ${uw} ${-zEnd}` : `M ${uc} ${-(zt - 40)} L ${uc} ${-zEnd}`;'),
        ('      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);',
         '      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "stroke-linejoin": "round", "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "stroke-linejoin": "round", "data-keep": 1 }, g);\n      el("line", { x1: px - sd * 22, y1: -((gn ? zk - Math.abs(uc - uw) : zt) - 80), x2: px - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < (gn ? zk - Math.abs(uc - uw) : zt) - 600; z += 1100) el("rect", { x: px - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);'),
        # [MM] garajā fasādē ar pārkari: spāres gals (jumta pīrāgs bez iekšējās apdares) visā jumta garumā, arī sānu pārkarēs; dēļi horizontāli
        ('    // sarkanajam: balta fascija ar mazu jumta toņa skārda lentu; pārējiem tikai tieva (100 mm) skārda mala, dēļi iet līdz jumtam\n    if (FAS) {',
         '    if (ROOF.ov > 0) {\n'
         '      const RL = (typeof LAYERS === "function" && LAYERS("J1") && LAYERS("J1").layers) || [], ki = RL.findIndex(l => l[2] === "i");\n'
         '      const tPV = ((ki >= 0 ? RL.slice(0, ki + 1).reduce((s, l) => s + l[1], 0) : ROOF.th) + 20) / Math.cos(ROOF.pitch * Math.PI / 180);\n'
         '      const a = -ROOF.ov, b = span + ROOF.ov, top = -(eEdge + thV), bot = top + tPV, cid = "ovf-" + side + Math.random().toString(36).slice(2, 6);\n'
         '      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: FAS ? "#F2F0EA" : ((window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54") }, g);\n'
         '      if (!FAS) { el("rect", { x: a, y: top, width: b - a, height: tPV }, el("clipPath", { id: cid }, g));\n'
         '        const tg = el("g", { transform: "rotate(-90)" }, el("g", { "clip-path": `url(#${cid})` }, g));\n'
         '        for (let x = Math.floor(-bot / 2000) * 2000; x < -top + 2000; x += 2000) for (let y = Math.floor(a / 2000) * 2000; y < b; y += 2000) el("use", { href: "#cladTex", x, y }, tg); }\n'
         '      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: "none", stroke: C.ink, "stroke-width": 12 }, g);\n'
         '    }\n'
         '    // sarkanajam: balta fascija ar mazu jumta toņa skārda lentu; pārējiem tikai tieva (100 mm) skārda mala, dēļi iet līdz jumtam\n    if (FAS) {'),
        # [MM] ārējo mēru ķēžu līnijas atzīmē (data-chain), lai redaktorā jauns mērs pielīp tām
        ('  if (axis === "x") L(a0 - 120, at, a1 + 120, at); else L(at, a0 - 120, at, a1 + 120);',
         '  { const ml = axis === "x" ? L(a0 - 120, at, a1 + 120, at) : L(at, a0 - 120, at, a1 + 120); if (!inner && ml && ml.setAttribute) ml.setAttribute("data-chain", axis + ":" + at); }'),
        # [MM] zemes līnija fasādē: viss, kas iet zem zemes (terases, stabi, pamati), tiek aizsegts; māja stāv aiz zemes līnijas
        ('  const axU = ax.map(([a]) => map(a)), AG =',
         '  { el("rect", { x: -1600, y: ROOF.plinth, width: span + 3200, height: 300, fill: "#fff" }, g); let d = ""; for (let x = -1400; x < span + 1400 - 260; x += 200) d += `M ${x} ${ROOF.plinth + 260} L ${x + 260} ${ROOF.plinth} `; el("path", { d, stroke: "#666", "stroke-width": 8, fill: "none" }, g);\n    el("line", { x1: -1600, y1: ROOF.plinth, x2: span + 1600, y2: ROOF.plinth, stroke: C.ink, "stroke-width": 45, "data-keep": 1 }, g); }   // [MM] zemes līnija virs visa, kas zem tās\n  const axU = ax.map(([a]) => map(a)), AG ='),
        # [MM] eksplikācija: ārtelpās arī terases (pakāpieni, t.up, netiek skaitīti)
        ("const n = v.rooms.length, pr = v.porch ? 2 : 0, rows = n + 4 + pr;",
         "const OUT = [].concat(v.porch ? [v.porch] : [], (v.terraces || []).filter(t => !t.up)), n = v.rooms.length, pr = OUT.length ? OUT.length + 1 : 0, rows = n + 4 + pr;"),
        ('cell(c1 / 2, yy + RH, String(n + 1), { a: "middle" }); cell(c1 + 2, yy + RH, v.porch.name || "Lievenis"); cell(WX - 2, yy + RH, f2(polyArea(v.porch.poly)), { a: "end" });',
         'OUT.forEach((o, oi) => { const y2 = yy + (oi + 1) * RH; cell(c1 / 2, y2, String(n + 1 + oi), { a: "middle" }); cell(c1 + 2, y2, o.name || (o === v.porch ? "Lievenis" : "Terase")); cell(WX - 2, y2, f2(polyArea(o.poly)), { a: "end" }); });'),
        ("(v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));",
         "(v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + (v.terraces || []).slice(0, ti).filter(q => !q.up).length));"),
        # [MM] loga ārējā aploda nedrīkst iziet ārpus ieejas nišas (ieliekuma) uz blakus sienu: ailu sānu aplodas apgriež pie nišas malas
        ("const win = (u0, u1, z0, z1, PN, cas) => {", "const win = (u0, u1, z0, z1, PN, cas, cl = cas, cr = cas) => {"),
        ("      R(u0 - cas, u1 + cas, z0 - CB, z1 + cas, { fill: cc, ...ln });",
         "      R(u0 - cl, u1 + cr, z0 - CB, z1 + cas, { fill: cc, ...ln });"),
        ("    window.MM_CASB = !!w.casingAll; win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w), w.casing ?? (window.AR && window.AR.win && window.AR.win.casing) ?? 0);",
         "    window.MM_CASB = !!w.casingAll;\n    const cs0 = w.casing ?? (window.AR && window.AR.win && window.AR.win.casing) ?? 0, nz = (rc || []).map(r => [Math.min(map(r[0]), map(r[1])), Math.max(map(r[0]), map(r[1]))]).find(r => u0 >= r[0] - 1 && u1 <= r[1] + 1);\n    win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w), cs0, nz ? Math.max(0, Math.min(cs0, u0 - nz[0])) : cs0, nz ? Math.max(0, Math.min(cs0, nz[1] - u1)) : cs0);"),
    ]:
        assert a in cad, 'SBE cad.js: nav atrasts ' + a[:50]
        cad = cad.replace(a, b, 1)
    # [MM] slīpais logs: kores virsotne fasādes vidū un apgriešana pie jumta līnijām tagad ir pašā cad.js (gableWins)
    # [MM] AR lapas: mazām mājām fasādes (un plāni) lielākā mērogā 1:75 vai 1:50; līnijas un teksts paliek tāda paša lieluma
    ARFIX = (
        'function arFix(g, k) {\n'
        '  if (!g || k === 1) return;\n'
        '  g.querySelectorAll("*").forEach(e => {\n'
        '    ["stroke-width", "font-size", "letter-spacing"].forEach(a => { const x = e.getAttribute(a); if (x != null && x !== "" && !isNaN(+x)) e.setAttribute(a, (+x * k).toFixed(3)); });\n'
        '    const d = e.getAttribute("stroke-dasharray"); if (d && d !== "none") e.setAttribute("stroke-dasharray", d.split(/[ ,]+/).map(x => (+x * k).toFixed(2)).join(" "));\n'
        '  });\n'
        '}\n'
        'function arScaleFas(v, H) {   // [s, d] lielākais standarta mērogs, kurā abas fasādes ietilpst lapā\n'
        '  const L = v.W + 2 * ROOF.ov, D = v.D + 2 * ROOF.ov;\n'
        '  for (const d of [50, 75]) { const s = 1 / d; if ((L + D) * s <= 315 && H * s <= 120) return [s, d]; }\n'
        '  return [0.01, 100];\n'
        '}\n'
        'function arScalePlan(v) {\n'
        '  for (const d of [50, 75]) { const s = 1 / d; if ((v.W + 6900) * s <= 222 && (v.D + 6900) * s <= 148) return [s, d]; }\n'
        '  return [0.01, 100];\n'
        '}\n')
    n0 = ar.index('function wrap(t, n) {')
    ar = ar[:n0] + ARFIX + ar[n0:]
    for a_, b_ in [
        # [MM] pamatu un komunikāciju plāns kā AR lapa
        ('    if (k === "plan" || k === "mebel") {', '    if (/^pam\\d$/.test(k)) { out.push(pamArSheet(v, k, sc => sheet(k, title, sc))); return; }\n    if (k === "plan" || k === "mebel") {'),
        ('      const svg = planSheet(v, { sheetEl: sheet(k, title, "1:100"),',
         '      const [ps_, pd_] = arScalePlan(v); window.AR_PK = ps_ === 0.01 ? null : ps_; window.AR_PD = pd_; window.MM_SCALE = pd_;\n      const svg = planSheet(v, { sheetEl: sheet(k, title, "1:" + pd_),'),
        ('      out.push(svg); return;\n    }\n    const svg = sheet(k, title, k === "mezgli"',
         '      window.AR_PK = null; window.AR_PD = 100; window.MM_SCALE = 100;\n      out.push(svg); return;\n    }\n    const [fs_, fd_] = (k === "fas1" || k === "fas2") ? arScaleFas(v, H) : [0.01, 100];\n    const svg = sheet(k, title, k === "fas1" || k === "fas2" ? "1:" + fd_ : k === "mezgli"'),
        ('      elevation(el("g", { "data-block": "elev-" + a, transform: `translate(52 150) scale(0.01)` }, svg), v, a, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, a)}` });\n'
         '      elevation(el("g", { "data-block": "elev-" + b, transform: `translate(266 150) scale(0.01)` }, svg), v, b, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, b)}` });\n',
         '      { const La = v.W + 2 * ROOF.ov, Lb = v.D + 2 * ROOF.ov, wa = (k === "fas1" ? v.D : v.D) , xa = 40 + ROOF.ov * fs_, xb = Math.min(266, xa + La * fs_ + 60 + ROOF.ov * fs_);\n'
         '        const aLen = (a === "south" || a === "north") ? La : Lb, bLen = (b === "south" || b === "north") ? La : Lb; void wa; void bLen;\n'
         '        const x1 = fs_ === 0.01 ? 52 : 62 + ROOF.ov * fs_, x2 = fs_ === 0.01 ? 266 : Math.min(266, x1 + aLen * fs_ + 70);\n'
         '        const gy_ = fs_ === 0.01 ? 150 : Math.min(150, 174.5 - 2450 * fs_);   // nosaukums paliek tajā pašā vietā lapā\n        window.AR_K = 0.01 / fs_; window.MM_SCALE = fd_;\n'
         '        const ga = el("g", { "data-block": "elev-" + a, transform: `translate(${x1} ${gy_}) scale(${fs_})` }, svg); elevation(ga, v, a, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, a)}` }); arFix(ga, 0.01 / fs_);\n'
         '        const gb = el("g", { "data-block": "elev-" + b, transform: `translate(${x2} ${gy_}) scale(${fs_})` }, svg); elevation(gb, v, b, { levels: true, title: `FASĀDE ASĪS ${sideAxes(v, b)}` }); arFix(gb, 0.01 / fs_);\n'
         '        window.AR_K = 1; window.MM_SCALE = 100; void xa; void xb; }\n'),
    ]:
        assert a_ in ar, 'SBE ar.js: nav atrasts ' + a_[:50]
        ar = ar.replace(a_, b_, 1)
    # [MM] slānis ar veidu "n" (piem. pretgrauzēju barjera latojumā) neskaita kopējā biezumā: lapā biezums 0, mm nosaukumā
    a_ = 'const LAYERS = k => (ARC && ARC.layers && ARC.layers[k]) || null;'
    assert a_ in ar, 'SBE ar.js: nav atrasts LAYERS'
    ar = ar.replace(a_, 'const LAYERS = k => { const s = (ARC && ARC.layers && ARC.layers[k]) || null; return s && s.layers.some(l => l[2] === "n") ? { ...s, layers: s.layers.map(l => l[2] === "n" ? [l[0] + " (" + l[1] + " mm latojumā)", 0, ""] : l) } : s; };', 1)
    for a_, b_ in [
        ('  const g = el("g", { transform: "translate(61 50) scale(0.01)" }, svg);\n  cadPlan(g, v, { furniture: o.furniture ?? true, axes: true, levels: true, tag: o.tag || "-a3", tags: o.tags ?? !!v.marks, wallTags: o.wallTags, sections: o.sections });',
         '  const g = el("g", { transform: window.AR_PK ? `translate(${27 + 3450 * window.AR_PK} ${22 + 3450 * window.AR_PK}) scale(${window.AR_PK})` : "translate(61 50) scale(0.01)" }, svg);\n  cadPlan(g, v, { furniture: o.furniture ?? true, axes: true, levels: true, tag: o.tag || "-a3", tags: o.tags ?? !!v.marks, wallTags: o.wallTags, sections: o.sections });\n  if (window.AR_PK) arFix(g, 0.01 / window.AR_PK);'),
        ('  T_(svg, 26 + hd.length * 2.75 + 6, 197, "M 1:100", { fs: 3.4, fill: "#444" });\n  el("line", { x1: 26, y1: 199,', '  T_(svg, 26 + hd.length * 2.75 + 6, 197, "M 1:" + (window.AR_PD || 100), { fs: 3.4, fill: "#444" });\n  el("line", { x1: 26, y1: 199,'),
        ('ttl.length * 262 + 350', '(ttl.length * 262 + 350) * (window.AR_K || 1)'),
    ]:
        if a_ in cad: cad = cad.replace(a_, b_, 1)
        else: print('BRĪDINĀJUMS: cad.js neatrasts:', a_[:50])
    cad = _ov_per_edge(cad)
    cad = _mm_extra(cad)
    cad = cad.replace('/*AR*/', ar + '\n' + sheet, 1)
    cad = cad.replace('function sheetHeading(svg, x, y, w, title, scale = "M 1:100")', 'function sheetHeading(svg, x, y, w, title, scale = "M 1:" + (window.MM_SCALE || 100))', 1)
    # fasādes tonis: SBE apdares tekstūru aizstāj ar izvēlēto (sablons/tex)
    import re
    tex = (pr.get('fasade_tex') if pr.get('fasade_hex') else None) or base64.b64encode(open(os.path.join(HERE, 'sablons', tone['tex']), 'rb').read()).decode()
    cad, n = re.subn(r'const CLAD_TEX = "data:image/jpeg;base64,[^"]*";', lambda _: f'const CLAD_TEX = "data:image/jpeg;base64,{tex}";', cad, count=1)
    assert n == 1, 'SBE cad.js: nav atrasta CLAD_TEX tekstūra'

    h = open(os.path.join(SBE, 'plani', 'planojuma-varianti.html'), encoding='utf-8').read()
    mk = '<!-- cad-mode -->'
    h = h[:h.index(mk)].rstrip() + '\n' + mk + '\n<script>\n' + cad + '</script>\n'
    tt = 'const T = 310, t = 170;'
    assert tt in h, 'SBE html: nav atrasti sienu biezumi'
    h = h.replace(tt, f'const T = {T:g}, t = {t:g};', 1)
    assert h.count('pārkare ${ROOF.ov} mm.') == 1, 'SBE: nav atrasta pārkares piezīme'
    h = h.replace('pārkare ${ROOF.ov} mm.', 'pārkare ${ROOF.ov} mm${ROOF.ov > 0 ? (window.AR && AR.projekts && AR.projekts.vejkaste ? ", ar vēja kasti" : ", bez vēja kastes") : ""}.', 1)   # [MM] pārkare ar vai bez vēja kastes
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
    css += """<style>html{overflow:hidden;background:#e9e7e2;touch-action:none}body{touch-action:none;transform-origin:0 0;margin:0;cursor:grab}body.mmdrag{cursor:grabbing}
@media print{html{overflow:visible!important;background:none}body{transform:none!important;cursor:auto}}</style>
<script>(function(){var b=document.body,s=1,x=0,y=0,d=null,fit=1;
function ap(){b.style.transform='translate('+x+'px,'+y+'px) scale('+s+')';if(window.MMZ_ON)MMZ_ON()}
window.MMZ={get:function(){return{s:s,x:x,y:y}},set:function(v){s=v.s;x=v.x;y=v.y;ap()}};
function reset(){var es=document.querySelectorAll('svg.a3');if(!es.length)return;var L=1e9,T=1e9,R=-1e9,B=-1e9;es.forEach(function(e){var r=e.getBoundingClientRect();L=Math.min(L,r.left);T=Math.min(T,r.top);R=Math.max(R,r.right);B=Math.max(B,r.bottom)});
var w=(R-L)/s,h=(B-T)/s,ox=es.length>1?(L-x)/s:0,oy=es.length>1?(T-y)/s:0;
fit=Math.min(innerWidth/w,innerHeight/h);if(window.MMZ_INIT){var v=MMZ_INIT;MMZ_INIT=null;s=v.s;x=v.x;y=v.y;ap();return}s=fit;x=(innerWidth-w*s)/2-ox*s;y=(innerHeight-h*s)/2-oy*s;ap()}
window.MMZ.reset=function(){MMZ_INIT=null;reset()};
addEventListener('load',function(){setTimeout(reset,50)});addEventListener('resize',function(){if(!window.MM_ED)reset()});
addEventListener('wheel',function(e){e.preventDefault();var k=Math.exp(-e.deltaY*(e.ctrlKey?.01:.0015)),n=Math.min(Math.max(s*k,fit*.5),fit*12);k=n/s;
x=e.clientX-(e.clientX-x)*k;y=e.clientY-(e.clientY-y)*k;s=n;ap()},{passive:false});
var P={},pc=null;   /* [MM] telefons: divu pirkstu tuvināšana un bīdīšana */
function two(){var k=Object.keys(P);return k.length>=2?[P[k[0]],P[k[1]]]:null}
function mid(t){return{x:(t[0][0]+t[1][0])/2,y:(t[0][1]+t[1][1])/2,r:Math.hypot(t[0][0]-t[1][0],t[0][1]-t[1][1])||1}}
addEventListener('pointerdown',function(e){P[e.pointerId]=[e.clientX,e.clientY];var t=two();if(t){d=null;b.classList.remove('mmdrag');if(window.MMZ_CANCEL)MMZ_CANCEL();pc=mid(t);return}
if(window.MMZ_HOOK&&MMZ_HOOK(e))return;d=[e.clientX-x,e.clientY-y];b.classList.add('mmdrag')});
addEventListener('pointermove',function(e){if(P[e.pointerId])P[e.pointerId]=[e.clientX,e.clientY];var t=two();
if(t&&pc){var m=mid(t),n=Math.min(Math.max(s*m.r/pc.r,fit*.5),fit*12),k=n/s;x=m.x-(pc.x-x)*k;y=m.y-(pc.y-y)*k;s=n;pc=m;ap();return}
if(d){x=e.clientX-d[0];y=e.clientY-d[1];ap()}});
function up(e){delete P[e.pointerId];if(Object.keys(P).length<2)pc=null;d=null;b.classList.remove('mmdrag')}
addEventListener('pointerup',up);addEventListener('pointercancel',up);
addEventListener('dblclick',function(e){if(window.MM_ED)return;reset()})})()</script>"""
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
