---
name: sbe
description: MM Homes modeļu bots: no mājas gabarītiem (garums, platums, kores augstums) uztaisa klienta projekta A3 lapu (plāni, fasādes, eksplikācija, rakstlaukums) LV un EN.
---

# MM Homes modeļu bots

Bots ir šajā plugin mapē `${CLAUDE_PLUGIN_ROOT}/bot/` (galvenā versija, GitHub repo `eziz-reely/SBE-Architect`). Rezultāti tiek saglabāti mapē `MM System\MĀJAS\<m2 grupa>\<modeļa id>\`.
Botam ir divas sadaļas: **KLIENTA PROJEKTS** (aktīvā, visu dara šeit) un **RAŽOŠANAS PROJEKTS** (vēl nav uztaisīts).

## 1. Vispirms OBLIGĀTI uzdod jautājumus

Lietotājam jāieraksta tikai mājas gabarīti, viss pārējais ir izvēle. Jautājumus OBLIGĀTI uzdod kā atķeksējamus variantus:
- Claude Code datorā: rīks AskUserQuestion (ķeksīši).
- Projekta thread: jautājumus raksti PARASTĀ ČATA ZIŅĀ (post_message) kā numurētu sarakstu ar [x]/[ ] variantiem un noklusējumiem jau atzīmētiem [x]. Kartīti (`writing_draft_v0`, post_widget) NELIETO, lietotājam tā ir neērta. Lietotājs atbild čatā ar numuriem (piem. "1 ok, 2 Freya, 3 sarkans"), ieraksta gabarītus un nosaukumu. Kas nav pateikts, paliek noklusējums.
- Numurēts saraksts čatā arī tad, ja AskUserQuestion nav pieejams. Pie katra jautājuma noklusējums ir atzīmēts.

1. **Fāze**: [x] Klienta projekts (uz lapas "SKICES PROJEKTS")   [ ] Ražošanas projekts (vēl nav pieejams)
2. **Gabarīti** (jāieraksta): garums × platums × kores augstums, mm. Piemērs: 8570 × 3500 × 4000.
   Kores augstumu (mājas augstumu) lietotājs norāda no grīdas paneļa APAKŠAS ("4m" = 4000 mm no paneļa apakšas). Arhitektūras atzīmes paliek no ±0,000 (grīdas pīrāga augšas), tāpēc stabveida pamatiem kore virs ±0,000 = augstums − grīdas pīrāgs G1 (275,5 mm): 4000 mm → atzīme +3,725. Bots to izdara pats (`augstums_0` model.json); rakstlaukumā rāda lietotāja augstumu. Platnei grīdas paneļa nav, atņem 0. Pie 4000 un griestiem 2200 kore virs lofta grīdas ir ~1029 mm; loft derīgs, ja ≥ 1000 mm [MM].
3. **Modeļa nosaukums** (jāieraksta, piem. Freya). Rakstlaukumā zem tā raksta "MM <m²>", piem. "MM 30". Mapes id paliek MM-<m2>-NN.
4. **Fasādes tonis** (tekstūras `sablons\tex`): [x] Grafīta pelēks   [ ] Norvēģu sarkans (automātiski balti logi, durvis, apmales un 90 mm stūru apdare)   [ ] Dabīgs koks   [ ] Tumši zaļš (balti logi)   [ ] Balts (gaiši pelēks, tumši logi)
5. **Mansards**: [x] Jā, mansarda stāvs ar guļvietu un logiem (`--mansards ja`)   [ ] Nē (`--mansards ne`)
5a. **Plānojuma varianti**: [x] Nē, viens plāns (etalons MM 30 tips)   [ ] Jā, N varianti (`--varianti N`, plānotājs: II/L/T, ar mansardu tikai II; guļamistabu skaits pēc laukuma vai `--gulamistabas`)
5b. **Pīrāgu biezumi** (ārsienu pīrāga biezumi ar mēriem plānos): [x] Nerādīt (`--piragi ne`, noklusējums: sienu biezuma mēri 284/283 netiek zīmēti, un telpu mēru ķēdes beidzas pie telpu virsmām bez sienas biezuma atzīmēm/svītriņām ārpus sienas)   [ ] Rādīt (`--piragi ja`). Pīrāgu zīmējumi ar slāņiem (S1, S2, grīda, jumts) botā vēl nav uztaisīti klienta lapai, tos pasaki lietotājam, ja prasa.
6. **Pamati**: [x] Stabveida, cokols metāla apdare RAL 9005   [ ] Stabveida, cokols metāla apdare RAL 7016 (`--cokols "RAL 7016"`)   [ ] Pamatu plātne, betona cokols
7. **Piezīmes rakstlaukumā** (var atķeksēt vairākas):
   [x] Pamatu veids un cokols (no 6. jautājuma)
   [x] Griestu augstums zem mansarda: [x] 2200 mm   [ ] cits (ierakstīt)
   [ ] Papildu info par šo projektu (ierakstīt, var vairākas rindas)
8. **Objekta adrese**: [x] Tukuma nov., Kandavas pag. | "Melnupes", Kandava | Latvia, LV-3120   [ ] Cita (ierakstīt)   [ ] Bez adreses (`--bez-adreses`, sadaļu rakstlaukumā nerāda)
9. **Revīzija**: [x] 00, pirmais izdevums   [ ] Nākamā (01, 02, ...), jāieraksta, kas mainīts
10. **Papildu rādītāji rakstlaukumā**: [x] Tikai standarta   [ ] Pievienot (ierakstīt "Nosaukums=Vērtība")
11. **Valodas**: [x] LV un EN   [ ] Tikai LV (`--valodas LV`)
11b. **3D modelis SketchUp**: [ ] Nē   [x] Jā, uztaisīt `--skp` (3d/<id>.dae atveras SketchUp ar File > Import, vienības mm; <id>_skp.rb palaiž Ruby konsolē; .obj rezerves). Modelis no model.json: grīdas panelis uz stabiem, cokols, ārsienas ar logu/durvju caurumiem, iekšsienas, mansarda grīda, divslīpju jumts, logi ar rāmjiem un apmalēm, ārdurvis, mansarda logi. Mēbeles netiek modelētas. Pa tiešo .skp bots nevar uzrakstīt (SketchUp slēgts formāts), tāpēc .dae un Ruby skripts.
12. **Vizualizāciju atmosfēra** (katram modelim sava, visiem 3 toņiem tā pati):
    [x] Automātiski pēc modeļa numura (01 mežs, 02 fjords, 03 krasts, 04 plato, 05 ziema, 06 rudens, tad no sākuma)
    [ ] Priežu mežs un granīta klintis (`mezs`)   [ ] Fjords un kalni (`fjords`)   [ ] Jūras krasts (`krasts`)
    [ ] Kalnu plato (`plato`)   [ ] Ziema, sniegs (`ziema`)   [ ] Rudens bērzu birzs (`rudens`)

Ja kāda atbilde prasa ko tādu, ko bots vēl neprot (piem. mansards L/T formai), to pasaki un neizdomā pats.

## 2. Palaišana (viena komanda: jautājumi ar ķeksīšiem, tad viss pats)

Bots ir `${CLAUDE_PLUGIN_ROOT}/bot/`. Tajā ir viss: skripti, `rules_check.py`, šabloni, toņu tekstūras, LOGO, konkurentu dati. Nekas nav jālasa no lietotāja datora.

1. Uzdod 1. sadaļas jautājumus ar ķeksīšiem. Lietotājam jāieraksta tikai gabarīti un nosaukums.
   - Garums no platuma: ja lietotājs prasa "N m²", garums = N / platums, noapaļots uz leju līdz 5 mm (10 mm solis), apbūves laukums nepārsniedz N. Piem. 3500 platums, 40 m² -> garums 11425 (39,99 m²).
2. Nokopē botu uz scratchpad: `cp -r ${CLAUDE_PLUGIN_ROOT}/bot mms/modelu-bots` un tukšu `mms/MĀJAS`. Plugin mapi nelabo darba laikā.
3. Nākamo numuru noskaidro no lietotāja datora `MM System\MĀJAS\<m2>\` (device_list_dir). Ja scratchpad jau ir iepriekšēja izvade, norādi nākamo id pats, citādi numurs paceļas.
4. Palaid BEZ `--viz`. **Vienmēr sāc ar `--varianti 1`** (citus variantus tikai pēc lietotāja pieprasījuma):

       python3 generate.py 11425 3500 4000 MM-40-03 --mansards ja --varianti 1 --nosaukums <nos> --tonis peleks --pamati stabveida --griesti 2200 --rev 00 --adrese "..."

5. Pārbaude: `node sablons/mm-check.mjs <html>` jābeidzas ar "OK". Ja ir kļūdas, pasaki lietotājam. Lapu apskati ar Playwright ekrānuzņēmumu (`/opt/node22/lib/node_modules/playwright`).
6. **Plānojumus vispirms rāda lietotājam apstiprināšanai. Projekta threadā PĒC NOKLUSĒJUMA plānu rāda tieši čatā kā Artifact (publicē rasējumu HTML `rasejumi/<id>_LV.html` ar Artifact rīku un pievieno ziņai). Ne PDF, ne PNG, ne failu pielikumi. Ekrānuzņēmumu pievieno tikai, ja lietotājs to prasa. Vizualizācijas (`viz.py` vai `--viz`) netaisa, kamēr lietotājs nav apstiprinājis plānojumu UN pateicis, ka grib redzēt viz.** Tad: `python3 viz.py <id>` (Gemini, atslēga `GEMINI_API_KEY`).
7. Pēc apstiprinājuma failus saglabā `/mnt/project-files/mm-system/MAJAS/<m2>/<id>/` un lietotāja datorā `MM System\MĀJAS\<m2>\<id>\` (device_commit_files): model.json, rasejumi/*.html, viz/*. Visi izveidotie faili tiks izmantoti mājaslapā, tāpēc nekā neizlaid.

`--griesti 0` nozīmē, ka griestu piezīmi nerāda. Ja `model.json` ir labots ar roku, lapu pārbūvē ar `python3 build_model.py <model.json>`. Pieejami 5 fasādes toņi: `peleks` (grafīta pelēks, noklusējums), `koks` (dabīgs koks), `sarkans`, `zals` (tumši zaļš), `balts` (gaiši pelēks/balts). Visi tiek taisīti vizualizācijās (`viz.py`), `--tonis` izvēlas lapas toni.

## 3. KLIENTA PROJEKTS: noteikumi

0. **Izmēru ķēdes:** mansarda plānam ir tie paši mājas gabarīti (garums, platums) kā 1. stāvam. Ķēde ar atverēm, kurā nav atveru, nedublē kopējo izmēru: 1. stāva apakšā un sānos katrs gabarīts parādās vienu reizi (10 000 un 4000).
0a. **Mājas augstuma ķēde:** katrā fasādē pa labi viena vertikāla mēra ķēde ar mājas augstumu no grīdas paneļa apakšas līdz kores jumta virsmai (piem. 4000). Skaitlis ir lietotāja ievadītais augstums; atzīmes (+3,725 u.c.) paliek no ±0,000.
0b. **Mansarda piecstūra (slīpais) logs** gala fasādē ir TĀDĀ PAŠĀ platumā kā lielais frontālais stiklojums zem tā, simetrisks un centrēts uz kores ass. Ja ar rāmi neietilpst, logu nesašaurina, bet paaugstina virzienā uz jumtu (atkāpe no jumta 200 mm, sānu malas ≥ 300 mm); šaurāku logu pieļauj tikai tad, ja sānu malas citādi < 300 mm. Pēc jebkuras sašaurināšanas logu pārcentrē (nevis atstāj veco `y`, tad forma sanāk sakropļota).
1. **Rakstlaukums ir dizainisks un vertikāls**, labajā joslā (x 247–287). No augšas uz leju tajā ir:
   - MM HOMES zīmols tumšā laukā;
   - fāzes nosaukums: uz lapas "SKICES PROJEKTS" (EN "SKETCH DESIGN"), iekšēji fāze saucas klienta projekts;
   - modelis: nosaukums (piem. Freya) lieliem burtiem, zem tā "MM <m²>" (piem. MM 30). Pilnu id (MM-30-01) uz lapas neraksta;
   - galvenie rādītāji (apbūves laukums, iekštelpu platība, gabarīti, kores augstums, jumta slīpums);
   - objekta adrese;
   - PIEZĪMES: konkrētā projekta piezīmes no izvēlēm (pamati un cokols, griestu augstums, papildu info);
   - revīziju tabula (nr., datums, apraksts);
   - mērogs, formāts un lapa;
   - apakšā REV. nr. un datums.
   Revīzijas nr. ir obligāts. Adresi var izlaist ar `--bez-adreses`.
   - Galvenajos rādītājos standartā ir arī griestu augstums 2,20 m. Citus rādītājus var pievienot ar `--raditajs`.
   - Logo: `modelu-bots\LOGO.png` (vai `MM System\LOGO.png`), rakstlaukumā tiek likts īstais MM logo (brūnganais tonis). Ja faila nav, tiek likts teksta zīmols.
2. **Pirmie modeļi ir ar mansardu.** Vienā A3 stāvus lapā ir 1. stāva plāns, mansarda plāns, 4 fasādes un apakšā MATERIĀLI UN TOŅI (krāsu paraugi). Piezīmju bloka klienta projektā nav.
3. **Asis tuvu izmēru ķēdēm.** Ass burbulis ir tieši aiz ārējās ķēdes (1. stāvā axOff 1650, mansardā 900).
4. **Bez elementu markām.** Lapā nav ĀD-1, L-1, D-, S1/S2 marku, jo tās ir tikai ražošanas projektā.
5. **Eksplikācija ir blakus katram plānam**, labajā pusē: 1. stāva tabula blakus 1. stāvam, mansarda tabula blakus mansardam. Tabulām ir tumša galvene, numurētas rindas, kopsumma, un 1. stāvā arī apbūves laukums.
6. **Neviena mēbele loga priekšā.**
   - Loga zona ir 700 mm dziļa telpā, un tai ir 50 mm atstarpe uz sāniem.
   - Mēbele ne aizsedz logu, ne pieskaras tā malām.
   - Izņēmumi:
     - virs poda drīkst būt logs;
     - dīvāns drīkst būt ar sānu pret logu (atzveltne pie perpendikulāras sienas);
     - gulta var būt zem augsta loga (palodze ≥ 1200 mm), lietotājs to vēl precizēs.
   - generate.py `window_rule` šo noteikumu pārbauda un aptur būvi, ja tas tiek pārkāpts.
7. **Iekšējie telpu izmēri**, platums un garums, ir iekšējās izmēru ķēdēs (`innerDims`). Sienu (pīrāgu) biezumus klienta lapā nerāda.
8. **WC izkārtojums.**
   - Uz poda vienmēr var normāli apsēsties: poda centrs ir ≥ 400 mm no sānu sienas, un priekšā ir brīvs 800 × 600 mm laukums (generate.py `wc_rule` to pārbauda).
   - Ja netiek klāt veļasmašīnai, pārbīda izlietni vai veļasmašīnu, nevis podu.
   - WC logs ir virs poda. Izlietne var būt pie ārsienas blakus podam.
9. **Mēbeles netraucē durvīm.** Starp mēbeli un durvju vērtnes zonu paliek vismaz 50 mm.
   - Dīvāns ir vismaz 700 mm no virtuves fronta. Ja tā dīvāns neietilpst (īsāks par 1200 mm), dīvānu neliek.
10. Telpu nosaukumu zīmes neuzbrauc mēbelēm, durvju vērtnēm un izmēru ķēdēm.
11. **Fasādes:**
   - Notekcaurules ir zīmētas ar diametru (Ø100, ar kontūru).
   - Izplūde ir pret skatītāju: taisns gals, caurules neieiet zemē, galā nav līkuma uz sāniem.
   - Ja jumtam nav pārkares, zem dzegas nav ēnas.
   - Notekcaurules ir taisnas, bez lauzumiem (gala fasādē arī), un beidzas 50 mm virs zemes.
   - Garām mājām (garā fasāde netiek līdz gala fasādei) zemes līnija ir īsāka (600 mm), lai neuzbrauc gala fasādes atzīmēm.
   - Stabveida pamatiem fasādēs ir metāla cokols (noklusējums RAL 9005, var RAL 7016) no grīdas līdz 40 mm virs zemes; pamatu plātnei ir betona cokols.
   - Fasādes materiāls ir "vertikāls apdares dēlis".
   - Logu, durvju un apmaļu ārējais tonis seko fasādes tonim automātiski:
     - norvēģu sarkans: balti (RAL 9016), un mājas stūros ir balta stūru apdare 90 mm (norvēģu standarts);
     - grafīta pelēks un dabīgs koks: RAL 7016.
   - Grīdas pīrāgs (G1, ~276 mm) ir redzams: ±0,000 = tīrā grīda, logi un durvis sākas no ±0,000, apdare iet līdz grīdas apakšai. Stabveida pamatiem zeme ir −0,600 (`floor.posts_ground`).
   - Visās fasādēs ir logu palodzes un augšas atzīmes (piem. +0,900, +2,100); gala fasādēs arī ±0,000.
   - Pie materiāliem ir piezīme "Fasāžu krāsu toņus saskaņot ar pasūtītāju".
12. EN versija visur ir angliski, arī rakstlaukumā un tabulās.

12a. **Lietotāja noteikumi 05.11.2026** (pilns saraksts `zinasanas_mebeles_logi.md`, sadaļa "Lietotāja komentāri 05.11.2026"): ieeja vienmēr no dienvidiem; maza guļamistaba bez skapja; skapis nedrīkst slēgt caurgājienu; virtuve šaurā mājā gar iekšējo galasienu; logu veidi (>1100 līdz zemei fixed, >1000 divdaļīgs, loft 1000x550 hopper, piecstūra logs virs lielā); WC pods zem loga vai pie sānsienas, izlietne >= 600 no dušas.

## 3b. VIZUALIZĀCIJAS (Gemini)

- `generate.py` pats uztaisa `viz/ref_<tonis>.png`: 3D stūra skats no model.json (precīza kontūra, logi, durvis, jumts, tonis).
- `generate.py --viz` (vai `python3 viz.py <id>`): Gemini uztaisa fotoreālu `viz/V1_peleks.png`.
  - Gaisma: mākoņaina dienas gaisma.
  - Apkārtne: modeļa atmosfēra no `mm-config.json` → `atmosferas` (6 Norvēģijas ainavas, var pielikt jaunas). Katram modelim sava, visiem 3 toņiem tā pati. Kamera un stils ir viena konstante (`CAMERA` failā viz.py).
  - Bez terases, mēbelēm un cilvēkiem.
- Uzreiz pēc tam no tā paša foto tiek uztaisīti `V1_sarkans.png` un `V1_koks.png`. Mainās tikai mājas tonis, apkārtne un kadrs paliek tie paši.
- Atslēga: mākoņa vides mainīgais `GEMINI_API_KEY` (vai `MM System\.env`). Modelis: noklusējumā `gemini-3-pro-image`, maina ar `GEMINI_IMAGE_MODEL`. Atslēgu nekad neraksta čatā, failos vai ziņās.
- Ja Google atbild 429 "free tier ... limit: 0", Google AI Studio projektam nav ieslēgts maksājums. Pasaki to lietotājam un neej cauri visiem modeļiem.
- Prompti tiek saglabāti blakus bildei (`*_prompt.txt`). Jaunu atmosfēru pievieno `mm-config.json` → `atmosferas` ar `lv` nosaukumu un `en` aprakstu (Setting + Light).
- **Logi un durvis ir iedziļināti sienā** (~150 mm), nevis vienā plaknē ar apšuvumu. ref.py to zīmē 3D: rāmis ailas dziļumā, redzamie ailas sāni un augša fasādes tonī (ēnoti), palodze izvirzīta no sienas. Aila (ailas sāni un augša) ir tajā pašā tonī un materiālā kā fasāde. Katram logam apakšā ir izvirzīta metāla palodze loga rāmja tonī.
- **Jumta vējmala (slīpā fascia gala fasādē):** baltus koka vējmalas dēļus liek TIKAI sarkanajam tonim (kopā ar baltajiem logiem un stūru apdari; `mm-config.json` → `toni.sarkans.vejmala = "balta"`). Pelēkajam un koka (dzeltenajam) tonim ir tikai tieva metāla vējmalas skārda RAL 7016.
- **Ārdurvis** (references bildē, fasādēs un Gemini promptā vienādi): plakana vērtne rāmja tonī, viena šaura vertikāla stikla josla (160 mm, 150–1950 mm augstumā) eņģu pusē un garš vertikāls nerūsējošā tērauda rokturis (~1100 mm, 500–1600 mm augstumā) atvēršanas pusē. ref.py `opening(door=True)` to zīmē, viz.py `materials()` to prasa.
- Ja Gemini maina logus vai durvis, ģenerē vēlreiz. Prompts to aizliedz ("Do not add, remove, merge, enlarge or divide any opening").

## 4. RAŽOŠANAS PROJEKTS (vēlāk)

Tas pats modelis, bet ar SBE noformējumu:
- elementu markas (ĀD-1, L-1, S1);
- logu un durvju specifikācija;
- sienu pīrāgi un griezumi.
Noteikumus pierakstīs, kad lietotājs sāks šo fāzi.

## 4b. ZINĀŠANU BIBLIOTĒKA (tikai zināšanas, noformējums paliek MM)

`planlib.py` lasa konkurentu plānojumus (`competitor-analize\<konkurents>\planojumi.json`, attēli blakus mapē `planojumi\`) un izrēķina normas: telpu platību diapazoni, moduļu platumi, garumi.
- Bibliotēka NEMAINA rasējumu izskatu, rakstlaukumu, krāsas vai noformējumu. No konkurentiem ņem tikai proporcijas un loģiku, nekad stilu.
- `generate.py` pirms un pēc būves izdrukā `BRĪDINĀJUMS: ...`, ja gabarīti vai telpu platības krasi atšķiras no bibliotēkas. Tie ir brīdinājumi, ne aizliegumi. Pasaki tos lietotājam un jautā, vai turpināt.
- `python planlib.py <garums> <platums> <augstums>` parāda normas un tuvāko references modeli.
- **KLASES NEDRĪKST JAUKT.** Bibliotēka ir sadalīta pēc klases (`lidz60` = apbūve līdz 60 m², `virs60` = lielākas mājas) un tipa (`modulu` = rūpnīcā gatavas moduļu mājas, `karkass` = uz vietas būvēta koka karkasa māja). Projektējot māju līdz 60 m², izmanto TIKAI klase `lidz60` + tips `modulu` (tāds ir `norms()` un `check_*` noklusējums). Lielo māju (`virs60`) un karkasa māju plānus lieto tikai tad, ja lietotājs prasa tādu pašu klasi/tipu, un nekad neliec to platības, telpu izmērus vai izkārtojumus mazās mājas plānā. Lielo māju principi (garāki koridori, vairākas guļamistabas, L/T/II formas) ir zināšanām par lielāku māju projektēšanu, nevis par to, kā palielināt mazu māju.
- `python planlib.py` parāda normas pa klasēm; `python planlib.py virs60` tikai lielajām.
- Jaunu konkurentu pievieno kā `competitor-analize\<nosaukums>\planojumi.json` (tāda pati struktūra) un normas atjaunojas pašas.
- Ja vajag saprast, kā konkurents risinājis plānu, apskati `planojumi\*.jpg` (vizuāli).
- **Mēbeļu un logu izvietošanas principi:** `zinasanas_mebeles_logi.md`. Pirms jauna izkārtojuma vai mēbeļu/logu loģikas maiņas izlasi to. Pie katra noteikuma ir avots: [MM] saistoši, [MyCabin] novērots plānos, [prakse] vispārēja prakse, jāapstiprina.

**Istabu plānotājs** (`planner.py`, pieslēgts `generate.py`): ievadi tikai mājas izmērus, vai būs mansards un vai vajag variantus. `python generate.py 9340 6420 4800 --mansards ja --varianti 4`. Plānotājs uztaisa līdz N atšķirīgiem plānojumiem (II / L / T; ar mansardu tikai II, ar mansarda stāvu un tā logiem). Katrs iziet `rules_check.py` ar 0 kļūdām un 0 brīdinājumiem, un katram tiek uztaisīta tā pati MM rasējumu lapa (noformējums nemainās). Izvade: `MĀJAS/<grupa>/MM-xx-nn-V01/model.json` + `rasejumi/MM-xx-nn-V01_LV.html` (+ viz references) ..., kopsavilkums `MM-xx-nn/varianti.html` (arī noraidītie). `--viz` strādā katram variantam. Guļamistabu un vannasistabu skaitu nosaka laukums, bet tos var norādīt ar `--gulamistabas 2 --vannas 1`. Formas izvēlas ar `--forma II,L,T`. Bez `--varianti` strādā vecais etalons (MM 30 tips). Tad `--mansards ne` noņem mansarda stāvu un tā logus. Plānotāju var palaist arī atsevišķi: `python planner.py L B H [guļ] [vann] --forma II,L,T --loft --n 4`. Noteikumi: `zinasanas_mebeles_logi.md` 10. nodaļa [MM]; zināšanas par formām un loft ir 6.–9. nodaļā. Klases (lidz60 / virs60) nejaukt. Ierobežojumi: logi tikai uz bbox fasādēm, virs60 L/T ar 2 vannām nav, L/T fasādes un jumtu zīmē `cad.js` (tur var būt R8), L/T formām `ref.py` 3D references un vizualizācijas netaisa.

## 5. Ko nemainīt

- `SBE-ARHITEKTS` mapi nemaina. Bots izmanto savu kopiju `sablons/sbe`, un MM labojumi tiek ielikti būvējot (build_model.py).
- Google API atslēgu neglabā bota failos: tikai mākoņa vides mainīgajā `GEMINI_API_KEY` vai `MM System\.env`.
