"""Sagatavo app/public: uzbūvē katras mājas redaktoru un houses.json.
Lietošana: python app/build.py   (no repo saknes)"""
import glob, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
out = os.path.join(HERE, 'public', 'redaktors'); os.makedirs(out, exist_ok=True)
houses = []
for mp in sorted(glob.glob(os.path.join(ROOT, 'MĀJAS', '**', 'model.json'), recursive=True)):
    m = json.load(open(mp, encoding='utf-8'))
    dst = os.path.join(out, m['id'] + '.html')
    subprocess.run([sys.executable, os.path.join(ROOT, 'bot', 'redaktors.py'), mp, dst], check=True, stdout=subprocess.DEVNULL)
    houses.append({'id': m['id'], 'name': (m.get('projekts') or {}).get('modela_nosaukums') or m.get('nosaukums') or m['id'], 'area': m.get('platiba_grupa', ''), 'W': m.get('W'), 'D': m.get('D')})
json.dump({'houses': houses, 'v': len(houses)}, open(os.path.join(HERE, 'public', 'houses.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(houses), 'mājas')
