  // ---- 3D skats + Gemini prompts: references PNG ar fotogrāfa kadru un gatavs prompts (tāds pats kā viz.py) ----
  (function () {
    const V = { open: false, inited: false, view: "SE", free: false, lens: 85, tone: null, atm: "auto", az: 45, el: 0, dist: 30000 };
    const SIDES = { south: "south", north: "north", east: "east", west: "west" };
    const SIDE_LV = { south: "Dienvidi (ieeja)", north: "Ziemeļi", east: "Austrumi", west: "Rietumi" };
    const VIEWS = [["S", "Fasāde S", 0], ["E", "Fasāde A", 90], ["N", "Fasāde Z", 180], ["W", "Fasāde R", 270],
      ["SE", "3/4 DA", 45], ["NE", "3/4 ZA", 135], ["NW", "3/4 ZR", 225], ["SW", "3/4 DR", 315]];
    const ATM = __MM_ATMOS__;
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
    // fasādes detaļas kā rasējumā: aplodas, palodzes, dalījumi, durvju stikls un rokturis, notekas, stabi, terases, lievenis
    function details(m, geo, grp, mat, frameM, T) {
      const P = m.projekts || {}, J = m.jumts || {}, W = m.W, D = m.D, pitch = J.pitch || 30, tan = Math.tan(pitch * Math.PI / 180), eave = J.eave || 2600, ov = +J.ov || 0;
      const hip = +J.hip || (/^(cetr|četr)/i.test(J.forma || "") ? pitch : 0), tanH = hip ? Math.tan(hip * Math.PI / 180) : 0;
      const RL = tanH ? null : roofL(m), roofZ = (x, y) => RL ? RL.z(x, y) : eave + Math.min(Math.min(y, D - y) * tan, tanH ? Math.min(x, W - x) * tanH : Infinity);
      const steel = mat("#c9cdd1"), glassD = mat("#8fb0c0", { transparent: true, opacity: .8 }), gutM = mat(hexOf(P.noteku_tonis || "RAL 7016"));
      geo.forEach(g => {
        if ((g.k !== "g" && g.k !== "d") || !g.n) return;
        const o = [-g.n[0], -g.n[1]], o3 = new THREE.Vector3(o[0], 0, o[1]), face = g.pts.map(p => T3([p[0] + o[0] * T / 2, p[1] + o[1] * T / 2, p[2]]));
        const w = g.k === "g" ? (g.ref.k === "win" ? (m.windows || [])[g.ref.i] : (m.gableWins || [])[g.ref.i]) : (m.doors || [])[g.ref.i], cas = w && w.casing === 0 ? 0 : 1;
        if (cas) edgeBoards(face, o3, 100, 24, frameM, grp, !(w && w.casingAll));
        const z0 = Math.min(...g.pts.map(p => p[2])), z1 = Math.max(...g.pts.map(p => p[2])), bot = g.pts.filter(p => p[2] <= z0 + 1);
        if (bot.length >= 2) {
          const a = bot[0], b = bot[bot.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), t = [(b[0] - a[0]) / L, (b[1] - a[1]) / L], cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2, at = (f, off, z) => [a[0] + (b[0] - a[0]) * f + o[0] * off, a[1] + (b[1] - a[1]) * f + o[1] * off, z];
          if (g.k === "g") {
            grp.add(obox([cx + o[0] * (T / 2 + 25), cy + o[1] * (T / 2 + 25), z0 - 8], t, L + 70, 90, 16, frameM));   // skārda palodze
            const cuts = []; if (w && w.parts && w.parts.length > 1) { let u = 0; w.parts.slice(0, -1).forEach(q => { u += +q.len || 0; cuts.push(u / (w.len || L)); }); } else if (w && /^slide/.test(w.kind || "")) cuts.push(.5);
            cuts.forEach(f => grp.add(obox(at(f, 15, (z0 + z1) / 2), t, 70, 80, z1 - z0, frameM)));   // dalījuma statnis
          } else {
            const fl = g.hinge === "e" ? 1 : 0, f = x => fl ? 1 - x : x;
            grp.add(obox(at(f(.76), 14, 1100), t, Math.min(140, L * .16), 10, 1500, glassD));   // šaura stikla josla
            grp.add(obox(at(f(.9), 70, 1050), t, 30, 30, 1000, steel)); [650, 1450].forEach(z => grp.add(obox(at(f(.9), 40, z), t, 24, 60, 24, steel)));   // garais rokturis
            grp.add(obox([cx + o[0] * (T / 2 + 20), cy + o[1] * (T / 2 + 20), -10], t, L + 40, 120, 20, steel));   // slieksnis
          }
        }
      });
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
      if (RL) RL.eaves.forEach(([p, q, key]) => run(p, q, wallOf, key)); else {
      run([-oW, -oN - 60, eave - oN * tan], [W + oE, -oN - 60, eave - oN * tan], t => [Math.max(60, Math.min(W - 60, t[0])), 0], "north");
      run([-oW, D + oS + 60, eave - oS * tan], [W + oE, D + oS + 60, eave - oS * tan], t => [Math.max(60, Math.min(W - 60, t[0])), D], "south");
      if (tanH) { const zW = eave - oW * tanH, zE = eave - oE * tanH;
        run([-oW - 60, -oN, zW], [-oW - 60, D + oS, zW], t => [0, Math.max(60, Math.min(D - 60, t[1]))], "west");
        run([W + oE + 60, -oN, zE], [W + oE + 60, D + oS, zE], t => [W, Math.max(60, Math.min(D - 60, t[1]))], "east"); } }
      // stabi: līdz jumta apakšai vai līdz savam augstumam (posts[i].h)
      const texOf = (o, k) => { if (!o || !o.tex) return null; const t = new THREE.TextureLoader().load(o.tex, () => draw()); t.wrapS = t.wrapT = THREE.RepeatWrapping; const w = Math.max(100, +o.texW || 1000); t.repeat.set(k / w, k / w); if (o.texRot) t.rotation = o.texRot * Math.PI / 180; return t; };
      const wood = (c, o) => { const t = texOf(o, 300); return t ? new THREE.MeshLambertMaterial({ map: t, side: THREE.DoubleSide }) : mat(c || "#b98a5c"); };
      (m.posts || []).forEach((q, i) => { const w = +q.w || 200, d = +q.d || w, cx = q.x + w / 2, cy = q.y + d / 2, top = q.h && q.h < 99999 ? +q.h : roofZ(cx, cy) - 5, b = new THREE.Mesh(new THREE.BoxGeometry(w, top + 300, d), wood(q.col, q)); b.position.set(cx, (top - 300) / 2, cy); b.userData.bk = { k: "post", i }; grp.add(b); });
      ((m.porch && m.porch.posts) || []).forEach(q => { if (!q || q.x == null) return; const w = +q.w || 200, d = +q.d || w, cx = q.x + w / 2, cy = q.y + d / 2, top = roofZ(cx, cy) - 5, b = new THREE.Mesh(new THREE.BoxGeometry(w, top + 300, d), wood(q.col)); b.position.set(cx, (top - 300) / 2, cy); grp.add(b); });
      // terases un lievenis pa kontūru
      const deck = (pl, top, th, col, bk, o) => { if (!pl || pl.length < 3) return; const own = texOf(o, 1), tx = own || stripeTex(600, 4, .45, .12); if (own) col = "#ffffff"; me = new THREE.Mesh(new THREE.ExtrudeGeometry(new THREE.Shape(pl.map(p => new THREE.Vector2(p[0], p[1]))), { depth: th, bevelEnabled: false }), new THREE.MeshLambertMaterial({ color: col || "#4a4f55", map: tx, side: THREE.DoubleSide }));
        me.rotation.x = Math.PI / 2; me.position.y = top; me.userData.bk = bk; grp.add(me); };
      (m.terraces || []).forEach((t, i) => deck(t.poly, -25, Math.max(60, (+t.th || 300) - 25), t.col, { k: "ter", i }, t));
      if (m.porch) { deck(m.porch.poly, -25, 275, m.porch.col, { k: "porch" }, m.porch); const s = m.porch.step, sp = m.porch.stepPoly || (s && [[s[0], s[1]], [s[2], s[1]], [s[2], s[3]], [s[0], s[3]]]); if (sp) deck(sp, -165, 135, m.porch.col, { k: "porch" }); }
    }
    function buildScene(m) {
      const P = m.projekts || {}, tk = V.tone || lv0(), wallHex = (tk === lv0() && P.sienas_hex) || TONES[tk].sw, frameHex = hexOf(P.logu_tonis || TONES[tk].logi);
      const geo = []; skpRb(m, geo);
      const grp = new THREE.Group(), walls = [], picks = [];
      const mat = (c, o = {}) => new THREE.MeshLambertMaterial(Object.assign({ color: c, side: THREE.DoubleSide }, o));
      const cladTex = stripeTex(600, 4, .5, .1), seamTex = stripeTex(500, 1, .35, 0), sideHex = (tk === lv0() && P.fasade_side) || {}, wallM = {};
      const wallMat = sd => wallM[sd] || (wallM[sd] = [mat((sideHex[sd] && sideHex[sd].hex) || wallHex, { map: cladTex }), mat((sideHex[sd] && sideHex[sd].hex) || wallHex)]);   // [fasādes plakne ar dēļiem, ailu un galu malas]
      const mats = { M_WALL: mat(wallHex), M_INT: mat("#f2efe9"), M_FLOOR: mat(P.pamati === "platne" ? "#9a9a96" : hexOf(P.cokols || "RAL 9005")), M_ROOF: mat("#454b50", { map: seamTex }), M_STAIR: mat("#c9a77c") };
      const frameM = mat(frameHex), glassM = mat("#7fa5b8", { transparent: true, opacity: .75 });
      const facts = { win: { south: 0, north: 0, east: 0, west: 0 }, door: { south: 0, north: 0, east: 0, west: 0 }, gable: { east: 0, west: 0 } };
      geo.forEach(g => {
        if (g.k === "s") { const me = extrude(g, g.mat === "M_WALL" ? wallMat(sideOfN(g.dir)) : mats[g.mat] || mats.M_WALL);
          if (g.mat === "M_ROOF" && P.parkare_hex && tk === lv0()) { const sf = extrude(Object.assign({}, g, { d: 18 }), mat(P.parkare_hex)); sf.userData.bk = { k: "ov" }; sf.position.addScaledVector(new THREE.Vector3(g.dir[0], g.dir[2], g.dir[1]).normalize(), -19); grp.add(sf); } /* jumta pārkares apakša savā tonī */ if (g.mat === "M_WALL") { walls.push(me); me.userData.bk = { k: "fas", side: sideOfN(g.dir) }; } if (g.mat === "M_ROOF") me.userData.bk = { k: "ov" }; if (g.mat !== "M_INT" && g.mat !== "M_STAIR") grp.add(me); }
        else if (g.k === "g") {
          const p3 = g.pts.map(T3); { const gm = planeMesh(p3, glassM.clone(), 0); gm.userData.ref = g.ref; picks.push(gm); grp.add(gm); } frameAround(p3, frameM, grp, 80, 90);
          const sd = sideOf(g.pts, m.W, m.D); if (sd) { if (g.pts.some(p => p[2] > (m.jumts && m.jumts.eave || 2600) - 400) || g.pts.length > 4) facts.gable[sd] = (facts.gable[sd] || 0) + 1; else facts.win[sd]++; }
        } else if (g.k === "d") {
          const p3 = g.pts.map(T3); { const dm = planeMesh(p3, frameM.clone(), 0); dm.userData.ref = g.ref; picks.push(dm); grp.add(dm); } frameAround(p3, frameM, grp, 90, 100);
          const sd = sideOf(g.pts, m.W, m.D); if (sd) facts.door[sd]++;
        }
      });
      { const wg = geo.find(g => g.k === "s" && g.mat === "M_WALL"); try { details(m, geo, grp, mat, frameM, wg ? wg.d : 283.5); } catch (e) { console.error("3D detaļas:", e); } }
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
      return { grp, walls, facts, tr, picks };
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
      const m = model, bb = V.bb = bbox(m), cam = V.cam, a = V.az * Math.PI / 180, el = V.free ? V.el * Math.PI / 180 : 0;
      const f = V.free ? { dist: V.dist, cx: (bb.x0 + bb.x1) / 2, cz: (bb.y0 + bb.y1) / 2 } : camFor(V.az, bb); V.dist = V.dist0 || f.dist; V.cx = f.cx; V.cz = f.cz;
      const cx = V.cx, cz = V.cz, ty = V.free ? 1400 : CAM_H, d = V.dist;
      cam.position.set(cx + Math.sin(a) * Math.cos(el) * d, ty + Math.sin(el) * d, cz + Math.cos(a) * Math.cos(el) * d);
      cam.lookAt(cx, ty, cz);
      const W = V.w, H = V.h;
      if (V.free) cam.clearViewOffset(); else cam.setViewOffset(W, H, 0, -H / 6, W, H);   // horizonts apakšējā trešdaļā
      cam.fov = fovOf(V.lens); cam.aspect = W / H; cam.updateProjectionMatrix();
    }
    function resize() {
      const st = $("v3stage"), r = st.getBoundingClientRect(); let w = r.width - 20, h = w / ASPECT; if (h > r.height - 20) { h = r.height - 20; w = h * ASPECT; }
      w = Math.max(200, Math.floor(w)); h = Math.floor(w / ASPECT); V.w = w; V.h = h;
      V.renderer.setPixelRatio(Math.min(2, devicePixelRatio || 1)); V.renderer.setSize(w, h, false);
      V.canvas.style.width = w + "px"; V.canvas.style.height = h + "px"; draw();
    }
    function draw() { if (!V.renderer) return; applyCam(); sun(); V.renderer.render(V.scene, V.cam); }
    function sun() {   // saule no kameras puses, pa kreisi un augstu: fasāde izgaismota, pārkare met ēnu
      const a = (V.az + 35) * Math.PI / 180, cx = V.cx || 0, cz = V.cz || 0; V.light.target.position.set(cx, 1200, cz); V.light.position.set(cx + Math.sin(a) * 30000, 26000, cz + Math.cos(a) * 30000); V.light.target.updateMatrixWorld();
    }
    function rebuild() {
      if (!V.scene) return;
      if (V.grp) V.scene.remove(V.grp);
      const r = buildScene(model); V.grp = r.grp; V.walls = r.walls; V.picks = r.picks; V.picked = null; V.facts = r.facts; V.scene.add(V.grp); draw(); promptUpdate();
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
    function setView(id) { V.view = id; V.az = VIEWS.find(v => v[0] === id)[2]; V.dist0 = null; document.querySelectorAll("#v3views button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === id))); draw(); promptUpdate(); }
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
      V.renderer.shadowMap.enabled = true; V.renderer.shadowMap.type = THREE.PCFSoftShadowMap; V.light.castShadow = true; V.light.shadow.mapSize.set(4096, 4096); V.light.shadow.bias = -0.0004; V.light.shadow.normalBias = 40;
      { const c = V.light.shadow.camera; c.left = c.bottom = -22000; c.right = c.top = 22000; c.near = 1000; c.far = 120000; c.updateProjectionMatrix(); }
      V.cam = new THREE.PerspectiveCamera(fovOf(V.lens), ASPECT, 100, 400000);
      $("v3views").innerHTML = VIEWS.map(v => `<button type="button" data-v="${v[0]}" aria-pressed="false">${v[1]}</button>`).join("");
      $("v3views").onclick = e => { const b = e.target.closest("button"); if (b) setView(b.dataset.v); };
      $("v3tone").innerHTML = Object.keys(TONES).map(k => `<option value="${k}">${TONE_N[k] || k}</option>`).join("");
      $("v3atm").innerHTML = `<option value="auto">Automātiski (pēc modeļa nr.)</option>` + ATM_KEYS.map(k => `<option value="${k}">${(ATM[k].lv || k)}</option>`).join("");
      $("v3tone").onchange = e => { V.tone = e.target.value; rebuild(); };
      $("v3atm").onchange = e => { V.atm = e.target.value; promptUpdate(); };
      $("v3lens").onchange = e => { V.lens = +e.target.value; V.dist0 = null; draw(); promptUpdate(); };
      $("v3free").onchange = e => { V.free = e.target.checked; if (V.free) { V.el = 12; V.dist0 = null; } draw(); };
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
      $("v3reset").onclick = () => { V.dist0 = null; V.free = false; $("v3free").checked = false; draw(); };
      let dr = null;
      const rayOf = e => { const r = V.canvas.getBoundingClientRect(), ray = new THREE.Raycaster(); ray.setFromCamera(new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height * 2 - 1)), V.cam); return ray; };
      V.canvas.addEventListener("pointerdown", e => {
        dr = { x: e.clientX, y: e.clientY, moved: 0 }; V.canvas.setPointerCapture(e.pointerId); V.dragWin = null;
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
        V.az = (V.az - dx * .4 + 360) % 360; if (V.free) V.el = Math.max(-3, Math.min(80, V.el + dy * .3));
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
      V.canvas.addEventListener("wheel", e => { e.preventDefault(); const f = V.dist0 || V.dist; V.dist0 = Math.max(6000, Math.min(150000, f * (e.deltaY > 0 ? 1.08 : .92))); draw(); }, { passive: false });
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
      let best = VIEWS[0], bd = 999; VIEWS.forEach(v => { const d = Math.min(Math.abs(v[2] - V.az), 360 - Math.abs(v[2] - V.az)); if (d < bd) { bd = d; best = v; } });
      V.view = best[0]; promptUpdate();
    }
    function openV() {
      V.open = true; $("v3").hidden = false; init(); if (!V.renderer) return;
      V.tone = V.tone || lv0(); $("v3lens").value = V.lens; $("v3tone").value = V.tone; $("v3atm").value = V.atm; terraceUI(); terList(); rebuild(); resize(); setView(V.view);
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
    window.MM_VIZ3D = { open: openV, state: V, prompt: promptText, model: () => model };
  })();
