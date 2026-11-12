# Ceļvedis: MM Home pārbūve

Statuss 2026-11-12: daļēji īstenots, skat. tabulu beigās. Pamatprincips: **viena patiesība ir `model.json`**; 2D, 3D, SketchUp un ražošanas lapas tikai lasa to. Vilkšana un rīki raksta atpakaļ modelī un pārbūvē skatu (`rebuild()`), nekad nelabo 3D tīklu tieši.

## Esošais stāvoklis (pārbaudīts kodā)
- `viz3d.js` jau ir Three.js skats: kamera griežas (azimuts, brīvais režīms), tālummaiņa ar ritenīti, `Raycaster` klikšķis uz fasādes (terases piesaiste), terase ar dēļu tekstūru.
- 3D ģeometriju dod `skpRb(m, geo)` (`lapa.html`), tā pati funkcija būvē SketchUp .rb. Elementiem (`geo`: `s` sienas/plaknes, `g` logi, `d` durvis) vēl **nav ID**, tāpēc 3D klikšķi nevar atpazīt konkrētu logu.
- Pamatu plāns jau ir `mm-pamati.js` un `projekts.pamatu_plans` (stabi, režģis, kontūras `parts`, komunikācijas `kom`).

## 0. fāze: kopīgs ģeometrijas starpslānis
`geo` elementiem pievieno `id` (`w:3`, `d:1`, `p:2`...) saskaņā ar redaktora izvēles ID (`x:i`, `p:` utt.). Tad 3D klikšķis = 2D izvēle. Pārbaude: 1 logs ar ID abos skatos.

## 1. fāze: interaktīvais 3D (Prioritāte 1)
1. 3D klikšķis izvēlas logu/durvis/stabu, izceļ kontūru, sinhronizē ar plāna izvēli.
2. Logu vilkšana pa sienas plakni + platuma/augstuma rokturi, raksta `windows[i]`.
3. Stabu pārvietošana (`pamatu_plans.mov`).
4. Fasādes tekstūra: `CanvasTexture` no tās pašas apdares definīcijas (dēļu virziens, krāsa), nevis zīmēta atsevišķi.
5. Eyedropper (Alt+klikšķis) un krāsojamā spainis, kas ņem tekstūru, ne tikai RAL.

## 2. fāze: trīs dokumentācijas režīmi (Prioritāte 2)
Datu modelis: `projekts.rezims = "skice" | "noformejums" | "razosana"`; `projekts.razosana = { lapas: ["skice","pamati","logu_plans","logu_specif","durvju_specif"] }`.
- Skiču profils: esošā `mmSheets()` skice.
- Arhitektūras noformējums: pilnā A3 lapa (esošais `build_model.py`).
- Ražošanas faili: izvēles dialogs lapām, pakešģenerēšana (PDF/SVG pa lapām).
Jāveido: logu plāns, logu specifikācija, ārdurvju specifikācija (tabulas no `windows`/`doors`).

## 3. fāze: UI pārkārtošana
- Kreisā ikonu rīkjosla (zīmēšana un labošana), labais panelis tikai: Lapa, Ēka/Jumts/Sienas, Rīku opcijas.
- Viens vienots "štampa" modālis visiem titullapas laukiem.

## 4. fāze: rediģēšana skatlogā
- "Edit plan" režīms (izolēts), izejot pārrēķina blokus (eksplikācija, fasādes, leģenda) pret jauno kontūru.
- Pamatu plāna skatlogs ar automātisku mērogu uz lapas.

## 5. fāze: jumti
Jauns `jumts.kontura`, `jumts.malas[i].ov` (pārkare uz malu, 0 = līdzena), `jumts.spares`, terases jumts `terase.jumts = {tips, biezums, materials, spares_only}`. L-formas krustošanās: plakņu krustpunkti (ieleju līnijas) pa plakņu vienādojumiem; **vissarežģītākā daļa**, pirms tās vajag testu komplektu ar 5 kontūrām.

## 6. fāze: dimensionēšana un pamatu/MEP ražošanas uzlabojumi
Piesaistes (asis, C24 mala, apdares mala), mēru ķēžu vilkšana, polilīnijas kontūra, pāļu dalīšana `/N`, sarkana pārtraukta apdares nobīde (no sienu konstrukcijas), spoku pārklājums ar plānu, ūdens ievads + kolektors, tualete + Ø110 kanalizācija (8 cm no starpsienas), sinhronizācija uz pamatu plānu.

## Riski
Jumtu krustošanās (5. fāze); vienota izvēle 2D SVG un 3D (0. fāze); `lapa.html` jau 2900 rindu, jauno kodu likt atsevišķos failos (`bot/sablons/redaktors/`), lai neaugtu monolīts.


## Īstenošanas statuss (2026-11-12)
| Darbs | Statuss |
|---|---|
| 0. fāze: logu/durvju ID 3D, klikšķis izceļ | gatavs |
| Loga vilkšana pa sienu 3D (raksta `model.json`) | gatavs |
| Labā paneļa kartītes kompaktas, spaiņa kļūda | gatavs |
| Mobilais izkārtojums (apakšējā rīku josla, panelis zem) | gatavs (pamata) |
| Ražošanas pakete (izvēle, logu plāns, logu/ārdurvju specifikācija) | gatavs (pamata, skice/pamati caur esošo lapu) |
| Pamatu plāns: sarkana apdares līnija, Ø110, kolektors, spoks (3 režīmi) | gatavs |
| Loga platums/augstums 3D ar taustiņiem (← → + - PgUp PgDn) gatavs; peles rokturi, stabu vilkšana 3D, tekstūras 3D, eyedropper | nav |
| Trīs dokumentācijas režīmi kā atsevišķi profili | nav |
| Vienots štampa logs, paneļa sadalījums Lapa/Ēka/Rīki | daļēji (Rakstlaukums jau bija) |
| Pamatu polilīnija, auto/manuāli stabi ar /N poligonam, diagonālie mēri | nav (/N taisnstūrim jau bija) |
| Jumta pārkare pa malām (`projekts.ov_side`, 0 = fasāde līdz jumtam): fasādes, 3D, redaktora lauki | gatavs (divslīpju jumts; četrslīpju tikai tuvināti) |
| Jumti: L krustošanās, terases jumts un spāres | nav |
| Piebūve (taisnstūra spārns dienvidu/austrumu pusē, Māja → Izmēri) | gatavs (pamata; ārsienu vilkšana taisnstūrim jau bija) |
| Ieliekumi, piebūve ziemeļos/rietumos, brīva kontūra, izolēts viewport režīms | nav |
| Mēru pielipšana pret asīm/C24/apdari, mēru ķēžu vilkšana | nav |
| Elektrības plāns, mēbeļu bibliotēka no egmalt/house-planner (MIT) | nav |
