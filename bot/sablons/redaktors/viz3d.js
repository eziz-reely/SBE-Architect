  // ---- 3D skats + Gemini prompts: references PNG ar fotogrāfa kadru un gatavs prompts (tāds pats kā viz.py) ----
  (function () {
    const V = { open: false, inited: false, view: "SE", free: false, lens: 85, tone: null, atm: "auto", az: 45, el: 0, dist: 30000 };
    const SIDES = { south: "south", north: "north", east: "east", west: "west" };
    const SIDE_LV = { south: "Dienvidi (ieeja)", north: "Ziemeļi", east: "Austrumi", west: "Rietumi" };
    const VIEWS = [["S", "Fasāde S", 0], ["E", "Fasāde A", 90], ["N", "Fasāde Z", 180], ["W", "Fasāde R", 270],
      ["SE", "3/4 DA", 45], ["NE", "3/4 ZA", 135], ["NW", "3/4 ZR", 225], ["SW", "3/4 DR", 315]];
    const ATM = __MM_ATMOS__, KAR_SNAP = __MM_KAR3D__;
    function syncKar() { document.querySelectorAll("#v3mode button").forEach(b => b.setAttribute("aria-pressed", String((b.dataset.k === "1") === !!V.kar))); if ($("v3kBox")) $("v3kBox").hidden = !V.kar; }
    const ATM_KEYS = Object.keys(ATM);
    const CAM_H = 1600, ASPECT = 1.5, fovOf = mm => 2 * Math.atan(12 / mm) * 180 / Math.PI;
    const hexOf = ral => { const r = RAL[ral]; return r ? r[1] : "#383E42"; };
    const lv0 = () => { const P = model.projekts || {}; return TONES[P.tonis] ? P.tonis : "peleks"; };
    const terr = () => model.terase && model.terase.side ? model.terase : null;

    // ---------- ģeometrija ----------
    function T3(p) { return new THREE.Vector3(p[0], p[2], p[1]); }   // plāna (x,y,z) -> three (x,z,y), y uz dienvidiem = +z
    function basis(pts, dir) {
      const n = new THREE.Vector3();
      for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; n.x += (a.y - b.y) * (a.z + b.z); n.y += (a.z - b.z) * (a.x + b.x); n.z += (a.x - b.x) * (a.y + b.y); }
      n.normalize();
      if (dir && n.dot(dir) < 0) n.negate();
      let u = new THREE.Vector3().subVectors(pts[1], pts[0]); if (u.lengthSq() < 1e-6) u.set(1, 0, 0);
      u.addScaledVector(n, -u.dot(n)).normalize();
      const v = new THREE.Vector3().crossVectors(n, u);
      return { n, u, v };
    }
    function extrude(g, mat) {
      const o = g.outer.map(T3), dir = new THREE.Vector3(g.dir[0], g.dir[2], g.dir[1]).normalize(), { n, u, v } = basis(o, dir), O = o[0];
      const to2 = p => new THREE.Vector2(p.clone().sub(O).dot(u), p.clone().sub(O).dot(v));
      const sh = new THREE.Shape(o.map(to2));
      (g.holes || []).forEach(h => sh.holes.push(new THREE.Path(h.map(T3).map(to2))));
      const geo = new THREE.ExtrudeGeometry(sh, { depth: g.d, bevelEnabled: false });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.applyMatrix4(new THREE.Matrix4().makeBasis(u, v, n).setPosition(O));
      return mesh;
    }
    // sienu gala skaldnes, kas sakrīt ar blakus sienas ārējo vai iekšējo plakni (stūros), izmet: nav pārklājošos plakņu (z-cīņas) uz frontoniem
    function trimShared(me, g, WL) {
      const geo = me.geometry, gr = geo.groups; if (!gr || gr.length < 2) return;
      me.updateMatrix(); const mx = me.matrix, P = geo.attributes.position, UV = geo.attributes.uv, N = geo.attributes.normal;
      const oth = WL.filter(q => q !== g).map(q => { const o = q.outer.map(T3), dir = new THREE.Vector3(q.dir[0], q.dir[2], q.dir[1]).normalize(), b = basis(o, dir), O = o[0]; return { q, b, O, dir, p2: o.map(p => [p.clone().sub(O).dot(b.u), p.clone().sub(O).dot(b.v)]), nn: b.n }; });
      const inside = (pt, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > pt[1]) !== (b[1] > pt[1]) && pt[0] < (b[0] - a[0]) * (pt[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
      me.userData.oth = oth;
      const keepIdx = [], A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3(), cen = new THREE.Vector3(), nrm = new THREE.Vector3();
      const g1 = gr[1], first = g1.start;
      for (let t = first; t < first + g1.count; t += 3) {
        A.fromBufferAttribute(P, t).applyMatrix4(mx); B.fromBufferAttribute(P, t + 1).applyMatrix4(mx); C.fromBufferAttribute(P, t + 2).applyMatrix4(mx);
        nrm.crossVectors(B.clone().sub(A), C.clone().sub(A)).normalize(); cen.copy(A).add(B).add(C).multiplyScalar(1 / 3);
        let drop = false;
        if (Math.abs(nrm.y) < .5) oth.forEach(w => {
          if (drop || Math.abs(Math.abs(nrm.dot(w.nn)) - 1) > .01) return;
          const dd = cen.clone().sub(w.O).dot(w.nn); if (Math.abs(dd) > 1 && Math.abs(dd - w.q.d * Math.sign(w.nn.dot(w.dir) || 1)) > 1 && Math.abs(dd - w.q.d) > 1 && Math.abs(dd + w.q.d) > 1) return;
          if (inside([cen.clone().sub(w.O).dot(w.b.u), cen.clone().sub(w.O).dot(w.b.v)], w.p2)) drop = true;
        });
        if (!drop) keepIdx.push(t);
      }
      const cp = (att, items) => { const out = new Float32Array(items * att.itemSize); return out; };
      const total = first + keepIdx.length * 3, mk = att => { const o = new Float32Array(total * att.itemSize); o.set(att.array.subarray(0, first * att.itemSize)); keepIdx.forEach((t, k) => o.set(att.array.subarray(t * att.itemSize, (t + 3) * att.itemSize), (first + k * 3) * att.itemSize)); return new THREE.BufferAttribute(o, att.itemSize); };
      geo.setAttribute("position", mk(P)); if (N) geo.setAttribute("normal", mk(N)); if (UV) geo.setAttribute("uv", mk(UV));
      g1.count = keepIdx.length * 3; geo.computeBoundingSphere();
    }
    // ---------- ražošanas karkass (karkass.py frame3d): statņi, gulšņi, pārsedzes, spāres kā SketchUp modelis ----------
    const KCOL = { stud: "#dcbe8f", bottom_plate: "#c29a64", top_plate: "#c29a64", king: "#d3aa76", jack: "#d3aa76", junction: "#cfa672", junction_rot: "#c6995f", header: "#b88a55", opening_plate: "#c29a64", sill: "#c29a64", cripple: "#dcbe8f", nogging: "#e0c79c", rafter: "#e8cf9e" };
    function buildFrame(kd, lay) {
      const g = new THREE.Group(), up = new THREE.Vector3(0, 1, 0), mats = {}, edgeM = new THREE.LineBasicMaterial({ color: "#0b0d0e" });
      const mt = r => mats[r] || (mats[r] = new THREE.MeshLambertMaterial({ color: KCOL[r] || "#d8b98a", side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 }));
      const add = me => { const l = new THREE.LineSegments(new THREE.EdgesGeometry(me.geometry, 25), edgeM); l.raycast = () => {}; me.add(l); me.castShadow = me.receiveShadow = true; g.add(me); };
      if (lay !== "r") (kd.det || []).forEach(([pi, role, poly, d]) => {
        const p = kd.paneli[pi], u3 = new THREE.Vector3(p.d[0], 0, p.d[1]), n3 = new THREE.Vector3(p.n[0], 0, p.n[1]);
        const sh = new THREE.Shape(poly.map(q => new THREE.Vector2(q[0], q[1])));
        const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: d, bevelEnabled: false }), mt(role));
        me.applyMatrix4(new THREE.Matrix4().makeBasis(u3, up, n3).setPosition(T3([p.o[0], p.o[1], 0]))); add(me);
      });
      if (lay !== "w" && kd.rafs) kd.rafs.forEach(r => {   // spāre ar iezāģi un vertikāliem galiem: profils vertikālā plaknē, biezums B
        const sh = new THREE.Shape(r.poly.map(q => new THREE.Vector2(q[0], q[1])));
        const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: kd.B, bevelEnabled: false }), mt("rafter"));
        me.applyMatrix4(new THREE.Matrix4().makeBasis(new THREE.Vector3(r.d[0], 0, r.d[1]), up, new THREE.Vector3(r.n[0], 0, r.n[1])).setPosition(T3([r.o[0], r.o[1], 0]))); add(me);
      });
      if (lay !== "w" && !kd.rafs) (kd.spares || []).forEach(([a, b, nv]) => {
        const p0 = T3(a), p1 = T3(b), dv = p1.clone().sub(p0), L = dv.length(); if (L < 5) return; dv.normalize();
        const n = new THREE.Vector3(nv[0], nv[2], nv[1]), l = new THREE.Vector3().crossVectors(n, dv).normalize(), nn = new THREE.Vector3().crossVectors(dv, l).normalize();
        const me = new THREE.Mesh(new THREE.BoxGeometry(L, kd.DJ, kd.B), mt("rafter"));
        me.applyMatrix4(new THREE.Matrix4().makeBasis(dv, nn, l).setPosition(p0.clone().add(p1).multiplyScalar(.5).addScaledVector(nn, kd.DJ / 2))); add(me);
      });
      return g;
    }
    function planeMesh(pts3, mat, off) {
      const { n, u, v } = basis(pts3), O = pts3[0].clone().addScaledVector(n, off || 0);
      const to2 = p => new THREE.Vector2(p.clone().sub(pts3[0]).dot(u), p.clone().sub(pts3[0]).dot(v));
      const mesh = new THREE.Mesh(new THREE.ShapeGeometry(new THREE.Shape(pts3.map(to2))), mat);
      mesh.applyMatrix4(new THREE.Matrix4().makeBasis(u, v, n).setPosition(O));
      return mesh;
    }
    function frameAround(pts3, mat, out, fw, fd) {   // rāmis: plāna kaste katrai ailas malai
      const { n } = basis(pts3);
      pts3.forEach((a, i) => {
        const b = pts3[(i + 1) % pts3.length], d = new THREE.Vector3().subVectors(b, a), L = d.length(); if (L < 1) return; d.normalize();
        const w = new THREE.Vector3().crossVectors(n, d).normalize();
        const box = new THREE.Mesh(new THREE.BoxGeometry(L + fw, fw, fd), mat);
        box.applyMatrix4(new THREE.Matrix4().makeBasis(d, w, n).setPosition(a.clone().add(b).multiplyScalar(.5).addScaledVector(n, 25)));
        out.add(box);
      });
    }
    const sideOf = (pts, W, D) => {
      const c = pts.reduce((s, p) => [s[0] + p[0] / pts.length, s[1] + p[1] / pts.length], [0, 0]);
      const dx = Math.max(...pts.map(p => p[0])) - Math.min(...pts.map(p => p[0])), dy = Math.max(...pts.map(p => p[1])) - Math.min(...pts.map(p => p[1]));
      if (dx < 5) return c[0] < W / 2 ? "west" : "east";
      if (dy < 5) return c[1] < D / 2 ? "north" : "south";
      return null;
    };
    function terraceRect(m) {
      const t = terr(); if (!t) return null;
      const W = m.W, D = m.D, dp = +t.depth || 1100, a = +t.a || 0, b = +t.b || 0;
      return { south: [-a, D, W + b, D + dp], north: [-a, -dp, W + b, 0], west: [-dp, -a, 0, D + b], east: [W, -a, W + dp, D + b] }[t.side] || null;
    }
    function boardsTex() {
      const c = document.createElement("canvas"); c.width = 64; c.height = 64; const x = c.getContext("2d");
      x.fillStyle = "#3d4247"; x.fillRect(0, 0, 64, 64); x.fillStyle = "#2a2e32"; for (let i = 0; i < 64; i += 16) x.fillRect(0, i, 64, 2);
      const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
    }
    // horizontālais vagondēlis: dēļi gar sienu, sprauga starp dēļiem
    function stripeTexH(mod, n, gap, vary) {
      const c = document.createElement("canvas"); c.width = 8; c.height = 64 * n; const x = c.getContext("2d");
      for (let i = 0; i < n; i++) { const l = Math.round(255 * (1 - vary * ((i * 37 % 10) / 10))); x.fillStyle = `rgb(${l},${l},${l})`; x.fillRect(0, i * 64, 8, 64); x.fillStyle = `rgba(0,0,0,${gap})`; x.fillRect(0, i * 64, 8, 4); x.fillStyle = "rgba(255,255,255,.16)"; x.fillRect(0, i * 64 + 4, 8, 2); }
      const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1 / 1000, 1 / mod); t.anisotropy = 8; return t;
    }
    function D0(m) { return m.D; }
    // joslu tekstūra (pelēktoņi, krāsu dod materiāls): fasādes dēļi, jumta valči, terases dēļi. mod = viena raksta platums mm
    function stripeTex(mod, n, gap, vary) {
      const c = document.createElement("canvas"); c.width = 64 * n; c.height = 8; const x = c.getContext("2d");
      for (let i = 0; i < n; i++) { const l = Math.round(255 * (1 - vary * ((i * 37 % 10) / 10))); x.fillStyle = `rgb(${l},${l},${l})`; x.fillRect(i * 64, 0, 64, 8); x.fillStyle = `rgba(0,0,0,${gap})`; x.fillRect(i * 64, 0, 4, 8); x.fillStyle = "rgba(255,255,255,.16)"; x.fillRect(i * 64 + 4, 0, 2, 8); }
      const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1 / mod, 1 / 1000); t.anisotropy = 8; return t;
    }
    const sideOfN = n => { const ox = -n[0], oy = -n[1]; return Math.abs(ox) > Math.abs(oy) ? (ox > 0 ? "east" : "west") : (oy > 0 ? "south" : "north"); };   // n = sienas iekšējā normāle plānā
    function obox(c, t, len, dep, hgt, mat) {   // kaste plāna koordinātās: centrs [x,y,z], garums pa t, dziļums šķērsām, augstums
      const b = new THREE.Mesh(new THREE.BoxGeometry(len, hgt, dep), mat); b.position.set(c[0], c[2], c[1]); b.rotation.y = Math.atan2(-t[1], t[0]); return b;
    }
    function cyl(a, b, r, mat) {
      const d = new THREE.Vector3().subVectors(b, a), L = d.length(), me = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, 14), mat);
      me.position.copy(a).addScaledVector(d, .5); me.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize()); return me;
    }
    function edgeBoards(P3, o3, cw, th, mat, out, skipBottom) {   // aplodas ap ailu (arī piecstūra logam): dēlis gar katru malu ārpusē
      const c = P3.reduce((s, p) => s.add(p), new THREE.Vector3()).multiplyScalar(1 / P3.length), minY = Math.min(...P3.map(p => p.y));
      P3.forEach((a, i) => {
        const b = P3[(i + 1) % P3.length], d = new THREE.Vector3().subVectors(b, a), L = d.length(); if (L < 1) return; d.normalize();
        const mid = a.clone().add(b).multiplyScalar(.5); if (skipBottom && Math.abs(d.y) < .01 && mid.y <= minY + 1) return;
        let w = new THREE.Vector3().crossVectors(o3, d).normalize(); if (w.dot(mid.clone().sub(c)) < 0) { w.negate(); d.negate(); }
        const bx = new THREE.Mesh(new THREE.BoxGeometry(L + cw, cw, th), mat);
        bx.applyMatrix4(new THREE.Matrix4().makeBasis(d, w, o3).setPosition(mid.addScaledVector(w, cw / 2).addScaledVector(o3, th / 2))); out.add(bx);
      });
    }
    // gredzens ap daudzstūri: katra mala nobīdīta par amts[i] (+ uz āru, - uz iekšu), stūri ar paslīpinājumu (bez krustojošām līnijām)
    function offPoly(q, amts) {
      const n = q.length; let ar = 0; q.forEach((a, i) => { const b = q[(i + 1) % n]; ar += a[0] * b[1] - b[0] * a[1]; });
      const sg = ar > 0 ? 1 : -1;
      const ln = q.map((a, i) => { const b = q[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, w = amts[i]; return [a[0] + sg * dy / L * w, a[1] - sg * dx / L * w, dx, dy]; });
      return q.map((a, i) => { const l0 = ln[(i + n - 1) % n], l1 = ln[i], det = l0[2] * l1[3] - l0[3] * l1[2]; if (Math.abs(det) < 1e-6) return [l1[0], l1[1]]; const t = ((l1[0] - l0[0]) * l1[3] - (l1[1] - l0[1]) * l1[2]) / det; return [l0[0] + l0[2] * t, l0[1] + l0[3] * t]; });
    }
    // viens paslīpināts gredzens: ārējā mala nobīdīta par wo, iekšējā par wi (vienādi visām malām; botAmt1 = apakšējai malai atsevišķi), izspiests d garumā pa nrm no punkta o
    function ringMesh(P3, nrm, wo, wi, d, mat, out, botOut, botIn) {
      const upv = new THREE.Vector3(0, 1, 0), u = new THREE.Vector3().crossVectors(upv, nrm).normalize(), o = P3[0].clone();
      const q = P3.map(p => [p.clone().sub(o).dot(u), p.y - o.y]), n = q.length, minV = Math.min(...q.map(p => p[1]));
      const isBot = i => { const a = q[i], b = q[(i + 1) % n]; return Math.abs(b[1] - a[1]) < .01 * (Math.hypot(b[0] - a[0], b[1] - a[1]) || 1) && Math.max(a[1], b[1]) <= minV + 1; };
      const out2 = offPoly(q, q.map((_, i) => botOut != null && isBot(i) ? botOut : wo)), in2 = offPoly(q, q.map((_, i) => botIn != null && isBot(i) ? botIn : wi));
      const sh = new THREE.Shape(out2.map(p => new THREE.Vector2(p[0], p[1]))); sh.holes.push(new THREE.Path(in2.slice().reverse().map(p => new THREE.Vector2(p[0], p[1]))));
      const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: d, bevelEnabled: false }), mat);
      me.applyMatrix4(new THREE.Matrix4().makeBasis(u, upv, nrm).setPosition(o)); out.add(me); return me;
    }
    function revealUV(rm, ni) {   // ailas oderes fasādes dēļu raksts: u pa fasādi, v augšup
      rm.updateMatrix(); const ps = rm.geometry.attributes.position, uv = [], v3 = new THREE.Vector3(), lu = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), ni).normalize();
      for (let i = 0; i < ps.count; i++) { v3.fromBufferAttribute(ps, i).applyMatrix4(rm.matrix); uv.push(v3.dot(lu), v3.y); }
      rm.geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    }
    // lāsenis: mazs metāla profils (plāksne 1,5 mm virs aplodas, priekšējā mala ar nolaidumu, aizmugurē atloks pie sienas) gar aplodu augšējām malām, arī slīpajām
    function dripFlash(P3, o3, cw, mat, out) {
      const upv = new THREE.Vector3(0, 1, 0), u = new THREE.Vector3().crossVectors(upv, o3).normalize(), o = P3[0];
      const q = P3.map(p => [p.clone().sub(o).dot(u), p.y - o.y]), n = q.length; let ar = 0; q.forEach((a, i) => { const b = q[(i + 1) % n]; ar += a[0] * b[1] - b[0] * a[1]; });
      const sg = ar > 0 ? 1 : -1, outer = offPoly(q, q.map(() => cw)), prof = [[-1.5, 18], [-1.5, 0], [28.5, 0], [28.5, -20], [30, -20], [30, 1.5], [0, 1.5], [0, 18]];
      outer.forEach((a, i) => {
        const b = outer[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy); if (L < 20) return;
        const nx = sg * dy / L, ny = -sg * dx / L; if (ny < .3) return;   // tikai augšpusē vērstās malas
        const sh = new THREE.Shape(prof.map(p => new THREE.Vector2(p[0], p[1])));
        const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: L, bevelEnabled: false }), mat);
        const tv = u.clone().multiplyScalar(dx / L).addScaledVector(upv, dy / L), wv = u.clone().multiplyScalar(nx).addScaledVector(upv, ny);
        me.applyMatrix4(new THREE.Matrix4().makeBasis(o3, wv, tv).setPosition(o.clone().addScaledVector(u, a[0]).addScaledVector(upv, a[1]))); out.add(me);
      });
    }
    function casingBoards(P3, o3, mat, out, skipBottom, cw) {   // aplodas: vienāds platums visās malās (arī slīpajām; kā 2D win.casing, noklusējums 100), stūri ar paslīpinājumu, biezums 19
      ringMesh(P3, o3, cw || 100, 0, 19, mat, out, skipBottom ? 0 : null, 0);
    }
    // ārdurvis: lapa ar ierobežotu stiklojuma izgriezumu, dubultā paketē (2 × 4 mm + 16 mm distancētājs), vāķi, rokturis, eņģes, aiļu odere
    function doorDetail(P3, o3, hl, grp, leafM, steel, glM, revM, fac) {
      const upv = new THREE.Vector3(0, 1, 0), u = new THREE.Vector3().crossVectors(upv, o3).normalize(), o = P3[0];
      const xs = P3.map(p => p.clone().sub(o).dot(u)), x0 = Math.min(...xs), O = o.clone().addScaledVector(u, x0), y0 = Math.min(...P3.map(p => p.y)); O.y = y0;
      const Wd = Math.max(...xs) - x0, Hd = Math.max(...P3.map(p => p.y)) - y0, SH = -65;   // lapa iestumta ailā kā logs (aila 150 mm dziļa)
      const dark = new THREE.MeshLambertMaterial({ color: "#1b1d1f", side: THREE.DoubleSide });
      const rect = (a, b, c, d) => [[a, b], [c, b], [c, d], [a, d]];
      const ex = (outer, hole, d0, d1, m) => { const sh = new THREE.Shape(outer.map(p => new THREE.Vector2(p[0], p[1]))); if (hole) sh.holes.push(new THREE.Path(hole.slice().reverse().map(p => new THREE.Vector2(p[0], p[1]))));
        const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: d1 - d0, bevelEnabled: false }), m); me.applyMatrix4(new THREE.Matrix4().makeBasis(u, upv, o3).setPosition(O.clone().addScaledVector(o3, d0 + SH))); grp.add(me); return me; };
      const bx = (cx, cy, w, h, d0, d1, m) => { const me = new THREE.Mesh(new THREE.BoxGeometry(w, h, d1 - d0), m); me.applyMatrix4(new THREE.Matrix4().makeBasis(u, upv, o3).setPosition(O.clone().addScaledVector(u, cx).addScaledVector(upv, cy).addScaledVector(o3, (d0 + d1) / 2 + SH))); grp.add(me); return me; };
      { const rm = ringMesh(P3.map(p => p.clone().addScaledVector(o3, -150)), o3, -1, -20, 150, revM || leafM, grp, -1, -1);   // ailas odere (bez apakšas): aplodu tonī vai fasādes dēļi
        if (fac) revealUV(rm, o3); }
      const gx = hl ? 120 : Wd - 280, gy0 = 150, gy1 = Math.min(Hd - 150, 1950), G = rect(gx, gy0, gx + 160, gy1);
      ex(rect(20, 0, Wd - 20, Hd - 20), G, -85, -45, leafM);                                    // durvju lapa 40 mm ar stiklojuma izgriezumu (pati ir rāmis)
      ex(G, null, -74, -70, glM); ex(G, null, -58, -54, glM);                                   // divi stikli 4 mm
      ex(rect(gx - 2, gy0 - 2, gx + 162, gy1 + 2), rect(gx + 12, gy0 + 12, gx + 148, gy1 - 12), -70, -58, dark);   // distancētājs 12 mm
      ex(rect(gx - 20, gy0 - 20, gx + 180, gy1 + 20), rect(gx + 6, gy0 + 6, gx + 154, gy1 - 6), -45, -38, leafM);  // stikla līste
      const hx = hl ? Wd - 240 : 240;
      [650, 1450].forEach(y => bx(hx, y, 16, 16, -45, 25, steel)); bx(hx, 1050, 26, 1100, 25, 45, steel);   // rokturis ar balstiem
      bx(hl ? Wd - 40 : 40, 1050, 20, 180, -45, -36, steel);                                       // slēdzenes plāksne
      [250, 1050, 1850].forEach(y => bx(hl ? 26 : Wd - 26, y, 16, 110, -45, -32, steel));          // eņģes
    }
    // fasādes detaļas kā rasējumā: aplodas, palodzes, dalījumi, durvju stikls un rokturis, notekas, stabi, terases, lievenis
    function details(m, geo, grp, mat, frameM, T, X) {
      X = X || {}; const casM = X.casM || frameM, sillM = X.sillM || casM;
      const P = m.projekts || {}, J = m.jumts || {}, W = m.W, D = m.D, pitch = J.pitch || 30, tan = Math.tan(pitch * Math.PI / 180), eave = J.eave || 2600, ov = +J.ov || 0;
      const hip = +J.hip || (/^(cetr|četr)/i.test(J.forma || "") ? pitch : 0), tanH = hip ? Math.tan(hip * Math.PI / 180) : 0;
      const RL = tanH ? null : roofL(m), roofZ = (x, y) => RL ? RL.z(x, y) : eave + Math.min(Math.min(y, D - y) * tan, tanH ? Math.min(x, W - x) * tanH : Infinity);
      const steel = mat("#c9cdd1"), glassD = mat("#8fb0c0", { transparent: true, opacity: .8 }), gutM = mat(hexOf(P.noteku_tonis || "RAL 7016"));
      geo.forEach(g => {
        if ((g.k !== "g" && g.k !== "d") || !g.n) return;
        const o = [-g.n[0], -g.n[1]], o3 = new THREE.Vector3(o[0], 0, o[1]), face = g.pts.map(p => T3([p[0] + o[0] * T / 2, p[1] + o[1] * T / 2, p[2]]));
        const w = g.k === "g" ? (g.ref.k === "win" ? (m.windows || [])[g.ref.i] : (m.gableWins || [])[g.ref.i]) : (m.doors || [])[g.ref.i], cas = w && w.casing != null ? +w.casing : ((window.AR && window.AR.win && window.AR.win.casing) ?? 100);
        if (cas > 0) casingBoards(face, o3, casM, grp, !(w && w.casingAll), cas);
        const z0 = Math.min(...g.pts.map(p => p[2])), z1 = Math.max(...g.pts.map(p => p[2])), bot = g.pts.filter(p => p[2] <= z0 + 1);
        if (bot.length >= 2) {
          const a = bot[0], b = bot[bot.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), t = [(b[0] - a[0]) / L, (b[1] - a[1]) / L], cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2, at = (f, off, z) => [a[0] + (b[0] - a[0]) * f + o[0] * off, a[1] + (b[1] - a[1]) * f + o[1] * off, z];
          if (g.k === "g") {
            grp.add(obox([cx + o[0] * (T / 2 + 13), cy + o[1] * (T / 2 + 13), z0 - 12.5], t, L + 2 * cas + 90, 26, 25, sillM));   // palodze: izvirzījums max 7 mm aiz aplodām (19 + 7)
            if (cas > 0) dripFlash(face, o3, cas, sillM, grp);   // lāsenis virs aplodām (arī slīpajām malām)
            const cuts = []; if (w && w.parts && w.parts.length > 1) { let u = 0; w.parts.slice(0, -1).forEach(q => { u += +q.len || 0; cuts.push(u / (w.len || L)); }); } else if (w && /^slide/.test(w.kind || "")) cuts.push(.5);
            cuts.forEach(f => grp.add(obox(at(f, -155, (z0 + z1) / 2), t, 60, 60, z1 - z0, frameM)));   // dalījuma statnis
          } else {
            const sdD = sideOf(g.pts, W, D), hl = (g.hinge !== "e") !== (sdD === "north" || sdD === "east");   // viris kā 2D: eņģes kreisajā pusē (skatoties no ārpuses)
            { const facD = (P.logu_odere === "fasade") && X.wallTex; doorDetail(face, o3, hl, grp, frameM, steel, mat("#5f808f", { transparent: true, opacity: .7 }), facD ? X.wallTex(sdD || "south") : casM, facD); }
            grp.add(obox([cx + o[0] * (T / 2 + 20), cy + o[1] * (T / 2 + 20), -10], t, L + 40, 120, 20, steel));   // slieksnis
          }
        }
      });
      // dekoratīvie stūra dēļi (projekts.sturi_opc: nav / balts / melns / tonis; noklusējums pēc toņa): 90 mm josla katras fasādes galā līdz jumta augšai (kā 2D)
      { const TN = (typeof TONES !== "undefined" && TONES[X.tk]) || {}, so = P.sturi_opc || (TN.sturi ? "balts" : "nav");
        if (so !== "nav") {
          const sm = mat({ balts: "#F2F0EA", melns: "#1d1d1d", tonis: X.wallHex || "#8a8f94" }[so] || "#F2F0EA"), CB = 90, TH = 19, RTH = 285, up3 = new THREE.Vector3(0, 1, 0);
          const cpoly = m.poly && m.poly.length > 2 ? m.poly : [[0, 0], [W, 0], [W, D], [0, D]]; let ar = 0; cpoly.forEach((a, i) => { const b = cpoly[(i + 1) % cpoly.length]; ar += a[0] * b[1] - b[0] * a[1]; });
          cpoly.forEach((a, i) => {
            const b = cpoly[(i + 1) % cpoly.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 2 * CB + 100) return;
            const dx = (b[0] - a[0]) / L, dy = (b[1] - a[1]) / L, nx = (ar > 0 ? dy : -dy), ny = (ar > 0 ? -dx : dx), o3 = new THREE.Vector3(nx, 0, ny), u3 = new THREE.Vector3(dx, 0, dy);
            [0, 1].forEach(end => {
              const t0 = end ? L - CB : 0, t1 = end ? L : CB, pt = t => [a[0] + dx * t, a[1] + dy * t], zt = t => { const p = pt(t); return roofZ(p[0] - nx * 5, p[1] - ny * 5) + RTH; };
              const sh = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(CB, 0), new THREE.Vector2(CB, zt(t1)), new THREE.Vector2(0, zt(t0))].map((p, k) => k < 2 ? p : p));
              const me = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: TH, bevelEnabled: false }), sm), P0 = T3([pt(t0)[0] + nx * T / 2 * 0, pt(t0)[1] + ny * T / 2 * 0, 0]);
              me.applyMatrix4(new THREE.Matrix4().makeBasis(u3, up3, o3).setPosition(P0)); grp.add(me);
            });
          });
        } }
      // notekas gar dzegām un notekcaurules pie stūriem (ja tur ir siena)
      const OS = P.ov_side || {}, od = q => (OS[q] != null && !isNaN(+OS[q])) ? +OS[q] : ov, oN = od("north"), oS = od("south"), oW = od("west"), oE = od("east");
      const poly = (m.poly && m.poly.length > 2 ? m.poly : [[0, 0], [W, 0], [W, D], [0, D]]), nearWall = (x, y) => poly.some((a, i) => { const b = poly[(i + 1) % poly.length], dx = b[0] - a[0], dy = b[1] - a[1], l = dx * dx + dy * dy || 1, u = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / l)); return Math.hypot(x - a[0] - u * dx, y - a[1] - u * dy) < 120; });
      const NK = P.notekas || {}, run = (p, q, wallAt, key) => {
        if (NK[key] === false || NK.visas === false) return;
        grp.add(cyl(T3([p[0], p[1], p[2] - 35]), T3([q[0], q[1], q[2] - 35]), 62, gutM));
        [p, q].forEach((e, i) => { const f = i ? q : p, g2 = i ? p : q, L = Math.hypot(g2[0] - f[0], g2[1] - f[1]) || 1, d = [(g2[0] - f[0]) / L, (g2[1] - f[1]) / L], top = [f[0] + d[0] * (i ? 250 + oE : 250 + oW), f[1] + d[1] * 250, f[2] - 60], w = wallAt(top);
          if (!nearWall(w[0], w[1])) return; const o2 = [top[0] - w[0], top[1] - w[1]], l2 = Math.hypot(o2[0], o2[1]) || 1, wp = [w[0] + o2[0] / l2 * 60, w[1] + o2[1] / l2 * 60];
          grp.add(cyl(T3(top), T3([wp[0], wp[1], top[2] - Math.max(250, l2 * .8)]), 45, gutM)); grp.add(cyl(T3([wp[0], wp[1], top[2] - Math.max(250, l2 * .8)]), T3([wp[0], wp[1], -250]), 45, gutM)); });
      };
      const wallOf = t => { let best = null, bd = 1e9; poly.forEach((p0, i) => { const p1 = poly[(i + 1) % poly.length], dx = p1[0] - p0[0], dy = p1[1] - p0[1], l = dx * dx + dy * dy || 1, u = Math.max(0, Math.min(1, ((t[0] - p0[0]) * dx + (t[1] - p0[1]) * dy) / l)), q = [p0[0] + u * dx, p0[1] + u * dy], d2 = Math.hypot(t[0] - q[0], t[1] - q[1]); if (d2 < bd) { bd = d2; best = q; } }); return best; };
      // teknes un notekcaurules zīmē roofDetail (pēc fasādes: pustekne ar 120 mm augstumu, caurule Ø80 180 mm no stūra)
      // stabi: līdz jumta apakšai vai līdz savam augstumam (posts[i].h)
      const texOf = (o, k) => { if (!o || !o.tex) return null; const t = new THREE.TextureLoader().load(o.tex, () => draw()); t.wrapS = t.wrapT = THREE.RepeatWrapping; const w = Math.max(100, +o.texW || 1000); t.repeat.set(k / w, k / w); if (o.texRot) t.rotation = o.texRot * Math.PI / 180; return t; };
      const wood = (c, o) => { const t = texOf(o, 300); return t ? new THREE.MeshLambertMaterial({ map: t, side: THREE.DoubleSide }) : mat(c || "#b98a5c"); };
      (m.posts || []).forEach((q, i) => { const w = +q.w || 200, d = +q.d || w, cx = q.x + w / 2, cy = q.y + d / 2, top = q.h && q.h < 99999 ? +q.h : roofZ(cx, cy) - 5, b = new THREE.Mesh(new THREE.BoxGeometry(w, top + 300, d), wood(q.col, q)); b.position.set(cx, (top - 300) / 2, cy); b.userData.bk = { k: "post", i }; grp.add(b); });
      ((m.porch && m.porch.posts) || []).forEach(q => { if (!q || q.x == null) return; const w = +q.w || 200, d = +q.d || w, cx = q.x + w / 2, cy = q.y + d / 2, top = roofZ(cx, cy) - 5, b = new THREE.Mesh(new THREE.BoxGeometry(w, top + 300, d), wood(q.col)); b.position.set(cx, (top - 300) / 2, cy); grp.add(b); });
      // margas: stabiņi (bal × bal, sprauga gap) un lenteris; augšas apgriež jumta plaknes apakša (roofZ)
      (m.railings || []).forEach(r => {
        const base = r.z0 != null ? +r.z0 : r.lv === "loft" && m.loft ? +m.loft.level || 0 : 0, bd = +r.balD || +r.bal || 45, rW = +r.railW || 60, rH = +r.railH || 40, hh = r.h != null ? +r.h : 1000, bal = +r.bal || 45, gap = r.gap != null ? +r.gap : 50, P = r.pts || [], RM = wood(r.col || "#d9d4cb", r);
        const topAt = (x, y) => Math.min(base + hh, roofZ(x, y) - 5);
        P.forEach((a, j) => { const c = P[j + 1]; if (!c) return; const dx = c[0] - a[0], dy = c[1] - a[1], L = Math.hypot(dx, dy), n = Math.max(1, Math.round(L / (bal + gap))), ang = Math.atan2(dy, dx);
          for (let i = j ? 1 : 0; i <= n; i++) { const t = i / n, x = a[0] + dx * t, y = a[1] + dy * t, top = topAt(x, y); if (top - base < 30) continue;
            const b = new THREE.Mesh(new THREE.BoxGeometry(bal, top - base, bd), RM); b.position.set(x, base + (top - base) / 2, y); b.rotation.y = -ang; grp.add(b); }
          if (r.rail !== false) { const st = Math.max(1, Math.ceil(L / 400)); for (let q = 0; q < st; q++) { const t0 = q / st, t1 = (q + 1) / st, x0 = a[0] + dx * t0, y0 = a[1] + dy * t0, x1 = a[0] + dx * t1, y1 = a[1] + dy * t1, tp = Math.min(topAt(x0, y0), topAt(x1, y1)); if (tp - base < 60) continue;
            const rb = new THREE.Mesh(new THREE.BoxGeometry(Math.hypot(x1 - x0, y1 - y0) + 4, rH, rW), RM); rb.position.set((x0 + x1) / 2, tp - rH / 2, (y0 + y1) / 2); rb.rotation.y = -Math.atan2(y1 - y0, x1 - x0); grp.add(rb); } }
        });
      });
      // terases un lievenis pa kontūru
      const deck = (pl, top, th, col, bk, o) => { if (!pl || pl.length < 3) return; const own = texOf(o, 1), tx = own || stripeTex(600, 4, .45, .12); if (own) col = "#ffffff"; me = new THREE.Mesh(new THREE.ExtrudeGeometry(new THREE.Shape(pl.map(p => new THREE.Vector2(p[0], p[1]))), { depth: th, bevelEnabled: false }), new THREE.MeshLambertMaterial({ color: col || "#4a4f55", map: tx, side: THREE.DoubleSide }));
        me.rotation.x = Math.PI / 2; me.position.y = top; me.userData.bk = bk; grp.add(me); };
      (m.terraces || []).forEach((t, i) => deck(t.poly, -25, Math.max(60, (+t.th || 300) - 25), t.col, { k: "ter", i }, t));
      if (m.porch) { deck(m.porch.poly, -25, 275, m.porch.col, { k: "porch" }, m.porch); const s = m.porch.step, sp = m.porch.stepPoly || (s && [[s[0], s[1]], [s[2], s[1]], [s[2], s[3]], [s[0], s[3]]]); if (sp) deck(sp, -165, 135, m.porch.col, { k: "porch" }); }
    }
    // ---------- jumta mezgls: spāres ar vertikālu galu griezumu, pārkares apakša, fascija, kores/dzegu metāla nosegi ----------
    // Slāņu secība virs plaknes (perpendikulāri): [0..R0] iekšējie slāņi, [R0..R0+195] spāres, 50 latojumi, 2,5 jumta segums. Visi malu griezumi ir VERTIKĀLI (bīde pa vertikāli).
    function roofDetail(roofs, c) {
      const { grp, poly, P, roofM, th0, vk } = c, up = new THREE.Vector3(0, 1, 0), SH = 2.5, BT = 50, RAF = 195;
      const M = (col, o) => new THREE.MeshLambertMaterial(Object.assign({ color: col, side: THREE.DoubleSide }, o || {}));
      const dark = M("#3c4146"), fasM = M(P.fascia_hex || "#3c4146"), capM = M("#3c4146"), rafM = M(P.sparu_hex || "#8c6c48"), sofM = M(P.parkare_hex || "#3a4046");
      const S = roofs.map(g => {
        const o = g.outer.map(T3), d = new THREE.Vector3(g.dir[0], g.dir[2], g.dir[1]).normalize(), b = basis(o, d), O = o[0];
        { const uh = new THREE.Vector3().crossVectors(up, b.n).normalize(); if (uh.lengthSq() > .5) { b.u = uh; b.v = new THREE.Vector3().crossVectors(b.n, uh); } }   // falču raksts vienmēr pa kritumlīniju, nevis pa pirmo kontūras malu
        return { g, b, O, nz: b.n.y, th: +g.d || th0, pl: g.outer.map(p => [p[0], p[1]]), zAt: (x, y) => O.y - (b.n.x * (x - O.x) + b.n.z * (y - O.z)) / b.n.y };
      });
      const slab = (s, pl, t0, t1, mats, bk, noEdge) => {   // plāna daudzstūris uz slīpnes, biezums t0..t1 perpendikulāri, malas vertikālas
        if (pl.length < 3) return;
        const { u, v } = s.b, to2 = ([x, y]) => { const p = new THREE.Vector3(x, s.zAt(x, y), y).sub(s.O); return new THREE.Vector2(p.dot(u), p.dot(v)); };
        const ge = new THREE.ExtrudeGeometry(new THREE.Shape(pl.map(to2)), { depth: t1 - t0, bevelEnabled: false });
        ge.applyMatrix4(new THREE.Matrix4().makeBasis(u, v, up.clone().multiplyScalar(1 / s.nz)).setPosition(s.O.clone().addScaledVector(up, t0 / s.nz)));   // bīde ir ģeometrijā (Object3D.applyMatrix4 bīdi pazaudē)
        const me = new THREE.Mesh(ge, mats);
        if (bk) me.userData.bk = { k: "ov" }; if (noEdge) me.userData.noEdge = true; grp.add(me);
      };
      const hexa = (q, vec, mat, uvL) => {   // četrstūris (4 punkti) izvilkts pa vec
        const p = [...q, ...q.map(r => r.clone().add(vec))], pos = [];
        [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]].forEach(([a, b, c2, d]) => [a, b, c2, a, c2, d].forEach(i => pos.push(p[i].x, p[i].y, p[i].z)));
        const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
        if (uvL) { const uv = [], pv = new THREE.Vector3(); for (let i = 0; i < pos.length; i += 3) { pv.set(pos[i], pos[i + 1], pos[i + 2]); const t = uvL(pv); uv.push(t[0], t[1]); } g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2)); }   // dēļu raksts: u pa fasādi, v augšup
        const me = new THREE.Mesh(g, mat); grp.add(me); return me;
      };
      const at = (s, [x, y], t) => new THREE.Vector3(x, s.zAt(x, y) + t / s.nz, y);   // punkts uz slīpnes ar vertikālu bīdi t/nz
      const clip = (pl, a, n, d) => {   // pusplakne: paturam punktus ar (p-a)·n >= d
        const out = [], f = p => (p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1] - d;
        pl.forEach((p, i) => { const q = pl[(i + 1) % pl.length], fp = f(p), fq = f(q); if (fp >= 0) out.push(p); if ((fp >= 0) !== (fq >= 0)) { const k = fp / (fp - fq); out.push([p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k]); } });
        return out;
      };
      const rayHit = (m, n) => {   // attālums no punkta pa virzienu n līdz plāna kontūrai (0 = punkts jau uz kontūras)
        let best = 1e9;
        poly.forEach((p, i) => { const q = poly[(i + 1) % poly.length], dx = q[0] - p[0], dy = q[1] - p[1], dn = n[0] * dy - n[1] * dx; if (Math.abs(dn) < 1e-9) return;
          const t = ((p[0] - m[0]) * dy - (p[1] - m[1]) * dx) / dn, u = ((p[0] - m[0]) * n[1] - (p[1] - m[1]) * n[0]) / dn; if (u >= -1e-6 && u <= 1 + 1e-6 && t > -1e-6) best = Math.min(best, t); });
        return best > 1e8 ? 0 : best;
      };
      const key = (p) => p.map(v => Math.round(v)).join(",");
      const shared = {};
      S.forEach((s, k) => s.pl.forEach((p, i) => { const q = s.pl[(i + 1) % s.pl.length], a = [p[0], p[1], s.g.outer[i][2]], b = [q[0], q[1], s.g.outer[(i + 1) % s.pl.length][2]], kk = [key(a), key(b)].sort().join("|"); (shared[kk] = shared[kk] || []).push({ k, i }); }));
      const gutM = M(hexOf(P.noteku_tonis || "RAL 7016")), clampM = M("#22262a");
      const cylB = (a, b, r, mat) => { const d = new THREE.Vector3().subVectors(b, a), L = d.length(); if (L < 1) return; const me = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, 16), mat); me.position.copy(a).addScaledVector(d, .5); me.quaternion.setFromUnitVectors(up, d.clone().normalize()); grp.add(me); };
      const ball = (p, r, mat) => { const me = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8), mat); me.position.copy(p); grp.add(me); };
      // teknes pēc fasādes: pustekne ar 120 mm augstumu (augša vienā līmenī ar jumta malas augšu), āķi ik 600, gala vāki, notekcaurule Ø80 180 mm no stūra ar savienojumu, skavām un ceļgalu
      const gutter = (s, e, bt, ov, out, L3, O3, R0) => {
        const key = Math.abs(out[1]) > Math.abs(out[0]) ? (out[1] < 0 ? "north" : "south") : (out[0] < 0 ? "west" : "east"), NK = P.notekas || {};
        if (NK[key] === false || NK.visas === false) return;
        const r = 60, top = at(s, e.a, s.th + 4).y, zc = top - r, off = bt + r + 3, pt = (p, o, z) => new THREE.Vector3(p[0] + out[0] * o, z, p[1] + out[1] * o);
        const spans = []; poly.forEach((p, i) => { const q = poly[(i + 1) % poly.length], dx = q[0] - p[0], dy = q[1] - p[1], l = Math.hypot(dx, dy) || 1; if (Math.abs(dx * e.d[1] - dy * e.d[0]) / l > .01) return;
          const dist = (p[0] - e.a[0]) * e.ni[0] + (p[1] - e.a[1]) * e.ni[1]; if (Math.abs(dist - ov) > 8) return; const t0 = (p[0] - e.a[0]) * e.d[0] + (p[1] - e.a[1]) * e.d[1], t1 = (q[0] - e.a[0]) * e.d[0] + (q[1] - e.a[1]) * e.d[1]; spans.push([Math.min(t0, t1), Math.max(t0, t1)]); });
        // teknes gali: neiziet ārpus fasādes, beidzas 15 mm pirms tās (ja nav sienas, vecais pagarinājums)
        const tA = spans.length ? Math.min(...spans.map(q => q[0])) + 15 : -40, tB = spans.length ? Math.max(...spans.map(q => q[1])) - 15 : e.L + 40;
        const A = pt([e.a[0] + e.d[0] * tA, e.a[1] + e.d[1] * tA], off, zc), B = pt([e.a[0] + e.d[0] * tB, e.a[1] + e.d[1] * tB], off, zc), len = A.distanceTo(B);
        const gg = new THREE.CylinderGeometry(r, r, len, 28, 1, true, Math.PI / 2, Math.PI); gg.applyMatrix4(new THREE.Matrix4().makeBasis(O3, L3, up).setPosition(A.clone().add(B).multiplyScalar(.5))); grp.add(new THREE.Mesh(gg, gutM));
        [A, B].forEach(p => { const cg = new THREE.CircleGeometry(r, 28, Math.PI, Math.PI); cg.applyMatrix4(new THREE.Matrix4().makeBasis(O3, up, L3).setPosition(p)); grp.add(new THREE.Mesh(cg, gutM)); });   // gala vāki
        const nh = Math.max(1, Math.round((tB - tA) / 600));
        for (let i = 0; i <= nh; i++) { const t = Math.max(tA + 30, Math.min(tB - 30, tA + i * (tB - tA) / nh)), c0 = pt([e.a[0] + e.d[0] * t, e.a[1] + e.d[1] * t], off, zc);   // āķi: loks ap teknes profilu + josla uz dēļa
          const tg = new THREE.TorusGeometry(r + 2, 2.2, 6, 20, Math.PI); tg.applyMatrix4(new THREE.Matrix4().makeBasis(O3, up.clone().negate(), L3).setPosition(c0)); grp.add(new THREE.Mesh(tg, clampM));
        }
        // notekcaurules: pie sienas, 180 mm no stūra
        if (!spans.length) return;
        const t0 = Math.min(...spans.map(q => q[0])), t1 = Math.max(...spans.map(q => q[1])), ts = t1 - t0 > 1200 ? [t0 + 180, t1 - 180] : [(t0 + t1) / 2];
        ts.forEach(t => {
          const pe = [e.a[0] + e.d[0] * t, e.a[1] + e.d[1] * t], pw = [pe[0] + e.ni[0] * ov, pe[1] + e.ni[1] * ov], wo = 50, hz = off - ov - wo;
          const free = ov > 150;   // ar jumta pārkari noteka seko teknei: taisni lejup zem teknes, bez lieces uz sienu
          const P1 = pt(pe, off, zc - r + 30), P2 = P1.clone().setY(P1.y - 180), jog = free || Math.abs(hz) < 12 ? 0 : Math.max(300, Math.abs(hz) * 1.5), P3 = free ? P2.clone() : pt(pw, wo, P2.y - jog), P4 = free ? pt(pe, off, -150) : pt(pw, wo, -150);
          { const fg = new THREE.CylinderGeometry(58, 40, 50, 20, 1, true); const fm = new THREE.Mesh(fg, gutM); fm.position.copy(P1).setY(P1.y + 5); grp.add(fm); }   // notekas piltuve teknes dibenā
          cylB(P1, P2, 40, gutM); ball(P2, 40, gutM); if (jog) { cylB(P2, P3, 40, gutM); ball(P3, 40, gutM); } cylB(P3, P4, 40, gutM);
          for (let z = free ? 1e9 : 600; z < P3.y - 250; z += 1100) { const cl = new THREE.Mesh(new THREE.CylinderGeometry(46, 46, 30, 16), clampM); cl.position.set(P4.x, z, P4.z); grp.add(cl); }
          const foot = free ? pt(pe, off + 170, -215) : pt(pw, wo + 170, -215); ball(P4, 40, gutM); cylB(P4, foot, 40, gutM);   // apakšējais ceļgals uz āru
        });
      };
      const RE = [];   // vēja dēļu gali pie kores: 100 mm plakanā daļa starp tiem tiek aizpildīta
      S.forEach((s, k) => {
        const R0 = Math.max(0, s.th - SH - BT - RAF), n0 = s.pl.length, cen = s.pl.reduce((r, p) => [r[0] + p[0] / n0, r[1] + p[1] / n0], [0, 0]);
        let inner = s.pl.slice();
        const edges = s.pl.map((a, i) => {
          const b = s.pl[(i + 1) % n0], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 1) return null;
          const d = [(b[0] - a[0]) / L, (b[1] - a[1]) / L]; let ni = [-d[1], d[0]]; if ((cen[0] - a[0]) * ni[0] + (cen[1] - a[1]) * ni[1] < 0) ni = [-ni[0], -ni[1]];
          const za = s.g.outer[i][2], zb = s.g.outer[(i + 1) % n0][2], kk = [key([a[0], a[1], za]), key([b[0], b[1], zb])].sort().join("|"), mates = (shared[kk] || []).filter(q => q.k !== k);
          return { a, b, L, d, ni, za, zb, mates, i };
        }).filter(Boolean);
        edges.forEach(e => { if (e.mates.length) return; const mid = [(e.a[0] + e.b[0]) / 2, (e.a[1] + e.b[1]) / 2], onWall = poly.some((p, i) => { const q = poly[(i + 1) % poly.length], dx = q[0] - p[0], dy = q[1] - p[1], l2 = dx * dx + dy * dy || 1, u = Math.max(0, Math.min(1, ((mid[0] - p[0]) * dx + (mid[1] - p[1]) * dy) / l2)); return Math.hypot(mid[0] - p[0] - u * dx, mid[1] - p[1] - u * dy) < 6; });
          const ov = onWall ? 0 : rayHit(mid, e.ni); e.ov = ov > 5 && ov < 3000 ? ov : 0; if (e.ov) inner = clip(inner, e.a, e.ni, e.ov); });
        // pamatplaksne: viss pīrāgs [0..th], malas vertikālas
        slab(s, s.pl, s.th - SH - BT, s.th, [roofM, dark], true);   // augšējā kārta (latojumi + segums) visai slīpnei vienā gabalā, lai jumtā nav šuvju līniju
        slab(s, inner, 0, s.th - SH - BT, [dark, dark], true, true);   // spāru kārta: līnijas nav vajadzīgas (apakšā/sānos segta)
        edges.forEach(e => {
          const eave = !e.mates.length && Math.abs(e.za - e.zb) < 1 && s.zAt(cen[0], cen[1]) > e.za, out = [-e.ni[0], -e.ni[1]], ov = e.ov || 0, L3 = new THREE.Vector3(e.d[0], 0, e.d[1]), O3 = new THREE.Vector3(out[0], 0, out[1]);
          if (e.mates.length) {   // kore, grēda vai ieleja: metāla nosegs katrā pusē
            const o = S[e.mates[0].k], oc = o.pl.reduce((r, p) => [r[0] + p[0] / o.pl.length, r[1] + p[1] / o.pl.length], [0, 0]), convex = o.zAt(oc[0], oc[1]) < s.zAt(oc[0], oc[1]) - 1, w = convex ? 140 : 100;
            slab(s, [e.a, e.b, [e.b[0] + e.ni[0] * w, e.b[1] + e.ni[1] * w], [e.a[0] + e.ni[0] * w, e.a[1] + e.ni[1] * w]], s.th, s.th + (convex ? 10 : 6), [capM, capM], true);
            return;
          }
          const stripP = [e.a, e.b, [e.b[0] + e.ni[0] * ov, e.b[1] + e.ni[1] * ov], [e.a[0] + e.ni[0] * ov, e.a[1] + e.ni[1] * ov]];
          const full = s.th + 4, lo = R0 - 18;   // spāres gals vienmēr aizvērts: galda dēlis (dzega, vēja kaste) vai metāls (gals bez vēja kastes)
          const sdN = Math.abs(out[1]) > Math.abs(out[0]) ? (out[1] < 0 ? "north" : "south") : (out[0] < 0 ? "west" : "east"), flush = !ov && (eave || vk), tex = c.wallTex(sdN);   // bez pārkares: dzegas mala klāta ar to pašu vagondēli kā siena (14 mm), tikai augšā plāna metāla lāse
          const rake = !eave && ov > 0, bt = rake ? 25 : flush ? 3 : eave || vk ? 22 : 4, edgeM = rake ? (P.vejmala === "balta" ? M("#f2f2ef") : P.sparu_hex ? rafM : fasM) : flush || (!eave && vk) ? tex : eave ? fasM : capM;   // gals ar pārkari: spāres dekoratīvais dēlis (sparu_hex) pa slīpumu + metāla mala   // vēja kaste: fasādes dēļi (arī ar pārkari), augšā tikai plāns metāls
          if (ov) {   // pārkare: slīpā apakša (zem spārēm) + masīvs pīrāgs ar vertikālu griezumu
            slab(s, stripP, lo, R0, [sofM, sofM], true);
            slab(s, stripP, R0, s.th - SH - BT, [dark, dark], true);
          }
          const hiA = !eave && s.zAt(e.a[0], e.a[1]) > s.zAt(e.b[0], e.b[1]), ea = e.a, eb = e.b;
          hexa([at(s, ea, ov ? lo : 0), at(s, eb, ov ? lo : 0), at(s, eb, full), at(s, ea, full)], O3.clone().multiplyScalar(bt), edgeM, edgeM === tex ? c.wallUV(sdN, at(s, e.a, 0)) : null);
          { const sm = grp.children[grp.children.length - 1]; sm.userData.bk = { k: "ov" }; if (edgeM === tex) { sm.userData.noEdge = true; grp.userData.noSeam = true; if (!eave) { const he = hiA ? e.a : e.b; RE.push({ lo: at(s, he, 0), hi: at(s, he, full), O3, bt, tex, uv: c.wallUV(sdN, at(s, e.a, 0)) }); } } }   // bez pārkares: dēļi tajā pašā plaknē kā siena (3 mm), bez šuves līnijas   // galda / vēja dēlis vai metāla mala
          if (eave && !ov) hexa([at(s, ea, s.th - 55), at(s, eb, s.th - 55), at(s, eb, s.th - 53), at(s, ea, s.th - 53)].map(q => q.addScaledVector(O3, bt + 2.5)), O3.clone().multiplyScalar(7), capM);   // lāseņa nolaidums (atloks uz āru)
          if (eave || (vk && !ov) || rake) {   // metāla lāses mala virs dēļa (dzegai un vēja kastei bez pārkares)
            hexa([at(s, e.a, s.th - (flush ? 55 : 40)), at(s, e.b, s.th - (flush ? 55 : 40)), at(s, e.b, full + 2), at(s, e.a, full + 2)].map(q => q.addScaledVector(O3, bt)), O3.clone().multiplyScalar(2.5), capM);
            if (eave) gutter(s, e, bt, ov, out, L3, O3, R0);
          }
          if (!eave) slab(s, [e.a, e.b, [e.b[0] + e.ni[0] * 45, e.b[1] + e.ni[1] * 45], [e.a[0] + e.ni[0] * 45, e.a[1] + e.ni[1] * 45]], s.th, s.th + 4, [capM, capM], true);   // vēja loksnes metāla josla uz jumta
        });
      });
      RE.forEach((a, i) => RE.slice(i + 1).forEach(b => { if (a.O3.distanceTo(b.O3) > .01 || Math.hypot(a.lo.x - b.lo.x, a.lo.z - b.lo.z) > 250 || Math.abs(a.lo.y - b.lo.y) > 150) return;   // vēja dēļu galu starpa pie kores
        const m2 = hexa([a.lo, b.lo, b.hi, a.hi], a.O3.clone().multiplyScalar(a.bt), a.tex, a.uv); m2.userData.noEdge = true; }));
    }
    // ---------- logs kā realitātē: aplodas ārpusē, ailas odere, rāmis un spārns, dubultā stikla pakete 4-16-4 ar distancētāju ----------
    // dziļumi d mērīti no sienas ārējās virsmas uz iekšu: odere 0..120, rāmis 120..190, stikli 140..144 un 160..164, distancētājs 144..160
    function windowDetail(g, T, grp, frameM, glassM, picks, revM, facade) {
      const ni = new THREE.Vector3(g.n[0], 0, g.n[1]).normalize(), F = g.pts.map(T3).map(p => p.addScaledVector(ni, -T / 2));
      const cen = F.reduce((r, p) => r.add(p), new THREE.Vector3()).multiplyScalar(1 / F.length), at = (p, d) => p.clone().addScaledVector(ni, d);
      const spM = new THREE.MeshLambertMaterial({ color: "#1b1d1f", side: THREE.DoubleSide });
      const ring = (w, d0, d1, mat, inset) => ringMesh(F.map(p => p.clone().addScaledVector(ni, d0)), ni, -inset, -(inset + w), d1 - d0, mat, grp);
      { const rm = ringMesh(F.map(p => p.clone()), ni, -1, -20, 120, revM || frameM, grp, -1, -1);   // ailas odere (bez apakšas): aplodu tonī vai fasādes dēļi (projekts.logu_odere)
        if (facade) revealUV(rm, ni);
        const low = F.slice().sort((p, q) => p.y - q.y).slice(0, 2); if (Math.abs(low[0].y - low[1].y) < 2) {   // ailas apakšējā palodze vienmēr loga rāmja tonī
          const t = low[1].clone().sub(low[0]), L = t.length(); t.normalize(); const bxm = new THREE.Mesh(new THREE.BoxGeometry(L, 19, 120), frameM);
          bxm.applyMatrix4(new THREE.Matrix4().makeBasis(t, new THREE.Vector3(0, 1, 0), ni).setPosition(low[0].clone().add(low[1]).multiplyScalar(.5).addScaledVector(new THREE.Vector3(0, 1, 0), 9.5).addScaledVector(ni, 60))); grp.add(bxm); } }
      ring(50, 120, 190, frameM, 0);    // ārējais rāmis 50 × 70
      ring(35, 130, 182, frameM, 50);   // spārns
      ring(14, 144, 160, spM, 85);      // stikla distancētājs
      const pane = d => { const { n, u, v } = basis(F), to2 = p => new THREE.Vector2(p.clone().sub(F[0]).dot(u), p.clone().sub(F[0]).dot(v)), ge = new THREE.ExtrudeGeometry(new THREE.Shape(F.map(to2)), { depth: 4, bevelEnabled: false }), me = new THREE.Mesh(ge, glassM.clone());
        me.applyMatrix4(new THREE.Matrix4().makeBasis(u, v, n).setPosition(at(F[0], n.dot(ni) > 0 ? d : d + 4))); me.material.opacity = .5; me.userData.ref = g.ref; picks.push(me); grp.add(me); };
      pane(140); pane(160);
    }
    function buildScene(m) {
      const P = m.projekts || {}, tk = V.tone || lv0(), wallHex = (tk === lv0() && P.sienas_hex) || TONES[tk].sw, frameHex = (tk === lv0() && P.logu_hex) || hexOf(P.logu_tonis || TONES[tk].logi);
      const colOf = (v, fb) => !v ? fb : v === "tonis" ? wallHex : /^#/.test(v) ? v : hexOf(v), casHex = colOf(tk === lv0() && P.aplodas, frameHex), sillHex = colOf(tk === lv0() && P.palodzes, casHex);
      const geo = []; skpRb(m, geo);
      const grp = new THREE.Group(), walls = [], picks = [];
      const mat = (c, o = {}) => new THREE.MeshLambertMaterial(Object.assign({ color: c, side: THREE.DoubleSide }, o));
      const cladTex = (P.apdare_orient === "h" ? stripeTexH : stripeTex)(600, 4, .6, .1), seamTex = stripeTex(500, 1, .35, 0), sideHex = (tk === lv0() && P.fasade_side) || {}, wallM = {};
      const wallMat = sd => wallM[sd] || (wallM[sd] = [mat((sideHex[sd] && sideHex[sd].hex) || wallHex, { map: cladTex }), mat((sideHex[sd] && sideHex[sd].hex) || wallHex)]);   // [fasādes plakne ar dēļiem, ailu un galu malas]
      const mats = { M_WALL: mat(wallHex), M_INT: mat("#f2efe9"), M_FLOOR: mat(P.pamati === "platne" ? "#9a9a96" : hexOf(P.cokols || "RAL 9005")), M_ROOF: mat("#3c4146", { map: seamTex }), M_STAIR: mat("#c9a77c") };
      const frameM = mat(frameHex), casM = mat(casHex), sillM = mat(sillHex), glassM = mat("#6f8d9b", { transparent: true, opacity: .75 });
      const facts = { win: { south: 0, north: 0, east: 0, west: 0 }, door: { south: 0, north: 0, east: 0, west: 0 }, gable: { east: 0, west: 0 } };
      const roofs = [], WT = (geo.find(q => q.k === "s" && q.mat === "M_WALL") || {}).d || 283.5;
      const WL = geo.filter(q => q.k === "s" && q.mat === "M_WALL");
      const wallUV = (sd, p0) => {   // tas pats dēļu raksts kā sienas plaknei (izspiešanas UV): joslas dēļi turpina sienas dēļus
        const cand = WL.filter(q => sideOfN(q.dir) === sd).map(q => { const o = q.outer.map(T3), dir = new THREE.Vector3(q.dir[0], q.dir[2], q.dir[1]).normalize(), b = basis(o, dir); return { O: o[0], u: b.u, v: b.v, n: b.n }; });
        const w = cand.sort((a, b) => Math.abs(p0.clone().sub(a.O).dot(a.n)) - Math.abs(p0.clone().sub(b.O).dot(b.n)))[0];
        return p => w ? [p.clone().sub(w.O).dot(w.u), p.clone().sub(w.O).dot(w.v)] : [p.x, p.y];
      };
      geo.forEach(g => {
        if (g.k === "s" && g.mat === "M_ROOF") { roofs.push(g); return; }
        if (g.k === "s") { const me = extrude(g, g.mat === "M_WALL" ? wallMat(sideOfN(g.dir)) : mats[g.mat] || mats.M_WALL);
          if (g.mat === "M_ROOF" && P.parkare_hex && tk === lv0()) { const sf = extrude(Object.assign({}, g, { d: 18 }), mat(P.parkare_hex)); sf.userData.bk = { k: "ov" }; sf.position.addScaledVector(new THREE.Vector3(g.dir[0], g.dir[2], g.dir[1]).normalize(), -19); grp.add(sf); } /* jumta pārkares apakša savā tonī */ if (g.mat === "M_WALL") { me.userData.wallTop = g.outer.map(T3); try { trimShared(me, g, WL); } catch (e) { console.error("trim", e); } walls.push(me); me.userData.bk = { k: "fas", side: sideOfN(g.dir) }; } if (g.mat === "M_ROOF") me.userData.bk = { k: "ov" }; if (g.mat !== "M_INT" && g.mat !== "M_STAIR") grp.add(me); }
        else if (g.k === "g") {
          { const rsd = sideOf(g.pts, m.W, m.D) || "south", fac = P.logu_odere === "fasade"; windowDetail(g, WT, grp, frameM, glassM, picks, fac ? wallMat(rsd)[0] : casM, fac); }
          const sd = sideOf(g.pts, m.W, m.D); if (sd) { if (g.pts.some(p => p[2] > (m.jumts && m.jumts.eave || 2600) - 400) || g.pts.length > 4) facts.gable[sd] = (facts.gable[sd] || 0) + 1; else facts.win[sd]++; }
        } else if (g.k === "d") {
          const p3 = g.pts.map(T3); { const dm = planeMesh(p3, frameM.clone(), 0); dm.userData.ref = g.ref; picks.push(dm); grp.add(dm); } frameAround(p3, frameM, grp, 90, 100);
          const sd = sideOf(g.pts, m.W, m.D); if (sd) facts.door[sd]++;
        }
      });
      if (roofs.length) {
        const poly0 = m.poly && m.poly.length > 2 ? m.poly : [[0, 0], [m.W, 0], [m.W, m.D], [0, m.D]];
        try { roofDetail(roofs, { grp, poly: poly0.map(p => [+p[0], +p[1]]), P, roofM: mats.M_ROOF, th0: roofs[0].d || 300, wallPlain: sd => wallMat(sd)[1], wallTex: sd => wallMat(sd)[0], wallUV, vk: (m.jumts || {}).vejkaste !== false }); }
        catch (e) { console.error("3D jumts:", e); roofs.forEach(g => { const me = extrude(g, mats.M_ROOF); me.userData.bk = { k: "ov" }; grp.add(me); }); }
      }
      { const wg = geo.find(g => g.k === "s" && g.mat === "M_WALL"); try { details(m, geo, grp, mat, frameM, wg ? wg.d : 283.5, { casM, sillM, tk, wallHex, wallTex: sd => wallMat(sd)[0] }); } catch (e) { console.error("3D detaļas:", e); } }
      (m.freeWalls || []).forEach(f => { const hh = (m.jumts && m.jumts.eave) || 2600, b = new THREE.Mesh(new THREE.BoxGeometry(f[2], hh, f[3]), mat(wallHex)); b.position.set(f[0] + f[2] / 2, hh / 2, f[1] + f[3] / 2); grp.add(b); });   // brīvās sienas
      // terase
      const tr = terraceRect(m);
      if (tr) {
        const [x0, y0, x1, y1] = tr, h = 275, topZ = -25, bt = boardsTex();
        bt.repeat.set((x1 - x0) / 1000, (y1 - y0) / 1000); if (terr().side === "east" || terr().side === "west") bt.rotation = Math.PI / 2;
        const top = new THREE.MeshLambertMaterial({ map: bt }), side = new THREE.MeshLambertMaterial({ color: "#383e42" });
        const box = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, h, y1 - y0), [side, side, top, side, side, side]);
        box.position.set((x0 + x1) / 2, topZ - h / 2, (y0 + y1) / 2); grp.add(box);
      }
      // terases jumts (viena slīpuma; pilns vai tikai spāres) + stabi
      const R = tr && terr().roof;
      if (R && R.mode) {
        const t = terr(), dp = +t.depth || 1100, ov = 250, L = (tr[2] - tr[0]) + 2 * ov, hw = +R.h || 2500, sl = Math.max(2, Math.min(35, +R.sl || 10)) * Math.PI / 180, th = +R.th || 200;
        const run = dp + ov, dh = run * Math.tan(sl), len = Math.hypot(run, dh), ho = hw - dh;
        const side = t.side, lateral = (side === "south" || side === "north") ? [(tr[0] + tr[2]) / 2, side === "south" ? D0(m) : 0] : [side === "east" ? m.W : 0, (tr[1] + tr[3]) / 2];
        const yaw = { south: 0, north: Math.PI, east: Math.PI / 2, west: -Math.PI / 2 }[side];
        const lat = (side === "south" || side === "north") ? (tr[2] - tr[0]) : (tr[3] - tr[1]), Lm = lat + 2 * ov;
        const rg = new THREE.Group(); rg.position.set(lateral[0], 0, lateral[1]); rg.rotation.y = yaw;
        const rm = mats.M_ROOF, wood = mat("#b89868");
        if (R.mode === "pilns") {
          const sb = new THREE.Mesh(new THREE.BoxGeometry(Lm, 40, len), rm); sb.position.set(0, hw - dh / 2, run / 2); sb.rotation.x = Math.atan2(dh, run); rg.add(sb);
          const fb = new THREE.Mesh(new THREE.BoxGeometry(Lm, th, 40), wood); fb.position.set(0, ho - th / 2, run); rg.add(fb);
        }
        const sp = new THREE.Group();
        const n = Math.max(2, Math.round(Lm / 600) + 1), step = Lm / (n - 1);
        for (let i = 0; i < n; i++) { const r = new THREE.Mesh(new THREE.BoxGeometry(60, th, len), wood); r.position.set(-Lm / 2 + i * step, hw - dh / 2 - (R.mode === "pilns" ? th / 2 + 20 : 0), run / 2); r.rotation.x = Math.atan2(dh, run); sp.add(r); }
        rg.add(sp);
        const bm2 = new THREE.Mesh(new THREE.BoxGeometry(Lm, th, 60), wood); bm2.position.set(0, ho - th / 2, run); if (R.mode !== "pilns") rg.add(bm2);
        const pn = Math.max(2, Math.ceil(lat / 3000) + 1), ps = lat / (pn - 1);
        for (let i = 0; i < pn; i++) { const ph = ho - th - 25; const po = new THREE.Mesh(new THREE.BoxGeometry(140, ph, 140), wood); po.position.set(-lat / 2 + i * ps, -25 + ph / 2, dp - 100); rg.add(po); }
        grp.add(rg);
      }
      // zeme
      const gr = new THREE.Mesh(new THREE.PlaneGeometry(200000, 200000), new THREE.MeshLambertMaterial({ color: "#939c84" }));
      gr.rotation.x = -Math.PI / 2; gr.position.y = -301; grp.add(gr);
      grp.traverse(o => { if (o.isMesh && o !== gr && !(o.material && o.material.transparent)) { o.castShadow = true; o.receiveShadow = true; } }); gr.receiveShadow = true;
      // SketchUp stila malas: smalka melna līnija visai ģeometrijai (leņķis > 25°); virsmas nobīdītas, lai līnijas nemirgo
      { const edgeM = new THREE.LineBasicMaterial({ color: "#0b0d0e" }), ms = [];
        grp.traverse(o => { if (o.isMesh && o !== gr && o.geometry && !(o.material && !Array.isArray(o.material) && o.material.transparent)) ms.push(o); });
        ms.forEach(o => { (Array.isArray(o.material) ? o.material : [o.material]).forEach(q => { q.polygonOffset = true; q.polygonOffsetFactor = 1; q.polygonOffsetUnits = 1; });
          if (o.userData.noEdge) return;
          let eg = new THREE.EdgesGeometry(o.geometry, 25);
          if (o.userData.wallTop && grp.userData.noSeam) {   // sienas augšmala sakrīt ar vagondēļa joslu tajā pašā plaknē: šuves līniju nerāda
            o.updateMatrix(); const ep = eg.attributes.position, WT2 = o.userData.wallTop, keep = [], a = new THREE.Vector3(), b = new THREE.Vector3();
            const dseg = (p, q, r) => { const d = q.clone().sub(p), t = Math.max(0, Math.min(1, r.clone().sub(p).dot(d) / (d.lengthSq() || 1))); return r.distanceTo(p.clone().addScaledVector(d, t)); };
            for (let i = 0; i < ep.count; i += 2) { a.fromBufferAttribute(ep, i).applyMatrix4(o.matrix); b.fromBufferAttribute(ep, i + 1).applyMatrix4(o.matrix); let drop = false;
              WT2.forEach((p, k) => { const q = WT2[(k + 1) % WT2.length]; if (Math.min(p.y, q.y) < 50 || Math.abs(p.y - q.y) < 1 && p.y < 50) return; if (Math.hypot(q.x - p.x, q.z - p.z) < 5) return; if (dseg(p, q, a) < 3 && dseg(p, q, b) < 3) drop = true; });
              if (!drop) keep.push(ep.getX(i), ep.getY(i), ep.getZ(i), ep.getX(i + 1), ep.getY(i + 1), ep.getZ(i + 1)); }
            eg = new THREE.BufferGeometry(); eg.setAttribute("position", new THREE.Float32BufferAttribute(keep, 3)); }
          if (o.userData.oth) { o.updateMatrix(); const ep = eg.attributes.position, keep = [], a = new THREE.Vector3(), b = new THREE.Vector3(), mid = new THREE.Vector3();   // līnijas uz blakus sienas plaknes, ar tās kontūras iekšpusē, nerāda
            const dist2 = (p, poly) => { let d = 1e9; poly.forEach((q, i) => { const r = poly[(i + 1) % poly.length], dx = r[0] - q[0], dy = r[1] - q[1], l2 = dx * dx + dy * dy || 1, t = Math.max(0, Math.min(1, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / l2)); d = Math.min(d, Math.hypot(p[0] - q[0] - dx * t, p[1] - q[1] - dy * t)); }); return d; };
            const inside = (pt, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a2 = poly[i], b2 = poly[j]; if ((a2[1] > pt[1]) !== (b2[1] > pt[1]) && pt[0] < (b2[0] - a2[0]) * (pt[1] - a2[1]) / (b2[1] - a2[1]) + a2[0]) c = !c; } return c; };
            for (let i = 0; i < ep.count; i += 2) { a.fromBufferAttribute(ep, i).applyMatrix4(o.matrix); b.fromBufferAttribute(ep, i + 1).applyMatrix4(o.matrix); mid.copy(a).add(b).multiplyScalar(.5); let drop = false;
              o.userData.oth.forEach(w => { if (drop) return; const dd = mid.clone().sub(w.O).dot(w.nn), pa = a.clone().sub(w.O).dot(w.nn), pb = b.clone().sub(w.O).dot(w.nn); if (Math.abs(pa - pb) > 1) return; if (Math.abs(dd) > 1 && Math.abs(dd - w.q.d) > 1 && Math.abs(dd + w.q.d) > 1) return; const p2 = [mid.clone().sub(w.O).dot(w.b.u), mid.clone().sub(w.O).dot(w.b.v)]; if (inside(p2, w.p2) && dist2(p2, w.p2) > 3) drop = true; });
              if (!drop) keep.push(ep.getX(i), ep.getY(i), ep.getZ(i), ep.getX(i + 1), ep.getY(i + 1), ep.getZ(i + 1)); }
            eg = new THREE.BufferGeometry(); eg.setAttribute("position", new THREE.Float32BufferAttribute(keep, 3)); }
          const l = new THREE.LineSegments(eg, edgeM); l.userData.edge = 1; l.raycast = () => {}; l.castShadow = false; l.receiveShadow = false; o.add(l); }); }
      return { grp, walls, facts, tr, picks, gr };
    }
    // ---------- kamera ----------
    function bbox(m) {
      const J = m.jumts || {}, eave = J.eave || 2600, ridge = eave + m.D / 2 * Math.tan((J.pitch || 30) * Math.PI / 180), tr = terraceRect(m) || [0, 0, 0, 0];
      const ex = (m.terraces || []).flatMap(t => t.poly || []).concat((m.posts || []).flatMap(q => [[q.x, q.y], [q.x + (+q.w || 0), q.y + (+q.d || 0)]]));   // terases un stabi arī ietilpst kadrā
      const x0 = Math.min(0, tr[0], ...ex.map(q => q[0])), x1 = Math.max(m.W, tr[2], ...ex.map(q => q[0])), y0 = Math.min(0, tr[1], ...ex.map(q => q[1])), y1 = Math.max(m.D, tr[3], ...ex.map(q => q[1]));
      return { x0, x1, y0, y1, z0: -300, z1: ridge };
    }
    function camFor(az, bb) {   // fotogrāfa kadrs: līmenis horizonts, 1,6 m augstumā, kameras nobīde (shift)
      const cx = (bb.x0 + bb.x1) / 2, cz = (bb.y0 + bb.y1) / 2, a = az * Math.PI / 180, dirv = [Math.sin(a), Math.cos(a)];
      const cam = new THREE.PerspectiveCamera(fovOf(V.lens), ASPECT, 100, 400000), corners = [];
      [bb.x0, bb.x1].forEach(x => [bb.y0, bb.y1].forEach(y => [bb.z0, bb.z1].forEach(z => corners.push(new THREE.Vector3(x, z, y)))));
      let dist = 8000;
      for (; dist < 120000; dist += 400) {
        cam.position.set(cx + dirv[0] * dist, CAM_H, cz + dirv[1] * dist); cam.lookAt(cx, CAM_H, cz); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
        const sh = vShift(cam), ok = corners.every(c => { const p = c.clone().project(cam); return Math.abs(p.x) <= .76 && p.y - sh >= -.9 && p.y - sh <= .86; });
        if (ok) break;
      }
      return { dist, cx, cz };
    }
    // horizonts apakšējā trešdaļā: kadru paceļ virs horizonta (shift)
    function vShift() { return 1 / 3; }   // kadra nobīde: punkta y logā = y - 1/3 (horizonts lejas trešdaļā)
    function applyCam() {
      const m = model, bb = V.bb = bbox(m); V.cam = V.ortho ? V.camO : V.camP; const cam = V.cam, a = V.az * Math.PI / 180, el = V.free ? V.el * Math.PI / 180 : 0;
      const f = V.free ? { dist: V.dist, cx: (bb.x0 + bb.x1) / 2, cz: (bb.y0 + bb.y1) / 2 } : camFor(V.az, bb); V.dist = V.dist0 || f.dist; V.cx = f.cx; V.cz = f.cz;
      const pn = V.free && V.pan ? V.pan : [0, 0, 0], cx = V.cx + pn[0], cz = V.cz + pn[2], ty = V.free ? 1400 + pn[1] : CAM_H, d = V.dist;
      cam.position.set(cx + Math.sin(a) * Math.cos(el) * d, ty + Math.sin(el) * d, cz + Math.cos(a) * Math.cos(el) * d);
      cam.lookAt(cx, ty, cz);
      const W = V.w, H = V.h;
      if (V.ortho) { const hh = d * Math.tan(fovOf(V.lens) * Math.PI / 360), hw = hh * W / H; cam.left = -hw; cam.right = hw; cam.top = hh; cam.bottom = -hh; cam.updateProjectionMatrix(); return; }   // paralēlā projekcija (kā SketchUp): tas pats kadrs bez perspektīvas
      if (V.free) cam.clearViewOffset(); else cam.setViewOffset(W, H, 0, -H / 6, W, H);   // horizonts apakšējā trešdaļā
      cam.fov = fovOf(V.lens); cam.aspect = W / H; cam.updateProjectionMatrix();
    }
    function resize() {
      const st = $("v3stage"), r = st.getBoundingClientRect(); let w = r.width - 20, h = w / ASPECT; if (h > r.height - 20) { h = r.height - 20; w = h * ASPECT; }
      w = Math.max(200, Math.floor(w)); h = Math.floor(w / ASPECT); V.w = w; V.h = h;
      V.renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1)); V.renderer.setSize(w, h, false);
      V.canvas.style.width = w + "px"; V.canvas.style.height = h + "px"; draw();
    }
    function draw() { if (!V.renderer) return; applyCam(); sun(); V.light.castShadow = !!V.shadows; V.renderer.render(V.scene, V.cam); }
    function sun() {   // saule no kameras puses, pa kreisi un augstu: fasāde izgaismota, pārkare met ēnu
      const a = (V.az + 35) * Math.PI / 180, cx = V.cx || 0, cz = V.cz || 0; V.light.target.position.set(cx, 1200, cz); V.light.position.set(cx + Math.sin(a) * 30000, 26000, cz + Math.cos(a) * 30000); V.light.target.updateMatrixWorld();
    }
    function rebuild() {
      if (!V.scene) return;
      if (V.grp) V.scene.remove(V.grp);
      const r = buildScene(model);
      if (V.kar) {   // ražošanas karkass: apvalks nerādās, tikai zeme un karkass
        const ms = $("v3kMsg"), now = JSON.stringify(model);
        if (V.kdata && V.kAt === now) { const op = Math.max(0, Math.min(1, (V.kShell || 0) / 100));   // apvalka redzamība karkasa režīmā: 0 = paslēpts, 100 = pilns
          if (op <= 0) r.grp.children.slice().forEach(c => { if (c !== r.gr) r.grp.remove(c); });
          else { const lm = new THREE.LineBasicMaterial({ color: "#0b0d0e", transparent: true, opacity: op * .7 }); r.grp.traverse(o => { if (o === r.gr) return; if (o.isLineSegments) { o.material = lm; return; } if (o.isMesh) { (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => { m.transparent = true; m.opacity = (m.opacity == null ? 1 : m.opacity) * op; m.depthWrite = false; m.needsUpdate = true; }); o.castShadow = false; o.receiveShadow = false; } }); }
          r.grp.add(buildFrame(V.kdata, V.kLay || "")); r.picks = []; r.walls = []; if (ms) ms.textContent = `${V.kdata.det.length} karkasa detaļas, ${V.kdata.spares.length} spāres${V.kSnap ? " (pēc lapas būvēšanas brīža modeļa)" : ""}`; }
        else if (!V.kBusy) {
          const snap = () => { if (!KAR_SNAP) return false; V.kdata = KAR_SNAP; V.kAt = now; V.kSnap = true; V.kBusy = false; rebuild(); return true; };
          V.kBusy = true;
          if (!(window.MM_LOCAL || {}).key) { if (snap()) return; V.kBusy = false; V.kar = false; syncKar(); if (ms) ms.textContent = "Karkasu neizdevās uzbūvēt."; }
          else { if (ms) ms.textContent = "Gatavo karkasu…";
            fetch("/api/karkass3d/" + window.MM_LOCAL.key, { method: "POST", headers: { "Content-Type": "application/json" }, body: now }).then(async x => { if (!x.ok) throw new Error((await x.text()) || x.status); return x.json(); })
              .then(j => { V.kdata = j; V.kAt = now; V.kSnap = false; V.kBusy = false; rebuild(); }).catch(e => { if (!snap()) { V.kBusy = false; V.kar = false; syncKar(); if (ms) ms.textContent = "Karkasu neizdevās uzbūvēt: " + ((e && e.message) || e); rebuild(); } }); }
        }
      } else { const ms = $("v3kMsg"); if (ms) ms.textContent = ""; }
      V.grp = r.grp; V.walls = r.walls; V.picks = r.picks; V.picked = null; V.facts = r.facts; V.scene.add(V.grp); draw(); promptUpdate();
    }
    // ---------- prompts (viz.py angļu teksti) ----------
    const KEEP = "DO NOT CHANGE (the reference image is exact): camera position and angle, house outline and proportions, roof shape and pitch, position, width, height and number of every window and door. Do not add, remove, merge, enlarge or divide any opening. Window and door frames keep the colour shown.";
    const FORBID_T = "Do not add: any other terrace, deck, patio or steps than the one shown in the reference, railings, furniture, people, animals, cars, fences, lamps, signs, text, logos, plants or bushes against the walls, extra buildings.";
    function atmText() {
      let k = V.atm; if (k === "auto") { let n = 1; try { n = parseInt(String(model.id).split("-").pop(), 10) || 1; } catch (e) {} k = ATM_KEYS[(n - 1) % ATM_KEYS.length]; }
      return (ATM[k] || ATM[ATM_KEYS[0]]).en;
    }
    function visibleSides(id) { return id.length === 1 ? [{ S: "south", N: "north", E: "east", W: "west" }[id]] : [{ S: "south", N: "north" }[id[0]], { E: "east", W: "west" }[id[1]]]; }
    function cameraText(id) {
      const base = `eye-level photograph from 1.6 m above the ground, ${V.lens} mm lens (35 mm equivalent), `+" 3:2 frame, vertical lines perfectly straight (architectural shift lens), the whole house together with its whole terrace is fully visible inside the frame with comfortable margins on all sides (house and terrace fill about three quarters of the frame width), horizon in the lower third.";
      const vs = visibleSides(id), nm = s => ({ south: "south", north: "north", east: "east", west: "west" })[s];
      const v = id.length === 1 ? `Straight-on view of the ${nm(vs[0])} facade, camera exactly perpendicular to that wall and centred on the house.` : `Classic three-quarter view from the ${nm(vs[0])}-${nm(vs[1])} corner: the ${nm(vs[0])} and the ${nm(vs[1])} facades are both visible at the angle shown in the reference.`;
      return `Camera: ${v} ${base} Style: photorealistic professional architectural photography, real materials, sharp detail, natural lens, no illustration look, no CGI look.`;
    }
    function openingsText(id) {
      const f = V.facts || { win: {}, door: {}, gable: {} }, vs = visibleSides(id), parts = [];
      vs.forEach(s => {
        const nw = f.win[s] || 0, nd = f.door[s] || 0, ng = (f.gable && f.gable[s]) || 0;
        parts.push(`the ${s} facade has ${nd ? nd + " exterior door(s) and " : "NO door and "}${nw ? "exactly " + nw + " window(s)" : "NO windows at all"}${ng ? " and " + ng + " sloped pentagon (house-shaped) window in the gable" : ""}${nw || nd || ng ? ", nothing else" : ""}`);
      });
      return ` OPENING COUNT (from the reference image, exact): ${parts.join("; ")}; the rest of every wall is plain cladding. Windows with a pentagon outline must stay clearly pentagonal with vertical sides and a pointed top parallel to the roof slopes. Do not invent any additional window, door, vent or shutter anywhere.`;
    }
    function materialsText(tk) {
      const t = TONES[tk], P = model.projekts || {}, J = model.jumts || {}, ck = P.cokols || "RAL 9005", tr = terr(), ov = +J.ov || 0, pitch = J.pitch || 30;
      const plinth = ck === "RAL 7016" ? "anthracite grey metal plinth RAL 7016" : "black metal plinth RAL 9005";
      const wall = { peleks: `painted graphite grey (close to RGB ${t.sw})`, sarkans: `painted traditional Norwegian red (close to RGB ${t.sw})`, koks: `natural oiled timber, warm honey-brown (close to RGB ${t.sw})`,
        zals: `painted dark forest green, deep and muted, matte Scandinavian paint (close to RGB ${t.sw})`, balts: `painted soft light grey-white, matte Scandinavian paint, clean and bright but not pure white (close to RGB ${t.sw})` }[tk];
      const frames = { "RAL 9016": "white (RAL 9016)", "RAL 9005": "black (RAL 9005)" }[t.logi] || "anthracite grey (RAL 7016)";
      let found;
      if (tr) {
        const lng = (tr.side === "south" || tr.side === "north") ? model.W : model.D, ext = (+tr.a || 0) + (+tr.b || 0);
        found = `The house stands directly on the ground. NO concrete, NO foundation, NO plinth, NO posts and NO slab edge are visible: only a wooden terrace (single step, about 25 cm above the ground) touches the ground and the house. The vertical cladding boards go down to the terrace deck surface and stop there. The terrace is made of horizontal anthracite grey (RAL 7016) wooden deck boards laid along the ${tr.side} wall, thin gaps between boards. It runs ${(+tr.depth / 1000 || 1.1).toFixed(1)} m deep along the whole ${tr.side} wall${ext ? ` and continues ${((+tr.a || 0) / 1000).toFixed(1)} m / ${((+tr.b || 0) / 1000).toFixed(1)} m beyond the wall ends` : ""}, exactly as in the reference image (no railing, no furniture on it). The doors on that wall open onto the terrace.`;
      } else found = P.pamati === "platne" ? "The house stands on a concrete slab foundation with a low plain concrete plinth, about 30 cm high." : `The house stands on a hidden post foundation: a ${plinth} about 30 cm high, with a thin shadow gap above the ground.`;
      const gut = t.vejmala === "balta" ? "mounted on the white fascia board directly under the roof edge" : "fixed to the top of the cladding boards directly under the roof edge (there is no fascia board)";
      let s = `Materials: walls are vertical cladding boards ${wall}. Roof: dark anthracite standing seam steel RAL 7016, pitch ${pitch}°, ${ov > 0 ? `a slim roof overhang of about ${Math.round(ov / 10)} cm` : "no overhang"}, thin anthracite gutter ${gut} and a round anthracite downpipe ending 5 cm above the ${tr ? "terrace deck" : "ground"}. ` +
        `Windows and exterior doors: ${frames} frames, set back (recessed) into the wall about 15 cm, NOT flush with the cladding; the window reveals are clad in the same colour as the facade. The entrance door leaf is flat in the frame colour with one narrow vertical glass strip and a long vertical stainless steel bar handle, as in the reference image. Every window has a thin projecting metal drip sill in the frame colour. Flat casing boards (about 10 cm wide) around every window and door are in the frame colour: ${frames}. Glass reflects the overcast sky. ${found}`;
      if (t.vejmala === "balta") s += " The fascia board and the sloping roof verge boards are white painted timber (classic Norwegian detail).";
      else s += " NO horizontal fascia board anywhere: the vertical cladding boards run straight up the wall to the underside of the roof edge; the roof edge is only a slim roof-coloured RAL 7016 metal flashing about 10 cm thick.";
      if (t.sturi) s += ` White corner trims ${t.sturi} mm wide on every corner of the house (classic Norwegian detail).`;
      return s;
    }
    function promptText() {
      const id = V.view, tk = V.tone || lv0();
      return "Turn this technical reference image of a house into a photorealistic photograph. " + KEEP + " " + materialsText(tk) + openingsText(id) + " Setting: " + atmText().replace(/^Setting:\s*/, "") + " Realistic Scandinavian colours. " + cameraText(id) + " " + FORBID_T;
    }
    function promptUpdate() { if ($("v3prompt")) $("v3prompt").value = promptText(); }
    // ---------- UI ----------
    // 3/4 skatu azimuts: garākā fasāde dominē (35° no tās normāles), īsā fasāde kā otrais plāns; fasāžu skati 0/90/180/270
    function viewAz(id) { const v = VIEWS.find(q => q[0] === id), L = (model.W || 1) >= (model.D || 1), b = L ? 35 : 55; return { SE: b, NE: 180 - b, NW: 180 + b, SW: 360 - b }[id] ?? v[2]; }
    function syncCam() { if ($("v3free")) $("v3free").checked = !!V.free; if ($("v3ortho")) $("v3ortho").checked = !!V.ortho; }
    function enterFree() { if (V.free) return; V.free = true; V.el = V.el || 0; V.pan = [0, CAM_H - 1400, 0]; syncCam(); }
    function setView(id) { V.view = id; V.az = viewAz(id); V.dist0 = null; V.pan = [0, 0, 0]; V.el = /^[NSEW]$/.test(id) ? 0 : (V.ortho ? 20 : 0); V.free = !!V.ortho; syncCam(); document.querySelectorAll("#v3views button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === id))); draw(); promptUpdate(); }
    function saveTerrace(patch) {
      const n = clone(model); n.terase = patch === null ? null : Object.assign({ side: "south", depth: 1100, a: 0, b: 0 }, n.terase || {}, patch); commit(n); rebuild(); terraceUI();
    }
    function terraceUI() {
      const t = terr(); $("v3tOn").checked = !!t; $("v3tBox").hidden = !t;
      if (t) { const R = t.roof || {}; $("v3rMode").value = R.mode || ""; $("v3rH").value = R.h || 2500; $("v3rSl").value = R.sl || 10; $("v3tSide").value = t.side; $("v3tDepth").value = t.depth; $("v3tA").value = t.a || 0; $("v3tB").value = t.b || 0; }
    }
    async function savePng() {
      const r = V.renderer, w0 = V.w, h0 = V.h, pr = r.getPixelRatio();
      V.w = 2400; V.h = 1600; r.setPixelRatio(1); r.setSize(2400, 1600, false); applyCam(); sun(); r.render(V.scene, V.cam);
      const blob = await new Promise(ok => V.canvas.toBlob(ok, "image/png"));
      V.w = w0; V.h = h0; r.setPixelRatio(pr); r.setSize(w0, h0, false); draw();
      const name = `${model.id}_ref_${V.view}.png`;
      if (dl) { try { await dl.save({ filename: name, data: blob }); } catch (e) { if (e && e.code !== "declined") status("PNG saglabāšana neizdevās: " + (e.message || e.code)); } }
      else { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove(); }
    }
    async function copyPrompt() {
      const ta = $("v3prompt"), txt = ta.value;
      try { await navigator.clipboard.writeText(txt); status("Prompts nokopēts."); } catch (e) { ta.select(); try { document.execCommand("copy"); status("Prompts nokopēts."); } catch (e2) { status("Atzīmē tekstu un spied Ctrl+C."); } }
      $("v3copy").textContent = "Nokopēts ✓"; setTimeout(() => { $("v3copy").textContent = "Kopēt promptu"; }, 1500);
    }
    function init() {
      if (V.inited) return; V.inited = true;
      if (!window.THREE) { $("v3stage").innerHTML = "<p class='v3msg'>3D bibliotēka nav ielādēta.</p>"; return; }
      V.canvas = $("v3canvas"); V.renderer = new THREE.WebGLRenderer({ canvas: V.canvas, antialias: true, preserveDrawingBuffer: true });
      V.renderer.setClearColor(0xe8ecef, 1); V.scene = new THREE.Scene(); V.scene.background = new THREE.Color(0xe8ecef);
      V.scene.add(new THREE.HemisphereLight(0xffffff, 0x99a090, .8)); V.light = new THREE.DirectionalLight(0xffffff, .75); V.scene.add(V.light); V.scene.add(V.light.target);
      V.renderer.shadowMap.enabled = true; V.shadows = !!V.shadows; V.renderer.shadowMap.type = THREE.PCFSoftShadowMap; V.light.castShadow = true; V.light.shadow.mapSize.set(4096, 4096); V.light.shadow.bias = -0.0004; V.light.shadow.normalBias = 40;
      { const c = V.light.shadow.camera; c.left = c.bottom = -22000; c.right = c.top = 22000; c.near = 1000; c.far = 120000; c.updateProjectionMatrix(); }
      V.camP = V.cam = new THREE.PerspectiveCamera(fovOf(V.lens), ASPECT, 100, 400000); V.camO = new THREE.OrthographicCamera(-1, 1, 1, -1, 100, 400000);
      $("v3views").innerHTML = VIEWS.map(v => `<button type="button" data-v="${v[0]}" aria-pressed="false">${v[1]}</button>`).join("");
      $("v3views").onclick = e => { const b = e.target.closest("button"); if (b) setView(b.dataset.v); };
      $("v3tone").innerHTML = Object.keys(TONES).map(k => `<option value="${k}">${TONE_N[k] || k}</option>`).join("");
      $("v3atm").innerHTML = `<option value="auto">Automātiski (pēc modeļa nr.)</option>` + ATM_KEYS.map(k => `<option value="${k}">${(ATM[k].lv || k)}</option>`).join("");
      $("v3tone").onchange = e => { V.tone = e.target.value; rebuild(); };
      $("v3atm").onchange = e => { V.atm = e.target.value; promptUpdate(); };
      $("v3lens").onchange = e => { V.lens = +e.target.value; V.dist0 = null; draw(); promptUpdate(); };
      $("v3mode").onclick = e => { const b = e.target.closest("button"); if (!b) return; V.kar = b.dataset.k === "1"; syncKar(); rebuild(); };
      $("v3kLay").onchange = e => { V.kLay = e.target.value; rebuild(); };
      $("v3kOp").oninput = e => { V.kShell = +e.target.value; $("v3kOpV").textContent = V.kShell + " %"; rebuild(); };
      $("v3shad").onchange = e => { V.shadows = e.target.checked; draw(); };   // ēnas (pēc noklusējuma izslēgtas)
      $("v3odere").onchange = e => { const n = clone(model); n.projekts = n.projekts || {}; if (e.target.value === "fasade") n.projekts.logu_odere = "fasade"; else delete n.projekts.logu_odere; commit(n); rebuild(); };
      $("v3free").onchange = e => { V.free = e.target.checked; if (V.free) { V.el = 12; V.dist0 = null; V.pan = V.pan || [0, 0, 0]; } draw(); };
      $("v3ortho").onchange = e => { V.ortho = e.target.checked; if (V.ortho) { V.free = true; V.pan = V.pan || [0, 0, 0]; } syncCam(); draw(); };
      const orb = (az, el, ortho) => { V.az = az; V.el = el; V.ortho = ortho; V.free = true; V.pan = [0, 0, 0]; V.dist0 = null; document.querySelectorAll("#v3views button").forEach(b => b.setAttribute("aria-pressed", "false")); syncCam(); draw(); };
      $("v3kviews").onclick = e => { const b = e.target.closest("button"); if (b) orb(+b.dataset.a, +b.dataset.e, true); };
      $("v3iso").onclick = () => orb(viewAz("SE"), 35.264, true); $("v3top").onclick = () => orb(0, 89, true);
      $("v3tOn").onchange = e => saveTerrace(e.target.checked ? {} : null);
      $("v3tSide").onchange = e => saveTerrace({ side: e.target.value });
      [["v3rMode", "mode"], ["v3rH", "h"], ["v3rSl", "sl"]].forEach(([id, k]) => { $(id).onchange = e => saveTerrace({ roof: Object.assign({}, (terr() || {}).roof, { [k]: k === "mode" ? e.target.value : +e.target.value || 0 }) }); });
      [["v3tDepth", "depth"], ["v3tA", "a"], ["v3tB", "b"]].forEach(([id, k]) => { $(id).onchange = e => saveTerrace({ [k]: Math.max(0, +e.target.value || 0) }); });
      $("v3bkRal").innerHTML = `<option value="">Brīva krāsa</option>` + Object.entries(RAL).map(([k, v]) => `<option value="${k}">${k} · ${v[0]}</option>`).join("");
      $("v3bk").onchange = e => { V.bucket = e.target.checked; if (V.bucket) { V.addTer = false; $("v3add").checked = false; } bkUI(); };
      $("v3add").onchange = e => { V.addTer = e.target.checked; if (V.addTer) { V.bucket = false; $("v3bk").checked = false; } bkUI(); V.canvas.style.cursor = V.addTer ? "crosshair" : ""; };
      $("v3bkRal").onchange = e => { const k = e.target.value; if (k) { BMAT.ral = k; BMAT.col = RAL[k][1]; BMAT.tex = null; } else BMAT.ral = null; bkUI(); };
      $("v3bkCol").onchange = e => { BMAT.col = e.target.value; BMAT.ral = null; BMAT.tex = null; bkUI(); };
      $("v3bkTex").onclick = () => $("v3bkFile").click();
      $("v3bkFile").onchange = () => { const f = $("v3bkFile").files[0]; $("v3bkFile").value = ""; if (f) terUpload(f, url => { BMAT.tex = url; BMAT.ral = null; bkUI(); status("Tekstūra izvēlēta: klikšķis uz staba, terases vai lieveņa to uzliek."); }); };
      $("v3bkNoTex").onclick = () => { BMAT.tex = null; bkUI(); };
      $("v3copy").onclick = copyPrompt; $("v3png").onclick = savePng; $("v3close").onclick = close;
      $("v3reset").onclick = () => { V.dist0 = null; V.free = false; V.ortho = false; V.el = 0; V.pan = null; syncCam(); draw(); };
      V.canvas.addEventListener("dblclick", () => $("v3reset").click()); V.canvas.addEventListener("contextmenu", e => e.preventDefault()); V.canvas.addEventListener("mousedown", e => { if (e.button === 1) e.preventDefault(); });
      let dr = null;
      const rayOf = e => { const r = V.canvas.getBoundingClientRect(), ray = new THREE.Raycaster(); ray.setFromCamera(new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height * 2 - 1)), V.cam); return ray; };
      V.canvas.addEventListener("pointerdown", e => {
        if (e.button === 1) e.preventDefault(); dr = { x: e.clientX, y: e.clientY, moved: 0 }; V.canvas.setPointerCapture(e.pointerId); V.dragWin = null;
        const ph = rayOf(e).intersectObjects(V.picks || [], false)[0], rf = ph && ph.object.userData.ref;
        if (rf && rf.k === "win" && V.picked === ph.object) {   // izvēlēta loga vilkšana pa sienu
          const o = model.windows[rf.i], nrm = ph.face.normal.clone().transformDirection(ph.object.matrixWorld);
          V.dragWin = { i: rf.i, o: o.o, p0: ph.point.clone(), plane: new THREE.Plane().setFromNormalAndCoplanarPoint(nrm, ph.point), x0: o.o === "h" ? o.x : o.y, len: o.len, moved: false };
        }
      });
      V.canvas.addEventListener("pointermove", e => {
        if (!dr) return; const dx = e.clientX - dr.x, dy = e.clientY - dr.y; dr.moved += Math.abs(dx) + Math.abs(dy); dr.x = e.clientX; dr.y = e.clientY;
        if (V.dragWin) {
          const w = V.dragWin, pt = new THREE.Vector3(); if (!rayOf(e).ray.intersectPlane(w.plane, pt)) return;
          const del = w.o === "h" ? pt.x - w.p0.x : pt.z - w.p0.z, lim = w.o === "h" ? model.W : model.D;
          const nv = Math.round(Math.max(0, Math.min(lim - w.len, w.x0 + del)) / 10) * 10, n = clone(model), o = n.windows[w.i];
          if ((w.o === "h" ? o.x : o.y) !== nv) { if (w.o === "h") o.x = nv; else o.y = nv; w.moved = true; commit(n); const keep = w.i; rebuild(); const mm = (V.picks || []).find(q => q.userData.ref && q.userData.ref.k === "win" && q.userData.ref.i === keep); if (mm) { V.picked = mm; mm.material.emissive && mm.material.emissive.setHex(0x2266d8); draw(); } }
          return;
        }
        if ((e.buttons & 4) ? e.shiftKey : (e.shiftKey || (e.buttons & 2))) {   // rullīša poga: orbīta, Shift+rullītis: pārbīde (kā SketchUp); kreisā poga arī orbīta, labā pārbīde: kustina mērķa punktu ekrāna plaknē
          enterFree(); const k = V.dist * Math.tan(fovOf(V.lens) * Math.PI / 360) * 2 / V.h, aa = V.az * Math.PI / 180; V.pan = V.pan || [0, 0, 0];
          V.pan[0] -= Math.cos(aa) * dx * k; V.pan[2] += Math.sin(aa) * dx * k; V.pan[1] += dy * k;
        } else { enterFree(); V.az = (V.az - dx * .4 + 360) % 360; V.el = Math.max(-5, Math.min(89, V.el + dy * .3)); }   // orbīta ap māju kā SketchUp
        document.querySelectorAll("#v3views button").forEach(b => b.setAttribute("aria-pressed", "false")); draw();
      });
      V.canvas.addEventListener("pointerup", e => {
        const moved = dr && dr.moved; dr = null; if (V.dragWin) { const mv = V.dragWin.moved; V.dragWin = null; if (mv || moved > 4) return; } if (moved > 4) { snapName(); return; }
        const r = V.canvas.getBoundingClientRect(), ray = new THREE.Raycaster(); ray.setFromCamera(new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height * 2 - 1)), V.cam);
        const ph = ray.intersectObjects(V.picks || [], false)[0];
        if (V.bucket) { bucket3d(ray, e); return; }
        if (V.addTer) { addTer3d(ray); return; }
        if (ph) { pickOpening(ph.object); return; }
        pickOpening(null);
        const hit = ray.intersectObjects(V.walls, false)[0]; if (!hit || !hit.face) return;
        const nrm = hit.face.normal.clone().transformDirection(hit.object.matrixWorld);
        const side = Math.abs(nrm.x) > Math.abs(nrm.z) ? (nrm.x > 0 ? "east" : "west") : (nrm.z > 0 ? "south" : "north");
        if (terr()) saveTerrace({ side }); else status("Terasi ieslēdz sānu panelī, tad klikšķis uz fasādes to pārvieto.");
      });
      V.canvas.addEventListener("wheel", e => { e.preventDefault(); const f = V.dist0 || V.dist; V.dist0 = Math.max(1500, Math.min(200000, f * (e.deltaY > 0 ? 1.1 : .9))); draw(); }, { passive: false });
      addEventListener("resize", () => { if (V.open) resize(); });
    }
    // krāsas spainis 3D: tas pats materiāls (BMAT) un tie paši modeļa lauki kā spainim rasējumā
    function bucket3d(ray, e) {
      const hs = ray.intersectObjects(V.grp.children, true).filter(h => h.object.userData.bk), t = hs[0] && hs[0].object.userData.bk;
      if (!t) { status("Spainis 3D: klikšķini uz fasādes, jumta pārkares, staba, terases vai lieveņa."); return; }
      const P = model.projekts || {}, SN = { north: "ziemeļu", south: "dienvidu", east: "austrumu", west: "rietumu" };
      if (e.altKey) {
        const FS = (P.fasade_side || {})[t.side], o = t.k === "post" ? model.posts[t.i] : t.k === "ter" ? model.terraces[t.i] : t.k === "porch" ? model.porch : t.k === "ov" ? { col: P.parkare_hex, ral: P.parkare_ral } : FS ? { col: FS.hex, ral: FS.ral } : { col: P.fasade_hex || TONES[lv0()].sw, ral: P.fasade_ral };
        if (!o || !o.col) { status("Šim elementam nav savas krāsas, nav ko paņemt."); return; }
        BMAT.col = o.col; BMAT.ral = o.ral || null; BMAT.tex = null; bkUI(); status("Krāsa paņemta: " + (o.ral || o.col)); return;
      }
      const col = BMAT.col || "#c68a58", ral = BMAT.ral || null, n = clone(model); n.projekts = n.projekts || {};
      if (t.k === "fas" && e.shiftKey) { n.projekts.fasade_hex = col; if (ral) n.projekts.fasade_ral = ral; else delete n.projekts.fasade_ral; delete n.projekts.fasade_side; status("Visa māja nokrāsota vienā tonī."); }
      else if (t.k === "fas") { const fs = n.projekts.fasade_side = Object.assign({}, n.projekts.fasade_side); fs[t.side] = ral ? { hex: col, ral } : { hex: col }; status("Nokrāsota " + SN[t.side] + " fasāde."); }
      else if (t.k === "ov") { n.projekts.parkare_hex = col; if (ral) n.projekts.parkare_ral = ral; else delete n.projekts.parkare_ral; status("Jumta pārkare nokrāsota."); }
      else { const o = t.k === "post" ? n.posts[t.i] : t.k === "ter" ? n.terraces[t.i] : n.porch; if (!o) return; if (BMAT.tex) { o.tex = BMAT.tex; o.texW = BMAT.texW || 1000; delete o.col; delete o.ral; status("Tekstūra uzlikta."); } else { o.col = col; if (ral) o.ral = ral; else delete o.ral; delete o.tex; status("Nokrāsots."); } }
      V.tone = lv0(); if ($("v3tone")) $("v3tone").value = V.tone; commit(n); rebuild();
    }
    // terases pie fasādēm: klikšķis uz sienas pieliek terasi (model.terraces, tās pašas, ko zīmē plāns un fasādes) visā sienas posma garumā
    function addTer3d(ray) {
      const hit = ray.intersectObjects(V.walls, false)[0]; if (!hit || !hit.face) { status("Uzklikšķini uz mājas sienas."); return; }
      const nrm = hit.face.normal.clone().transformDirection(hit.object.matrixWorld), px = hit.point.x, py = hit.point.z, m = model;
      const o = Math.abs(nrm.x) > Math.abs(nrm.z) ? [Math.sign(nrm.x), 0] : [0, Math.sign(nrm.z)];
      const poly = m.poly && m.poly.length > 2 ? m.poly : [[0, 0], [m.W, 0], [m.W, m.D], [0, m.D]]; let best = null, bd = 1e9;
      poly.forEach((a, i) => { const b = poly[(i + 1) % poly.length], vert = Math.abs(a[0] - b[0]) < .5; if (vert !== (o[0] !== 0)) return;
        const lo = vert ? Math.min(a[1], b[1]) : Math.min(a[0], b[0]), hi = vert ? Math.max(a[1], b[1]) : Math.max(a[0], b[0]), u = vert ? py : px, d = Math.abs((vert ? px - a[0] : py - a[1])); if (u >= lo - 50 && u <= hi + 50 && d < bd) { bd = d; best = { vert, c: vert ? a[0] : a[1], lo, hi }; } });
      if (!best || bd > 700) { status("Šai sienai terasi neizdevās piesaistīt."); return; }
      const dp = Math.max(300, +$("v3addDep").value || 2000), c = best.c, c2 = c + (best.vert ? o[0] : o[1]) * dp, n = clone(m);
      const pl = best.vert ? [[Math.min(c, c2), best.lo], [Math.max(c, c2), best.lo], [Math.max(c, c2), best.hi], [Math.min(c, c2), best.hi]] : [[best.lo, Math.min(c, c2)], [best.hi, Math.min(c, c2)], [best.hi, Math.max(c, c2)], [best.lo, Math.max(c, c2)]];
      n.terraces = (n.terraces || []).concat([{ name: "Terase " + ((n.terraces || []).length + 1), poly: pl, th: 300, corners: false, texRot: 0 }]);
      commit(n); rebuild(); terList(); status("Terase pievienota. Vari klikšķināt uz nākamās fasādes.");
    }
    function terList() {   // terašu saraksts: izmērs, dziļuma maiņa (taisnstūrim), dzēšana
      const h = $("v3tList"); if (!h) return; h.textContent = "";
      (model.terraces || []).forEach((t, i) => {
        const xs = t.poly.map(q => q[0]), ys = t.poly.map(q => q[1]), w = Math.max(...xs) - Math.min(...xs), d = Math.max(...ys) - Math.min(...ys);
        const r = document.createElement("div"); r.className = "v3row"; r.style.cssText = "grid-template-columns:1fr auto;align-items:center;margin:2px 0";
        const s = document.createElement("span"); s.textContent = `${t.name || "Terase"} · ${Math.round(w)} × ${Math.round(d)} mm`;
        const b = document.createElement("button"); b.type = "button"; b.className = "v3b"; b.textContent = "Dzēst"; b.onclick = () => { const n = clone(model); n.terraces.splice(i, 1); commit(n); rebuild(); terList(); };
        r.append(s, b); h.appendChild(r);
      });
    }
    function bkUI() { $("v3bkBox").hidden = !V.bucket; $("v3bkCol").value = /^#[0-9a-f]{6}$/i.test(BMAT.col || "") ? BMAT.col : "#c68a58"; $("v3bkRal").value = BMAT.ral || ""; $("v3bkNoTex").hidden = !BMAT.tex; $("v3bkTex").textContent = BMAT.tex ? "Mainīt tekstūru" : "Tekstūra no faila"; V.canvas.style.cursor = V.bucket ? "crosshair" : ""; }
    function pickOpening(mesh) {   // klikšķis uz loga/durvīm: izcelšana un izmēri (ID sakrīt ar plāna izvēli k/i)
      if (V.picked && V.picked.material.emissive) V.picked.material.emissive.setHex(0);
      V.picked = mesh; if (!mesh) { draw(); return; }
      mesh.material.emissive && mesh.material.emissive.setHex(0x2266d8); const r = mesh.userData.ref || {};
      const o = ({ win: model.windows, door: model.doors, gwin: model.gableWins }[r.k] || [])[r.i];
      const nm = { win: "Logs", door: "Durvis", gwin: "Gala logs" }[r.k] || "Elements";
      status(o ? `${nm} ${r.i + 1}: ${Math.round(o.len || o.w || 0) || ""}${o.head != null ? " × " + Math.round(o.head - (o.sill || 0)) : ""} mm` : nm); draw();
    }
    function snapName() {   // tuvākais iepriekšiestatītais skats prompta tekstam
      let best = VIEWS[0], bd = 999; VIEWS.forEach(v => { const va = viewAz(v[0]), d = Math.min(Math.abs(va - V.az), 360 - Math.abs(va - V.az)); if (d < bd) { bd = d; best = v; } });
      V.view = best[0]; promptUpdate();
    }
    function openV() {
      V.open = true; $("v3").hidden = false; init(); if (!V.renderer) return;
      V.tone = V.tone || lv0(); $("v3lens").value = V.lens; $("v3tone").value = V.tone; $("v3shad").checked = !!V.shadows; $("v3odere").value = (model.projekts || {}).logu_odere === "fasade" ? "fasade" : "aplodas"; syncKar(); $("v3atm").value = V.atm; terraceUI(); terList(); rebuild(); resize(); setView(V.view);
    }
    function close() { V.open = false; $("v3").hidden = true; }
    $("b3d").onclick = openV;
    // izvēlēta loga labošana ar taustiņiem: ←→ pārbīda (Shift = 100 mm, citādi 10), +/- platums, PgUp/PgDn augstums (loga augša)
    function winKey(e) {
      const r = V.picked && V.picked.userData.ref; if (!V.open || !r || r.k !== "win") return false;
      const st = e.shiftKey ? 100 : 10, n = clone(model), o = n.windows[r.i], H = o.o === "h", lim = H ? model.W : model.D; if (!o) return false;
      const pos = H ? "x" : "y"; let ok = true;
      if (e.key === "ArrowLeft") o[pos] = Math.max(0, o[pos] - st);
      else if (e.key === "ArrowRight") o[pos] = Math.min(lim - o.len, o[pos] + st);
      else if (e.key === "+" || e.key === "=") o.len = Math.min(lim - o[pos], o.len + 100);
      else if (e.key === "-") o.len = Math.max(300, o.len - 100);
      else if (e.key === "PageUp") o.head = (o.head || 2100) + 100;
      else if (e.key === "PageDown") o.head = Math.max((o.sill || 0) + 300, (o.head || 2100) - 100);
      else ok = false;
      if (!ok) return false;
      e.preventDefault(); e.stopPropagation(); commit(n); const keep = r.i; rebuild();
      const mm = (V.picks || []).find(q => q.userData.ref && q.userData.ref.k === "win" && q.userData.ref.i === keep); if (mm) pickOpening(mm); return true;
    }
    addEventListener("keydown", e => { if (V.open && e.key === "Escape") close(); else if (winKey(e)) return; }, true);
    // ---------- eksports uz SketchUp: tā pati detalizētā 3D aina (apvalks ar visām detaļām + karkass) kā Ruby skripts ----------
    // katrs materiāls = viena PolygonMesh; koordinātas SketchUp asīs (X uz austrumiem, Y uz ziemeļiem = D - plāna y, Z uz augšu), mm
    function exportRb(m, kd) {
      const D = +m.D || 0, rd = v => Math.round(v * 10) / 10;
      const mkGroup = (grp, skip) => {
        grp.updateMatrixWorld(true);
        const mats = {};
        grp.traverse(o => {
          if (!o.isMesh || o === skip || !o.geometry || !o.geometry.attributes.position) return;
          const ms = Array.isArray(o.material) ? o.material : [o.material], g = o.geometry, pos = g.attributes.position, idx = g.index, v = new THREE.Vector3();
          const groups = g.groups && g.groups.length ? g.groups : [{ start: 0, count: idx ? idx.count : pos.count, materialIndex: 0 }];
          groups.forEach(gr => {
            const mt = ms[gr.materialIndex] || ms[0]; if (!mt || mt.visible === false) return;
            const op = mt.transparent ? Math.max(0, Math.min(1, mt.opacity)) : 1, hex = (mt.color ? mt.color.getHexString() : "888888"), key = hex + "_" + Math.round(op * 100);
            const M = mats[key] || (mats[key] = { hex, op, map: new Map(), V: [], T: [] });
            const vi = i => { const j = idx ? idx.getX(i) : i; v.fromBufferAttribute(pos, j).applyMatrix4(o.matrixWorld); const x = rd(v.x), y = rd(D - v.z), z = rd(v.y), k = x + "," + y + "," + z; let n = M.map.get(k); if (n == null) { n = M.V.length / 3; M.map.set(k, n); M.V.push(x, y, z); } return n; };
            const end = Math.min(gr.start + gr.count, idx ? idx.count : pos.count);
            for (let i = gr.start; i + 2 < end; i += 3) { const a = vi(i), b = vi(i + 1), c = vi(i + 2); if (a !== b && b !== c && a !== c) M.T.push(a, b, c); }
          });
        });
        return Object.values(mats).map(M => ({ hex: M.hex, op: M.op, V: M.V, T: M.T })).filter(M => M.T.length);
      };
      const r = buildScene(m), shell = mkGroup(r.grp, r.gr);
      const parts = [{ name: "MM " + m.id, mats: shell }];
      const kdat = kd || V.kdata || KAR_SNAP;
      if (kdat) { try { parts.push({ name: "KARKASS", mats: mkGroup(buildFrame(kdat, "")) }); } catch (e) { console.error("karkass eksportam:", e.message); } }
      const tag = String(m.id).replace(/[^A-Za-z0-9]/g, "_").replace(/^[^A-Za-z]/, "X$&"), js = JSON.stringify(parts.map(p => ({ n: p.name, m: p.mats.map(q => [q.hex, q.op, q.V, q.T]) })));
      const n = parts.reduce((s, p) => s + p.mats.reduce((t, q) => t + q.T.length / 3, 0), 0);
      return ["# encoding: UTF-8", `# MM Homes 3D modelis ar visām detaļām: ${m.id} (SBE Architect). Apvalks (sienas, jumts, logi, durvis, aplodas, teknes, lāseņi) un ražošanas karkass.`,
        `module MM3D${tag}`, `  PARTS = ${js}`, "  def self.run", "    model = Sketchup.active_model", `    model.start_operation('MM 3D: ${String(m.id).replace(/'/g, "")}', true)`, "    begin",
        "      PARTS.each do |nm, mats|", "        grp = model.entities.add_group", "        grp.name = nm",
        "        mats.each do |hex, op, vs, ts|", "          mat = model.materials.add(\"MM_#{hex}_#{(op * 100).round}\")", "          mat.color = Sketchup::Color.new(hex[0, 2].to_i(16), hex[2, 2].to_i(16), hex[4, 2].to_i(16))", "          mat.alpha = op if op < 1",
        "          mesh = Geom::PolygonMesh.new", "          pts = (0...vs.size / 3).map { |i| mesh.add_point(Geom::Point3d.new(vs[3 * i].mm, vs[3 * i + 1].mm, vs[3 * i + 2].mm)) }",
        "          ts.each_slice(3) { |a, b, c| mesh.add_polygon(pts[a], pts[b], pts[c]) }", "          grp.entities.add_faces_from_mesh(mesh, 0, mat, mat)", "        end",
        "        grp.entities.grep(Sketchup::Edge).each { |e| f = e.faces; e.soft = e.smooth = true if f.size == 2 && f[0].normal.parallel?(f[1].normal) }   # trijstūru šuves koplanārās virsmās paslēptas",
        "      end", "      model.commit_operation", `      UI.messagebox("MM 3D ${String(m.id).replace(/"/g, "")}: ${n} trijstūri, #{PARTS.size} grupas (apvalks un karkass).")`,
        "    rescue StandardError => e", "      model.abort_operation", "      UI.messagebox(\"MM 3D eksports neizdevās:\\n#{e.message}\")", "    end", "  end", "end", `MM3D${tag}.run if Sketchup.active_model`, ""].join("\n");
    }
    window.MM_VIZ3D = { open: openV, state: V, prompt: promptText, model: () => model, exportRb };
  })();
