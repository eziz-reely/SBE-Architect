"""Plānojumu bibliotēka: konkurentu plānojumi (competitor-analize/*/planojumi.json) -> projektēšanas normas.

Normas netiek rakstītas ar roku: tās tiek aprēķinātas no bibliotēkas datiem, tāpēc pievienojot jaunu
konkurentu vai modeli, normas atjaunojas pašas.

SVARĪGI: bibliotēka ir sadalīta pēc KLASES un TIPA, un tie netiek jaukti:
  klase  lidz60 (apbūves laukums līdz 60 m2) | virs60 (lielākas mājas)
  tips   modulu (rūpnīcā gatavas moduļu mājas) | karkass (uz vietas būvēta koka karkasa māja)
Normas un pārbaudes mājai līdz 60 m2 ņem TIKAI klase=lidz60 un tips=modulu.
Lielāko māju (virs60) un karkasa māju zināšanas ir bibliotēkā, bet tās izmanto tikai tad, ja projektē tādu pašu klasi/tipu.

    from planlib import norms, check_input, check_model, nearest
    python planlib.py                      # normas pa klasēm
    python planlib.py 8570 3500 4000       # pārbauda gabarītus pret atbilstošās klases bibliotēku
    python planlib.py virs60               # normas lielajām mājām
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, 'competitor-analize')
LIMIT = 62   # m2: robeža starp klasēm (60 m2 + nelielas noapaļošanas atšķirības)

KIND = [  # (regex pēc telpas nosaukuma, veids)
    (r'vannas|^wc', 'bath'), (r'pirts', 'sauna'), (r'dzīvojam', 'living'),
    (r'guļamistab|istaba', 'bed'), (r'halle|priekštelp|priekšnam', 'hall'), (r'koridor', 'corridor'),
]
MODEL_KIND = {'Guļamistaba': 'bed', 'WC': 'bath', 'Priekšnams': 'hall', 'Dzīvojamā istaba ar virtuvi': 'living'}


def kind(name):
    n = name.lower()
    for rx, k in KIND:
        if re.search(rx, n):
            return k


def built_area(m):
    """Apbūves laukums m2: L/T mājām aprēķina no dzīvojamās platības, citādi no ārējiem izmēriem."""
    if m.get('built_area_m2'):
        return m['built_area_m2']
    if m.get('shape') in ('L', 'T') and m.get('living_area_m2'):
        return m['living_area_m2'] * 1.25
    if 'outer_m' in m:
        return m['outer_m'][0] * m['outer_m'][1]
    return (m.get('living_area_m2') or 0) * 1.2


def klase_of(m_or_area):
    a = m_or_area if isinstance(m_or_area, (int, float)) else built_area(m_or_area)
    return 'lidz60' if a <= LIMIT else 'virs60'


def load(klase=None, tips=None):
    """Referenču modeļi. klase/tips filtrē; None = visi (izmantot tikai apzināti, nejaukt klases)."""
    out = []
    for f in sorted(glob.glob(os.path.join(LIB, '*', 'planojumi.json'))):
        src = os.path.basename(os.path.dirname(f))
        for mid, m in json.load(open(f, encoding='utf-8')).items():
            if mid.startswith('_'):
                continue
            m = dict(m, src=src, id=mid)
            m.setdefault('tips', 'modulu')
            m['klase'] = m.get('klase') or klase_of(m)
            if klase and m['klase'] != klase:
                continue
            if tips and m['tips'] != tips:
                continue
            out.append(m)
    return out


def norms(klase='lidz60', tips='modulu'):
    """Telpu platību diapazoni (m2), plati un apbūves gabarīti vienai klasei un tipam.
    Gabarītu statistikā neiet L un T formas mājas (to ierobežojošais taisnstūris neder platuma pārbaudei)."""
    lib = load(klase, tips)
    rooms, outer = {}, []
    for m in lib:
        if 'outer_m' in m and m.get('shape') not in ('L', 'T'):
            outer.append(m['outer_m'])
        for r in m.get('rooms', []):
            k, a = kind(r['name']), r.get('m2')
            if k and a and r.get('n') != 'loft' and not str(r.get('n', '')).endswith('st.'):
                rooms.setdefault(k, []).append(a)
    short = sorted(min(o) for o in outer)
    return {
        'klase': klase, 'tips': tips,
        'rooms_m2': {k: (min(v), max(v), len(v)) for k, v in rooms.items()},
        'outer_short_m': (short[0], short[-1]) if short else None,
        'short_sides_m': sorted({round(x, 1) for x in short}),
        'outer_long_m': (min(max(o) for o in outer), max(max(o) for o in outer)) if outer else None,
        'models': len(lib),
    }


def nearest(L_mm, B_mm, n=2, tips='modulu'):
    """Tuvākie references modeļi pēc apbūves platības, TAJĀ PAŠĀ klasē (līdz 60 / virs 60) un tipā."""
    A = L_mm * B_mm / 1e6
    lib = [m for m in load(klase_of(A), tips) if 'outer_m' in m]
    return sorted(lib, key=lambda m: abs(built_area(m) - A))[:n]


def check_input(L, B, H, tips='modulu'):
    """Brīdinājumi par gabarītiem pret tās pašas klases bibliotēku (tikai brīdinājumi)."""
    klase = klase_of(L * B / 1e6)
    N, w = norms(klase, tips), []
    if not N['outer_short_m']:
        return [f'Bibliotēkā nav {tips} mājas klasē {klase}, pārbaudi nevar veikt.']
    side, long_ = min(L, B) / 1000, max(L, B) / 1000
    known = N['short_sides_m']
    if min(abs(side - k) for k in known) > 0.35:
        w.append(f'Īsā mala {side:.2f} m: {klase} {tips} mājām bibliotēkā tā ir {", ".join(f"{k:g}" for k in known)} m.')
    l0, l1 = N['outer_long_m']
    if long_ < l0 - 1 or long_ > l1 + 1.5:
        w.append(f'Garums {long_:.2f} m ārpus bibliotēkas diapazona {l0:.1f}-{l1:.1f} m ({klase}).')
    if not 3500 <= H <= 4500:
        w.append(f'Kores augstums {H / 1000:.2f} m neparasts: bibliotēkas mājām ~3.8-4.0 m, ar mansardu līdz 4.5 m.')
    return w


def check_model(path, tips='modulu'):
    """Pārbauda uzģenerētā model.json telpu platības pret tās pašas klases diapazoniem (±15 %/25 %)."""
    m = json.load(open(path, encoding='utf-8'))
    P = m.get('poly')   # L/T: klase pēc īstā apbūves laukuma, nevis ārējā taisnstūra
    A = abs(sum(P[i][0] * P[i - 1][1] - P[i - 1][0] * P[i][1] for i in range(len(P)))) / 2e6 if P else m['W'] * m['D'] / 1e6
    klase = klase_of(A)
    N, w = norms(klase, tips)['rooms_m2'], []
    for r in m['rooms']:
        k = MODEL_KIND.get(r['n'])
        if k not in N:
            continue
        a = sum(x[2] * x[3] for x in r['r']) / 1e6
        lo, hi, _ = N[k]
        if a < lo * 0.85:
            w.append(f"{r['n']} {a:.1f} m2 par mazu: {klase} bibliotēkas minimums {lo:g} m2.")
        elif a > hi * 1.25:
            w.append(f"{r['n']} {a:.1f} m2 par lielu: {klase} bibliotēkas maksimums {hi:g} m2.")
    return w


def show(klase, tips):
    N = norms(klase, tips)
    print(f"[{klase} / {tips}] {N['models']} modeļi")
    for k, (lo, hi, n) in N['rooms_m2'].items():
        print(f'  {k:9s} {lo:g}-{hi:g} m2  ({n} telpas)')
    if N['outer_long_m']:
        print('  īsā mala', N['short_sides_m'], 'm; garā mala', N['outer_long_m'], 'm')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if len(a) == 3:
        L, B, H = map(float, a)
        show(klase_of(L * B / 1e6), 'modulu')
        for x in check_input(L, B, H) or ['Gabarīti atbilst bibliotēkai.']:
            print('!', x)
        for m in nearest(L, B):
            print('  tuvākais references:', m['src'], m['id'], m['outer_m'], m['living_area_m2'], 'm2')
    elif a and a[0] in ('lidz60', 'virs60'):
        show(a[0], a[1] if len(a) > 1 else 'modulu')
    else:
        for kl in ('lidz60', 'virs60'):
            for tp in ('modulu', 'karkass'):
                if load(kl, tp):
                    show(kl, tp)
