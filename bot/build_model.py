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
            'wallTags', 'sections', 'gableWins', 'ceiling', 'ceilingNote', 'planNotes', 'winOk', 'noLeaf', 'decor', 'entryInChain', 'porch', 'terraces', 'axOff', 'posts', 'railings', 'freeWalls', 'apbuve', 'dimOff', 'wallCuts', 'wallPad']
    rv = {'id': 'A', 'rev': rev, 'short': m['nosaukums'], 'marks': True, 'openRooms': [], 'fixtures': [], 'openings': [],
          'poly': m.get('poly') or [[0, 0], [m['W'], 0], [m['W'], m['D']], [0, m['D']]], 'recess': m.get('recess', {})}
    rv.update({k: m[k] for k in keys if k in m})
    if (m.get('loft')):
        rv['loftLevel'] = m['loft'].get('level')
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
    k = body.index('const eEdge = MN ? MN.eE : LP ? LP.eE : ROOF.eave - ROOF.ov * tan')
    head, rest = body[:k], body[k:]
    ins = ('const _OV = (window.AR && AR.projekts && AR.projekts.ov_side) || {}, _od = q => (_OV[q] != null && !isNaN(+_OV[q])) ? +_OV[q] : ROOF.ov;\n'
           '  const _LR = { south: ["west", "east"], north: ["east", "west"], east: ["south", "north"], west: ["north", "south"] }[side] || ["west", "east"];\n'
           '  const OVL = _od(_LR[0]), OVR = _od(_LR[1]), OVV = endV ? ROOF.ov : _od(side);\n  ')
    rest = rest.replace('ROOF.eave - ROOF.ov * tan', 'ROOF.eave - OVV * tan', 1)
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
            'function mmFacSegs(v, side) {   // [MM] fasādes atsevišķas sienas (plaknes): mājas kontūras malas, kas skatās uz šo pusi; [{u0, u1}] fasādes koordinātēs\n'
            '  const P = v.poly || [], n = P.length, ar = P.reduce((s, q, i) => s + q[0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * q[1], 0) > 0 ? 1 : -1, nm = { north: [0, -1], south: [0, 1], west: [-1, 0], east: [1, 0] }[side], out = [];\n'
            '  P.forEach((a, i) => { const b = P[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], o = ar > 0 ? [dy, -dx] : [-dy, dx]; if (!(o[0] * nm[0] + o[1] * nm[1] > 0)) return;\n'
            '    const hz = side === "north" || side === "south", f = q => hz ? (side === "north" ? v.W - q[0] : q[0]) : (side === "east" ? v.D - q[1] : q[1]), u0 = f(a), u1 = f(b); if (Math.abs(u1 - u0) > 1) out.push({ u0: Math.min(u0, u1), u1: Math.max(u0, u1) }); });\n'
            '  out.sort((p, q) => p.u0 - q.u0);\n'
            '  const ex = { north: Math.min(...P.map(q => q[1])), south: Math.max(...P.map(q => q[1])), west: Math.min(...P.map(q => q[0])), east: Math.max(...P.map(q => q[0])) }[side], SP = side === "north" || side === "south" ? v.W : v.D;   // [MM] ieliekuma siena (atkāpta no ārējās plaknes) beidzas pie karnīzes; virs tās tā pati ārējās plaknes siena\n'
            '  P.forEach((a, i) => { const b = P[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], o = ar > 0 ? [dy, -dx] : [-dy, dx]; if (!(o[0] * nm[0] + o[1] * nm[1] > 0)) return;\n'
            '    const hz = side === "north" || side === "south", f = q => hz ? (side === "north" ? v.W - q[0] : q[0]) : (side === "east" ? v.D - q[1] : q[1]), u0 = Math.min(f(a), f(b)), u1 = Math.max(f(a), f(b)), c = hz ? a[1] : a[0], sg = out.find(q => Math.abs(q.u0 - u0) < 2 && Math.abs(q.u1 - u1) < 2); if (sg) sg.rec = Math.abs(c - ex) > 1; });\n'
            '  const outer = out.filter(q => !q.rec); let cur = 0; const gaps = [];\n'
            '  outer.forEach(q => { if (q.u0 > cur + 1) gaps.push([cur, q.u0]); cur = Math.max(cur, q.u1); }); if (cur < SP - 1) gaps.push([cur, SP]);\n'
            '  gaps.forEach(g => { const ow = outer.find(q => Math.abs(q.u1 - g[0]) < 2) || outer.find(q => Math.abs(q.u0 - g[1]) < 2); if (ow) (ow.ext = ow.ext || []).push(g); });\n'
            '  return out;\n}\nwindow.mmFacSegs = mmFacSegs;\n'
            'function mmFacPick(v, side, u, z, eE) {   // [MM] siena fasādē punktā (u, z): ieliekuma siena tikai zem karnīzes, virs tās pieder ārējās plaknes sienai\n'
            '  const sg = mmFacSegs(v, side), s = sg.find(q => u >= q.u0 && u <= q.u1); if (!s || !s.rec || z == null || z <= eE) return s || null;\n'
            '  return sg.find(q => (q.ext || []).some(g => u >= g[0] - 1 && u <= g[1] + 1)) || s;\n}\nwindow.mmFacPick = mmFacPick;\n'
            'function mmFacEdges(v) {   // [MM] mājas kontūras malas ar fasādes pusi un u-diapazonu: [{side, u0, u1, a, b}]\n'
            '  const P = v.poly || [], n = P.length, ar = P.reduce((s, q, i) => s + q[0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * q[1], 0) > 0 ? 1 : -1, out = [];\n'
            '  P.forEach((a, i) => { const b = P[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], o = ar > 0 ? [dy, -dx] : [-dy, dx]; if (!dx && !dy) return;\n'
            '    const side = Math.abs(o[0]) > Math.abs(o[1]) ? (o[0] > 0 ? "east" : "west") : (o[1] > 0 ? "south" : "north"), hz = side === "north" || side === "south", f = q => hz ? (side === "north" ? v.W - q[0] : q[0]) : (side === "east" ? v.D - q[1] : q[1]), u0 = f(a), u1 = f(b);\n'
            '    out.push({ side, u0: Math.min(u0, u1), u1: Math.max(u0, u1), a, b }); });\n'
            '  return out;\n}\nwindow.mmFacEdges = mmFacEdges;\n'
            'function mmFacEdge(v, p, tol) {   // [MM] tuvākā kontūras mala punktam plānā (p = [x, y]) ne tālāk par tol\n'
            '  let best = null;\n'
            '  mmFacEdges(v).forEach(e => { const dx = e.b[0] - e.a[0], dy = e.b[1] - e.a[1], L2 = dx * dx + dy * dy, t = Math.max(0, Math.min(1, ((p[0] - e.a[0]) * dx + (p[1] - e.a[1]) * dy) / L2)), d = Math.hypot(p[0] - e.a[0] - t * dx, p[1] - e.a[1] - t * dy); if (d <= tol && (!best || d < best.d)) best = Object.assign({ d }, e); });\n'
            '  return best;\n}\nwindow.mmFacEdge = mmFacEdge;\n'
            'function mmParkHex(side) { const P = (window.AR && AR.projekts) || {}, q = (P.parkare_side || {})[side]; return q || P.parkare_hex || null; }   // [MM] jumta pārkares tonis pa fasādes pusēm (projekts.parkare_side), citādi viens visai mājai\n'
            'function mmFasHex(side, d) { const P = (window.AR && AR.projekts) || {}, q = (P.fascia_side || {})[side]; return q || P.fascia_hex || mmParkHex(side) || d; }   // [MM] fascijas dēļa (vējmalas) tonis: pa pusēm (projekts.fascia_side), visai mājai (fascia_hex), citādi kā jumta pārkare\n'
            'function mmRoofFill(d) { const P = (window.AR && AR.projekts) || {}, hx = P.jumta_hex || "#40464b"; if (P.jumta_tex !== "spanish") return P.jumta_hex || d;   // [MM] Spanish tiles: svg raksts (jumta tonis + viļņoti rindu loki)\n'
            '  const id = "mmSpanish" + hx.slice(1); if (!document.getElementById(id)) { let h = document.getElementById("mmPatHost"); if (!h) { h = document.createElementNS("http://www.w3.org/2000/svg", "svg"); h.id = "mmPatHost"; h.setAttribute("width", 0); h.setAttribute("height", 0); h.style.position = "absolute"; document.body.appendChild(h); }\n'
            '    h.insertAdjacentHTML("beforeend", `<defs><pattern id="${id}" width="320" height="240" patternUnits="userSpaceOnUse"><rect width="320" height="240" fill="${hx}"/><g fill="none" stroke="#000" stroke-opacity=".38" stroke-width="7"><path d="M0 60Q40 20 80 60T160 60T240 60T320 60"/><path d="M-80 180Q-40 140 0 180T80 180T160 180T240 180T320 180"/></g><g fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="5"><path d="M0 52Q40 12 80 52T160 52T240 52T320 52"/><path d="M0 172Q40 132 80 172T160 172T240 172T320 172"/></g></pattern></defs>`); }\n'
            '  return `url(#${id})`; }\n'
            'function mmSideHex(side) { const q = ((window.AR && AR.projekts && AR.projekts.fasade_side) || {})[side]; return q ? (q.hex || q) : null; }\n')
    a = 'function cadPlan(parent, v, opt = {}) {'
    assert a in cad, 'SBE cad.js: nav atrasts cadPlan'
    cad = cad.replace(a, TINT + a, 1)
    cad = cad.replace('fill: roofSeams() ? "#40464b" : "url(#shingle)"', 'fill: mmRoofFill(roofSeams() ? "#40464b" : "url(#shingle)")')   # [MM] jumta toņa izvēle
    # [MM] piezīmes plānā: projekts.notes_off sarakstā esošās netiek zīmētas; katra piezīme ir atsevišķa grupa ar data-note (dzēšanai redaktorā)
    a = '  notes.forEach((t, i) => { const ls = wrap(t, 64); T_(ex, 0, yL, `${i + 1}.`, { fs: 2.4, fill: "#333" }); ls.forEach((l, j) => T_(ex, 5, yL + j * 3.6, l, { fs: 2.4, fill: "#333" })); yL += ls.length * 3.6 + 1; });'
    assert a in cad, 'SBE cad.js: nav atrastas piezīmes'
    cad = cad.replace(a, '  const _noff = (window.AR && AR.projekts && AR.projekts.notes_off) || [];\n  notes.filter(t => !_noff.includes(t)).forEach((t, i) => { const ls = wrap(t, 64), gn = el("g", { "data-note": t }, ex); T_(gn, 0, yL, `${i + 1}.`, { fs: 2.4, fill: "#333" }); ls.forEach((l, j) => T_(gn, 5, yL + j * 3.6, l, { fs: 2.4, fill: "#333" })); yL += ls.length * 3.6 + 1; });', 1)
    for a, b in [
        # stabs fasādē: augstums q.h (mm virs ±0,000); virs jumta pārkares apakšas tiek nogriezts pa pārkari (gala fasādē pa slīpumu)
        ('    el("rect", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#c68a58", stroke: C.ink, "stroke-width": 4 }, g);',
         '    const RLp = (typeof LAYERS === "function" && LAYERS("J1") && LAYERS("J1").layers) || [], kip = RLp.findIndex(l => l[2] === "i"), tPQ = ((kip >= 0 ? RLp.slice(0, kip + 1).reduce((s_, l) => s_ + l[1], 0) : ROOF.th) + 20) / Math.cos(ROOF.pitch * Math.PI / 180), pzc = uu => (gable ? eEdge + (Math.min(uu, span - uu) + (uu < span / 2 ? OVL : OVR)) * tan : eEdge + thV - tPQ) + (gable ? thV - tPQ : 0), ph = pq && +pq.h > 0 ? +pq.h : 0, pzL = ph && ph < pzc(u) ? ph : pzc(u) + 12, pzR = ph && ph < pzc(u + s) ? ph : pzc(u + s) + 12, pzm = Math.min(pzL, pzR);\n'
         '    if (window.__FDF && window.__FDF[side]) window.__FDF[side].pz = [gable ? 1 : 0, OVL, OVR, tan]; window.__FDF[side].fb = ROOF.plinth - 40;\n'
         '    el("polygon", { points: [P(u, -fT), P(u + s, -fT), P(u + s, pzR)].concat(ph && (pzc(u) - ph) * (pzc(u + s) - ph) < 0 ? [P(u + (pzc(u) - ph) / (pzc(u) - pzc(u + s)) * s, ph)] : [], [P(u, pzL)]).join(" "), fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#c68a58", stroke: C.ink, "stroke-width": 4 }, g);'),
        ('el("line", { x1: u + k * 50, y1: -eEdge + 15, x2: u + k * 50, y2: fT - 15, stroke: "#5a3a1e", "stroke-width": 6 }, g);',
         'void 0;'),   # [MM] stabam fasādē nav vektora līniju: tikai tekstūra vai krāsa
        # fasādes tonis tikai vienai pusei (krāsas spainis): projekts.fasade_side[side]
        ('  boards(el("g", { "clip-path": `url(#${wid})` }, g), 0, span, -(gable || LP || (MN && (MN.role === "prof" || MN.par)) ? ridgeTop : (FAS ? eEdge : eEdge + thV - 20)), fT, side.length);',
         '  boards(el("g", Object.assign({ "clip-path": `url(#${wid})` }, mmSideHex(side) ? { filter: `url(#${mmTint(g, mmSideHex(side))})` } : {}), g), 0, span, -(gable || LP || (MN && (MN.role === "prof" || MN.par)) ? ridgeTop : (FAS ? eEdge : eEdge + thV - 20)), fT, side.length);\n'
         '  { const WW = (((window.AR && AR.projekts && AR.projekts.fasade_wall) || {})[side]) || []; WW.forEach(q => { const rid = "wr-" + side + Math.random().toString(36).slice(2, 7); { const cp = el("clipPath", { id: rid }, g), sgq = mmFacSegs(v, side).find(z => Math.abs(z.u0 - q.u0) < 2 && Math.abs(z.u1 - q.u1) < 2) || {}; if (sgq.rec) el("rect", { x: q.u0, y: -eEdge, width: q.u1 - q.u0, height: 20000 + eEdge }, cp); else { el("rect", { x: q.u0, y: -20000, width: q.u1 - q.u0, height: 40000 }, cp); (sgq.ext || []).forEach(gp => el("rect", { x: gp[0], y: -20000, width: gp[1] - gp[0], height: 20000 - eEdge }, cp)); } } boards(el("g", { "clip-path": `url(#${rid})`, filter: `url(#${mmTint(g, q.hex)})` }, el("g", { "clip-path": `url(#${wid})` }, g)), 0, span, -(gable || LP || (MN && (MN.role === "prof" || MN.par)) ? ridgeTop : (FAS ? eEdge : eEdge + thV - 20)), fT, side.length); }); }   // [MM] atsevišķu sienu toņi (projekts.fasade_wall[side] = [{u0, u1, hex}])\n'),
        # jumta pārkares tonis (projekts.parkare_hex): gala fasādes pārkare, vēja kaste, garās fasādes spāres gals
        ('      const BC = FAS ? "#F2F0EA" : (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54";\n',
         '      const PKH = mmParkHex(side), BC = PKH || (FAS ? "#F2F0EA" : (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54");\n'),
        ('        if (!FAS) {   // fasādes dēļu tekstūra, pagriezta pa jumta slīpumu (dēļi gar spāri)\n',
         '        if (!FAS || PKH) {   // fasādes dēļu tekstūra, pagriezta pa jumta slīpumu (dēļi gar spāri)\n'),
        ('          const tg = el("g", { transform: `rotate(${th} ${cx} ${cy})` }, el("g", { "clip-path": `url(#${cid})` }, g));\n',
         '          const tg = el("g", { transform: `rotate(${th} ${cx} ${cy})` }, el("g", Object.assign({ "clip-path": `url(#${cid})` }, PKH ? { filter: `url(#${mmTint(g, PKH)})` } : {}), g));\n'),
        ('fill: FAS ? "#F2F0EA" : (AR.projekts.tonis_sw || "#555"), stroke: C.ink, "stroke-width": 12 }, g);',
         'fill: mmParkHex(side) || (FAS ? "#F2F0EA" : (AR.projekts.tonis_sw || "#555")), stroke: C.ink, "stroke-width": 12 }, g);'),
        ('      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: FAS ? "#F2F0EA" : ((window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54") }, g);\n'
         '      if (!FAS) { el("rect", { x: a, y: top, width: b - a, height: tPV }, el("clipPath", { id: cid }, g));\n'
         '        const tg = el("g", { transform: "rotate(-90)" }, el("g", { "clip-path": `url(#${cid})` }, g));',
         '      const PKH = mmParkHex(side);\n'
         '      el("rect", { x: a, y: top, width: b - a, height: tPV, fill: PKH || (FAS ? "#F2F0EA" : ((window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54")) }, g);\n'
         '      if (!FAS || PKH) { el("rect", { x: a, y: top, width: b - a, height: tPV }, el("clipPath", { id: cid }, g));\n'
         '        const tg = el("g", { transform: "rotate(-90)" }, el("g", Object.assign({ "clip-path": `url(#${cid})` }, PKH ? { filter: `url(#${mmTint(g, PKH)})` } : {}), g));'),
        # [MM] sienas posma sabiezinājums (model.wallPad): zīmē plānā aiz ārsienas kontūras
        ('  el("polygon", { points: ps(rings[0]), fill: "none", stroke: C.ink, "stroke-width": 16 * WL("outer") }, g);\n',
         '  el("polygon", { points: ps(rings[0]), fill: "none", stroke: C.ink, "stroke-width": 16 * WL("outer") }, g);\n' + '\n  // [MM] sienas posma sabiezinājums (model.wallPad: [{side, a, b, t, wt, inHex, endHex}]): posms uz āru pie nemainīgas telpu izkārtojuma; savs sienas veids (pīrāgs), iekšpuses un gala tonis\n  (v.wallPad || []).forEach(q => {\n    const H = q.side === "north" || q.side === "south", neg = q.side === "north" || q.side === "west", pick = (R, ext) => { let pos = null;\n      for (let i = 0; i < R.length; i++) { const A = R[i], B = R[(i + 1) % R.length]; if (H ? Math.abs(A[1] - B[1]) > 1 : Math.abs(A[0] - B[0]) > 1) continue;\n        const c = H ? A[1] : A[0], lo = H ? Math.min(A[0], B[0]) : Math.min(A[1], B[1]), hi = H ? Math.max(A[0], B[0]) : Math.max(A[1], B[1]);\n        if (lo <= q.a + 1 && hi >= q.b - 1 && (pos == null || (neg === ext ? c < pos : c > pos))) pos = c; } return pos; };\n    const po = pick(rings[0], true), pi = pick(rings[rings.length - 1], false); if (po == null) return;\n    const WT = (q.wt && typeof LAYERS === "function" && LAYERS(q.wt)) || null, LY = WT ? WT.layers.filter(l => !(l[2] === "n")) : [], t = q.t || (LY.length ? LY.reduce((s, l) => s + l[1], 0) : 100), s = neg ? -1 : 1;\n    const R = (u0, u1, c0, c1) => (H ? [[u0, c0], [u1, c0], [u1, c1], [u0, c1]] : [[c0, u0], [c0, u1], [c1, u1], [c1, u0]]);\n    el("polygon", { points: ps(R(q.a, q.b, po, po + s * t)), fill: "#fff", stroke: C.ink, "stroke-width": 16 * WL("outer") }, g);\n    let acc = 0; LY.slice(0, -1).forEach(l => { acc += l[1]; if (acc < t) el("polygon", { points: ps(R(q.a, q.b, po + s * acc, po + s * acc)), fill: "none", stroke: C.line, "stroke-width": 9 * WL("outer") }, g); });\n    el("line", { x1: H ? q.a : po, y1: H ? po : q.a, x2: H ? q.b : po, y2: H ? po : q.b, stroke: "#fff", "stroke-width": 20 }, g);   // sabiezinājums saplūst ar esošo sienu\n    if (q.inHex && pi != null) { const pj = pi + (neg ? -35 : 35); el("line", { x1: H ? q.a : pj, y1: H ? pj : q.a, x2: H ? q.b : pj, y2: H ? pj : q.b, stroke: q.inHex, "stroke-width": 70, "stroke-linecap": "butt" }, g); }\n    if (q.endHex) [q.a, q.b].forEach(u => { const c0 = po, c1 = po + s * t; el("line", { x1: H ? u : c0, y1: H ? c0 : u, x2: H ? u : c1, y2: H ? c1 : u, stroke: q.endHex, "stroke-width": 70 }, g); });\n  });\n'),
        # [MM] fasādes dēļu virziens (projekts.apdare_orient = "h": horizontāli): visa dēļu tekstūra (fasādes, materiālu paraugs) pagriezta par 90°
        ('for (let x = x0; x < x1; x += TS) for (let y = y0; y < y1; y += TS) el("use", { href: "#cladTex", x, y }, g);',
         'const HZ = window.AR && AR.projekts && AR.projekts.apdare_orient === "h";\n  for (let x = x0; x < x1; x += TS) for (let y = y0; y < y1; y += TS) el("use", Object.assign({ href: "#cladTex", x, y }, HZ ? { transform: `rotate(90 ${x + TS / 2} ${y + TS / 2})` } : {}), g);'),
        # [MM] fascijas dēļa tonis atsevišķi (projekts.fascia_side / fascia_hex), pēc noklusējuma tāds pats kā jumta pārkare
        ('P(span / 2, ridgeTop - vt)].join(" "), fill: FAS ? "#F2F0EA" : "#4a5055"',
         'P(span / 2, ridgeTop - vt)].join(" "), fill: FAS ? mmFasHex(side, "#F2F0EA") : "#4a5055"'),   # metāla vējmala vienmēr jumta tonī; tonis maināms tikai baltajam fascijas dēlim (sarkanais)
        # [MM] gala pārkares dēlis (spāres gals ar tekstūru) = fascijas dēlis: atsevišķs tonis, noklusēti kā pārkare; augstumu izdod redaktoram
        ('const fill = (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54";\n',
         'const FSH = mmFasHex(side, null), fill = FSH || (window.AR && AR.projekts && AR.projekts.tonis_sw) || "#4a4f54"; ((window.__FDF = window.__FDF || {})[side] = (window.__FDF || {})[side] || {}).govT = tPV;\n'),
        ('const tg = el("g", { transform: `rotate(${ang})` }, el("g", { "clip-path": `url(#${cid})` }, g));',
         'const tg = el("g", { transform: `rotate(${ang})` }, el("g", Object.assign({ "clip-path": `url(#${cid})` }, FSH ? { filter: `url(#${mmTint(g, FSH)})` } : {}), g));'),
        ('height: thV - 70, fill: "#F2F0EA"', 'height: thV - 70, fill: mmFasHex(side, "#F2F0EA")'),
        # [MM] loga rāmja un aplodu tonis atsevišķam logam (model.windows[i].col / .cascol), citādi viens visiem logiem
        ('const WINC = () => { const w = (window.AR && window.AR.win) || {}, out = w.colorOut || w.color || "RAL 7016", inn = w.colorIn || out; return { out, inn, cas: w.casingColor || out }; };',
         'const WINC = () => { const w = (window.AR && window.AR.win) || {}, o = window.__WO || {}, g = w.colorOut || w.color || "RAL 7016", out = o.out || g, inn = w.colorIn || out; return { out, inn, cas: o.cas || w.casingColor || g }; };'),
        ('    win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w), cs0, nz ? Math.max(0, Math.min(cs0, u0 - nz[0])) : cs0, nz ? Math.max(0, Math.min(cs0, nz[1] - u1)) : cs0);',
         '    window.__WO = { out: w.col || null, cas: w.cascol || null }; try { win(u0, u1, w.sill ?? 0, w.head ?? 2100, panesOut(v, w), cs0, nz ? Math.max(0, Math.min(cs0, u0 - nz[0])) : cs0, nz ? Math.max(0, Math.min(cs0, nz[1] - u1)) : cs0); } finally { window.__WO = null; }'),
        ('p[0] === a && q[0] === a : p[1] === a && q[1] === a);\n    if (!E.length) return a;\n    const [p, q] = E[0], m = dir === "x" ? (p[1] + q[1]) / 2 : (p[0] + q[0]) / 2;\n    return dir === "x" ? (inside(a + 5, m) ? a + off : a - off) : (inside(m, a + 5) ? a + off : a - off);',
         'Math.abs(p[0] - a) <= 120 && p[0] === q[0] : Math.abs(p[1] - a) <= 120 && p[1] === q[1]);\n    if (!E.length) return a;\n    E.sort(([p], [q]) => Math.abs(p[dir === "x" ? 0 : 1] - a) - Math.abs(q[dir === "x" ? 0 : 1] - a));\n    const [p, q] = E[0], m = dir === "x" ? (p[1] + q[1]) / 2 : (p[0] + q[0]) / 2, e = dir === "x" ? p[0] : p[1];   // [MM] ass tuvu ārsienas malai (±120 mm) tiek pielīdzināta C24 ārmalai\n    return dir === "x" ? (inside(e + 5, m) ? e + off : e - off) : (inside(m, e + 5) ? e + off : e - off);'),
        ('  // a partition meeting the outer wall merges with it: no contour line across the joint, the hatching runs on',
         '  // [MM] starpsienas pagarinājums (v.freeWalls ar f[5] = "i"): tiek zīmēts virs telpu baltā pildījuma, ar šrafējumu un plānu kontūru; pie krustojošās sienas kontūras nav\n  (v.freeWalls || []).filter(f => f[5] === "i").forEach(f => {\n    const [x, y, w, h, o] = f, vv = o === "v", id = `${cid}-fi${Math.round(x)}-${Math.round(y)}`, sw = 8 + 14 * WL("inner");\n    el("rect", { x, y, width: w, height: h, fill: "#fff" }, g);\n    el("rect", { x, y, width: w, height: h }, el("clipPath", { id }, g));\n    el("path", { d: vv ? loops(x, y, 0, 1, 1, 0, h, w) : loops(x, y, 1, 0, 0, 1, w, h), ...INS, "clip-path": `url(#${id})` }, g);\n    const inW = (px, py) => walls.some(o2 => o2[4] !== o && !o2.free_ && px >= o2[0] - 6 && px <= o2[0] + o2[2] + 6 && py >= o2[1] - 6 && py <= o2[1] + o2[3] + 6);\n    const L = vv ? [[[x, y], [x, y + h]], [[x + w, y], [x + w, y + h]]] : [[[x, y], [x + w, y]], [[x, y + h], [x + w, y + h]]];\n    const ends = vv ? [[[x, y], [x + w, y]], [[x, y + h], [x + w, y + h]]] : [[[x, y], [x, y + h]], [[x + w, y], [x + w, y + h]]];\n    L.concat(ends.filter(([a, b]) => !inW((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))).forEach(([a, b]) => el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: C.ink, "stroke-width": sw }, g));\n  });\n  // a partition meeting the outer wall merges with it: no contour line across the joint, the hatching runs on'),
    ]:
        assert a in cad, 'SBE cad.js (mm_extra): nav atrasts ' + a[:60]
        cad = cad.replace(a, b, 1)
    return cad


def build(model_path, langs=None):
    m = json.load(open(model_path, encoding='utf-8'))
    if m.get('kontura'):   # kontūra no blokiem un robiem → poly, recess (fasāžu ieliekumi)
        import kontura
        err = kontura.apply(m)
        if err:
            print('BRĪDINĀJUMS: kontūra:', err)
    cfg = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))
    j = m.get('jumts', {})
    cfg['roof'].update({k: j[k] for k in ('pitch', 'ov', 'eave') if k in j})
    if j.get('forma') in ('vienslipa', 'parapets'):   # vienslīpu jumts / plakans ar parapetu
        import math
        par = j.get('forma') == 'parapets'
        fall = j.get('krit') if j.get('krit') in ('north', 'south', 'east', 'west') else 'south'
        run = m['D'] if fall in ('north', 'south') else m['W']
        lo = round(j.get('h_zema') or j.get('eave') or 2600); hi = round(j.get('h_augsta') or lo + (500 if par else 900))
        dz = float(j.get('dz') if j.get('dz') is not None else 300)
        sl = round(math.degrees(math.atan(max(0, hi - dz - lo) / run)), 3)
        mono = {'fall': fall, 'lo': lo, 'hi': hi}
        if par: mono.update(par=True, dz=dz)
        cfg['roof'].update(mono=mono, eave=lo, hip=0, pitch=sl if par else round(math.degrees(math.atan((hi - lo) / run)), 3))
        if par: cfg['roof']['ov'] = 0
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
    AXH = 'function padRects(v) {   // [MM] wallPad → taisnstūri [x, y, w, h, o] fasādēm\n  return (v.wallPad || []).map(q => { const L = q.b - q.a; return q.side === "west" ? [-q.t, q.a, q.t, L, "v"] : q.side === "east" ? [v.W, q.a, q.t, L, "v"] : q.side === "north" ? [q.a, -q.t, L, q.t, "h"] : [q.a, v.D, L, q.t, "h"]; });\n}\nfunction axOffs(v, opt) {   // [MM] asu galu attālums katrā pusē: pēc noklusējuma ārpus mērķēdēm un ārtelpām (lieveņa, terases), v.axOff to pārraksta\n  const base = opt.axOff || 3150, pts = [].concat((v.porch ? [v.porch.poly] : []), (v.terraces || []).map(t => t.poly)).flat();\n  const ex = { n: Math.max(0, ...pts.map(q => -q[1])), s: Math.max(0, ...pts.map(q => q[1] - v.D)), w: Math.max(0, ...pts.map(q => -q[0])), e: Math.max(0, ...pts.map(q => q[0] - v.W)) };\n  const r = {}; ["n", "s", "w", "e"].forEach(k => { r[k] = (v.axOff && v.axOff[k] != null) ? v.axOff[k] : base + (ex[k] > 0 ? ex[k] + 400 : 0); });\n  return r;\n}\nfunction terFix(t) {   // [MM] lietotāja terase: kopija ar stūru statņiem (t.corners), ja nav norādīti\n  const xs = t.poly.map(q => q[0]), ys = t.poly.map(q => q[1]), cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2, sz = 300;\n  const posts = t.posts || (t.corners ? t.poly.map(q => [q[0] > cx ? q[0] - sz : q[0], q[1] > cy ? q[1] - sz : q[1], sz]) : []);\n  return Object.assign({}, t, { __ter: 1, posts });\n}\nfunction terPat(g, pc, x0, y0) {   // [MM] terases tekstūra (augšupielādēta), pagriežama: tekstūras platums texW mm\n  const id = "tp" + Math.random().toString(36).slice(2, 7), w = pc.texW || 1000, h = pc.texH || w;\n  const pat = el("pattern", { id, patternUnits: "userSpaceOnUse", width: w, height: h, patternTransform: `rotate(${pc.texRot || 0}) translate(${x0 || 0} ${y0 || 0})` }, g);\n  el("image", { href: pc.tex, width: w, height: h, preserveAspectRatio: "none" }, pat);\n  return id;\n}\nfunction postVisible(v, side, q) {   // [MM] brīvais stabs fasādē redzams tikai, ja māja to neaizsedz (stabi otrā mājas pusē nerādās)\n  const X = side === "west" || side === "east", pos = side === "south" || side === "east", c = X ? q.y + q.d / 2 : q.x + q.w / 2, front = X ? (pos ? q.x + q.w : q.x) : (pos ? q.y + q.d : q.y), P = v.poly;\n  let ext = null;\n  for (let i = 0; i < P.length; i++) { const A = P[i], B = P[(i + 1) % P.length], u0 = X ? A[1] : A[0], u1 = X ? B[1] : B[0], w0 = X ? A[0] : A[1], w1 = X ? B[0] : B[1];\n    if ((u0 - c) * (u1 - c) > 0 || u0 === u1) continue; const w = w0 + (w1 - w0) * (c - u0) / (u1 - u0); ext = ext == null ? w : (pos ? Math.max(ext, w) : Math.min(ext, w)); }\n  for (const f of (v.freeWalls || []).filter(f_ => f_[5] !== \"i\")) { const fu0 = X ? f[1] : f[0], fu1 = X ? f[1] + f[3] : f[0] + f[2], ff = X ? (pos ? f[0] + f[2] : f[0]) : (pos ? f[1] + f[3] : f[1]); if (c > fu0 && c < fu1 && (pos ? ff > front + 50 : ff < front - 50)) return false; }   // izbīdītā siena priekšā aizsedz stabu\n  return ext == null || (pos ? front >= ext - 50 : front <= ext + 50);\n}\nfunction terEdge(pc, side, v) {   // [MM] terases redzamā mala fasādē: tikai ja iziet aiz fasādes līnijas\n  const xs = pc.poly.map(q => q[0]), ys = pc.poly.map(q => q[1]), a = Math.min(...xs), b = Math.max(...xs), c = Math.min(...ys), d = Math.max(...ys);\n  const bx = b <= 1 || a >= v.W - 1, by = d <= 1 || c >= v.D - 1;   // terase blakus mājai: no sāniem redzama kā dēļu plātne\n  if ((side === "north" || side === "south") && bx) return [[a, c], [b, c]];\n  if ((side === "west" || side === "east") && by) return [[a, c], [b, c]];\n  // [MM] mala redzama tur, kur māja (ieliekumos, nišās) ir tālāk par terases malu: paraugs gar malu pret mājas kontūru\n  const X = side === "west" || side === "east", pos = side === "south" || side === "east", lo = X ? c : a, hi = X ? d : b, edge = side === "south" ? d : side === "north" ? c : side === "east" ? b : a, P = v.poly;\n  let m0 = null, m1 = null;\n  for (let u = lo; u <= hi + 0.5; u += Math.max(20, (hi - lo) / 400)) {\n    let ext = null;\n    for (let i = 0; i < P.length; i++) { const A = P[i], B = P[(i + 1) % P.length], u0 = X ? A[1] : A[0], u1 = X ? B[1] : B[0], w0 = X ? A[0] : A[1], w1 = X ? B[0] : B[1];\n      if ((u0 - u) * (u1 - u) > 0 || u0 === u1) continue; const w = w0 + (w1 - w0) * (u - u0) / (u1 - u0); ext = ext == null ? w : (pos ? Math.max(ext, w) : Math.min(ext, w)); }\n    if (ext == null || (pos ? edge > ext + 50 : edge < ext - 50)) { if (m0 == null) m0 = u; m1 = u; }\n  }\n  if (m0 == null) return [];\n  return X ? [[edge, m0], [edge, m1]] : [[m0, edge], [m1, edge]];\n}\n'
    cad = cad.replace('function cadPlan(parent, v, opt = {}) {', AXH + 'function cadPlan(parent, v, opt = {}) {', 1)
    # [MM] faktiskais ārsienas biezums pēc telpu malām (ja tas nedaudz mazāks par slāņu summu T): logu rāmja līnijas neiziet telpā
    try:
        _rr = [q for rm_ in m.get('rooms', []) for q in rm_.get('r', [])]
        if _rr:
            _tg = min(min(q[0] for q in _rr), min(q[1] for q in _rr), m['W'] - max(q[0] + q[2] for q in _rr), m['D'] - max(q[1] + q[3] for q in _rr))
            if T - 40 < _tg < T - 1:
                cad = cad.replace('function cadPlan(parent, v, opt = {}) {', 'window.__TGEO = %s;\nfunction cadPlan(parent, v, opt = {}) {' % _tg, 1)
    except Exception:
        pass
    # [MM] stabu materiāls fasādēs: krāsa vai tekstūra (q.col / q.tex), citādi lamellu koks
    cad = cad.replace('postsU.forEach(([u, s]) => {', 'postsU.forEach(([u, s, pq]) => {', 1)
    # [MM] margas: kopīgie parametri (plāns, fasāde, griezums): redeles bal × balD, sprauga gap, lenteris railW × railH, apakšas atzīme z0
    RAIL_JS = r"""// [MM] margas: parametri un redeļu punkti
function mmRailBase(v, r) { return r.z0 != null ? +r.z0 : r.lv === "loft" ? (v.loftLevel || v.level || ((v.ceiling || 2200) + 164.5)) : 0; }
function mmRailBals(r) {
  const bal = +r.bal || 45, gap = r.gap != null ? +r.gap : 50, P = r.pts || [], out = [];
  P.forEach((a, j) => { const c = P[j + 1]; if (!c) return; const dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy), n = Math.max(1, Math.round(L / (bal + gap))), ang = Math.atan2(dy, dx);
    for (let i = j ? 1 : 0; i <= n; i++) out.push([a[0] + dx * i / n, a[1] + dy * i / n, ang]); });
  return out;
}
function mmRailTop(v, r, x, y) { return Math.min(mmRailBase(v, r) + (r.h != null ? +r.h : 1000), ROOF.eave + Math.max(0, Math.min(y, v.D - y)) * tan - 5); }
"""
    cad = cad.replace('const ROOF = { ov: 600,', RAIL_JS + 'const ROOF = { ov: 600,', 1)
    ELEV_RAIL = r"""  (v.railings || []).forEach(r => {   // [MM] margas fasādē: ārpus mājas pēc noklusējuma vai r.fas = true
    const P0 = r.pts || []; if (P0.length < 2) return;
    const cx = P0.reduce((a, q) => a + q[0], 0) / P0.length, cy = P0.reduce((a, q) => a + q[1], 0) / P0.length, outside = cx < 0 || cx > v.W || cy < 0 || cy > v.D;
    if (!(r.fas != null ? r.fas : outside)) return;
    if (!({ south: cy >= v.D / 2, north: cy <= v.D / 2, east: cx >= v.W / 2, west: cx <= v.W / 2 })[side]) return;
    const bal = +r.bal || 45, bd = +r.balD || bal, rw = +r.railH || 40, z0 = mmRailBase(v, r), U = (x, y) => map(endV ? y : x), rg = el("g", { "data-rail": 1 }, g);
    P0.forEach((a, j) => { const c = P0[j + 1]; if (!c || r.rail === false) return; const L = Math.hypot(c[0] - a[0], c[1] - a[1]), st = Math.max(1, Math.ceil(L / 300));
      for (let q = 0; q < st; q++) { const x0 = a[0] + (c[0] - a[0]) * q / st, y0 = a[1] + (c[1] - a[1]) * q / st, x1 = a[0] + (c[0] - a[0]) * (q + 1) / st, y1 = a[1] + (c[1] - a[1]) * (q + 1) / st, tp = Math.min(mmRailTop(v, r, x0, y0), mmRailTop(v, r, x1, y1)); if (tp - z0 < 60) continue;
        const u0 = U(x0, y0), u1 = U(x1, y1); el("rect", { x: Math.min(u0, u1), y: -tp, width: Math.abs(u1 - u0) + 1, height: rw, fill: "#cfc8bc", stroke: C.ink, "stroke-width": 3 }, rg); } });
    mmRailBals(r).forEach(([x, y, ang]) => { const top = mmRailTop(v, r, x, y); if (top - z0 < 30) return; const th = endV ? ang - Math.PI / 2 : ang, w = bal * Math.abs(Math.cos(th)) + bd * Math.abs(Math.sin(th)), u = U(x, y);
      el("rect", { x: u - w / 2, y: -top, width: w, height: top - z0, fill: "#cfc8bc", stroke: C.ink, "stroke-width": 3 }, rg); });
  });
"""
    cad = cad.replace('postsU.forEach(([u, s, pq]) => {', ELEV_RAIL + 'postsU.forEach(([u, s, pq]) => {', 1)
    SEC_RAIL = r"""  (v.railings || []).forEach(r => {   // [MM] margas griezumā: pārgrieztie stabiņi melni, tālākie ar kontūru
    const P0 = r.pts || []; if (P0.length < 2) return;
    const bal = +r.bal || 45, bd = +r.balD || bal, rh = +r.railH || 40, z0 = mmRailBase(v, r), dist = (x, y) => (s.o === "v" ? x : y) - s.at, U = (x, y) => (s.o === "v" ? y : x), rg = el("g", { "data-rail": 1 }, g);
    if (r.rail !== false) P0.forEach((a, j) => { const c = P0[j + 1]; if (!c) return; const L = Math.hypot(c[0] - a[0], c[1] - a[1]), st = Math.max(1, Math.ceil(L / 300));
      for (let q = 0; q < st; q++) { const x0 = a[0] + (c[0] - a[0]) * q / st, y0 = a[1] + (c[1] - a[1]) * q / st, x1 = a[0] + (c[0] - a[0]) * (q + 1) / st, y1 = a[1] + (c[1] - a[1]) * (q + 1) / st;
        if (dist(x0, y0) * s.look < -1 && dist(x1, y1) * s.look < -1) continue; const tp = Math.min(mmRailTop(v, r, x0, y0), mmRailTop(v, r, x1, y1)); if (tp - z0 < 60) continue;
        const u0 = U(x0, y0), u1 = U(x1, y1); el("rect", { x: Math.min(u0, u1), y: -tp, width: Math.abs(u1 - u0) + 1, height: rh, fill: "#fff", stroke: C.ink, "stroke-width": 4 }, rg); } });
    mmRailBals(r).forEach(([x, y, ang]) => { const d = dist(x, y), top = mmRailTop(v, r, x, y); if (top - z0 < 30) return; const cutD = Math.abs(d) <= (s.o === "v" ? Math.abs(Math.cos(ang)) * bd + Math.abs(Math.sin(ang)) * bal : Math.abs(Math.sin(ang)) * bd + Math.abs(Math.cos(ang)) * bal) / 2 + 2;
      if (!cutD && d * s.look < 0) return; const th = s.o === "v" ? ang - Math.PI / 2 : ang, w = bal * Math.abs(Math.cos(th)) + bd * Math.abs(Math.sin(th)), u = U(x, y);
      el("rect", { x: u - w / 2, y: -top, width: w, height: top - z0, fill: cutD ? C.ink : "#fff", stroke: C.ink, "stroke-width": 4 }, rg); });
  });
"""
    ar = ar.replace('  // axes under the section\n  const ax = s.o === "v" ? v.axes.y : v.axes.x;', SEC_RAIL + '  // axes under the section\n  const ax = s.o === "v" ? v.axes.y : v.axes.x;', 1)
    # MM labojumi SBE plānam: īsākas asis (axOff), plāns bez izmēriem (noDims), telpa bez zīmes (void)
    for a, b in [('el("line", { x1: x, y1: -3150, x2: x, y2: v.D + 3150, ...dash }, ag);\n      bub(x, -3450, n); bub(x, v.D + 3450, n);',
                  'const AX = axOffs(v, opt); const onW = true; if (onW) { el("line", { x1: x, y1: -AX.n, x2: x, y2: -30, ...dash }, ag); el("line", { x1: x, y1: v.D + 30, x2: x, y2: v.D + AX.s, ...dash }, ag); } else el("line", { x1: x, y1: -AX.n, x2: x, y2: v.D + AX.s, ...dash }, ag);\n      bub(x, -AX.n - 300, n); bub(x, v.D + AX.s + 300, n);'),
                 ('el("line", { x1: -3150, y1: y, x2: v.W + (longPlan ? 1600 : 3150), y2: y, ...dash }, ag);\n      bub(-3450, y, n); bub(v.W + (longPlan ? 1900 : 3450), y, n);',
                  'const AX = axOffs(v, opt); const onW = true, XE = v.W + (longPlan ? 1600 : AX.e); if (onW) { el("line", { x1: -AX.w, y1: y, x2: -30, y2: y, ...dash }, ag); el("line", { x1: v.W + 30, y1: y, x2: XE, y2: y, ...dash }, ag); } else el("line", { x1: -AX.w, y1: y, x2: XE, y2: y, ...dash }, ag);\n      bub(-AX.w - 300, y, n); bub(v.W + (longPlan ? 1900 : AX.e + 300), y, n);'),
                 ('lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(0)', 'lvlMark(g, ...(v.levelAt || [7750, 8250]), lv(v.level || 0)'),
                 ('  const dg = el("g", {}, g);', '  const dg = el("g", opt.noDims ? { display: "none" } : {}, g);'),
                 ('    stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,', '    if (!rm.void) stamp(g, cx, cy, FULL[rm.n] || rm.n, i + 1,'),
                 ('  v.rooms.forEach((rm, i) => {\n    const big = rm.r.reduce((a, b) => (b[2] * b[3] > a[2] * a[3] ? b : a));', '  if (v.level) v.rooms.filter(rm => !rm.void).forEach(rm => {   // [MM] mansarda telpas kontūra melna līnija: redzams, kur panelis beidzas\n    const xs = [...new Set(rm.r.flatMap(q => [q[0], q[0] + q[2]]))].sort((a, b) => a - b), ys = [...new Set(rm.r.flatMap(q => [q[1], q[1] + q[3]]))].sort((a, b) => a - b);\n    const ins = (i, j) => i >= 0 && j >= 0 && i < xs.length - 1 && j < ys.length - 1 && rm.r.some(q => xs[i] >= q[0] - .5 && xs[i + 1] <= q[0] + q[2] + .5 && ys[j] >= q[1] - .5 && ys[j + 1] <= q[1] + q[3] + .5);\n    const seg = (x1, y1, x2, y2) => el("line", { x1, y1, x2, y2, stroke: C.ink, "stroke-width": 12, "stroke-linecap": "square" }, g);\n    for (let i = 0; i < xs.length - 1; i++) for (let j = 0; j < ys.length - 1; j++) { if (!ins(i, j)) continue;\n      if (!ins(i, j - 1)) seg(xs[i], ys[j], xs[i + 1], ys[j]);\n      if (!ins(i, j + 1)) seg(xs[i], ys[j + 1], xs[i + 1], ys[j + 1]);\n      if (!ins(i - 1, j)) seg(xs[i], ys[j], xs[i], ys[j + 1]);\n      if (!ins(i + 1, j)) seg(xs[i + 1], ys[j], xs[i + 1], ys[j + 1]); } });\n  (v.railings || []).filter(r => (r.lv || "main") === (v.level ? "loft" : "main")).forEach(r => {   // [MM] margas plānā: redeles bal × balD, sprauga, lenteris railW\n    const bal = +r.bal || 45, bd = +r.balD || bal, P = r.pts || [];\n    if (r.rail !== false) el("polyline", { points: P.map(q => q.join(",")).join(" "), fill: "none", stroke: C.ink, "stroke-opacity": .35, "stroke-width": +r.railW || 60, "stroke-linejoin": "round", "data-rail": 1 }, g);\n    mmRailBals(r).forEach(([x, y, ang]) => el("rect", { x: x - bal / 2, y: y - bd / 2, width: bal, height: bd, fill: "#fff", stroke: C.ink, "stroke-width": 4, transform: `rotate(${ang * 180 / Math.PI} ${x} ${y})` }, g));\n  });\n  v.rooms.forEach((rm, i) => {\n    const big = rm.r.reduce((a, b) => (b[2] * b[3] > a[2] * a[3] ? b : a));'),
                 # stabveida pamati: metāla cokols RAL 9005 no grīdas apakšas līdz 40 mm virs zemes, ēnas sprauga zem tā
                 ('  } else el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "#9b9c98", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  } else if ((window.AR && AR.projekts && AR.projekts.pamati) === "platne") el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: (AR.projekts.cokols_plate_hex || "#9b9c98"), stroke: C.ink, "stroke-width": 14 }, g);\n  else { el("rect", { x: 0, y: 0, width: span, height: ROOF.plinth, fill: "rgba(0,0,0,.25)" }, g); el("rect", { x: -20, y: 0, width: span + 40, height: ROOF.plinth - 40, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g); el("line", { x1: -20, y1: 22, x2: span + 20, y2: 22, stroke: "rgba(255,255,255,.18)", "stroke-width": 8 }, g); }'),
                 # stūru dēļi (sarkanais tonis): balti, 90 mm, no grīdas apakšas līdz dzegai
                 ('  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);',
                  '  el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);\n  { const CB = (window.AR && AR.projekts && AR.projekts.sturi) || 0, zt = u => (gable ? roofTopW + (ridgeTop - roofTopW) * Math.min(u, span - u) / (span / 2) : (FAS ? eEdge : eEdge + thV - 20)); if (CB) [0, span - CB].forEach(u => { el("polygon", { points: [P(u, -fT), P(u + CB, -fT), P(u + CB, zt(u + CB)), P(u, zt(u))].join(" "), fill: (AR.projekts.sturi_hex || "#F2F0EA"), stroke: C.ink, "stroke-width": 6 }, g); const lx = u + (u ? 12 : CB - 12); el("line", { x1: lx, y1: -zt(lx) + 10, x2: lx, y2: fT - 10, stroke: "rgba(0,0,0,.18)", "stroke-width": 6 }, g); }); }   // [MM] gala fasādē stūra dēļi līdz vējmalai (pa jumta slīpumu)'),
                 ('  // recessed parts of the facade: v.recess[side] = [[u0, u1, depth mm]]; default: porch between the wings on the south',
                  '  // brīvās sienas (redaktora gala pagarinājums): redzamas arī fasādēs ar kontūru kā plānā; pakaļējās (aiz mājas) neredz\n  (v.freeWalls || []).filter(f => f[5] !== "i").concat(padRects(v)).forEach(f => {   // [MM] sienas posma sabiezinājums (wallPad) fasādēs kā izvilkta siena\n    const xs = [f[0], f[0] + f[2]], ys = [f[1], f[1] + f[3]], U = endV ? ys.map(map) : xs.map(map), u0 = Math.min(...U), u1 = Math.max(...U);\n    const front = side === "south" ? ys[1] > v.D / 2 : side === "north" ? ys[0] < v.D / 2 : side === "east" ? xs[1] > v.W / 2 : xs[0] < v.W / 2;\n    (front ? [[u0, u1]] : [[u0, Math.min(u1, 0)], [Math.max(u0, span), u1]]).forEach(([a0, a1]) => {   // aiz mājas paslēptā daļa nezīmējas\n      if (a1 - a0 < 20) return;\n      const ft = el("g", { "data-fw": 1, "data-u0": a0, "data-u1": a1, "data-side": side }, g), RLf = (typeof LAYERS === "function" && LAYERS("J1") && LAYERS("J1").layers) || [], kif = RLf.findIndex(l => l[2] === "i"), tPf = ((kif >= 0 ? RLf.slice(0, kif + 1).reduce((s_, l) => s_ + l[1], 0) : ROOF.th) + 20) / Math.cos(ROOF.pitch * Math.PI / 180), zf = u => Math.max(fT + 100, (gable ? eEdge + (Math.min(u, span - u) + (u < span / 2 ? OVL : OVR)) * tan : eEdge) + thV - tPf + 12), zA = zf(a0), zB = zf(a1), zt = Math.max(zA, zB), cid = "fw-" + Math.random().toString(36).slice(2, 7), fp = [[a0, fT], [a0, -zA], [a1, -zB], [a1, fT]].map(q => q.join(",")).join(" ");   // [MM] izvilktās sienas augša tiek apgriezta pa jumta pārkares apakšējo plakni\n      el("polygon", { points: fp }, el("clipPath", { id: cid }, ft));\n      const twf = ((((window.AR || {}).projekts || {}).fasade_wall || {})[side] || []).filter(q_ => q_.u0 <= a0 + 2 && q_.u1 >= a1 - 2).sort((x_, y_) => (x_.u1 - x_.u0) - (y_.u1 - y_.u0))[0], cgf = el("g", Object.assign({ "clip-path": `url(#${cid})` }, twf && twf.hex ? { filter: `url(#${mmTint(g, twf.hex)})` } : {}), ft);   // [MM] izvilktās sienas plaknes tonis (fasade_wall)\n      boards(cgf, a0, a1, -zt, fT);\n      el("polygon", { points: fp, fill: "none", stroke: C.ink, "stroke-width": 10, "data-keep": 1 }, ft);\n      el("rect", { x: a0 - 20, y: fT, width: a1 - a0 + 40, height: ROOF.plinth - 40 - fT, fill: "#3a3f43", stroke: C.ink, "stroke-width": 10 }, ft);\n    });\n  });\n' + '  // recessed parts of the facade: v.recess[side] = [[u0, u1, depth mm]]; default: porch between the wings on the south'),
                 # brīvo (izvilkto) ārsienu kontūra plānā: garās malas un brīvais gals ar ārsienas līniju, savienojums ar māju bez līnijas
                 ('    }); }\n}\n// wall sample for the legend, drawn in model mm (scale it outside)',
                  '    }); }\n  (v.freeWalls || []).filter(f => f[5] !== "i").forEach(f => {   // [MM] izvilktās ārsienas kontūra (starpsienas pagarinājumam f[5] = "i" nav)\n    const [x, y, w, h, o] = f, X = o === "h", e0 = X ? x : y, e1 = X ? x + w : y + h, c0 = X ? y : x, c1 = X ? y + h : x + w, sp = X ? [y, y + h] : [x, x + w];\n    const touch = e => poly.some((a, i) => { const b = poly[(i + 1) % poly.length]; return X ? (a[0] === b[0] && Math.abs(a[0] - e) < 3 && Math.min(a[1], b[1]) <= y + 5 && Math.max(a[1], b[1]) >= y + h - 5) : (a[1] === b[1] && Math.abs(a[1] - e) < 3 && Math.min(a[0], b[0]) <= x + 5 && Math.max(a[0], b[0]) >= x + w - 5); });\n    const P = (u, k) => X ? [u, k] : [k, u], free = [e0, e1].filter(e => !touch(e)), st = { fill: "none", stroke: C.ink, "stroke-width": 16 * WL("outer") };\n    el("polyline", { points: [P(e0, c0), P(e1, c0)].map(q => q.join(",")).join(" "), ...st }, g); el("polyline", { points: [P(e0, c1), P(e1, c1)].map(q => q.join(",")).join(" "), ...st }, g);\n    free.forEach(e => el("polyline", { points: [P(e, c0), P(e, c1)].map(q => q.join(",")).join(" "), ...st }, g));\n  });\n}\n// wall sample for the legend, drawn in model mm (scale it outside)'),
                 # zonu (telpu) uzraksti: viens fonts un viens teksta izmērs visām telpām, mērogs iestatījumos (projekts.zonu_mers)
                 ('(v.stampScale && v.stampScale[i]) || (rm.small ? .78 : 1));',
                  '(window.AR && AR.projekts && +AR.projekts.zonu_mers) || .7);'),
                 # stabveida pamatu cokols RAL 9005
                 ('    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: "#3a3f43", stroke: C.ink, "stroke-width": 10 }, g);',
                  '    el("rect", { x: -20, y: fT, width: span + 40, height: ROOF.plinth - 40 - fT, fill: (AR.projekts.cokols_hex || "#1d1d1d"), stroke: C.ink, "stroke-width": 10 }, g);'),
                 # logu (palodzes, augšas) augstuma atzīmes visās fasādēs; gala fasādēm arī ±0,000
                 ('    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }',
                  '    lvl(-ROOF.plinth, lv(-ROOF.plinth));\n  }\n  { const top = MN && MN.role === "prof" ? MN.lo : gable ? ROOF.eave : eEdge, zs = [];\n    (v.windows || []).filter(w => w.side === side).forEach(w => { if (w.sill > 0) zs.push(w.sill); zs.push(w.head); });\n    (v.doors || []).filter(d => d.entry && side === "south").forEach(() => zs.push(2100));\n    if (!opt.levels) lvl(0, lv(0));\n    if (MN && MN.role === "prof" && !opt.levels) { lvl(Math.round(MN.hi), lv(Math.round(MN.hi))); lvl(Math.round(MN.lo), lv(Math.round(MN.lo))); }\n    let last = 0; [...new Set(zs)].sort((a, b) => a - b).forEach(z => { if (z - last >= 300 && top - z >= 300) { lvl(z, lv(z)); last = z; } }); }'),
                 # zemes līnija: īsāka garām mājām (opt.ground), lai garā fasāde neuzbrauc gala fasādes atzīmēm
                 ('for (let x = -1400; x < span + 1400 - 260; x += 200)', 'const GX = opt.ground || 1600; for (let x = -(GX - 200) - (opt.gl || 0); x < span + GX - 200 - 260 + (opt.gr || 0); x += 200)'),
                 ('el("line", { x1: -1600, y1: ROOF.plinth, x2: span + 1600, y2: ROOF.plinth,', 'el("line", { x1: -(opt.ground || 1600) - (opt.gl || 0), y1: ROOF.plinth, x2: span + (opt.ground || 1600) + (opt.gr || 0), y2: ROOF.plinth,'),
                 # klienta lapā grīdas apakšas atzīmi nerāda (uzbrauc ±0,000)
                 ('    if (fT) lvl(-fT, lv(-fT), 1);\n', ''),
                 # bez jumta pārkares nav ēnas zem dzegas
                 ('  if (LP || (MN && (MN.role === "prof" || MN.par))) { /* slīpa jumta mala, ēna nav vajadzīga */ } else if (!gable) el("rect", { x: 0, y: -eEdge, width: span, height: 420, fill: "url(#eaveShadow)" }, g);\n  else el(',
                  '  if (LP || (MN && (MN.role === "prof" || MN.par))) { /* slīpa jumta mala, ēna nav vajadzīga */ } else if (ROOF.ov > 0 && !gable) el("rect", { x: 0, y: -eEdge, width: span, height: 420, fill: "url(#eaveShadow)" }, g);\n  else if (ROOF.ov > 0) el('),
                 # notekcaurule garajā fasādē: taisns gals 300 mm virs zemes (izplūde pret skatītāju), bez līkuma
                 ('      el("rect", { x: u - 40, y: -(eEdge + thV - 240), width: 80, height: eEdge + thV - 240 + 150, fill: GUT, stroke: C.ink, "stroke-width": 9 }, g);\n      el("path", { d: `M ${u - 50} ${150} q 0 110 110 110 h 60 v -100 h -70 z`, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);',
                  '      el("rect", { x: u - 50, y: -(eEdge + thV - 240), width: 100, height: eEdge + thV - 240 + ROOF.plinth - 50, fill: GUT, stroke: C.ink, "stroke-width": 9 }, g);\n      el("line", { x1: u - 22, y1: -(eEdge + thV - 260), x2: u - 22, y2: ROOF.plinth - 70, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);'),
                 # notekcaurule gala fasādē: Ø100 caurule ar kontūru, taisns gals 300 mm virs zemes
                 ('      const d = `M ${uc} ${-(zt - 40)} L ${uc} ${-(zt - 260)} L ${uw} ${-(zt - 700)} L ${uw} ${150}`;\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 98, "stroke-linejoin": "round" }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 80, "stroke-linejoin": "round" }, g);',
                  '      const zEnd = 50 - ROOF.plinth, d = `M ${uc} ${-(zt - 40)} L ${uc} ${-zEnd}`;\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);')]:
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
        # [MM] ārdurvis (entry) mēru ķēdē visās četrās pusēs (nevis tikai dienvidos): attālums no ārsienas līdz durvīm
        ('  const S = opt.axes ? 1 : 0, E = opt.tags ? 300 : 0;',
         '  const ent = sd => v.entryInChain ? v.doors.filter(d => d.entry && (d.o === "h" ? (d.y < v.D / 2 ? "north" : "south") : (d.x < v.W / 2 ? "west" : "east")) === sd).flatMap(d => d.o === "h" ? [d.x, d.x + d.w] : [d.y, d.y + d.w]) : [];\n  const S = opt.axes ? 1 : 0, E = opt.tags ? 300 : 0;'),
        ('winSide(v, w) === "north", w => w.x)], [0, v.W, ...at(1, 0)]', 'winSide(v, w) === "north", w => w.x), ...ent("north")], [0, v.W, ...at(1, 0)]'),
        ('winSide(v, w) === "west", w => w.y)], [0, v.D, ...at(0, 0)]', 'winSide(v, w) === "west", w => w.y), ...ent("west")], [0, v.D, ...at(0, 0)]'),
        ('winSide(v, w) === "east", w => w.y)], [0, v.D, ...at(0, v.W)]', 'winSide(v, w) === "east", w => w.y), ...ent("east")], [0, v.D, ...at(0, v.W)]'),
        ('  const entryX = v.entryInChain ? v.doors.filter(d => d.entry).flatMap(d => [d.x, d.x + d.w]) : [];', '  const entryX = ent("south");'),
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
        ('  const GUT = "#2f3438";\n  if (LP || (MN && MN.role !== "low")) { /* tekne zemajā pusē; augstajā pusē tās nav, profilā zīmēta kopā ar jumtu */ } else if (!gable) {', '  const GUT = "#2f3438", NOT = s => !(window.AR && AR.projekts && AR.projekts.notekas && AR.projekts.notekas[s] === false);\n  const PIPE = u => side[0] + (side === "north" ? (u < span / 2 ? "e" : "w") : (u < span / 2 ? "w" : "e"));\n  if (LP || (MN && MN.role !== "low")) { /* tekne zemajā pusē; augstajā pusē tās nav, profilā zīmēta kopā ar jumtu */ } else if (!gable && NOT(side)) {'),
        ('  } else {\n    [-1, 1].forEach(sd => {\n      // half-round gutter', '  } else if (gable) {\n    [-1, 1].forEach(sd => {\n      if (!NOT(side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"))) return;\n      // half-round gutter'),
        # [MM] katru noteku un katru notekcauruli var noņemt atsevišķi (projekts.notekas: north/south = noteka, nw/ne/sw/se = caurule stūrī)
        ('else if (!gable && NOT(side)) {\n    const gz = eEdge + thV - 120;\n    el("rect", { x: -ROOF.ov - 40, y: -gz, width: span + 2 * ROOF.ov + 80, height: 120, rx: 40, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);\n    el("line", { x1: -ROOF.ov - 25, y1: -gz + 18, x2: span + ROOF.ov + 25, y2: -gz + 18, stroke: "rgba(255,255,255,.28)", "stroke-width": 7 }, g);\n    [180, span - 180].forEach(u => {',
         'else if (!gable) {\n    const gz = eEdge + thV - 120;\n    if (NOT(side)) {\n    el("rect", { x: -ROOF.ov - 40, y: -gz, width: span + 2 * ROOF.ov + 80, height: 120, rx: 40, fill: GUT, stroke: C.ink, "stroke-width": 10 }, g);\n    el("line", { x1: -ROOF.ov - 25, y1: -gz + 18, x2: span + ROOF.ov + 25, y2: -gz + 18, stroke: "rgba(255,255,255,.28)", "stroke-width": 7 }, g);\n      { const ga = -ROOF.ov - 40, gb = span + ROOF.ov + 40, gl = gb - ga, nb = Math.max(1, Math.round(gl / 600));   // [MM] notekas metāla detaļas: ārējā mala, kronšteini, savienojumu šuves, noslēgi\n        el("line", { x1: ga + 30, y1: -gz + 100, x2: gb - 30, y2: -gz + 100, stroke: "rgba(0,0,0,.35)", "stroke-width": 6 }, g);\n        for (let i = 0; i <= nb; i++) { const bx = ga + 60 + (gl - 120) * i / nb; el("rect", { x: bx - 14, y: -gz - 18, width: 28, height: 150, rx: 8, fill: "#1d2124", stroke: C.ink, "stroke-width": 5 }, g); }\n        for (let x = ga + 3000; x < gb - 600; x += 3000) { el("rect", { x: x - 20, y: -gz - 4, width: 40, height: 128, fill: "#3b4247", stroke: C.ink, "stroke-width": 6 }, g); el("line", { x1: x, y1: -gz + 4, x2: x, y2: -gz + 116, stroke: "rgba(255,255,255,.3)", "stroke-width": 4 }, g); }\n        [ga, gb].forEach((x, i) => el("rect", { x: i ? x - 36 : x, y: -gz - 6, width: 36, height: 132, rx: 18, fill: "#3b4247", stroke: C.ink, "stroke-width": 8 }, g)); }\n    }\n    [180, span - 180].forEach(u0_ => {\n      const u = (((window.AR || {}).projekts || {}).notekas_u || {})[PIPE(u0_)] ?? u0_;   // [MM] notekcaurules pozīciju var pārbīdīt (projekts.notekas_u)\n      if (!NOT(PIPE(u0_))) return;'),
        ('      if (!NOT(side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"))) return;',
         '      const LS = side === "west" ? (sd < 0 ? "north" : "south") : (sd < 0 ? "south" : "north"), gOn = NOT(LS), pOn = NOT(LS[0] + side[0]);\n      if (!gOn && !pOn) return;'),
        ('      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);\n      el("path", { d: `M ${ue} ${-zt}',
         '      if (pOn) {\n      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);\n      }\n      if (gOn) el("path", { d: `M ${ue} ${-zt}'),
        # [MM] rietumu terase (v.terrace): klājs plānā kā lievenis, fasādēs kā lieveņa klājs
        ('  if (v.porch) porchPlan(g, v.porch, v.rooms.length + 1);', '  if (v.porch) porchPlan(g, v.porch, v.rooms.length + 1);\n  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));'),
        ('  if (v.porch) {\n    const pc = v.porch, out =', '  for (const pc of [v.porch, ...(v.terraces || []).map(terFix)].filter(Boolean)) {\n    const out ='),
        ("    el(\"rect\", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: \"#4a4f53\", stroke: C.ink, \"stroke-width\": 14 }, g);\n    el(\"line\", { x1: u + s * .35, y1: -eEdge + 20, x2: u + s * .35, y2: fT - 20, stroke: \"rgba(255,255,255,.15)\", \"stroke-width\": 8 }, g);",
         "    el(\"rect\", { x: u, y: -eEdge, width: s, height: eEdge + fT, fill: pq && pq.tex ? `url(#${terPat(g, pq, 0, 0)})` : (pq && pq.col) || (window.AR && AR.projekts && AR.projekts.tonis_sw) || \"#c68a58\", stroke: C.ink, \"stroke-width\": 4 }, g);\n    for (let k = 1; k < Math.round(s / 50) && !(pq && (pq.tex || pq.col)); k++) el(\"line\", { x1: u + k * 50, y1: -eEdge + 15, x2: u + k * 50, y2: fT - 15, stroke: \"#5a3a1e\", \"stroke-width\": 6 }, g);   // [MM] dekoratīvs lamellu statnis"),
        ("  el(\"path\", { d, stroke: \"#b0b0b0\", \"stroke-width\": 4, fill: \"none\", \"clip-path\": `url(#${id})` }, g);\n  el(\"polygon\", { points: pts, fill: \"none\", stroke: C.line, \"stroke-width\": 8 }, g);",
         "  if (pc.tex || pc.col) el(\"polygon\", { points: pts, fill: pc.tex ? `url(#${terPat(g, pc, x0, y0)})` : pc.col }, g); else el(\"path\", { d, stroke: \"#b0b0b0\", \"stroke-width\": 4, fill: \"none\", \"clip-path\": `url(#${id})` }, g);\n  el(\"polygon\", { points: pts, fill: \"none\", stroke: C.line, \"stroke-width\": 8 }, g);"),
        ("        const tg = el(\"g\", { transform: `rotate(-90) scale(${k})` }, el(\"g\", { \"clip-path\": `url(#${id})` }, g));\n        for (let x = Math.floor(-bot / k / 2000) * 2000; x < -top / k + 2000; x += 2000) for (let y = Math.floor(a / k / 2000) * 2000; y < b / k; y += 2000) el(\"use\", { href: \"#cladTex\", x, y }, tg);",
         "        if (pc.tex || pc.col) el(\"rect\", { x: a, y: top, width: b - a, height: bot - top, fill: pc.tex ? `url(#${terPat(g, pc, 0, 0)})` : pc.col }, g); else {\n        const tg = el(\"g\", { transform: `rotate(-90) scale(${k})` }, el(\"g\", { \"clip-path\": `url(#${id})` }, g));\n        for (let x = Math.floor(-bot / k / 2000) * 2000; x < -top / k + 2000; x += 2000) for (let y = Math.floor(a / k / 2000) * 2000; y < b / k; y += 2000) el(\"use\", { href: \"#cladTex\", x, y }, tg); }"),
        ("    const along = q => endV ? q[1] : q[0], edge = pc.poly.filter(out).map(q => map(along(q)));",
         "    const along = q => endV ? q[1] : q[0], edge = (pc.__ter ? terEdge(pc, side, v) : pc.poly.filter(out)).map(q => map(along(q)));"),
        ("      face(u0, u1, fT, ROOF.plinth - 40);   // lievenis cokola augstumā",
         "      face(u0, u1, pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT, ROOF.plinth - 40);   // lievenis cokola augstumā"),
        ("      jamb(w.x, w.y, w.x, w.y + th); jamb(w.x + L, w.y, w.x + L, w.y + th);\n      el(\"rect\", { x: w.x, y: w.y + th * .36",
         "      (() => { const so_ = [\"north\", \"west\"].includes(winSide(v, w)), ya = so_ ? w.y : w.y + 7, yb = so_ ? w.y + th - 7 : w.y + th; return [[w.x - 11, ya, w.x - 11, yb], [w.x + L + 11, ya, w.x + L + 11, yb]]; })().forEach(q => el(\"line\", { x1: q[0], y1: q[1], x2: q[2], y2: q[3], stroke: C.line, \"stroke-width\": 22 }, g));   // [MM] ailas gals ar biezu sienas griezuma līniju\n      el(\"rect\", { x: w.x, y: w.y + th * .36"),
        ("      jamb(w.x, w.y, w.x + th, w.y); jamb(w.x, w.y + L, w.x + th, w.y + L);\n      el(\"rect\", { x: w.x + th * .36",
         "      (() => { const so_ = [\"north\", \"west\"].includes(winSide(v, w)), xa = so_ ? w.x : w.x + 7, xb = so_ ? w.x + th - 7 : w.x + th; return [[xa, w.y - 11, xb, w.y - 11], [xa, w.y + L + 11, xb, w.y + L + 11]]; })().forEach(q => el(\"line\", { x1: q[0], y1: q[1], x2: q[2], y2: q[3], stroke: C.line, \"stroke-width\": 22 }, g));   // [MM] ailas gals ar biezu sienas griezuma līniju\n      el(\"rect\", { x: w.x + th * .36"),
        ("  lvlMark(g, tx, cy + 720, lv(-ROOF.floorT));",
         "  lvlMark(g, tx, cy + 720, lv(pc.up ? -ROOF.plinth + 40 + pc.up + (pc.th || 120) : -ROOF.floorT));"),
        ("pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT, ROOF.plinth - 40);",
         "(pc.__ter && pc.up ? ROOF.plinth - 40 - pc.up - (pc.th || 120) : pc.__ter && pc.th ? Math.max(-300, ROOF.plinth - 40 - pc.th) : fT), pc.__ter && pc.up ? ROOF.plinth - 40 - pc.up : ROOF.plinth - 40);"),   # [MM] pakāpiens = th biezs bloks, up = bloka apakšas augstums no zemes
        #",   # [MM] pakāpiens: virs zemākās terases augšas (ne zem tās, ja pakāpiena th mazāks)),
        ("  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));",
         "  (v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));\n  (v.posts || []).forEach(q => { el(\"rect\", { x: q.x, y: q.y, width: q.w, height: q.d, fill: \"#fff\", stroke: C.ink, \"stroke-width\": 12 }, g); el(\"path\", { d: `M ${q.x} ${q.y} L ${q.x + q.w} ${q.y + q.d} M ${q.x + q.w} ${q.y} L ${q.x} ${q.y + q.d}`, stroke: C.ink, \"stroke-width\": 6 }, g); });   // [MM] brīvie stabi"),
        ("  // openings\n  const reveal =",
         "  (v.posts || []).forEach(q => { if (!postVisible(v, side, q)) return; const a = endV ? q.y : q.x, l = endV ? q.d : q.w; postsU.push([Math.min(map(a), map(a + l)), l, q]); });   // [MM] brīvie stabi fasādēs\n  // openings\n  const reveal ="),
        # [MM] loga ailai nav izvirzītu līniju: palodzes līnija beidzas ar ailas malu; iekšpusē smalka (5) ailas līnija paliek (AGENTS.md), līnijas mala vienā līmenī ar ārsienas iekšējo malu (nobīde puse līnijas)
        # [MM] telpas kontūra sākas tieši uz telpas robežas (sienas iekšējās malas), lai izmēru līnijas beidzas uz redzamās sienas līnijas; balto pildījumu pagarina par 8 tikai pret tās pašas telpas blakus taisnstūri (šuves)
        ('R.forEach(([x, y, w, h]) => el("rect", { x, y, width: w, height: h, fill: "none", stroke: C.line, "stroke-width": 2 * (8 + 14 * WL("inner")) }, g));',
         'R.forEach(([x, y, w, h]) => el("rect", { x, y, width: w, height: h, fill: "none", stroke: C.line, "stroke-width": 2 * 14 * WL("inner") }, g));'),
        ('R.forEach(([x, y, w, h]) => el("rect", { x: x - 8, y: y - 8, width: w + 16, height: h + 16, fill: "#fff" }, g));',
         'v.rooms.forEach(rm => rm.r.forEach(([x, y, w, h]) => { const nb = (f) => rm.r.some(q => q !== rm.r.find(z => z[0] === x && z[1] === y && z[2] === w && z[3] === h) && f(q)) ? 8 : 0, oy = q => q[1] < y + h && q[1] + q[3] > y, ox = q => q[0] < x + w && q[0] + q[2] > x;\n    const l = nb(q => Math.abs(q[0] + q[2] - x) < 1 && oy(q)), r = nb(q => Math.abs(q[0] - x - w) < 1 && oy(q)), t = nb(q => Math.abs(q[1] + q[3] - y) < 1 && ox(q)), b = nb(q => Math.abs(q[1] - y - h) < 1 && ox(q));\n    el("rect", { x: x - l, y: y - t, width: w + l + r, height: h + t + b, fill: "#fff" }, g); }));'),
        ('line(w.x - 40, oy, w.x + L + 40, oy, 10); line(w.x, iy, w.x + L, iy, 5); }', 'line(w.x, oy, w.x + L, oy, 10); { const q = iy + (so ? -2.5 : 2.5); line(w.x, q, w.x + L, q, 5); } }'),
        ('line(ox, w.y - 40, ox, w.y + L + 40, 10); line(ix, w.y, ix, w.y + L, 5); }', 'line(ox, w.y, ox, w.y + L, 10); { const q = ix + (so ? -2.5 : 2.5); line(q, w.y, q, w.y + L, 5); } }'),
        # [MM] loga dziļums = faktiskais sienas biezums (ārsienas slāņu summa), lai rāmja līnijas neiziet telpā
        ('  v.windows.forEach(w => {\n    const th = T, L = w.len;', '  v.windows.forEach(w => {\n    const th = window.__TGEO || T, L = w.len;'),
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
        ('      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "data-keep": 1 }, g);\n      el("line", { x1: uc - sd * 22, y1: -(zt - 80), x2: uc - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < zt - 600; z += 1100) el("rect", { x: uc - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);',
         '      el("path", { d, fill: "none", stroke: C.ink, "stroke-width": 118, "stroke-linejoin": "round", "data-keep": 1 }, g);\n      el("path", { d, fill: "none", stroke: GUT, "stroke-width": 100, "stroke-linejoin": "round", "data-keep": 1 }, g);\n      el("line", { x1: px - sd * 22, y1: -((gn ? zk - Math.abs(uc - uw) : zt) - 80), x2: px - sd * 22, y2: -zEnd - 20, stroke: "rgba(255,255,255,.22)", "stroke-width": 8 }, g);\n      for (let z = 600; z < (gn ? zk - Math.abs(uc - uw) : zt) - 600; z += 1100) el("rect", { x: px - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);'),
        # [MM] garajā fasādē ar pārkari: spāres gals (jumta pīrāgs bez iekšējās apdares) visā jumta garumā, arī sānu pārkarēs; dēļi horizontāli
        ('    // sarkanajam: balta fascija ar mazu jumta toņa skārda lentu; pārējiem tikai tieva (100 mm) skārda mala, dēļi iet līdz jumtam\n    if (FAS) {',
         '    if (OVL > 0 || OVR > 0) {\n'
         '      const RL = (typeof LAYERS === "function" && LAYERS("J1") && LAYERS("J1").layers) || [], ki = RL.findIndex(l => l[2] === "i");\n'
         '      const tPV = ((ki >= 0 ? RL.slice(0, ki + 1).reduce((s, l) => s + l[1], 0) : ROOF.th) + 20) / Math.cos(ROOF.pitch * Math.PI / 180);\n'
         '      const a = -OVL, b = span + OVR, top = -(eEdge + thV), bot = top + tPV, cid = "ovf-" + side + Math.random().toString(36).slice(2, 6);\n'
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
        # [MM] ieliekums fasādē: papildus ēnai skaidra kontūra (augša, apakša un malas), lai redzams, kas ar fasādi notiek
        ('    [u0, u1].forEach(u => u > 0 && u < span && el("line", { x1: u, y1: ROOF.plinth, x2: u, y2: -eEdge, stroke: C.ink, "stroke-width": 14 }, g));',
         '    el("rect", { x: u0, y: -eEdge, width: u1 - u0, height: eEdge + ROOF.plinth, fill: "none", stroke: "#000", "stroke-width": 30 }, g);'),
        # [MM] fasādes sienas kontūra biezāka (mājas kontūra nolasāma)
        ('el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 14 }, g);', 'el("polygon", { points: wallPoly.join(" "), fill: "none", stroke: C.ink, "stroke-width": 28 }, g);'),
        # [MM] gala fasādes jumta pārkare: nedaudz biezāka kontūra (10, data-keep, citādi fasādē visu nogriež uz 5) un ēna uz sienas zem pārkares, bet ne uz izbīdītās sienas
        ('        el("polygon", { points: pts.map(q => q.join(",")).join(" "), fill: "none", stroke: C.ink, "stroke-width": 12 }, g);\n      });\n    }\n',
         '        el("polygon", { points: pts.map(q => q.join(",")).join(" "), fill: "none", stroke: C.ink, "stroke-width": 10, "data-keep": 1 }, g);\n'
         '        if (_od(side) > 0) {   // [MM] ēna zem gala pārkares uz fasādes sienas; izbīdītā siena (vienā plaknē ar pārkari) bez ēnas\n'
         '          const ex = (v.freeWalls || []).filter(f => f[5] !== "i").concat(typeof padRects === "function" ? padRects(v) : []).filter(f => { const xs = [f[0], f[0] + f[2]], ys = [f[1], f[1] + f[3]]; return side === "south" ? ys[1] > v.D / 2 : side === "north" ? ys[0] < v.D / 2 : side === "east" ? xs[1] > v.W / 2 : xs[0] < v.W / 2; })\n'
         '            .map(f => { const U = endV ? [f[1], f[1] + f[3]].map(map) : [f[0], f[0] + f[2]].map(map); return [Math.min(...U), Math.max(...U)]; });\n'
         '          let segs = [[Math.max(u0, 0), Math.min(u1, span)]];\n'
         '          ex.forEach(([a_, b_]) => { segs = segs.flatMap(([s0, s1]) => [[s0, Math.min(s1, a_)], [Math.max(s0, b_), s1]]).filter(([s0, s1]) => s1 - s0 > 1); });\n'
         '          const zz = u => zA - tPV + (zB - zA) * (u - u0) / (u1 - u0), SH = 260;\n'
         '          segs.forEach(([s0, s1]) => el("polygon", { points: [[s0, -zz(s0)], [s1, -zz(s1)], [s1, -zz(s1) + SH], [s0, -zz(s0) + SH]].map(q => q.join(",")).join(" "), fill: "rgba(0,0,0,.24)" }, g));\n'
         '        }\n      });\n    }\n'),
        ('P(span / 2, ridgeTop - vt)].join(" "), fill: FAS ? "#F2F0EA" : "#4a5055", stroke: C.ink, "stroke-width": 12 }, g);',
         'P(span / 2, ridgeTop - vt)].join(" "), fill: FAS ? "#F2F0EA" : "#4a5055", stroke: C.ink, "stroke-width": 10, "data-keep": 1 }, g);'),
        # [MM] terases/lieveņa zīme (nosaukums, Nr., m²) pārvietojama: pozīcija v.stampAt[nr], atlasāma kā telpas zīme
        ('  stamp(g, tx, cy, pc.name || "Lievenis", nr, polyArea(pc.poly), 1);\n  lvlMark(g, tx, cy + 720, lv(pc.up ? -ROOF.plinth + 40 + pc.up + (pc.th || 120) : -ROOF.floorT));',
         '  { let sa = (window.__SA || {})[nr];\n    if (!sa && pc.__ter && !pc.up) {   // noklusēti: terases kontūras iekšienē vistālāk no malām (L formas terasei nav bbox centrā mājas iekšā)\n      const P_ = pc.poly, inP = (x, y) => { let c = false; for (let i = 0, j = P_.length - 1; i < P_.length; j = i++) if ((P_[i][1] > y) !== (P_[j][1] > y) && x < (P_[j][0] - P_[i][0]) * (y - P_[i][1]) / (P_[j][1] - P_[i][1]) + P_[i][0]) c = !c; return c; };\n      const dE = (x, y) => Math.min(...P_.map((q, i) => { const r_ = P_[(i + 1) % P_.length], dx = r_[0] - q[0], dy = r_[1] - q[1], l2 = dx * dx + dy * dy || 1, t_ = Math.max(0, Math.min(1, ((x - q[0]) * dx + (y - q[1]) * dy) / l2)); return Math.hypot(x - q[0] - t_ * dx, y - q[1] - t_ * dy); }));\n      let bd = -1; for (let x = x0 + 100; x < x1; x += 150) for (let y = y0 + 100; y < y1; y += 150) if (inP(x, y)) { const d_ = dE(x, y); if (d_ > bd) { bd = d_; sa = [x, y]; } }\n    }\n    const zx = sa ? sa[0] : tx, zy = sa ? sa[1] : cy, sg = el("g", pc.__ter ? { "data-tstamp": nr } : {}, g);\n    stamp(sg, zx, zy, pc.name || "Lievenis", nr, polyArea(pc.poly), 1);\n    if (!(pc.__ter && pc.up)) lvlMark(g, zx, zy + 720, lv(pc.up ? -ROOF.plinth + 40 + pc.up + (pc.th || 120) : -ROOF.floorT)); }'),
        ('  const g = el("g", { "data-block": "plan" }, parent);\n  const pts = v.poly.map(p => p.join(",")).join(" ");',
         '  const g = el("g", { "data-block": "plan" }, parent);\n  window.__SA = v.stampAt || {};\n  const pts = v.poly.map(p => p.join(",")).join(" ");'),
        # [MM] ārējās mēru ķēdes sākas aiz terasēm un lieveņa (noklusēti nedrīkst iet pāri tām)
        ('  const S = opt.axes ? 1 : 0, E = opt.tags ? 300 : 0;',
         '  const S = opt.axes ? 1 : 0, E0 = opt.tags ? 300 : 0, XP = [].concat(v.porch ? [v.porch.poly] : [], (v.terraces || []).map(t => t.poly)).flat(),\n'
         '    EXN = Math.max(0, ...XP.map(q => -q[1])), EXS = Math.max(0, ...XP.map(q => q[1] - v.D)), EXW = Math.max(0, ...XP.map(q => -q[0])), EXE = Math.max(0, ...XP.map(q => q[0] - v.W)), E = E0, CO = (window.AR && AR.projekts && AR.projekts.chainOff) || {};'),
        ('axX, "x", -1, -E);', 'axX, "x", -1, -E - (EXN ? EXN + 300 : 0) - (CO.n || 0));'),
        ('axY, "y", -1, -E);', 'axY, "y", -1, -E - (EXW ? EXW + 300 : 0) - (CO.w || 0));'),
        ('axY, "y", 1, v.W + E);', 'axY, "y", 1, v.W + E + (EXE ? EXE + 300 : 0) + (CO.e || 0));'),
        ('axX, "x", 1, v.D + E);', 'axX, "x", 1, v.D + E + (EXS ? EXS + 300 : 0) + (CO.s || 0));'),
        # [MM] pakāpiens nav telpa: zīmē tikai nosaukumu (bez Nr. un m²), eksplikācijā neiet
        ('    stamp(sg, zx, zy, pc.name || "Lievenis", nr, polyArea(pc.poly), 1);',
         '    if (pc.__ter && pc.up) lvlMark(sg, zx, zy, lv(pc.up ? -ROOF.plinth + 40 + pc.up + (pc.th || 120) : -ROOF.floorT)); else stamp(sg, zx, zy, pc.name || "Lievenis", nr, polyArea(pc.poly), 1);'),
        # [MM] noteksūkņa skavas garajā fasādē: smalka melna kontūra
        ('x: u - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b" }, g);',
         'x: u - 65, y: -z - 25, width: 130, height: 50, fill: "#24282b", stroke: "#000", "stroke-width": 5 }, g);'),
        # [MM] zemes līnija fasādē: viss, kas iet zem zemes (terases, stabi, pamati), tiek aizsegts; māja stāv aiz zemes līnijas
        ('  const axU = ax.map(([a]) => map(a)), AG =',
         '  { el("rect", { x: -1600, y: ROOF.plinth, width: span + 3200, height: 300, fill: "#fff" }, g); let d = ""; for (let x = -1400; x < span + 1400 - 260; x += 200) d += `M ${x} ${ROOF.plinth + 260} L ${x + 260} ${ROOF.plinth} `; el("path", { d, stroke: "#666", "stroke-width": 8, fill: "none" }, g);\n    el("line", { x1: -1600, y1: ROOF.plinth, x2: span + 1600, y2: ROOF.plinth, stroke: C.ink, "stroke-width": 45, "data-keep": 1 }, g); }   // [MM] zemes līnija virs visa, kas zem tās\n  const axU = ax.map(([a]) => map(a)), AG ='),
        # [MM] eksplikācija: ārtelpās arī terases (pakāpieni, t.up, netiek skaitīti)
        ("const n = v.rooms.length, pr = v.porch ? 2 : 0, rows = n + 4 + pr;",
         "const OUT = [].concat(v.porch ? [v.porch] : [], (v.terraces || []).filter(t => !t.up)), n = v.rooms.length, pr = OUT.length ? OUT.length + 1 : 0, rows = n + 4 + pr;"),
        ('cell(c1 / 2, yy + RH, String(n + 1), { a: "middle" }); cell(c1 + 2, yy + RH, v.porch.name || "Lievenis"); cell(WX - 2, yy + RH, f2(polyArea(v.porch.poly)), { a: "end" });',
         'OUT.forEach((o, oi) => { const y2 = yy + (oi + 1) * RH; cell(c1 / 2, y2, String(n + 1 + oi), { a: "middle" }); cell(c1 + 2, y2, o.name || (o === v.porch ? "Lievenis" : "Terase")); cell(WX - 2, y2, f2(polyArea(o.poly)), { a: "end" }); });'),
        ("(v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), v.rooms.length + (v.porch ? 2 : 1) + ti));",
         "(v.terraces || []).forEach((t, ti) => porchPlan(g, terFix(t), t.up ? 1000 + ti : v.rooms.length + (v.porch ? 2 : 1) + (v.terraces || []).slice(0, ti).filter(q => !q.up).length));"),
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
        'function mmSP() {   // palodzes profils (projekts.palodzes_prof): 0 = nav, citādi augstums mm (noklusēti 30)\n'
        '  const c = (window.AR && AR.projekts && AR.projekts.palodzes_prof) || {};\n'
        '  return c.on === false ? 0 : (+c.h > 0 ? +c.h : 30);\n'
        '}\n'
        'function arScalePlan(v) {\n'
        '  for (const d of [50, 75]) { const s = 1 / d; if ((v.W + 6900) * s <= 222 && (v.D + 6900) * s <= 148) return [s, d]; }\n'
        '  return [0.01, 100];\n'
        '}\n')
    n0 = ar.index('function wrap(t, n) {')
    ar = ar[:n0] + ARFIX + ar[n0:]
    for a_, b_ in [
        # [MM] pamatu un komunikāciju plāns kā AR lapa
        # [MM] griezumi virs diviem: 3. un 4. griezums nāk atsevišķā lapā "griez2" (lapu saraksts tiek sinhronizēts ar griezumu skaitu)
        ('  const total = ARC.parts.length, out = [];',
         '  { const ns = (v.sections || []).length, gi = ARC.parts.indexOf("griez"), g2 = ARC.parts.indexOf("griez2");   // [MM] papildu griezumu lapa\n    if (gi >= 0 && ns > 2 && g2 < 0) ARC.parts.splice(gi + 1, 0, "griez2"); else if (ns <= 2 && g2 >= 0) ARC.parts.splice(g2, 1);\n    ARC.parts.forEach(k_ => { const m_ = /^viz(\\d+)$/.exec(k_); if (m_) AR_PARTS[k_] = (((ARC.projekts || {}).ar_vizl || [])[+m_[1] - 1] || {}).n || "Vizualizācijas"; });\n    if (ns > 2) { const q = v.sections.slice(2, 4).map(z => z.n); AR_PARTS.griez2 = q.length > 1 ? `Griezumi ${q[0]}-${q[0]} un ${q[1]}-${q[1]}` : `Griezums ${q[0]}-${q[0]}`; } }\n  const total = ARC.parts.length, out = [];'),
        ('    if (k === "griez") {\n      const [s1, s2] = v.sections;\n      section(el("g", { "data-block": "sec-2", transform: "translate(52 122) scale(0.01)" }, svg), v, s2);\n      section(el("g", { "data-block": "sec-1", transform: "translate(52 222) scale(0.01)" }, svg), v, s1);',
         '    if (k === "griez" || k === "griez2") {\n      const G2 = k === "griez2", [s1, s2] = G2 ? [v.sections[2], v.sections[3]] : v.sections;\n      if (s2) section(el("g", { "data-block": "sec-" + (G2 ? 4 : 2), transform: "translate(52 122) scale(0.01)" }, svg), v, s2);\n      section(el("g", { "data-block": "sec-" + (G2 ? 3 : 1), transform: `translate(52 ${s2 ? 222 : 172}) scale(0.01)` }, svg), v, s1);'),
        # [MM] vizualizāciju lapas AR komplektā (ARC.parts atslēgas viz1, viz2 …): lapa ar rakstlauku, bildes un tukšas lapas "pievienot attēlu" laukums
        ('    const title = titles[k] || AR_PARTS[k];\n',
         '    const title = titles[k] || AR_PARTS[k];\n'
         '    const vm_ = /^viz(\\d+)$/.exec(k);\n'
         '    if (vm_) {\n'
         '      const vs_ = +vm_[1] - 1, S_ = ((ARC.projekts || {}).ar_vizl || [])[vs_] || {}, por_ = S_.o === "p", W_ = por_ ? 297 : 420, H_ = por_ ? 420 : 297, tm_ = Math.max(10, Math.min(120, +S_.top || 10));\n'
         '      const svg = el("svg", { viewBox: `0 0 ${W_} ${H_}`, class: "a3 vizl", role: "img", "aria-label": S_.n || "Vizualizācijas" });   // [MM] vertikāla/horizontāla lapa, rāmis ar atkāpi no augšas, rakstlauks apakšā labajā stūrī\n'
         '      el("rect", { width: W_, height: H_, fill: "#fff" }, svg); el("rect", { x: 20, y: tm_, width: W_ - 30, height: H_ - tm_ - 10, fill: "none", stroke: C.ink, "stroke-width": .5 }, svg);\n'
         '      arTitle(svg, S_.n || "Vizualizācijas", arNo(k), total, "-"); if (por_) svg.querySelector("[data-block=title]").setAttribute("transform", `translate(${W_ - 10 - 185} ${H_ - 10 - 44})`);\n'
         '      svg.dataset.part = "viz"; svg.dataset.vs = String(vs_);\n'
         '      (S_.im || []).forEach((q, i) => { const g = el("g", { class: "vimg", "data-i": i, transform: `rotate(${q.r || 0} ${q.x + q.w / 2} ${q.y + q.h / 2})` }, svg); el("image", { href: q.src, x: q.x, y: q.y, width: q.w, height: q.h, preserveAspectRatio: "none" }, g); });\n'
         '      if (!(S_.im || []).length) { const g = el("g", { "data-vadd": vs_, style: "cursor:pointer" }, svg); const cx_ = W_ / 2, cy_ = (tm_ + H_ - 10) / 2; el("rect", { x: cx_ - 90, y: cy_ - 50, width: 180, height: 100, rx: 3, fill: "#f6f7f8", stroke: "#2266d8", "stroke-width": .5, "stroke-dasharray": "3 2" }, g); T_(g, cx_, cy_ - 2, "+ Pievienot attēlu", { a: "middle", fs: 6, fw: 600 }); T_(g, cx_, cy_ + 10, "klikšķis vai Ctrl+V", { a: "middle", fs: 3.6 }); }\n'
         '      out.push(svg); return;\n'
         '    }\n'),
        ('const r = 300, ar = 1.414 * r, d = s.look, sheet = arNo("griez");',
         'const r = 300, ar = 1.414 * r, d = s.look, sheet = (si >= 2 && arNo("griez2")) || arNo("griez");'),
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
        # [MM] logu iestatījums: palodzes profils (ir/nav, augstums) montāžas mezglā un specifikācijā
        ('const f0 = studA + 14, f1 = f0 + 82, jb = kind === "sill" ? 50 : 20;',
         'const SP = kind === "sill" ? mmSP() : 0, f0 = studA + 14, f1 = f0 + 82, jb = kind === "sill" ? 20 + SP : 20; DET_ITEMS[4] = "Palodzes profils " + mmSP() + " mm";'),
        ('if (kind === "sill") poly([[f0, -20], [f1, -20], [f1, -50], [f0, -50]], { fill: "#dfe3e6" });',
         'if (kind === "sill" && SP) poly([[f0, -20], [f1, -20], [f1, -20 - SP], [f0, -20 - SP]], { fill: "#dfe3e6" });'),
        ('pl([[f0 + 6, -50], [-45, -26], [-45, 2]], { "stroke-width": .45 });',
         'pl([[f0 + 6, -20 - SP], [-45, -26], [-45, 2]], { "stroke-width": .45 });'),
        ('...(kind === "sill" ? [[DET_ITEMS[4], (f0 + f1) / 2, -35], [DET_ITEMS[5], -20, -26], [DET_ITEMS[6], Wt - 10, -12]]',
         '...(kind === "sill" ? [...(SP ? [[DET_ITEMS[4], (f0 + f1) / 2, -20 - SP / 2]] : []), [DET_ITEMS[5], -20, -26], [DET_ITEMS[6], Wt - 10, -12]]'),
        ('${r.sill ? "" : ", līdz grīdai"}.`, cas: r.cas,',
         '${r.sill ? (mmSP() ? ", palodzes profils " + mmSP() + " mm" : ", bez palodzes profila") : ", līdz grīdai"}.`, cas: r.cas,'),
        # [MM] griezuma noformējums: s.fill = aizpildīta krāsa (griezto elementu pildījums), citādi kontūra ar šrafējumu
        ('  const g = el("g", {}, parent), span = s.o === "v" ? v.D : v.W, ov = ROOF.ov, { eEdge, thV, ridgeTop } = roofGeo(v);',
         '  const g = el("g", {}, parent), span = s.o === "v" ? v.D : v.W, ov = ROOF.ov, { eEdge, thV, ridgeTop } = roofGeo(v), SF = s.fill || null;'),
        ('    el("polygon", { points: pts, fill: "#fff", stroke: C.ink, "stroke-width": 14 }, g);',
         '    el("polygon", { points: pts, fill: SF || "#fff", stroke: C.ink, "stroke-width": 14 }, g);'),
        ('    bands.forEach(b => el("path", { d: loops(...b), ...INS, "stroke-width": 5, "clip-path": `url(#${id})` }, g));',
         '    if (!SF) bands.forEach(b => el("path", { d: loops(...b), ...INS, "stroke-width": 5, "clip-path": `url(#${id})` }, g));'),
        ('bld.forEach(([p, q]) => el("rect", { x: p, y: 0, width: q - p, height: flT, fill: fl.some(l => (l[2] || "").includes("c")) ? "url(#concrete)" : "#fff", stroke: C.ink, "stroke-width": 14 }, g));',
         'bld.forEach(([p, q]) => el("rect", { x: p, y: 0, width: q - p, height: flT, fill: SF || (fl.some(l => (l[2] || "").includes("c")) ? "url(#concrete)" : "#fff"), stroke: C.ink, "stroke-width": 14 }, g));'),
        # [MM] starpstāvu pārseguma pīrāgs griezumā: slāņi virs istabām un starpsienām (agrāk plāna līnija); slāņi no ARC.layers.P1 vai noklusētie
        ('  // ceilings in rooms that are not open to the roof; room names\n  iv.forEach(c => {\n    if (!open(c.i)) el("rect", { x: c.a, y: -CEIL - 60, width: c.b - c.a, height: 60, fill: "#d9d9d6", stroke: C.ink, "stroke-width": 8 }, g);\n',
         '  const P1 = (LAYERS("P1") || { layers: [["OSB 22", 22, "o"], ["C24 sijas 45x195, minerālvate", 195, "i"], ["C24 latojums 45x45 instalācijas slānis", 45, "a"], ["Ģipškartons", 13, "k"]] }).layers.filter(l => l[1] > 0), P1T = P1.reduce((a, l) => a + l[1], 0);\n'
         '  { const sl = []; iv.forEach(c => { if (open(c.i)) return; const l = sl[sl.length - 1]; if (l && c.a - l.b < 400) l.b = c.b; else sl.push({ a: c.a, b: c.b }); });   // blakus istabas savieno pāri starpsienas augšai\n'
         '    sl.forEach(c => { bld.forEach(([p, q]) => { if (c.a >= p - 1 && c.a - p < 400) c.a = p; if (c.b <= q + 1 && q - c.b < 400) c.b = q; });\n'
         '      let z = CEIL; P1.slice().reverse().forEach(([n, th, f = ""]) => { const cid = "p1-" + Math.random().toString(36).slice(2, 8), y0 = -z - th;\n'
         '        el("rect", { x: c.a, y: y0, width: c.b - c.a, height: th }, el("clipPath", { id: cid }, g));\n'
         '        el("rect", { x: c.a, y: y0, width: c.b - c.a, height: th, fill: SF || "#fff", stroke: C.ink, "stroke-width": 6 }, g);\n'
         '        if (SF) { /* aizpildīts griezums: bez šrafējuma */ } else if (f.includes("i")) el("path", { d: loops(c.a, y0, 1, 0, 0, 1, c.b - c.a, th), ...INS, "stroke-width": 5, "clip-path": `url(#${cid})` }, g); else hatchBox(g, c.a, y0, c.b - c.a, th, f, 100, cid);\n'
         '        z += th; });\n'
         '      el("rect", { x: c.a, y: -CEIL - P1T, width: c.b - c.a, height: P1T, fill: "none", stroke: C.ink, "stroke-width": 12 }, g); }); }\n'
         '  // ceilings in rooms that are not open to the roof; room names\n  iv.forEach(c => {\n'),
    ]:
        assert a_ in ar, 'SBE ar.js: nav atrasts ' + a_[:50]
        ar = ar.replace(a_, b_, 1)
    # [MM] materiālu leģenda: twoCols var būt skaitlis = rindu skaits kolonnā (lai kolonnu skaits ietilptu lapas platumā)
    a_ = 'const yy = twoCols ? 7 + (i % 3) * 11 : 6 + i * 11, xx = twoCols ? Math.floor(i / 3) * 78 : 0;'
    assert a_ in ar, 'SBE ar.js: materials rindas'
    ar = ar.replace(a_, 'const RR = typeof twoCols === "number" ? twoCols : 3, yy = twoCols ? 7 + (i % RR) * 11 : 6 + i * 11, xx = twoCols ? Math.floor(i / RR) * 78 : 0;', 1)
    # [MM] AR fasāžu lapa: materiālu leģenda tā pati, kas Skicē (mmMatList: projekta toņi, cokols, logi, redaktora spaiņa toņi), nevis fiksētais saraksts
    a_ = '      materials(svg, 30, 196, false);'
    assert a_ in ar, 'SBE ar.js: fasāžu materiāli'
    ar = ar.replace(a_, '      { const keep_ = ARC.materials; let n_ = 0; try { ARC.materials = mmMatList("lv"); n_ = ARC.materials.length; } catch (e) { ARC.materials = keep_; }\n        window.AR_MATC = n_ > 8 ? 2 : 1; materials(svg, 30, 196, n_ > 8 ? Math.ceil(n_ / 2) : false); ARC.materials = keep_; }', 1)
    a_ = '      notesBlock(svg, 118, 196, 100, [...arNotes([]).slice(0, 2), "Fasāžu materiālu krāsu toņus'
    assert a_ in ar, 'SBE ar.js: fasāžu piezīmes'
    ar = ar.replace(a_, '      notesBlock(svg, window.AR_MATC > 1 ? 196 : 118, 196, window.AR_MATC > 1 ? 80 : 100, [...arNotes([]).slice(0, 2), "Fasāžu materiālu krāsu toņus', 1)
    # [MM] piezīmju bloks: notes_off piezīmes netiek zīmētas, katra piezīme ir grupa ar data-note
    a_ = '  notes.forEach((t, i) => {\n    const lines = wrap(t, Math.floor(w / 1.18));\n    T_(g, 0, yy, `${i + 1}.`, { fs: 2.4, fill: "#333" });\n    lines.forEach((l, j) => T_(g, 5, yy + j * 3.6, l, { fs: 2.4, fill: "#333" }));'
    assert a_ in ar, 'SBE ar.js: nav atrasts notesBlock'
    ar = ar.replace(a_, '  const _noff = (window.AR && AR.projekts && AR.projekts.notes_off) || [];\n  notes.filter(t => title !== "PIEZĪMES" || !_noff.includes(t)).forEach((t, i) => {\n    const lines = wrap(t, Math.floor(w / 1.18)), gn = el("g", title === "PIEZĪMES" ? { "data-note": t } : {}, g);\n    T_(gn, 0, yy, `${i + 1}.`, { fs: 2.4, fill: "#333" });\n    lines.forEach((l, j) => T_(gn, 5, yy + j * 3.6, l, { fs: 2.4, fill: "#333" }));', 1)
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
    # [MM] apbūves laukums: redaktorā uzzīmētie kontūri (model.apbuve = [{n, poly}], vecais formāts = viens poligons), citādi mājas kontūra
    FOOT = ('function footList(v) {\n  let a = v.apbuve;\n  if (a && a.length && typeof a[0][0] === "number") a = [{ n: "Dzīvojamā māja", poly: a }];\n'
            '  const L = (a || []).filter(e => e && e.poly && e.poly.length > 2).map(e => ({ n: e.n || "Apbūve", a: polyArea(e.poly) }));\n'
            '  return L.length ? L : [{ n: "Dzīvojamā māja", a: polyArea(v.poly) }];\n}\n'
            'function footA(v) { return footList(v).reduce((s, e) => s + e.a, 0); }\n')
    cad = cad.replace('polyArea(v.poly)', 'footA(v)')
    for a_, b_ in [('    box(y, 4);\n', '    const FL = footList(v);\n    box(y, 3 + FL.length);\n'),
                   ('    ln(c2, y + RH, c2, y + 4 * RH);\n', '    ln(c2, y + RH, c2, y + (3 + FL.length) * RH);\n'),
                   ('    y = 4 * RH + 8;\n', '    y = (3 + FL.length) * RH + 8;\n')]:
        assert a_ in cad, 'cad.js: nav atrasts ' + a_[:30]
        cad = cad.replace(a_, b_, 1)
    a_ = 'cell(c2 / 2, y + 2 * RH, "Dzīvojamā māja", { a: "middle" }); cell(WX - 2, y + 2 * RH, m2(footA(v)), { a: "end" }); ln(0, y + 3 * RH, WX, y + 3 * RH);\n    cell(c2 - 2, y + 3 * RH, "Kopā:", { a: "end" }); cell(WX - 2, y + 3 * RH, m2(footA(v)), { a: "end" });'
    assert a_ in cad, 'cad.js: nav atrasta apbūves tabula'
    cad = cad.replace(a_, 'FL.forEach((e, i) => { cell(c2 / 2, y + (2 + i) * RH, e.n, { a: "middle" }); cell(WX - 2, y + (2 + i) * RH, m2(e.a), { a: "end" }); ln(0, y + (3 + i) * RH, WX, y + (3 + i) * RH); });\n    cell(c2 - 2, y + (2 + FL.length) * RH, "Kopā:", { a: "end" }); cell(WX - 2, y + (2 + FL.length) * RH, m2(footA(v)), { a: "end" });', 1)
    cad = cad.replace('function cadPlan(', FOOT + 'function cadPlan(', 1)
    # [MM] plāna ārējās mēru ķēdes: katrai rindai atslēga "puse:veids" (o atveres, w sienas, a asis, t kopējais); izdzēstās (v.dimOff) izlaiž, pārējās salīdzina vienādos attālumos
    old = cad[cad.index('  const side = (open, wall, ax, dir, sgn, base) => {'):cad.index('  side([0, v.W, ...wins(w => w.o === "h" && winSide(v, w) === "north"')]
    new = ('''  const side = (open, wall, ax, dir, sgn, base, sid) => {
    const rows = [open], kinds = ["o"], uniq = p => [...new Set(p.map(Math.round))];
    const wl = uniq([...wall, ...(ax ? [Math.min(...ax), Math.max(...ax)] : [])]);
    if (wl.length > 2) { rows.push(wl); kinds.push("w"); }
    if (ax) { if (ax.length > 2) { rows.push(ax); kinds.push("a"); } rows.push([Math.min(...ax), Math.max(...ax)]); kinds.push("t"); }
    else if (wl.length > 2) { rows.push([Math.min(...wl), Math.max(...wl)]); kinds.push("t"); }
    else rows[0] = [...open, ...wl];
    if (rows.length > 1 && uniq(open).length <= 2) { rows.shift(); kinds.shift(); }   // atveru ķēde bez atverēm = tas pats kopējais izmērs, nedublē
    const HID = v.dimOff || []; let vi = 0;
    rows.forEach((p, i) => { const key = sid + ":" + kinds[i]; if (HID.includes(key)) return; const gg = el("g", { "data-dimrow": key }, dg); chainCad(gg, p, dir, base + sgn * (650 + 600 * vi++)); });
  };
''')
    cad = cad.replace(old, new, 1)
    _ids = iter("newse"[:4]); _sl = []
    for ln_ in cad.split('\n'):
        if ln_.startswith('  side([') and ln_.endswith(');'):
            ln_ = ln_[:-2] + ', "' + next(_ids) + '");'
        _sl.append(ln_)
    cad = '\n'.join(_sl)
    assert cad.count(', "s");') >= 1, 'cad.js: ķēžu izsaukumi bez atslēgām'
    # [MM] jumta plāns: pārkare pa malām (projekts.ov_side), nevis vienāda visām malām
    i_ = cad.index('function roofPlan(parent, v) {'); j_ = cad.index('\n}\n', i_) + 3
    rp = cad[i_:j_]
    for a_, b_ in [
        ('const g = el("g", { "data-block": "plan" }, parent), ov = ROOF.ov, W = v.W, Dd = v.D;',
         'const g = el("g", { "data-block": "plan" }, parent), ov = ROOF.ov, W = v.W, Dd = v.D;\n  const OS_ = (window.AR && AR.projekts && AR.projekts.ov_side) || {}, od_ = q => (!ROOF.hip && OS_[q] != null && !isNaN(+OS_[q])) ? +OS_[q] : ov, oW = od_("west"), oE = od_("east"), oN = od_("north"), oS = od_("south");'),
        ('const box = [-ov, -ov, W + 2 * ov, Dd + 2 * ov];', 'const box = [-oW, -oN, W + oW + oE, Dd + oN + oS];'),
        ('r0 = -ov + hi, r1 = W + ov - hi', 'r0 = -oW + hi, r1 = W + oE - hi'),
        (': [[[-ov, -ov], [W + ov, -ov], [W + ov, ym], [-ov, ym], "x"], [[-ov, ym], [W + ov, ym], [W + ov, Dd + ov], [-ov, Dd + ov], "x"]];',
         ': [[[-oW, -oN], [W + oE, -oN], [W + oE, ym], [-oW, ym], "x"], [[-oW, ym], [W + oE, ym], [W + oE, Dd + oS], [-oW, Dd + oS], "x"]];'),
        ('along ? [-ov, Dd + ov, -ov, W + ov] : [-ov, W + ov, -ov, Dd + ov]', 'along ? [-oN, Dd + oS, -oW, W + oE] : [-oW, W + oE, -oN, Dd + oS]'),
        ('[-ov, Dd + ov].forEach((y, k) => {', '[-oN, Dd + oS].forEach((y, k) => {'),
        ('`M ${-ov} ${y} V ${yo} H ${W + ov} V ${y}`', '`M ${-oW} ${y} V ${yo} H ${W + oE} V ${y}`'),
        ('[-ov + 140, W + ov - 140].forEach(x => el("circle"', '[-oW + 140, W + oE - 140].forEach(x => el("circle"'),
        ('leader(W * .55, -ov - 150, W * .55 + 350, -ov - 700, "1");', 'leader(W * .55, -oN - 150, W * .55 + 350, -oN - 700, "1");'),
        ('leader(W * .45, Dd + ov + 150, W * .45 + 350, Dd + ov + 700, "1");', 'leader(W * .45, Dd + oS + 150, W * .45 + 350, Dd + oS + 700, "1");'),
        ('leader(-ov + 140, -ov - 75, -ov + 520, -ov - 700, "2");', 'leader(-oW + 140, -oN - 75, -oW + 520, -oN - 700, "2");'),
        ('leader(W + ov - 140, Dd + ov + 75, W + ov - 520 - 260, Dd + ov + 700, "2");', 'leader(W + oE - 140, Dd + oS + 75, W + oE - 520 - 260, Dd + oS + 700, "2");'),
        ('chainCad(dg, [-ov, ...v.axes.x.map(a => a[0]), W + ov], "x", Dd + 1250);', 'chainCad(dg, [-oW, ...v.axes.x.map(a => a[0]), W + oE], "x", Dd + 1250);'),
        ('chainCad(dg, [-ov, W + ov], "x", Dd + 2450);', 'chainCad(dg, [-oW, W + oE], "x", Dd + 2450);'),
        ('chainCad(dg, [-ov, 0, Dd / 2, Dd, Dd + ov], "y", -1250);', 'chainCad(dg, [-oN, 0, Dd / 2, Dd, Dd + oS], "y", -1250);'),
        ('chainCad(dg, [-ov, Dd + ov], "y", -1850);', 'chainCad(dg, [-oN, Dd + oS], "y", -1850);'),
        # [MM] notekas un caurules: tās pašas, ko fasādēs (projekts.notekas), kas nodzēstas fasādē, pazūd arī jumta plānā
        ('const OS_ =', 'const NT_ = k => ((window.AR && AR.projekts && AR.projekts.notekas) || {})[k] !== false;\n  const OS_ ='),
        ('if (!ROOF.hip) el("path", { d: `M ${-oW}', 'if (!ROOF.hip && NT_(k ? "south" : "north")) el("path", { d: `M ${-oW}'),
        ('[-oW + 140, W + oE - 140].forEach(x => el("circle"', '[-oW + 140, W + oE - 140].forEach((x, xi) => NT_((k ? "s" : "n") + (xi ? "e" : "w")) && el("circle"'),
        ('  leader(W * .55, -oN', '  if (NT_("north")) leader(W * .55, -oN'),
        ('  leader(W * .45, Dd + oS', '  if (NT_("south")) leader(W * .45, Dd + oS'),
        ('  leader(-oW + 140, -oN - 75', '  if (NT_("nw")) leader(-oW + 140, -oN - 75'),
        ('  leader(W + oE - 140, Dd + oS + 75', '  if (NT_("se")) leader(W + oE - 140, Dd + oS + 75'),
        # [MM] zem jumta redzamie ārsienas izvilkumi (brīvās sienas, sienu sabiezinājumi) un stabi: raustīta kontūra kā ārsienām
        ('  // slope arrows (down the slope), pitch', '  [...(v.freeWalls || []).filter(f => f[5] !== "i"), ...(typeof padRects === "function" ? padRects(v) : []), ...(v.posts || []).map(q => [q.x, q.y, q.w, q.d])].forEach(f => el("rect", { x: f[0], y: f[1], width: f[2], height: f[3], fill: "none", stroke: C.ink, "stroke-width": 12, "stroke-dasharray": "160 90" }, g));\n  // slope arrows (down the slope), pitch'),
    ]:
        assert a_ in rp, 'ar.js roofPlan: nav atrasts ' + a_[:50]
        rp = rp.replace(a_, b_, 1)
    cad = cad[:i_] + rp + cad[j_:]
    # [MM] fasādes: zem būvasu mēru ķēdes kopējais būvasu izmērs (ja asu ir vairāk nekā divas)
    a_ = '    if (ax.length > 1) chainCad(AG, axU, "x", 1000, 0, true);'
    assert a_ in cad, 'cad.js: nav atrasta fasādes asu ķēde'
    cad = cad.replace(a_, '    if (ax.length > 1) chainCad(AG, axU, "x", ax.length > 2 ? 1180 : 1000, 0, true);\n    if (ax.length > 2) chainCad(AG, [Math.min(...axU), Math.max(...axU)], "x", 1430, 0, true);', 1)
    # [MM] fasādes nosaukums (FASĀDE ASĪS …) un tā līnija zemāk, zem asu burbuļiem ir vieta
    import re as _re2
    cad, n1 = _re2.subn(r'(T_\(g, -[\w.]+, )2450(, ttl,)', r'\g<1>2800\2', cad, count=1)
    cad, n2 = _re2.subn(r'(ttl\.length \* 262 \+ 350\)? ?(?:\* \(window\.AR_K \|\| 1\))?, )2450(, "M 1:)', r'\g<1>2800\2', cad, count=1)
    cad, n3 = _re2.subn(r'(y1: )2560(, x2: [^\n]*?, y2: )2560', r'\g<1>2910\g<2>2910', cad, count=1)
    assert n1 and n3, 'cad.js: fasādes nosaukums nav pārvietots'
    cad = cad.replace('y2: 2910, stroke: C.ink, "stroke-width": 12, "data-keep": 1', 'y2: 2910, stroke: C.ink, "stroke-width": 12, "data-keep": 1, "data-fasrule": 1', 1)   # nosaukuma līnija = fasādes jumta plašums, pēc tā lapā saliek pretējās fasādes vienā vertikālē
    # [MM] fasādes asu burbuļi zemāk, lai mēru skaitļi ir salasāmi un neuzbrauc zemes līnijai un uzrakstam "FASĀDE ASĪS"
    for a_, b_ in [('x2: u, y2: 1150, stroke: C.axis', 'x2: u, y2: 1530, stroke: C.axis'), ('cx: u, cy: 1450, r: 300', 'cx: u, cy: 1830, r: 300'), ('T_(AG, u, 1540, n,', 'T_(AG, u, 1922, n,'), ('ROOF.plinth + 80, Math.max(...axU) + 350, 1800]', 'ROOF.plinth + 80, Math.max(...axU) + 350, 2300]')]:
        assert a_ in cad, 'cad.js: fasādes asu bloks ' + a_[:30]
        cad = cad.replace(a_, b_, 1)
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
    _land = ((m.get('projekts') or {}).get('kompozicija') or {}).get('orient') == 'l'
    css = '<style>@page{size:420mm 297mm;margin:0} svg.a3{width:420mm!important;height:297mm!important}</style>' if _land else '<style>@page{size:297mm 420mm;margin:0} svg.a3{width:297mm!important;height:420mm!important}</style>'
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
    # [MM] L formas jumts (divi divslīpju jumti ar ieleju): plaknes un augstumu režģi rēķina lapā ar to pašu kodu kā redaktors (sablons/mm-roofl.js);
    # redaktors (MM_EDITOR) ieliek savu, tāpēc šeit tikai, ja tā nav
    _rm = {k: m.get(k) for k in ('W', 'D', 'poly', 'kontura', 'jumts')}
    _rm['jumts'] = dict(m.get('jumts') or {}, **{k: cfg['roof'][k] for k in ('pitch', 'ov', 'eave')})
    _rm['projekts'] = {'ov_side': pr.get('ov_side')}
    roofl = ('<script>' + open(os.path.join(HERE, 'sablons', 'mm-roofl.js'), encoding='utf-8').read()
             + f'\nif (!window.MM_EDITOR && window.AR && AR.projekts) AR.projekts.roofL = roofLGrid({js(_rm)});</script>')
    for lang in (langs or ['LV', 'EN']):
        pre = f"window.PRINT_MODE=true;window.PRINT_REV={REV};window.MODEL_SHEET=true;window.MM_LANG='{lang.lower()}';window.MM_LOGO={js(logo)};window.AR={js(cfg)};"
        page = (f'<!doctype html><html lang="{lang.lower()}"><head><meta charset="utf-8"><title>{m["nosaukums"]}</title>{font}</head>'
                f'<body><script>{pre}</script>{roofl}{h}{css}</body></html>')
        p = os.path.join(out_dir, f"{m['id']}_{lang}.html")
        open(p, 'w', encoding='utf-8').write(page)
        outs.append(p)
    return outs


if __name__ == '__main__':
    for p in build(sys.argv[1]):
        print(p)
