// [MM] L formas jumts: kopīgs redaktoram (lapa.html) un modeļa lapām (build_model.py).
// kGridPoly: taisnstūru (on) apvienojums mīnus izgriezumi (off) → kontūra pulksteņrādītāja virzienā, sākot no augšējā kreisā stūra; null, ja nesaskaras.
function kGridPoly(on, off) {
  const xs = [...new Set(on.concat(off).flatMap(r => [r[0], r[0] + r[2]]))].sort((a, b) => a - b), ys = [...new Set(on.concat(off).flatMap(r => [r[1], r[1] + r[3]]))].sort((a, b) => a - b);
  const inr = (r, x, y) => x > r[0] && x < r[0] + r[2] && y > r[1] && y < r[1] + r[3], C = [];
  for (let j = 0; j < ys.length - 1; j++) { C.push([]); for (let i = 0; i < xs.length - 1; i++) { const cx = (xs[i] + xs[i + 1]) / 2, cy = (ys[j] + ys[j + 1]) / 2; C[j].push(on.some(r => inr(r, cx, cy)) && !off.some(r => inr(r, cx, cy))); } }
  const ny = C.length, nx = ny ? C[0].length : 0, at = (i, j) => i >= 0 && j >= 0 && i < nx && j < ny && C[j][i], cells = [];
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) if (C[j][i]) cells.push([i, j]);
  if (!cells.length) return null;
  const seen = new Set([cells[0].join()]), st = [cells[0]]; while (st.length) { const [i, j] = st.pop(); [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([a, b]) => { const k = (i + a) + "," + (j + b); if (at(i + a, j + b) && !seen.has(k)) { seen.add(k); st.push([i + a, j + b]); } }); }
  if (seen.size !== cells.length) return null;
  const E = new Map(); cells.forEach(([i, j]) => { const x0 = xs[i], x1 = xs[i + 1], y0 = ys[j], y1 = ys[j + 1];
    if (!at(i, j - 1)) E.set(x0 + "," + y0, [x1, y0]); if (!at(i + 1, j)) E.set(x1 + "," + y0, [x1, y1]); if (!at(i, j + 1)) E.set(x1 + "," + y1, [x0, y1]); if (!at(i - 1, j)) E.set(x0 + "," + y1, [x0, y0]); });
  const start = [...E.keys()][0], out = []; let k = start, g = 0; do { const b = E.get(k); if (!b || g++ > 4000) return null; out.push(k.split(",").map(Number)); k = b.join(); } while (k !== start);
  if (out.length !== E.size) return null;
  const o2 = out.filter((q, i, A) => { const a = A[(i + A.length - 1) % A.length], b = A[(i + 1) % A.length]; return !((a[0] === q[0] && q[0] === b[0]) || (a[1] === q[1] && q[1] === b[1])); });
  const i0 = o2.reduce((b, q, i) => (q[1] < o2[b][1] || (q[1] === o2[b][1] && q[0] < o2[b][0]) ? i : b), 0); return o2.slice(i0).concat(o2.slice(0, i0));
}

// Jumta kontūra: ja modelim ir kontūra no blokiem, jumts iet pāri robiem (bloku apvienojums bez robiem), citādi m.poly.
function roofPolyOf(m) {
  const K = m.kontura, bl = K && (K.bloki || []).map(b => b.r);
  if (bl && bl.length) { const P = kGridPoly(bl, []); if (P) return P; }
  return m.poly || [];
}

// L jumts ieslēgts: jumts.L = true, vai kontūrā ir divi bloki un jumts.L nav false. Četrslīpju un vienslīpu jumtam nav.
function roofLOn(m) {
  const J = m.jumts || {};
  if (+J.hip || /^(cetr|četr|vienslip|parapet)/i.test(J.forma || "")) return false;
  if (J.L === false) return false;
  return !!J.L || ((m.kontura && m.kontura.bloki) || []).length === 2;
}

// ---- L formas jumts: divi divslīpju jumti ar ieleju. Atgriež null, ja kontūra nav L vai jumts ir četrslīpju. ----
// Galvenā daļa ir pilna garuma josla, spārna kore ieiet galvenās daļas slīpnē; izvēlas dalījumu, kurā spārns nav platāks par galveno daļu.
// jumts.pitch = galvenās daļas slīpums; jumts.pitch_sparns = spārna slīpums (nav = tāds pats); jumts.kore_kopiga = true: spārna slīpumu
// rēķina, lai abu daļu kores būtu vienā augstumā. Spārns nekad nav augstāks par galveno kori. Spārna sānu pārkare ir tāda, lai dzega būtu
// vienā augstumā ar galvenās daļas dzegu (ieleja sākas stūrī).
function roofL(m) {
  const J = m.jumts || {}, P = m.projekts || {}, W = m.W, D = m.D, poly = roofPolyOf(m);
  if (!roofLOn(m) || poly.length !== 6) return null;
  if (!poly.every((p, i) => { const q = poly[(i + 1) % 6]; return Math.abs(p[0] - q[0]) < 1 || Math.abs(p[1] - q[1]) < 1; })) return null;
  const r = poly.find(p => p[0] > 1 && p[0] < W - 1 && p[1] > 1 && p[1] < D - 1); if (!r) return null;
  const has = (x, y) => poly.some(p => Math.abs(p[0] - x) < 1 && Math.abs(p[1] - y) < 1), c = [[0, 0], [W, 0], [W, D], [0, D]].find(q => !has(q[0], q[1])); if (!c) return null;
  const tan = Math.tan((J.pitch || 30) * Math.PI / 180), eave = J.eave || 2600, ov = +J.ov || 0, OS = P.ov_side || {}, od = q => (OS[q] != null && !isNaN(+OS[q])) ? +OS[q] : ov;
  const cw = Math.abs(r[0] - c[0]), cd = Math.abs(r[1] - c[1]), A = (W - cw) <= (D - cd) ? 0 : 1;   // A = kores ass galvenajai daļai (0 = x, 1 = y)
  // kanoniskās koordinātas: u gar galveno kori, v no galvenās daļas malas, pie kuras ir spārns (spārns ir v < 0)
  const U = A ? D : W, cu = A ? c[1] : c[0], cv = A ? c[0] : c[1], nu = A ? cd : cw, nv = A ? cw : cd, V = A ? W : D;
  const a = cu === 0 ? nu : 0, b = cu === 0 ? U : U - nu, s = cv === 0 ? 1 : -1, v0 = cv === 0 ? nv : V - nv, dm = V - nv, dw = nv, hw = (b - a) / 2, wc = (a + b) / 2;
  const tMax = (dm / 2) * tan / hw;   // spārna slīpums, pie kura abu kores ir vienā augstumā
  let tanW = J.kore_kopiga ? tMax : (J.pitch_sparns ? Math.tan(+J.pitch_sparns * Math.PI / 180) : tan);
  if (!(tanW > 0)) tanW = tan;
  tanW = Math.min(tanW, tMax);
  const w3 = (u, v, z) => { const q = v0 + s * v; return A ? [q, u, z] : [u, q, z]; }, toUV = (x, y) => { const u = A ? y : x, q = A ? x : y; return [u, (q - v0) * s]; };
  const sd = A ? { u0: "north", u1: "south", far: s > 0 ? "east" : "west", wg: s > 0 ? "west" : "east" } : { u0: "west", u1: "east", far: s > 0 ? "south" : "north", wg: s > 0 ? "north" : "south" };
  const h = d => eave + d * tan, hW = d => eave + d * tanW, hr = h(dm / 2), hg = hW(hw);
  const oN = od(sd.wg), oF = od(sd.far), oG = oN, oNw = oN * tan / tanW, vR = (hg - eave) / tan;   // oNw: spārna sānu pārkare (dzega vienā augstumā), vR: kur spārna kore ieiet galvenajā slīpnē
  const o0 = a === 0 ? oNw : od(sd.u0), o1 = b === U ? oNw : od(sd.u1);
  const dv = (du, dvv) => { const q = w3(du, dvv * s === 0 ? 0 : dvv, 0), o = w3(0, 0, 0); return [q[0] - o[0], q[1] - o[1], 2]; };
  const z = (x, y) => { const [u, v] = toUV(x, y); if (v < 0) return hW(Math.min(u - a, b - u)); const zm = h(Math.min(v, dm - v)); return (u > a && u < b && v <= dm / 2) ? Math.max(zm, hW(Math.min(u - a, b - u))) : zm; };
  const near = [[-o0, -oN, h(-oN)], [a - oNw, -oN, h(-oN)], [wc, vR, hg], [b + oNw, -oN, h(-oN)], [U + o1, -oN, h(-oN)], [U + o1, dm / 2, hr], [-o0, dm / 2, hr]];
  const slopes = [
    { name: "Jumts, galvenā tālā slīpne", pts: [[-o0, dm + oF, h(-oF)], [U + o1, dm + oF, h(-oF)], [U + o1, dm / 2, hr], [-o0, dm / 2, hr]], dir: dv(0, 1) },
    { name: "Jumts, galvenā slīpne ar ieleju", pts: near, dir: dv(0, -1) },
    { name: "Jumts, spārna slīpne 1", pts: [[a - oNw, -dw - oG, h(-oN)], [a - oNw, -oN, h(-oN)], [wc, vR, hg], [wc, -dw - oG, hg]], dir: dv(-1, 0) },
    { name: "Jumts, spārna slīpne 2", pts: [[b + oNw, -dw - oG, h(-oN)], [b + oNw, -oN, h(-oN)], [wc, vR, hg], [wc, -dw - oG, hg]], dir: dv(1, 0) },
  ].map(q => ({ name: q.name, dir: q.dir, pts: q.pts.map(([u, v, zz]) => w3(u, v, zz)) }));
  // dzegas notekām: [sākums, beigas, mala]; 60 mm ārpus jumta malas
  const E = (u0, v0_, u1, v1, zz, key) => [w3(u0, v0_, zz), w3(u1, v1, zz), key], eaves = [E(-o0, dm + oF + 60, U + o1, dm + oF + 60, h(-oF), sd.far)];
  if (a > 0) { eaves.push(E(-o0, -oN - 60, a - oNw, -oN - 60, h(-oN), sd.wg)); eaves.push(E(a - oNw - 60, -oN, a - oNw - 60, -dw - oG, h(-oN), sd.u0)); } else eaves.push(E(a - oNw - 60, -oN, a - oNw - 60, -dw - oG, h(-oN), sd.u0));
  if (b < U) { eaves.push(E(b + oNw, -oN - 60, U + o1, -oN - 60, h(-oN), sd.wg)); eaves.push(E(b + oNw + 60, -oN, b + oNw + 60, -dw - oG, h(-oN), sd.u1)); } else eaves.push(E(b + oNw + 60, -oN, b + oNw + 60, -dw - oG, h(-oN), sd.u1));
  const deg = t => Math.round(Math.atan(t) * 1800 / Math.PI) / 10;
  return { z, slopes, eaves, ridge: Math.max(hr, hg), A, poly, dm, kore: { galvena: Math.round(hr), sparns: Math.round(hg) }, slipums: { galvena: deg(tan), sparns: deg(tanW) } };
}

// Jumta plaknes un augstumu režģis (200 mm; punkti uz plaknes malas arī skaitās plaknē) fasādēm, jumta plānam un 3D: AR.projekts.roofL = { slopes, grid, kore, slipums }.
function roofLGrid(m) {
  try {
    const r = roofL(m); if (!r) return null;
    const sl = r.slopes.map(s => ({ name: s.name, pts: s.pts })), all = sl.flatMap(s => s.pts), x0 = Math.floor(Math.min(...all.map(p => p[0])) / 200) * 200, y0 = Math.floor(Math.min(...all.map(p => p[1])) / 200) * 200, nx = Math.ceil((Math.max(...all.map(p => p[0])) - x0) / 200) + 1, ny = Math.ceil((Math.max(...all.map(p => p[1])) - y0) / 200) + 1;
    const inP = (P, x, y) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const a = P[i], b = P[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
    const pl = sl.map(s => { let g = null, best = 0; const Q = s.pts; for (let a = 0; a < Q.length; a++) for (let b = a + 1; b < Q.length; b++) for (let c = b + 1; c < Q.length; c++) { const ax = Q[b][0] - Q[a][0], ay = Q[b][1] - Q[a][1], az = Q[b][2] - Q[a][2], bx = Q[c][0] - Q[a][0], by = Q[c][1] - Q[a][1], bz = Q[c][2] - Q[a][2], det = ax * by - ay * bx; if (Math.abs(det) > best) { best = Math.abs(det); g = [(az * by - bz * ay) / det, (ax * bz - bx * az) / det, Q[a]]; } } return { P: Q.map(p => [p[0], p[1]]), g }; });
    const z = []; for (let j = 0; j < ny; j++) { const row = []; for (let i = 0; i < nx; i++) { const x = x0 + i * 200, y = y0 + j * 200; let zz = null; pl.forEach(q => { if (q.g && [[0, 0], [.5, .5], [-.5, -.5], [.5, -.5], [-.5, .5]].some(([e, f]) => inP(q.P, x + e, y + f))) { const v = q.g[2][2] + q.g[0] * (x - q.g[2][0]) + q.g[1] * (y - q.g[2][1]); if (zz == null || v > zz) zz = v; } }); row.push(zz == null ? null : Math.round(zz)); } z.push(row); }
    return { slopes: sl, grid: { x0, y0, d: 200, nx, ny, z }, kore: r.kore, slipums: r.slipums };
  } catch (e) { return null; }
}
