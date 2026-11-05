// Plan checker: run after every revision build.  node check.mjs plani/print7-h.html [...]
// Rules come from the client's review comments (22.10.2026); add new ones to RULES / REQ below.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';

// minimum room areas (m2) and other numbers per revision
const REQ = {
  7: { area: { "Virtuve + viesistaba": 60, "Bērnu vannas ist.": 8, "Katlu telpa": 4.75, "Garderobe": 5.6 } },
};
const HALL_MAX = 1300;      // hall / corridor clear width, mm
const DOOR_MARGIN = 50;     // furniture keeps this far from a door leaf, along the wall
const DOOR_BACK = 600;      // clear depth on the non-swing side of a door
const WIN_LOW = 900;        // windows with a lower sill must stay clear of furniture ...
const WIN_DEPTH = 500;      // ... for this depth in front
const TOL = 12;             // stroke width tolerance, mm

const page = await (await chromium.launch()).newPage();
let failed = 0;
for (const file of process.argv.slice(2)) {
  await page.goto('file://' + new URL(file, 'file://' + process.cwd() + '/').pathname);
  await page.waitForTimeout(800);
  const res = await page.evaluate(({ REQ, HALL_MAX, DOOR_MARGIN, DOOR_BACK, WIN_LOW, WIN_DEPTH, TOL }) => {
    const v = window.__PV, out = [];
    const bad = (rule, msg) => out.push(`[${rule}] ${msg}`);
    const ov = (a, b, t = TOL) => Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > t && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > t;
    const inside = (a, b, t = TOL) => a[0] >= b[0] - t && a[1] >= b[1] - t && a[2] <= b[2] + t && a[3] <= b[3] + t;
    const box = (x, y, w, h) => [x, y, x + w, y + h];
    const f1 = a => a.toFixed(0);
    // furniture rules on the sheet with furniture; marks on every plan sheet that has them
    const sheets = [...document.querySelectorAll('svg.a3')];
    const planSheet = sheets.find(s => s.querySelector('[data-block=plan] [data-furn]')) || sheets[0];
    let planG = planSheet.querySelector('[data-block=plan]');
    let inv = planG.getCTM().inverse();
    const bboxOf = els => {
      let b = null;
      els.forEach(e => {
        const r = e.getBBox(), m = inv.multiply(e.getCTM());
        [[r.x, r.y], [r.x + r.width, r.y], [r.x, r.y + r.height], [r.x + r.width, r.y + r.height]].forEach(([x, y]) => {
          const p = new DOMPoint(x, y).matrixTransform(m);
          b = b ? [Math.min(b[0], p.x), Math.min(b[1], p.y), Math.max(b[2], p.x), Math.max(b[3], p.y)] : [p.x, p.y, p.x, p.y];
        });
      });
      return b;
    };
    const group = attr => { const g = {}; planG.querySelectorAll(`[${attr}]`).forEach(e => (g[e.getAttribute(attr)] ||= []).push(e)); return Object.entries(g).map(([k, els]) => [isNaN(+k) ? k : +k, bboxOf(els)]); };
    const furn = group('data-furn'), stamps = group('data-stamp');
    const rects = v.rooms.flatMap((rm, i) => rm.r.map(q => ({ i, n: rm.n, b: box(...q) })));
    const where = b => { const r = rects.find(r => ov(b, r.b, -1)); return r ? r.n : "?"; };
    const label = (i, b) => `mēbele #${i} (${where(b)}, x ${f1(b[0])}–${f1(b[2])}, y ${f1(b[1])}–${f1(b[3])})`;

    // R1 furniture stays inside one room: never in a wall, an outer wall or another room
    furn.forEach(([i, b]) => { if (!rects.some(r => inside(b, r.b))) bad("R1 mēbele sienā", label(i, b)); });

    // R2 door swing and both sides of the leaf stay clear
    const doorZones = v.doors.map(d => {
      const { x, y, w, th, o, side } = d;
      if (o === "h") {
        const sw = side > 0 ? [y + th, y + th + w] : [y - w, y], bk = side > 0 ? [y - DOOR_BACK, y] : [y + th, y + th + DOOR_BACK];
        return { d, zones: [[x - DOOR_MARGIN, sw[0], x + w + DOOR_MARGIN, sw[1]], [x, bk[0], x + w, bk[1]]] };
      }
      const sw = side > 0 ? [x + th, x + th + w] : [x - w, x], bk = side > 0 ? [x - DOOR_BACK, x] : [x + th, x + th + DOOR_BACK];
      return { d, zones: [[sw[0], y - DOOR_MARGIN, sw[1], y + w + DOOR_MARGIN], [bk[0], y, bk[1], y + w]] };
    });
    doorZones.forEach(({ d, zones }) => furn.forEach(([i, b]) => {
      if (zones.some(z => ov(b, z))) bad("R2 durvis", `${label(i, b)} traucē durvīm x ${d.x}, y ${d.y}`);
    }));
    // R3 door swings do not clash with each other
    doorZones.forEach((a, k) => doorZones.slice(k + 1).forEach(b2 => {
      if (ov(a.zones[0], b2.zones[0], 30)) bad("R3 durvis pret durvīm", `x ${a.d.x}, y ${a.d.y} un x ${b2.d.x}, y ${b2.d.y}`);
    }));

    // R4 low windows (incl. floor-length) are not blocked
    v.windows.forEach(w => {
      if ((w.sill ?? 900) >= WIN_LOW) return;
      const z = w.o === "h" ? (w.y === 0 ? [w.x, w.y, w.x + w.len, w.y + 310 + WIN_DEPTH] : [w.x, w.y - WIN_DEPTH, w.x + w.len, w.y + 310])
        : (w.x === 0 ? [w.x, w.y, w.x + 310 + WIN_DEPTH, w.y + w.len] : [w.x - WIN_DEPTH, w.y, w.x + 310, w.y + w.len]);
      furn.forEach(([i, b]) => { if ((v.winOk || []).some(o => b[0] >= o[0] - 30 && b[1] >= o[1] - 30 && b[2] <= o[2] + 30 && b[3] <= o[3] + 30)) return; if (ov(b, z)) bad("R4 logs", `${label(i, b)} priekšā logam x ${w.x}, y ${w.y}`); });
    });

    // R5 room labels sit inside their room and do not cover furniture
    stamps.forEach(([i, b]) => {
      if (!v.rooms[i].r.some(q => inside(b, box(...q), 0))) bad("R5 telpas zīme", `${v.rooms[i].n} (#${i + 1}) iziet ārpus telpas`);
      furn.forEach(([j, fb]) => { if (ov(b, fb, 20)) bad("R5 telpas zīme", `${v.rooms[i].n} (#${i + 1}) pārklāj ${label(j, fb)}`); });
    });

    // R9 window / door marks stay clear of furniture, room labels, dimension text and each other
    const tagSheets = sheets.filter(s => s.querySelector('[data-block=plan] [data-tag]'));
    tagSheets.forEach(ts => {
    planG = ts.querySelector('[data-block=plan]'); inv = planG.getCTM().inverse();
    const tags = group('data-tag'), furn = group('data-furn'), stamps = group('data-stamp'), pg = `lapa ${sheets.indexOf(ts) + 1}: `;
    {
      const others = [...planG.querySelectorAll('text')].filter(t => !t.closest('[data-tag]') && !t.parentNode.hasAttribute('data-tag') && !t.hasAttribute('data-tag')).map(t => [t.textContent, bboxOf([t])]);
      tags.forEach(([k, b], i) => {
        const nm = pg + ({ w: 'logs #', d: 'durvis #', s: 'sienas tips #' }[k[0]]) + k.slice(1);
        furn.forEach(([j, fb]) => { if (ov(b, fb, 5)) bad("R9 marķējums", `${nm} pārklāj ${label(j, fb)}`); });
        stamps.forEach(([j, sb]) => { if (ov(b, sb, 5)) bad("R9 marķējums", `${nm} pārklāj telpas zīmi #${j + 1}`); });
        others.forEach(([t, ob]) => { if (ov(b, ob, 5)) bad("R9 marķējums", `${nm} pārklāj tekstu „${t}”`); });
        tags.slice(i + 1).forEach(([k2, b2]) => { if (ov(b, b2, 5)) bad("R9 marķējums", `${nm} pārklāj ${k2}`); });
      });
    }
    });

    // R6 halls max HALL_MAX wide (revisions from 7 on)
    if (v.rev >= 7) v.rooms.filter(rm => /Gaitenis|Priekšnams/.test(rm.n)).forEach(rm => rm.r.forEach(q => {
      if (Math.min(q[2], q[3]) > HALL_MAX) bad("R6 gaitenis", `${rm.n} ${Math.min(q[2], q[3])} mm > ${HALL_MAX}`);
    }));

    // R7 client's minimum areas
    const req = REQ[v.rev];
    if (req) Object.entries(req.area).forEach(([n, min]) => {
      const rm = v.rooms.find(r => r.n === n);
      const a = rm ? rm.r.reduce((s, q) => s + q[2] * q[3], 0) / 1e6 : 0;
      if (a + 1e-6 < min) bad("R7 platība", `${n} ${a.toFixed(2)} m² < ${min}`);
    });

    // R8 sheet layout: blocks inside the frame and not on top of each other
    document.querySelectorAll('svg.a3').forEach((s, k) => {
      // visible extent: union of drawn shapes, a clipped shape counts by its clip region
      const sm = s.getCTM().inverse();
      const ext = e => {
        let bb = null;
        const add = (el, r) => { const m = sm.multiply(el.getCTM()); [[r.x, r.y], [r.x + r.width, r.y + r.height], [r.x, r.y + r.height], [r.x + r.width, r.y]].forEach(([x, y]) => { const p = new DOMPoint(x, y).matrixTransform(m); bb = bb ? [Math.min(bb[0], p.x), Math.min(bb[1], p.y), Math.max(bb[2], p.x), Math.max(bb[3], p.y)] : [p.x, p.y, p.x, p.y]; }); };
        e.querySelectorAll('rect,line,path,polygon,polyline,circle,ellipse,text,use,image').forEach(el => {
          if (el.closest('clipPath,defs,pattern')) return;
          const cl = el.closest('[clip-path]');
          if (cl) { const cp = document.getElementById(cl.getAttribute('clip-path').slice(5, -1)); if (cp && cp.firstElementChild) { add(cl, cp.firstElementChild.getBBox()); return; } }
          add(el, el.getBBox());
        });
        return bb;
      };
      const bl = [...s.querySelectorAll('[data-block]')].filter(e => e.parentNode === s).map(e => [e.getAttribute('data-block'), ext(e)]).filter(x => x[1]);
      bl.forEach(([n, b]) => { if (!inside(b, s.viewBox.baseVal.width < 300 ? (n === 'title' ? [247, 10, 287, 410] : [20, 10, 247, 410]) : [20, 10, 410, 287], 0.5)) bad("R8 lapa", `lapa ${k + 1}: ${n} iziet ārpus rāmja`); });
      bl.forEach(([n, b], i) => bl.slice(i + 1).forEach(([n2, b2]) => { if (ov(b, b2, 0.5)) bad("R8 lapa", `lapa ${k + 1}: ${n} uzbrauc ${n2}`); }));
    });
    // R10 AR set: every reference "AR-n" in the notes points to a sheet of this set
    if (window.AR) {
      const n = window.AR.parts.length;
      sheets.forEach((sh, k) => [...sh.querySelectorAll('text')].forEach(t => (t.textContent.match(/AR-\d+/g) || []).forEach(r => {
        if (+r.slice(3) < 1 || +r.slice(3) > n) bad("R10 atsauce", `lapa ${k + 1}: „${t.textContent}” – lapas ${r} komplektā nav`);
      })));
    }
    return { rev: v.rev, label: v.label, out, nf: furn.length };
  }, { REQ, HALL_MAX, DOOR_MARGIN, DOOR_BACK, WIN_LOW, WIN_DEPTH, TOL });
  console.log(`\n${file}: Rev. ${res.rev}${res.label ? ` (variants ${res.label})` : ''}, ${res.nf} mēbeles — ${res.out.length ? res.out.length + ' kļūdas' : 'OK'}`);
  res.out.forEach(m => console.log('  ' + m));
  failed += res.out.length;
}
process.exit(failed ? 1 : 0);
