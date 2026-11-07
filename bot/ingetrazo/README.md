# MM Homes spraudnis IngeTrazo

[IngeTrazo](https://github.com/ingelibre/ingetrazo) ir bezmaksas 3D modelētājs (GPL-3.0). Šis spraudnis no SBE-Architect `model.json` pats uzbūvē mājas 3D modeli ar BIM atzīmēm.

## Uzstādīšana
1. IngeTrazo: **Extensions, Open plugins folder**.
2. Ieliec tajā visu mapi `mm_homes` (no šīs mapes). Windows: `%APPDATA%\ingetrazo\plugins\`, Linux: `~/.local/share/ingetrazo/plugins/`.
3. Restartē IngeTrazo. Izvēlnē **Extensions** parādās **MM Homes**.

## Lietošana
1. Redaktorā: **Eksportēt, model.json** (terase un citi labojumi iet līdzi).
2. IngeTrazo: **Extensions, MM Homes, Ielādēt model.json…**. Māja parādās uzreiz, viss ir viens solis (Ctrl+Z atceļ).
3. Pēc labojumiem redaktorā: eksportē `model.json` vēlreiz un spied **Pārbūvēt no šī paša faila**. Spraudnis nomaina tikai savus objektus, tavi zīmējumi paliek.
4. **Mainīt fasādes toni…** pārkrāso māju.

Ko tas uzbūvē (visi kā atsevišķas grupas ar IFC klasi): `IfcWall` (ārsienas ar logu un durvju ailām, starpsienas), `IfcWindow` (rāmis un stikls, arī slīpais gala logs), `IfcDoor` (ārdurvis), `IfcSlab` (grīda, mansarda pārsegums, terase), `IfcRoof`, `IfcStair`. Mēbeles netiek būvētas. Tālāk IngeTrazo var eksportēt IFC un daudzumus.

## Pārbaude
Ģeometrija (`mm_homes/geometry.py`) nav atkarīga no IngeTrazo un ir pārbaudīta: katrs ķermenis ir slēgts un ar pareizu virzienu.
`python3 -I bot/ingetrazo/tests/test_geometry.py` un `python3 -I -c "import sys;sys.path.insert(0,'bot/ingetrazo/tests');import test_adapter as t;t.test_build_into_and_replace()"`.
Savienojums ar pašu IngeTrazo (`__init__.py`) pārbaudīts tikai ar aizstājējiem (stub), tāpēc pirmajā reizē jāpārbauda programmā.

## Licence
Faili `mm_homes/*` ir GPL-3.0-or-later, lai derētu kopā ar IngeTrazo.
