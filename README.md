# SBE Architect

MM Homes modeļu bots kā Claude plugin. No mājas gabarītiem (garums, platums, kores augstums) uztaisa skiču projekta A3 lapu LV un EN (plāni, mansards, fasādes, eksplikācija, rakstlaukums) un Gemini vizualizācijas.

## Instalēšana

    /plugin marketplace add eziz-reely/SBE-Architect
    /plugin install sbe-architect@sbe-architect

## Lejupielāde kā zip (bez Claude)

1. GitHub lapā: **Code, Download ZIP** (vai tieši `https://github.com/eziz-reely/SBE-Architect/archive/refs/heads/main.zip`). Atarhivē jebkurā mapē.
2. Vajag tikai Python 3 (un pārlūku). Redaktora lapa: `python3 bot/redaktors.py "MĀJAS/100m2/MM-100-01/model.json"`, tad atver izveidoto failu `…/rasejumi/MM-100-01_LV_redaktors.html` ar Chrome vai Edge dubultklikšķi (ne čata priekšskatījumā).
3. Ar Claude Code to pašu var uzstādīt kā spraudni, skat. „Instalēšana" augstāk.

Redaktorā: rīku josla kreisajā malā, taustiņus var mainīt ar tastatūras ikonu joslas apakšā. Palīglīnijas: G, vai velc no rasējuma kreisās/augšējās malas.

## Darbvirsmas programma (arhīvs + redaktors)

`python bot/app_saisne.py` uzliek uz darbvirsmas saīsni **SBE projekti** ar savu ikonu. Tā atver vienu logu (Edge/Chrome lietotnes režīmā, tikai šajā datorā, `http://127.0.0.1:8737`):
- pirmā lapa ir arhīvs: uzņēmumu mapes kreisajā pusē, projekti kartītēs ar mazu plānu, meklēšana un kārtošana;
- **Jauns projekts**: izvēlas uzņēmumu, ievada garumu, platumu, kores augstumu (un pēc vēlēšanās nosaukumu, mansardu, pamatus, toni), bots uzģenerē modeli un atver to redaktorā;
- **Jauns uzņēmums** izveido mapi; mapes ikona atver uzņēmuma vai projekta mapi Explorer;
- redaktorā **Saglabāt** ieraksta `model.json` projekta mapē (iepriekšējais paliek kā `model.json.bak`) un fonā pārbūvē LV/EN lapu; "‹ Projekti" ved atpakaļ uz arhīvu.

Uz jauna datora (Google Drive jau sinhronizēts): `git clone https://github.com/eziz-reely/SBE-Architect`, tad `python bot/app_saisne.py`. Programma pati atrod Drive mapi `SBE\PROJEKTI` (jebkurā diska burtā) un rāda tos pašus projektus.

Mapes: `<arhīvs>/<uzņēmums>/<projekts>/model.json`. Iestatījumi `%USERPROFILE%\.sbe-arhivs.json`: `root` (noklusējums `Desktop\MM System\PROJEKTI`) un `companies`, kur esošas mapes piesaista kā uzņēmumu (noklusējumā "MM Homes" = `Desktop\MM System\MĀJAS`).

## Projektu arhīvs

`python3 bot/arhivs.py PROJEKTI` uzbūvē `PROJEKTI/arhivs.html`: viens logs ar visiem projektiem (nosaukums, laukums, plāna un fasādes miniatūra), meklēšana un filtrs pa uzņēmumiem. Klikšķis atver projekta redaktoru. Mapes: `PROJEKTI/<uzņēmums>/<projekts>/model.json`. Pievienot modeli: `python3 bot/arhivs.py PROJEKTI --pievienot model.json --uznemums "Uzņēmums"`. Miniatūras pārbūvējas pašas, ja `model.json` ir mainīts. Mape `PROJEKTI/` nonāk repo ignorēto sarakstā (klientu dati).

## Komandas

- `/sbe-arhitekts`: jauns modelis. Uzdod jautājumus ar ķeksīšiem, uzģenerē plānojumu (vienmēr sāk ar 1. variantu), pārbauda un parāda apstiprināšanai. Vizualizācijas tikai pēc apstiprinājuma.
- `/editbot <komentārs>`: papildina botu (noteikumi, logu veidi, mēbeļu izkārtojums), pārbauda un saglabā šajā repo.

## Struktūra

- `bot/`: kods (`planner.py`, `rules_check.py`, `generate.py`, `build_model.py`, `ref.py`, `viz.py`), `sablons/` (SBE šablons, toņu tekstūras) un noteikumi `bot/zinasanas_mebeles_logi.md`.
- `bot/redaktors.py` un `bot/sablons/redaktors/`: rasējuma redaktors (viena HTML lapa). `python3 bot/redaktors.py <model.json>` uztaisa `rasejumi/<id>_LV_redaktors.html`. Taustiņi: Shift+klikšķis atlasa vairākus logus/durvis/mēbeles, Ctrl+vilkšana kopē atlasīto, Ctrl+C / Ctrl+V kopē un iekopē, Delete dzēš visu atlasīto. Poga „3D un Gemini”: 3D skats (8 fotogrāfa kadri: 4 fasādes un 4 stūri), terase pie izvēlētās fasādes, references PNG 2400×1600 un gatavs Gemini prompts kopēšanai (`bot/sablons/redaktors/viz3d.js`, three.js r128 MIT).
- `bot/ingetrazo/`: spraudnis IngeTrazo (bezmaksas 3D modelētājs), kas no `model.json` pats uzbūvē mājas 3D modeli ar BIM atzīmēm. Skat. `bot/ingetrazo/README.md`.
- `bot/sketchup/`: SketchUp paplašinājums, kas importē redaktora eksportēto 3D modeli (.rb). Lai to uzinstalētu, abus failus saarhivē kā .rbz.
- `skills/sbe-arhitekts`, `skills/editbot`: komandu instrukcijas.

## Vides prasības

Python 3, Node.js ar Playwright (pārbaudei un ekrānuzņēmumiem). Vizualizācijām vides mainīgais `GEMINI_API_KEY` (to nekad neglabā repo).

## Kā lietot (īsi)

1. **Jauns modelis:** jaunā threadā raksti `/sbe-arhitekts` (vai "jauns modelis"). Atbildi čatā uz jautājumu sarakstu ar ķeksīšiem: gabarīti (garums × platums × kores augstums), nosaukums, tonis, mansards. Pārējam ir noklusējumi.
2. **Bots uztaisa vienu plānojumu (V01)**, A3 lapu LV un EN un pārbauda to ar `rules_check` un `mm-check`. Tu redzi plāna bildi.
3. **Tu apstiprini vai labo.** Ja kaut kas nav labi, raksti `/editbot` ar numurētiem punktiem un bildi. Bots to ieraksta noteikumos un nākamie modeļi to ievēro.
4. **Tikai pēc apstiprinājuma** raksti, ka gribi vizualizācijas. Tām vajag `GEMINI_API_KEY` (iestatīts projekta vidē `gemini`).
5. Faili ir `MM System\MĀJAS\<m2>\<id>\`: `model.json`, `rasejumi/*.html`, `viz/*.png`. Tos vēlāk izmanto mājaslapai.

## Redaktors

Redaktorā plānu un fasādes labo ar peli, un lapa pārzīmējas uzreiz.
- **Plāns:** logi, durvis, mēbeles, kāpnes, mēri un palīglīnijas. Ctrl + vilkšana uztaisa kopiju.
- **Mājas izmēri un jumts:** garums, platums, kores augstums, jumta slīpums, pārkare, vēja kaste un notekas.
- **Rakstlaukums:** modeļa nosaukums un logo.
- **AR projekts:** visas SBE AR lapas. Lapas var izslēgt, numerācija pārkārtojas pati, rakstlaukumu aizpilda vienā vietā.
- **Eksports:** PDF (150, 300 vai 600 dpi), SVG, DXF un SketchUp (.rb).

Redaktors nemaina `sablons/sbe`. Visi MM labojumi tiek ielikti būvējot (`build_model.py`).

## Lai komandas nesajūk

- `/sbe-arhitekts`: tikai jauns modelis. Neko nemaina botā.
- `/editbot`: tikai bota plānošanas prasmju uzlabošana (noteikumi, logi, mēbeļu izkārtojums). Modeli neveido, tikai pārbauda uz pēdējā.
- Vecos konta skilus (`modelu-bots`, `sbe-arhitekts`, `editbot`, `gemini-arch-foto`, `lwdc-plani-fasades`) vajag izslēgt vai dzēst Settings > Skills, lai tie nesajūk ar šī plugin `/sbe-arhitekts` un `/editbot`.
- Vienīgā galvenā bota versija ir šis repo. Neviena cita kopija (dators, projekta faili) vairs nav jālabo.
