// MM Homes: konti un projekti profilā. Cloudflare Worker + D1.
const enc = new TextEncoder(), DAY = 86400, MAXBODY = 3_000_000;
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
const unhex = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));
const json = (o, status = 200, h = {}) => new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...h } });
async function pbkdf2(pw, salt) {
  const k = await crypto.subtle.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveBits"]);
  return hex(await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations: 100000 }, k, 256));
}
const sha = async t => hex(await crypto.subtle.digest("SHA-256", enc.encode(t)));
const cookie = (t, age) => `mm=${t}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${age}`;
const getCookie = (req, n) => ((req.headers.get("cookie") || "").match(new RegExp("(?:^|; )" + n + "=([^;]+)")) || [])[1];

async function userOf(req, env) {
  const t = getCookie(req, "mm"); if (!t) return null;
  const th = await sha(t);
  return await env.DB.prepare("SELECT u.id, u.email FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ? AND s.expires > ?").bind(th, Math.floor(Date.now() / 1000)).first();
}
async function newSession(env, uid) {
  const t = hex(crypto.getRandomValues(new Uint8Array(32))), exp = Math.floor(Date.now() / 1000) + 30 * DAY;
  await env.DB.prepare("INSERT INTO sessions (token, user_id, expires) VALUES (?, ?, ?)").bind(await sha(t), uid, exp).run();
  await env.DB.prepare("DELETE FROM sessions WHERE expires < ?").bind(Math.floor(Date.now() / 1000)).run();
  return cookie(t, 30 * DAY);
}
async function body(req) { const t = await req.text(); if (t.length > MAXBODY) throw new Error("big"); return JSON.parse(t || "{}"); }

export default {
  async fetch(req, env) {
    const url = new URL(req.url), path = url.pathname;
    if (!path.startsWith("/api/")) return env.ASSETS.fetch(req);
    if (req.method !== "GET" && req.method !== "HEAD") {   // CSRF: tikai tas pats izcelsmes domēns
      const o = req.headers.get("origin"); if (o && o !== url.origin) return json({ error: "origin" }, 403);
    }
    try {
      if (path === "/api/register" && req.method === "POST") {
        const { email, password } = await body(req), e = String(email || "").trim().toLowerCase();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e) || String(password || "").length < 8) return json({ error: "Derīgs e-pasts un parole (vismaz 8 simboli)." }, 400);
        const allow = (env.ALLOWED_EMAILS || "").split(",").map(x => x.trim().toLowerCase()).filter(Boolean);
        if (allow.length && !allow.includes(e)) return json({ error: "Šim e-pastam reģistrācija nav atļauta." }, 403);
        const salt = crypto.getRandomValues(new Uint8Array(16)), h = await pbkdf2(password, salt);
        try { await env.DB.prepare("INSERT INTO users (email, salt, hash, created) VALUES (?, ?, ?, ?)").bind(e, hex(salt), h, new Date().toISOString()).run(); }
        catch (_) { return json({ error: "Šāds konts jau ir. Piesakies." }, 409); }
        const u = await env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(e).first();
        return json({ email: e }, 200, { "set-cookie": await newSession(env, u.id) });
      }
      if (path === "/api/login" && req.method === "POST") {
        const { email, password } = await body(req), e = String(email || "").trim().toLowerCase();
        const u = await env.DB.prepare("SELECT id, salt, hash FROM users WHERE email = ?").bind(e).first();
        const ok = u && (await pbkdf2(String(password || ""), unhex(u.salt))) === u.hash;
        if (!ok) return json({ error: "Nepareizs e-pasts vai parole." }, 401);
        return json({ email: e }, 200, { "set-cookie": await newSession(env, u.id) });
      }
      if (path === "/api/logout" && req.method === "POST") {
        const t = getCookie(req, "mm"); if (t) await env.DB.prepare("DELETE FROM sessions WHERE token = ?").bind(await sha(t)).run();
        return json({ ok: true }, 200, { "set-cookie": cookie("", 0) });
      }
      const u = await userOf(req, env); if (!u) return json({ error: "auth" }, 401);
      if (path === "/api/me") return json({ email: u.email });
      if (path === "/api/projects" && req.method === "GET") {
        const r = await env.DB.prepare("SELECT id, saved FROM projects WHERE user_id = ? ORDER BY saved DESC").bind(u.id).all();
        return json({ projects: r.results });
      }
      const m = path.match(/^\/api\/projects\/([^/]{1,80})$/);
      if (m) {
        const id = decodeURIComponent(m[1]);
        if (req.method === "GET") { const r = await env.DB.prepare("SELECT id, json, saved FROM projects WHERE user_id = ? AND id = ?").bind(u.id, id).first(); return r ? json(r) : json({ error: "nav" }, 404); }
        if (req.method === "PUT") {
          const b = await body(req); if (typeof b.json !== "string") return json({ error: "json" }, 400);
          JSON.parse(b.json);
          await env.DB.prepare("INSERT INTO projects (user_id, id, json, saved) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, id) DO UPDATE SET json = excluded.json, saved = excluded.saved").bind(u.id, id, b.json, new Date().toISOString()).run();
          return json({ ok: true });
        }
        if (req.method === "DELETE") { await env.DB.prepare("DELETE FROM projects WHERE user_id = ? AND id = ?").bind(u.id, id).run(); return json({ ok: true }); }
      }
      return json({ error: "nav" }, 404);
    } catch (e) { return json({ error: "Servera kļūda" }, 500); }
  }
};
