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
    function buildScene(m) {
      const P = m.projekts || {}, tk = V.tone || lv0(), wallHex = (tk === lv0() && P.sienas_hex) || TONES[tk].sw, frameHex = hexOf(P.logu_tonis || TONES[tk].logi);
      const geo = []; skpRb(m, geo);
      const grp = new THREE.Group(), walls = [], picks = [];
      const mat = (c, o = {}) => new THREE.MeshLambertMaterial(Object.assign({ color: c, side: THREE.DoubleSide }, o));
      const mats = { M_WALL: mat(wallHex), M_INT: mat("#f2efe9"), M_FLOOR: mat(P.pamati === "platne" ? "#9a9a96" : hexOf(P.cokols || "RAL 9005")), M_ROOF: mat("#40464b"), M_STAIR: mat("#c9a77c") };
      const frameM = mat(frameHex), glassM = mat("#7fa5b8", { transparent: true, opacity: .75 });
      const facts = { win: { south: 0, north: 0, east: 0, west: 0 }, door: { south: 0, north: 0, east: 0, west: 0 }, gable: { east: 0, west: 0 } };
      geo.forEach(g => {
        if (g.k === "s") { const me = extrude(g, mats[g.mat] || mats.M_WALL); if (g.mat === "M_WALL") walls.push(me); if (g.mat !== "M_INT" && g.mat !== "M_STAIR") grp.add(me); }
        else if (g.k === "g") {
          const p3 = g.pts.map(T3); { const gm = planeMesh(p3, glassM.clone(), 0); gm.userData.ref = g.ref; picks.push(gm); grp.add(gm); } frameAround(p3, frameM, grp, 80, 90);
          const sd = sideOf(g.pts, m.W, m.D); if (sd) { if (g.pts.some(p => p[2] > (m.jumts && m.jumts.eave || 2600) - 400) || g.pts.length > 4) facts.gable[sd] = (facts.gable[sd] || 0) + 1; else facts.win[sd]++; }
        } else if (g.k === "d") {
          const p3 = g.pts.map(T3); { const dm = planeMesh(p3, frameM.clone(), 0); dm.userData.ref = g.ref; picks.push(dm); grp.add(dm); } frameAround(p3, frameM, grp, 90, 100);
          const sd = sideOf(g.pts, m.W, m.D); if (sd) facts.door[sd]++;
        }
      });
      // terase
      const tr = terraceRect(m);
      if (tr) {
        const [x0, y0, x1, y1] = tr, h = 275, topZ = -25, bt = boardsTex();
        bt.repeat.set((x1 - x0) / 1000, (y1 - y0) / 1000); if (terr().side === "east" || terr().side === "west") bt.rotation = Math.PI / 2;
        const top = new THREE.MeshLambertMaterial({ map: bt }), side = new THREE.MeshLambertMaterial({ color: "#383e42" });
        const box = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, h, y1 - y0), [side, side, top, side, side, side]);
        box.position.set((x0 + x1) / 2, topZ - h / 2, (y0 + y1) / 2); grp.add(box);
      }
      // zeme
      const gr = new THREE.Mesh(new THREE.PlaneGeometry(200000, 200000), new THREE.MeshLambertMaterial({ color: "#aab39a" }));
      gr.rotation.x = -Math.PI / 2; gr.position.y = -301; grp.add(gr);
      return { grp, walls, facts, tr, picks };
    }
    // ---------- kamera ----------
    function bbox(m) {
      const J = m.jumts || {}, eave = J.eave || 2600, ridge = eave + m.D / 2 * Math.tan((J.pitch || 30) * Math.PI / 180), tr = terraceRect(m) || [0, 0, 0, 0];
      const x0 = Math.min(0, tr[0]), x1 = Math.max(m.W, tr[2]), y0 = Math.min(0, tr[1]), y1 = Math.max(m.D, tr[3]);
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
    function draw() { if (!V.renderer) return; applyCam(); V.light.position.copy(V.cam.position).add(new THREE.Vector3(-7000, 9000, 0)); V.renderer.render(V.scene, V.cam); }
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
      if (t) { $("v3tSide").value = t.side; $("v3tDepth").value = t.depth; $("v3tA").value = t.a || 0; $("v3tB").value = t.b || 0; }
    }
    async function savePng() {
      const r = V.renderer, w0 = V.w, h0 = V.h, pr = r.getPixelRatio();
      V.w = 2400; V.h = 1600; r.setPixelRatio(1); r.setSize(2400, 1600, false); applyCam(); V.light.position.copy(V.cam.position).add(new THREE.Vector3(-7000, 9000, 0)); r.render(V.scene, V.cam);
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
      V.scene.add(new THREE.HemisphereLight(0xffffff, 0x99a090, .8)); V.light = new THREE.DirectionalLight(0xffffff, .6); V.scene.add(V.light);
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
      [["v3tDepth", "depth"], ["v3tA", "a"], ["v3tB", "b"]].forEach(([id, k]) => { $(id).onchange = e => saveTerrace({ [k]: Math.max(0, +e.target.value || 0) }); });
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
      V.tone = V.tone || lv0(); $("v3lens").value = V.lens; $("v3tone").value = V.tone; $("v3atm").value = V.atm; terraceUI(); rebuild(); resize(); setView(V.view);
    }
    function close() { V.open = false; $("v3").hidden = true; }
    $("b3d").onclick = openV;
    addEventListener("keydown", e => { if (V.open && e.key === "Escape") close(); });
    window.MM_VIZ3D = { open: openV, state: V, prompt: promptText, model: () => model };
  })();
