"""SBE darbvirsmas programma: projektu arhīvs (uzņēmumu mapes) un rasējuma redaktors vienā logā.

Palaišana:   pythonw bot/app.py          (darbvirsmas saīsne to dara pati; skat. bot/app_saisne.py)
             python bot/app.py --konsole  (ar žurnālu konsolē)

Darbojas tikai šajā datorā (http://127.0.0.1:8737). Projekti ir parastas mapes:
    <arhīvs>/<uzņēmums>/<projekts>/model.json
Papildus var piesaistīt jau esošas mapes kā uzņēmumu (piem. "MM Homes" = MM System\\MĀJAS).
Iestatījumi: %USERPROFILE%\\.sbe-arhivs.json  {"root": "...", "companies": {"Nosaukums": "mape"}}

Redaktorā "Saglabāt" ieraksta model.json projekta mapē (iepriekšējo saglabā kā model.json.bak)
un fonā pārbūvē LV/EN lapas. Eksporti (PDF, DXF, …) lejupielādējas kā parasti pārlūkā.
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, threading, time, urllib.parse, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8737
CFG_PATH = os.path.join(os.path.expanduser('~'), '.sbe-arhivs.json')
SKIP = {'eksports', 'rasejumi', 'viz', 'miniaturas', '3d', 'node_modules', '.git', 'ref'}
LOCK = threading.Lock()
KEYS = {}   # atslēga -> projekta mape


def default_cfg():
    desk = os.path.join(os.path.expanduser('~'), 'Desktop', 'MM System')
    cfg = {'root': os.path.join(desk, 'PROJEKTI'), 'companies': {}}
    if os.path.isdir(os.path.join(desk, 'MĀJAS')):
        cfg['companies']['MM Homes'] = os.path.join(desk, 'MĀJAS')
    return cfg


def load_cfg():
    try:
        c = json.load(open(CFG_PATH, encoding='utf-8'))
    except Exception:
        c = default_cfg(); save_cfg(c)
    c.setdefault('companies', {})
    os.makedirs(c['root'], exist_ok=True)
    return c


def save_cfg(c):
    json.dump(c, open(CFG_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def companies(c):
    out = {n: p for n, p in c['companies'].items() if os.path.isdir(p)}
    for d in sorted(os.listdir(c['root'])):
        p = os.path.join(c['root'], d)
        if os.path.isdir(p) and d not in out and not d.startswith('.'):
            out[d] = p
    return out


def key_of(path):
    k = hashlib.sha1(os.path.abspath(path).lower().encode('utf-8')).hexdigest()[:12]
    KEYS[k] = os.path.abspath(path)
    return k


def scan():
    c = load_cfg(); out = []
    for co, base in companies(c).items():
        key_of(base)
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(d for d in dn if d not in SKIP and not d.startswith('.'))
            if 'model.json' not in fn:
                continue
            mp = os.path.join(dp, 'model.json')
            try:
                m = json.load(open(mp, encoding='utf-8'))
            except Exception:
                continue
            P = m.get('projekts') or {}
            rooms = [[round(v) for v in r] for rm in (m.get('rooms') or []) for r in (rm.get('r') or [])]
            mm = re.match(r'\d+', m.get('platiba_grupa') or '')
            out.append({'key': key_of(dp), 'company': co, 'ckey': key_of(base), 'id': m.get('id', os.path.basename(dp)),
                        'name': P.get('modela_nosaukums') or m.get('nosaukums') or m.get('id'),
                        'W': m.get('W', 0), 'D': m.get('D', 0), 'area': int(mm.group(0)) if mm else round(m.get('W', 0) * m.get('D', 0) / 1e6),
                        'loft': bool(m.get('loft')), 'rooms': rooms, 'poly': m.get('poly'), 'mtime': int(os.path.getmtime(mp)),
                        'rel': os.path.relpath(dp, base), **_counts(dp)})
            dn[:] = []   # projekta apakšmapēs (varianti u.c.) citu model.json nemeklē
    return out


def _counts(dp):
    f = files_of(dp)
    return {'nfiles': len(f['files']), 'lastSent': max((x.get('when', '') for x in f['sent']), default='')}


def path_for(key):
    if key not in KEYS:
        scan()
    return KEYS.get(key)


def editor_html(pdir):
    mp = os.path.join(pdir, 'model.json')
    m = json.load(open(mp, encoding='utf-8'))
    out = os.path.join(pdir, 'rasejumi', f"{m['id']}_LV_redaktors.html")
    src = [mp] + [os.path.join(HERE, 'sablons', 'redaktors', f) for f in ('lapa.html', 'iframe.js', 'viz3d.js')] + [os.path.join(HERE, 'sablons', 'sbe', 'plani', 'cad.js')]
    if not os.path.exists(out) or os.path.getmtime(out) < max(os.path.getmtime(f) for f in src if os.path.exists(f)):
        subprocess.run([sys.executable, os.path.join(HERE, 'redaktors.py'), mp, out], check=True, cwd=HERE,
                       stdout=subprocess.DEVNULL, env=dict(os.environ, PYTHONIOENCODING='utf-8'), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return open(out, encoding='utf-8').read()


SHIM = """<script>window.MM_LOCAL=%s;(function(){
var K=MM_LOCAL.key;function post(u,b){return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(function(r){if(!r.ok)return r.text().then(function(t){throw new Error(t||r.status)});return r.json()})}
var db={doc:function(){return{get:function(){return Promise.resolve({exists:false})},set:function(v){return post('/api/save/'+K,JSON.parse(v.json))}}}};
var dl={save:function(o){var d=o.data,b=d instanceof Blob?d:new Blob([d]);return fetch('/api/export/'+K+'?name='+encodeURIComponent(o.filename),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:b}).then(function(r){if(!r.ok)return r.text().then(function(t){throw new Error(t||r.status)});return r.json()}).then(function(j){var s=document.getElementById('status');setTimeout(function(){if(s)s.textContent='Saglabāts projekta mapē: eksports/'+j.name},50);})}};
window.claude={use:function(n){return n==='db'?Promise.resolve(db):n==='downloads'?Promise.resolve(dl):Promise.reject({code:'declined'})}};
addEventListener('DOMContentLoaded',function(){var mk=document.querySelector('header .mark');if(!mk)return;var a=document.createElement('a');a.href='/';a.className='mark back';a.title='Atpakaļ uz projektu arhīvu';a.innerHTML='<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>Projekti';mk.replaceWith(a);});
})();</script><style>header a.mark.back{display:inline-flex;align-items:center;gap:4px;color:#c9cfd6;text-decoration:none;letter-spacing:.04em;font:600 13px/42px var(--f-ui);padding-right:14px;margin-right:14px;border-right:1px solid #3d4248}header a.mark.back:hover{color:#fff}</style>"""


def rebuild_pages(mp):
    try:
        subprocess.run([sys.executable, os.path.join(HERE, 'build_model.py'), mp], cwd=HERE, timeout=600,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except Exception:
        pass


SPEC_KEYS = ('S1', 'S2', 'G1', 'J1')


def default_layers():
    c = json.load(open(os.path.join(HERE, 'sablons', 'mm-config.json'), encoding='utf-8'))['layers']
    return {k: {'name': c[k]['name'], 'layers': c[k]['layers']} for k in SPEC_KEYS if k in c}


def company_spec(cdir):
    try:
        return json.load(open(os.path.join(cdir, 'uznemums.json'), encoding='utf-8'))
    except Exception:
        return {}


def clean_layers(L):
    out = {}
    for k in SPEC_KEYS:
        rows = (L or {}).get(k)
        if not isinstance(rows, list):
            continue
        ok = []
        for r in rows[:30]:
            if isinstance(r, list) and len(r) >= 2:
                ok.append([str(r[0])[:120], max(0.0, min(2000.0, float(r[1] or 0))), str(r[2] if len(r) > 2 else '')[:2]])
        if ok:
            out[k] = ok
    return out


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', (s or '').strip()).strip('. ')
    return s[:80]


def new_project(b):
    c = load_cfg(); cos = companies(c)
    co = b.get('company') or ''
    if co not in cos:
        raise ValueError('Nav tāda uzņēmuma.')
    L, B, H = (float(b[k]) for k in ('garums', 'platums', 'augstums'))
    if not (3000 <= L <= 40000 and 2500 <= B <= 15000 and 2500 <= H <= 12000):
        raise ValueError('Izmēri ārpus robežām (garums 3–40 m, platums 2,5–15 m, kore 2,5–12 m).')
    args = [sys.executable, os.path.join(HERE, 'generate.py'), str(L), str(B), str(H), '--valodas', 'LV']
    pid = safe_name(b.get('id'))
    if not pid:   # nākamais brīvais MM-<m²>-NN visā arhīvā (generate.py pats skatās tikai repo MĀJAS mapi)
        g = int(round(L * B / 1e6 / 5.0) * 5); used = {x['id'] for x in scan()}; n = 1
        while any(u == f'MM-{g}-{n:02d}' or u.startswith(f'MM-{g}-{n:02d}-') for u in used) or os.path.exists(os.path.join(os.path.dirname(HERE), 'MĀJAS', f'{g}m2', f'MM-{g}-{n:02d}')):
            n += 1
        pid = f'MM-{g}-{n:02d}'
    if pid:
        args.insert(5, pid)
    if safe_name(b.get('nosaukums')): args += ['--nosaukums', safe_name(b.get('nosaukums'))]
    if b.get('mansards') in ('ja', 'ne'): args += ['--mansards', b['mansards']]
    if b.get('pamati') in ('stabveida', 'platne'): args += ['--pamati', b['pamati']]
    if b.get('tonis') in ('peleks', 'koks', 'sarkans', 'zals', 'balts'): args += ['--tonis', b['tonis']]
    r = subprocess.run(args, cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    mps = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().endswith('model.json') and os.path.exists(ln.strip())]
    if not mps:
        raise ValueError('Modeli neizdevās uzģenerēt: ' + (r.stderr.strip().splitlines() or ['?'])[-1])
    src = os.path.dirname(mps[0])
    dest = os.path.join(cos[co], os.path.basename(src))
    if os.path.abspath(src) != os.path.abspath(dest):
        n = 2
        while os.path.exists(dest):
            dest = os.path.join(cos[co], f'{os.path.basename(src)}-{n}'); n += 1
        shutil.move(src, dest)
        try: os.rmdir(os.path.dirname(src))   # tukšā <m²> mape repo MĀJAS
        except OSError: pass
    sp = company_spec(cos[co]).get('piragi_layers')
    if sp:   # uzņēmuma sienu specifikācijas kļūst par šī projekta pīrāgiem (projektā tās var mainīt redaktorā, cilnē Māja)
        mp = os.path.join(dest, 'model.json'); mj = json.load(open(mp, encoding='utf-8'))
        mj.setdefault('projekts', {})['piragi_layers'] = sp
        json.dump(mj, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        threading.Thread(target=rebuild_pages, args=(mp,), daemon=True).start()
    return key_of(dest)


def files_of(d):
    ed = os.path.join(d, 'eksports'); out = []
    if os.path.isdir(ed):
        for f in sorted(os.listdir(ed), key=lambda f: -os.path.getmtime(os.path.join(ed, f))):
            fp = os.path.join(ed, f)
            if os.path.isfile(fp):
                out.append({'name': f, 'size': os.path.getsize(fp), 'mtime': int(os.path.getmtime(fp))})
    try:
        sent = json.load(open(os.path.join(d, 'nosutits.json'), encoding='utf-8'))
    except Exception:
        sent = []
    return {'files': out, 'sent': sent}


def open_folder(p):
    if os.name == 'nt':
        os.startfile(p)
    else:
        subprocess.Popen(['xdg-open', p])


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        if '--konsole' in sys.argv:
            super().log_message(*a)

    def send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n).decode('utf-8') or '{}') if n else {}

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); p = u.path
        try:
            if p in ('/', '/index.html'):
                return self.send(200, open(os.path.join(HERE, 'sablons', 'arhivs', 'app.html'), encoding='utf-8').read(), 'text/html; charset=utf-8')
            if p == '/api/projects':
                pr = scan(); c = load_cfg()
                cos = [{'name': n, 'key': key_of(d), 'path': d, 'n': sum(1 for x in pr if x['company'] == n),
                        'spec': bool(company_spec(d).get('specifikacija_apstiprinata'))} for n, d in companies(c).items()]
                return self.send(200, {'projects': pr, 'companies': cos, 'root': c['root']})
            if p.startswith('/api/files/'):
                d = path_for(p[11:])
                return self.send(200, files_of(d)) if d else self.send(404, 'Nav', 'text/plain; charset=utf-8')
            if p.startswith('/file/'):   # /file/<key>/<nosaukums>: atver eksportēto failu pārlūkā
                k, _, nm = p[6:].partition('/'); d = path_for(k); nm = os.path.basename(urllib.parse.unquote(nm))
                fp = os.path.join(d or '', 'eksports', nm)
                if not d or not os.path.isfile(fp):
                    return self.send(404, 'Nav', 'text/plain; charset=utf-8')
                import mimetypes
                return self.send(200, open(fp, 'rb').read(), mimetypes.guess_type(nm)[0] or 'application/octet-stream')
            if p == '/api/company-spec':
                k = (urllib.parse.parse_qs(u.query).get('key') or [''])[0]; d = path_for(k)
                if not d:
                    return self.send(404, 'Uzņēmums nav atrasts', 'text/plain; charset=utf-8')
                cs = company_spec(d).get('piragi_layers') or {}
                return self.send(200, {'defaults': default_layers(), 'custom': cs, 'set': bool(cs)})
            if p == '/api/ping':
                return self.send(200, {'ok': True})
            if p.startswith('/edit/'):
                d = path_for(p[6:])
                if not d:
                    return self.send(404, 'Projekts nav atrasts', 'text/plain; charset=utf-8')
                pg = editor_html(d)
                return self.send(200, SHIM % json.dumps({'key': p[6:], 'dir': d}, ensure_ascii=False) + pg, 'text/html; charset=utf-8')
            if p == '/favicon.ico':
                f = os.path.join(HERE, 'sablons', 'arhivs', 'sbe.ico')
                return self.send(200, open(f, 'rb').read(), 'image/x-icon') if os.path.exists(f) else self.send(404, b'', 'text/plain')
            self.send(404, 'Nav', 'text/plain; charset=utf-8')
        except Exception as e:
            self.send(500, str(e), 'text/plain; charset=utf-8')

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        try:
            if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'):
                return self.send(403, 'Aizliegts', 'text/plain; charset=utf-8')
            if p.startswith('/api/export/'):
                d = path_for(p[12:])
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                nm = safe_name(os.path.basename((q.get('name') or ['fails'])[0])) or 'fails'
                if not d:
                    return self.send(404, 'Projekts nav atrasts', 'text/plain; charset=utf-8')
                data = self.rfile.read(int(self.headers.get('Content-Length') or 0))
                ed = os.path.join(d, 'eksports'); os.makedirs(ed, exist_ok=True)
                stem, ext = os.path.splitext(nm); fp = os.path.join(ed, nm)
                if os.path.exists(fp):   # nepārraksta: iepriekšējie nosūtītie faili paliek
                    nm = f"{stem}_{time.strftime('%Y-%m-%d_%H%M')}{ext}"; fp = os.path.join(ed, nm)
                open(fp, 'wb').write(data)
                return self.send(200, {'ok': True, 'name': nm})
            b = self.body()
            if p.startswith('/api/sent/'):
                d = path_for(p[10:])
                if not d or not b.get('file'):
                    return self.send(400, 'Norādi failu', 'text/plain; charset=utf-8')
                sp = os.path.join(d, 'nosutits.json')
                with LOCK:
                    try: L = json.load(open(sp, encoding='utf-8'))
                    except Exception: L = []
                    L.append({'file': os.path.basename(b['file']), 'to': (b.get('to') or '').strip()[:200], 'note': (b.get('note') or '').strip()[:500],
                              'when': time.strftime('%Y-%m-%dT%H:%M:%S')})
                    json.dump(L, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                return self.send(200, {'ok': True})
            if p.startswith('/api/save/'):
                d = path_for(p[10:])
                if not d or not isinstance(b, dict) or 'W' not in b:
                    return self.send(400, 'Nederīgs modelis', 'text/plain; charset=utf-8')
                mp = os.path.join(d, 'model.json')
                with LOCK:
                    if os.path.exists(mp):
                        shutil.copy2(mp, mp + '.bak')
                    tmp = mp + '.tmp'
                    json.dump(b, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                    os.replace(tmp, mp)
                threading.Thread(target=rebuild_pages, args=(mp,), daemon=True).start()
                return self.send(200, {'ok': True})
            if p == '/api/company':
                n = safe_name(b.get('name'))
                if not n:
                    return self.send(400, 'Ievadi nosaukumu', 'text/plain; charset=utf-8')
                c = load_cfg(); d = os.path.join(c['root'], n); os.makedirs(d, exist_ok=True)
                return self.send(200, {'ok': True, 'key': key_of(d)})
            if p == '/api/company-spec':
                d = path_for(b.get('key', ''))
                if not d:
                    return self.send(404, 'Uzņēmums nav atrasts', 'text/plain; charset=utf-8')
                cs = company_spec(d); L = clean_layers(b.get('piragi_layers'))
                dfl = {k: v['layers'] for k, v in default_layers().items()}
                L = {k: v for k, v in L.items() if v != dfl.get(k)}   # glabā tikai atšķirīgos
                if L: cs['piragi_layers'] = L
                else: cs.pop('piragi_layers', None)
                cs['specifikacija_apstiprinata'] = True
                json.dump(cs, open(os.path.join(d, 'uznemums.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                return self.send(200, {'ok': True})
            if p == '/api/new':
                return self.send(200, {'key': new_project(b)})
            if p == '/api/open':
                d = path_for(b.get('key', ''))
                if not d:
                    return self.send(404, 'Mape nav atrasta', 'text/plain; charset=utf-8')
                open_folder(d); return self.send(200, {'ok': True})
            self.send(404, 'Nav', 'text/plain; charset=utf-8')
        except ValueError as e:
            self.send(400, str(e), 'text/plain; charset=utf-8')
        except Exception as e:
            self.send(500, str(e), 'text/plain; charset=utf-8')


def running():
    import urllib.request
    try:
        return urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/ping', timeout=1).status == 200
    except Exception:
        return False


def open_window():
    url = f'http://127.0.0.1:{PORT}/'
    for b in (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
              r'C:\Program Files\Google\Chrome\Application\chrome.exe', os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')):
        if os.path.exists(b):
            subprocess.Popen([b, '--app=' + url, '--window-size=1440,900']); return
    webbrowser.open(url)


def main():
    if running():
        open_window(); return
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    if '--bez-loga' not in sys.argv:
        threading.Timer(0.4, open_window).start()
    srv.serve_forever()


if __name__ == '__main__':
    main()
