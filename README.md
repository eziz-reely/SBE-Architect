# SBE Architect

MM Homes modeļu bots kā Claude plugin. No mājas gabarītiem (garums, platums, kores augstums) uztaisa skiču projekta A3 lapu LV un EN (plāni, mansards, fasādes, eksplikācija, rakstlaukums) un Gemini vizualizācijas.

## Instalēšana

    /plugin marketplace add eziz-reely/SBE-Architect
    /plugin install sbe-architect@sbe-architect

## Komandas

- `/sbe-arhitekts`: jauns modelis. Uzdod jautājumus ar ķeksīšiem, uzģenerē plānojumu (vienmēr sāk ar 1. variantu), pārbauda un parāda apstiprināšanai. Vizualizācijas tikai pēc apstiprinājuma.
- `/editbot <komentārs>`: papildina botu (noteikumi, logu veidi, mēbeļu izkārtojums), pārbauda un saglabā šajā repo.

## Struktūra

- `bot/`: kods (`planner.py`, `rules_check.py`, `generate.py`, `build_model.py`, `ref.py`, `viz.py`), `sablons/` (SBE šablons, toņu tekstūras) un noteikumi `bot/zinasanas_mebeles_logi.md`.
- `bot/redaktors.py` un `bot/sablons/redaktors/`: rasējuma redaktors (viena HTML lapa). `python3 bot/redaktors.py <model.json>` uztaisa `rasejumi/<id>_LV_redaktors.html`. Taustiņi: Shift+klikšķis atlasa vairākus logus/durvis/mēbeles, Ctrl+vilkšana kopē atlasīto, Ctrl+C / Ctrl+V kopē un iekopē, Delete dzēš visu atlasīto. Poga „3D un Gemini”: 3D skats (8 fotogrāfa kadri: 4 fasādes un 4 stūri), terase pie izvēlētās fasādes, references PNG 2400×1600 un gatavs Gemini prompts kopēšanai (`bot/sablons/redaktors/viz3d.js`, three.js r128 MIT).
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
