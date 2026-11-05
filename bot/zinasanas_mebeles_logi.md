# Zināšanas: mēbeļu un logu izvietošanas principi moduļu mājās

Tikai zināšanas. Noformējums (līniju svars, krāsas, rakstlaukums) paliek MM Homes. Šeit nav nekā par izskatu.

Avoti un drošums:
- **[MyCabin]** novērots 9 MyCabin plānojumos (`competitor-analize/mycabin/planojumi/`). Pārbaudīts ar acīm.
- **[MM]** MM Homes noteikumi no `SKILL.md` 3. sadaļas. Tie ir saistoši, un `generate.py` tos pārbauda.
- **[prakse]** vispārēja projektēšanas prakse. Nav pārbaudīta pret LBN vai konkrētu projektu, jāapstiprina ar arhitektu.
Konfliktā uzvar [MM], tad [MyCabin], tad [prakse].

## 1. Telpu secība un zonēšana

1. **Mitrās telpas grupē kopā** [MyCabin]. Virtuve, WC/vanna un pirts ir blakus, ar vienu kopēju inženiertīklu sienu. Milla 40: virtuve un WC ir mājas vidū. Sauna 30: virtuve, pirts un WC ir pie vienas starpsienas. Living 100: abas vannasistabas ir blakus un abas pie ziemeļu sienas.
2. **Dzīvojamā istaba ar virtuvi ir lielākā telpa** un atrodas mājas galā, ar logiem gala fasādē [MyCabin]. Tā aizņem 27 % (Living 100) līdz 55 % (Milla 25) no dzīvojamās platības, jo mazāka māja, jo lielāka daļa.
3. **Guļamistaba ir pretējā galā** no dzīvojamās, pēc iespējas tālāk no ieejas un virtuves [MyCabin]. Milla 40: dzīvojamā un guļamistaba ir pretējos galos, starp tām mitrā josla.
4. **Ieeja no garās fasādes** [MyCabin]. Mājas ar vairākām telpām: ieeja ved halle (4.9 līdz 8.9 m²), no kuras iet uz visām telpām. Ļoti mazajās mājās (Milla 25) ieeja ved tieši dzīvojamā telpā.
5. **Divmoduļu mājām (7.8 m plata) koridors vai halle ir mājas vidū**, un telpas sadalās abās pusēs [MyCabin]. Vienmoduļu mājām (3.6 m) koridora nav: telpas ir viena otrai pakaļ pa garumu.
6. **Mansards** virs mitrās/pakalpojumu joslas un halles (zemā zona), bet virs dzīvojamās atstāj atvērtu telpu līdz jumtam [MyCabin Milla, MM].

## 2. Telpu platumi un izmēri (no bibliotēkas)

Aprēķina `python planlib.py`. Orientieri [MyCabin]:

| Telpa | Platība m² | Piezīme |
|---|---|---|
| Guļamistaba | 9 – 12.9 | divvietīga gulta un skapis; 11.8 m² (3.48 × 3.38 m) ir biežākā |
| Vannasistaba | 2.6 – 5.7 | duša + pods + izlietne sākas no ~3 m² |
| Dzīvojamā ar virtuvi | 15 – 27.9 | 15 m² mazajām mājām; 22 – 28 m² mājām virs 65 m² |
| Halle | 3 – 8.9 | |
| Iekšējais platums, vienmoduļa māja | ~3.09 m | ārējais 3.57 m |

## 3. Mēbeļu izvietošana

### Virtuve
- **Virtuves rinda ir pie iekšējās starpsienas**, kas robežojas ar mitro telpu (kopējie tīkli) [MyCabin Milla 25/40, Sauna 30]. Tā neaizņem loga sienu.
- **Divmoduļu mājām virtuve ir L veida vai ar pusostu pret dzīvojamo zonu**, un ēdamgalds atrodas starp virtuvi un dīvānu [MyCabin Living 80].
- **Izlietne zem loga vai pie ārsienas** ar logu virs darba virsmas ir pieņemama (Living 100, kur logs ir virs virtuves rindas) [MyCabin].
- Dīvāns ≥ 700 mm no virtuves fronta; ja neietilpst, dīvānu neliek [MM].

### Dzīvojamā zona
- **Dīvāns pret garo sienu vai ar atzveltni pret virtuvi**, televizora siena pretī [MyCabin Living 80/100]. Stūra dīvāns ir mazajās telpās.
- **Mēbele nedrīkst būt loga priekšā** (loga platums + 50 mm katrā pusē, 700 mm dziļumā); dīvāns ar sānu pret logu drīkst [MM].
- Apaļš galds (Ø ~1.2 m) tuvu virtuvei, ap to ~800 mm brīvas vietas [MyCabin Living 80, prakse].

### Guļamistaba
- **Gulta ar galvgali pie sienas**, ne logā [MyCabin Living 80: galvgalis pie ziemeļu sienas, logs sānos].
- **Skapis gar sienu pie durvīm**, ne pie loga [MyCabin].
- **Mazā guļamistabā (9 m²)** gulta pie gala sienas, skapis pie durvīm, visa gultas viena garā mala ir pieejama [MyCabin Milla 40].
- **Otrā istaba kā darbistaba:** rakstāmgalds pie loga, gulta vai dīvāns pretējā pusē (Living 80 / Living 100) [MyCabin].
- Gulta zem augsta loga (palodze ≥ 1200 mm) ir pieļaujama [MM].
- Brīva josla ap gultu ≥ 600 mm vismaz vienā pusē, labāk abās [prakse].

### Vannasistaba
- **Duša stūrī pie ārsienas, pods un izlietne gar vienu sienu** [MyCabin Living 80/100, Milla 25].
- Pods: centrs ≥ 400 mm no sānu sienas, priekšā brīvs 800 × 600 mm [MM].
- Veļasmašīnu liek vannasistabā vai halles skapī. Ja netiek klāt, bīda izlietni vai veļasmašīnu, nevis podu [MM].
- **Durvis atveras uz iekšu mazajās vannasistabās** vai uz halli, neaizsedzot podu [MyCabin].

### Garderobe un uzglabāšana
- **Iebūvētie skapji halle**: gar sienu pie ieejas [MyCabin Living 80/100]. Papildus iebūvētais skapis katrā guļamistabā pie durvīm.

### Durvis
- Starp mēbeli un durvju vērtnes zonu paliek ≥ 50 mm [MM].
- Iekšdurvis nedrīkst atvērties pret gultu vai podu.

## 4. Logu izvietošana

### Pamatprincipi
1. **Gala fasādes (īsās) ir lielais stiklojums** dzīvojamai telpai un guļamistabai [MyCabin Milla 25/40, Living 80: pilnas augstuma stiklojums galā].
2. **Garajā fasādē logi ir mazāki un atsevišķi**: pie ieejas, virtuves un guļamistabām [MyCabin].
3. **Katrai dzīvojamai telpai vismaz viens ārsienas logs.** Vannasistabai mazs logs ārsienā (Living 80: ap 0.5 līdz 0.9 m plats), WC logs virs poda [MyCabin, MM].
4. **Virtuvē logs virs darba virsmas** vai blakus tai [MyCabin Living 100].
5. **Guļamistabā logs sānu sienā blakus gultai**, nevis galvgalī [MyCabin Living 80].
6. **Dzīvojamai telpai logi vairākās pusēs** (gals + garā siena) dod cauršļūdi un vairāk gaismas [MyCabin].
7. **Mansarda logs gala fasādē**, parasti nelielas augstuma atzīmes (palodze ~2.3 līdz 2.7 m) [MyCabin Sauna 30 loft, MM].
8. **Ieejas durvis blakus logam** garajā fasādē [MyCabin Milla 25/40].

### Izmēri un atzīmes [MM, MyCabin]
- Standarta palodze 900 mm, augša 2100 mm; WC logs 600 mm plats; guļamistabas logs 900 mm.
- Gala fasādes stiklojums var sākties no ±0,000 (durvis uz terasi) [MM].
- Logu un durvju tonis seko fasādes tonim [MM].

### Dienasgaisma [prakse]
- Logu laukums ~1/8 līdz 1/6 no telpas grīdas laukuma. Pārbaudīt ar LBN, kas prasa atsevišķi.
- Izvairīties no loga uz ziemeļiem guļamistabai, ja iespējams (siltuma zudumi, maz saules), bet dzīvojamai gala stiklojums uz dienvidiem/rietumiem.

## 5. Ko NEDRĪKST darīt (biežākās kļūdas)

1. Neliek mēbeli loga priekšā [MM].
2. Neliek podu bez 800 × 600 mm brīvas vietas priekšā [MM].
3. Neliek guļamistabu blakus virtuves vai ieejas troksnim, ja var citādi [prakse].
4. Neizkaisa mitrās telpas pa visu māju: tās grupē, lai samazinātu inženiertīklus [MyCabin].
5. Neveido guļamistabu bez ārsienas loga [prakse; vai LBN to prasa, nav pārbaudīts].
6. Neliek durvju vērtni uz mēbeli (≥ 50 mm atstarpe) [MM].
7. Neveido koridoru vienmoduļa mājā, kur tas atņem pusi no platuma (iekšējais platums tikai 3.09 m) [MyCabin].
8. Neizdomā jaunu izkārtojumu, ja bibliotēkā ir tuvs references modelis: vispirms palaid `python planlib.py <garums> <platums> <augstums>`, kas parāda tuvāko references modeli, un apskati tā plāna attēlu.

---
# PAPILDINĀJUMS (2026-11-05): Ecospace, Arka-B, Timbero analīze

Avoti: `competitor-analize/{ecospace,arka-b,timbero}/planojumi.json` (~110 plānu, visi izlasīti vizuāli; izņēmums Ecospace Barn 60, kam plāna nav lapā). Atzīmes: [Eco] Ecospace, [Arka] Arka-B, [Timb] Timbero. KLASES NEDRĪKST JAUKT: līdz 60 m² māju projektē tikai pēc lidz60 datiem; virs60 ir tikai atsevišķa zināšanu daļa.

## 6. Plānu tipi (topoloģijas), ko konkurenti izmanto

### Līdz 60 m² apbūves
1. **Lineārs (vienmoduļa, 3.4–4.5 m plats)** [Eco Furu 25/45, Cube 35, Uno 35, MyCabin Milla]: telpas rindā pa garumu: guļamistaba | WC/vannasistaba | halle | dzīvojamā. Viena guļamistaba. Divām guļamistabām (Furu 45 B, Duo 30 B) otru guļamistabu liek pretējā galā vai blakus pirmajai.
2. **II-taisnstūris 6.0–6.4 × 9.3–9.6 m** [Arka Īve/Egle/Priede 60, Timb Austra 59]: dzīvojamā+virtuve vienā īsajā galā (~18–33 m²), guļamistaba(s) un sanitārais bloks otrā galā. Ieeja īsajā vai garajā sienā uz lielu priekšnamu/dzīvojamo. Šeit ir 1 līdz 2 guļamistabas, 1 vannasistaba.
3. **Kompakts kvadrāts 8.5 × 5.8 m** [Timb Birzs 44]: dzīvojamā 25, guļamistaba 11, vannasistaba 4.3, priekšnams 3.8, terase 5. Ieeja caur terasi.
4. **L / T / II formu varianti** [Eco Duo 60 u.c.]: tā pati platība, cits istabu skaits: L un T ar guļamistabām atsevišķā spārnā, T ar divām vannasistabām; II taisnstūris ar visu vienā korpusā.
5. **Mansards/loft**: skat. 7. nodaļu.

### Virs 60 m²
1. **Garš taisnstūris ar gaiteni pa vidu** [Arka Kļava 100–150, Timb Rasa 100]: dzīvojamā+virtuve vienā galā (30–46 m²), pārējā daļa sadalīta ar gaiteni (7–8 m²): guļamistabas abās pusēs, vannasistabas blakus.
2. **Divstāvu** [Timb Priede 107, Kapa 146]: 1. stāvā dzīvojamā+virtuve+kāpnes+WC+tehniskā, 2. stāvā 3 guļamistabas ap gaiteni 7–10 m², 2 vannasistabas.
3. **L forma** [Arka Liepa 165/190, Magnolija 130]: dzīvojamā spārns ar terasi, guļamistabu spārns ar garu gaiteni 10–13 m², vecāku istaba galā ar garderobi un savu sanmezglu.
4. **Ļoti garš (19–28 m)** [Timb Strazdi, Taka]: dzīvojamā vienā galā, vecāku istaba otrā galā, bērnu istabas centrā, garāža/noliktava piebūvēta.

## 7. Mansards un loft (ko rāda plāni)

1. **Loft ir atvērta guļtelpa virs priekšnama/sanitārā bloka**, nevis virs dzīvojamās. Virs dzīvojamās atstāj dubultaugstumu [Eco Furu, Uno, Barn; Timb Ziemeļi 31, Austra 58; Arka Priede/Egle 60].
2. **Loft platība:** 4.9 m² (Ziemeļi, tikai gulta) līdz 11.4 m² (Austra, guļamistaba ar rakstāmgaldu) mājām ap 30–60 m². Arka 60 m² mājām mansards 26–30 m² (ar vannasistabu 2.6–5.3 m² vai 2 guļamistabām 9.6 + 9.6).
3. **Kāpnes** iet gar īso vai garo sienu (~0.9 m platas, 8–9 pakāpieni 2 m garumā) blakus sanitārajam blokam; zem kāpnēm var būt pieliekamais [Timb Ziemeļi, Arka Priede].
4. **Gulta loftā** liek zem augstākās jumta daļas, galvgali pie sienas ar logu; plānā ap gultu paliek ≥ 0.6 m no malas.
5. **Mansarda logi** gala fasādē (augsti, 1.2–1.6 m platumā; stikloti durvju-logi uz Francijas balkonu [Arka Priede V2, V5]) un lukti jumta nogāzē.
6. **Mansarda sanmezgls** ir tikai pie vietas, kur jumta augstums ≥ 2 m (WC 2.6 m², vanna 5.3 m²).
7. **Ja loftā ir guļamistaba(s), apakšā ir 1 guļamistaba mazāk**, un apakšā ir jābūt WC (nevar rēķināties ar mansarda WC) [Arka Priede V3/V5, Timb Austra].

## 8. Telpu izmēri pa klasēm (no `planlib.py`, atjaunots)

| Telpa | lidz60 moduļu | lidz60 karkass | virs60 |
|---|---|---|---|
| Dzīvojamā+virtuve | 11.5–22.6 m² | 17.98–32.8 | 23.4–49.6 |
| Guļamistaba | 5.1–10.9 | 6.3–10.95 | 7.2–19.0 |
| Vannasistaba | 2.4–5.8 | 4.3–7.4 | 3.4–7.2 |
| Priekšnams/halle | 1.6–6.1 | 3.8–11.1 | 4.3–8.5 |

Papildu normas [Arka/Timb/Eco]:
- Bērnu istaba 7.2–8.5 m² pieņemama (gulta + rakstāmgalds + skapis), divvietīga guļamistaba ≥ 9.5 m², vecāku 11–15 m² (līdz 19 lielajās mājās).
- Ja guļamistaba < 9 m², gultu liek pie sienas ar logu un skapi ārpus durvju vērtnes.
- Vannasistaba 4.2–5.3 m² ar dušu vai vannu; 3.3 m² ir minimums ar dušu+pods+izlietne+veļasmašīna [Timb Ziemeļi].
- Atsevišķs WC 1.7–2.7 m² (tikai pods + izlietne).
- Tehniskā telpa 3–5 m² (boileris, veļasmašīna, ventilācija), gandrīz vienmēr pie ieejas vai sanmezgla.
- Gaitenis 5.6–8.2 m² 100 m² mājām, 10–13 m² 150–190 m² mājām; platums ≥ 1.1–1.3 m.
- Garderobe pie guļamistabas 2–4 m² vai iebūvēts skapis 0.6 m dziļš visā istabas sienā.

## 9. Citi atklājumi, kas jāņem vērā

1. **Mazā mājā (līdz 60 m²) viena vannasistaba**; otra parādās no ~100 m² (vecāku istaba) [visi konkurenti].
2. **Divu guļamistabu mājām** divas vienāda lieluma bērnu istabas blakus ar kopīgu skapi vai sienu, durvis uz kopējo gaiteni [Arka Īve V5, Kļava 120 V1].
3. **Ieeja** ir vai nu tieši dzīvojamā (mazās mājās ≤ 60 m²), vai uz priekšnamu 4–8 m² (virs 60 m²). Lielajās mājās ārdurvīm priekšā lievenis 3–4 m² (Arka) vai terase.
4. **Virtuves rindas** gar ārsienu pie loga vai gar starpsienu ar mitrajām telpām; sala 2 m×0.9 m parādās no 40 m² dzīvojamās [Arka Liepa, Timb Strazdi].
5. **Terase** 6–10 m² mazajām mājām (līdz 60 m²), 24–34 m² lielajām; terases durvis atveras no dzīvojamās.
6. **Pirts** (Eco Sauna 30, Timb Taka ar pirti) atsevišķs moduļa gals blakus vannasistabai, nekad blakus guļamistabai.
7. **Lielajām mājām garāža/nojume** piebūvēta galā vai blakus, nevis iekšā mājas korpusā.

---

# 10. Plānotāja noteikumi [MM] (`planner.py`, 2026-11-04)

Šos noteikumus plānotājs ievēro, ģenerējot variantus. Katrs izdotais variants iziet `rules_check.py` ar 0 kļūdām un 0 brīdinājumiem, citādi tiek noraidīts.

### Klases [MM]
- Klasi nosaka `planlib.klase_of` (robeža 62 m² apbūves). **lidz60** un **virs60** telpu izmēru tabulas ir atsevišķas, un viena plāna ietvaros tās nekad nejauc. Normas ņem no `planlib.norms(klase, 'modulu')`.
- Mērķa platības m² (mērķis / min / max, mazākā mala mm):

| Telpa | lidz60 | virs60 |
|---|---|---|
| Guļamistaba (galvenā) | 9.5 / 7.0 / 12.5, 2400 | 13.0 / 10.0 / 17.0, 2800 |
| Guļamistaba (mazā) | 7.8 / 6.3 / 10.5, 2400 | 10.5 / 8.0 / 13.0, 2700 |
| WC / vannasistaba | 3.8 / 2.8 / 5.8, 1500 | 5.2 / 4.0 / 7.2, 1700 |
| Priekšnams | 3.0 / 1.6 / 6.1, 1100 | 5.5 / 3.5 / 9.0, 1300 |
| Dzīvojamā ar virtuvi | 18 / 9 / 30, 2900 | 30 / 21 / 50, 3600 |
| Gaitenis (platums) | 1100 | 1200 |

### Formas un topoloģijas [MM]
- **II** (taisnstūris), ja dziļums ir mazāks par 4400: lineārs plāns, istabas rindā, un guļamistabas ir galos vai abos galos ap dzīvojamo.
- **II**, ja dziļums ir 4400–6600: divas rindas. Ziemeļu rindā ir guļamistabas un WC, dienvidu rindā priekšnams un dzīvojamā. Lielākam dziļumam ir varianti ar gaiteni pa vidu (ziemeļi/dienvidi).
- **L**: dzīvojamā atrodas stūrī, kur satiekas abi spārni. Privātais spārns (guļamistabas, WC) ir otrā kājā. Kājas garumu plānotājs pārlasa soļos.
- **T**: dzīvojamā ir šķērsspārnā, un privātās telpas ir kātā. Kāta garumu un nobīdi plānotājs pārlasa soļos.
- Vienam tipam izdod vairākus atšķirīgus plānus. Spoguļattēlus (x un y) uzskata par vienu un to pašu variantu.

### Priekšnams un dzīvojamā [MM]
- Priekšnams vai gaitenis ar dzīvojamo savienojas bez sienas (atvērts, kā MM 30 un 40 modeļos). Iekšdurvis ved tikai uz guļamistabām un WC.
- Ārdurvis ir priekšnamā vai dzīvojamā. Iekšpusē pie tām brīvs laukums 1000×1000. Ārdurvju platums ir 1000, iekšdurvju 800.

### Durvis [MM]
- Durvju aila sākas vismaz 75 mm no perpendikulārās sienas.
- Vērtnes zona plus 50 mm ir bez mēbelēm. Tas attiecas gan uz reālo vērtnes ceturtdaļloku, gan uz `rules_check` kvadrātu no sienas līnijas.
- Durvju nevēramajā pusē paliek brīva 600 mm josla. Divu durvju vērtnes nedrīkst pārklāties.
- WC un guļamistabu durvis ved uz priekšnamu vai gaiteni, un tikai tad, ja tas nav iespējams, uz dzīvojamo.

### Logi [MM]
- Logus liek tikai uz mājas ārējā taisnstūra (bbox) fasādēm, jo `rules_check` un `generate.py` logus klasificē pēc bbox sienām. L un T iekšstūru fasādēs logus neliek.
- Logs ir vismaz 250 mm no starpsienas vai stūra. Pārbaudes minimums ir 150.
- No ārdurvīm tajā pašā fasādē logs ir vismaz 400 mm attālumā. Pārbaudes minimums ir 300, un to pārbauda visām horizontālajām ārdurvīm pret dienvidu logiem.
- Loga zona (700 mm dziļumā, plus 50 mm katrā sānā) ir bez mēbelēm. Izņēmumi sakrīt ar `generate.window_rule`:
  - pods zem WC loga;
  - gulta zem loga, ja palodze ir ≥1200;
  - dīvāns blakus vertikālam logam.
- Dzīvojamai istabai logi ir vismaz uz 2 fasādēm. Viens no tiem ir stiklojums līdz grīdai (palodze 0) uz terases pusi.
- Guļamistabā un dzīvojamā logu laukums ir ≥1/8 no grīdas platības, un loga garumu aprēķina no šīs attiecības.
- WC logs ir 600 mm, augstu, virs poda. Telpai ar nosaukumu "WC" logs ir obligāts.

### Mēbeles [MM]
- **Gulta:**
  - galvgalis pret starpsienu, nevis zem zema loga;
  - vismaz vienā garajā malā ≥600 brīvs līdz sienai;
  - kājgalī ≥500 līdz mēbelei;
  - naktsgaldiņi abās pusēs, ja vieta to atļauj;
  - skapja priekšā 700 brīvs.
- **WC:**
  - poda ass ≥400 no sānu sienas;
  - ≥200 no izlietnes un dušas;
  - priekšā 800×600 brīvs;
  - izlietnes, veļasmašīnas un dušas priekšā 600 brīvs.
- **Dzīvojamā:**
  - virtuves rinda vēlams gar mitro sienu (pie WC), un tās priekšā 1000 brīvs;
  - dīvāns ir 1200–2400 garš un var stāvēt brīvi telpā, ≥700 no virtuves;
  - galds ≥700 no virtuves un dīvāna, ≥600 no sienas.
- **Priekšnams:** drēbju skapis, ja tas neaizsedz durvju zonu.

### Mansards / loft [MM]
- Mansards ir tikai II formai. Tas atrodas virs privātā bloka vienā mājas galā, rietumu vai austrumu, un plānotājs izmēģina abus galus.
- Dzīvojamā istaba aizņem visu mājas dziļumu. Virs tās ir "Atvērts uz 1. stāvu", un šai daļai jābūt vismaz 2400 platai. Ja aiz dzīvojamās ir vēl viens bloks (guļamistabas abos galos), tam ir griesti bez mansarda, un mansarda plānā tas paliek tukšs.
- Kāpnes (trepes 1000) ir priekšnamā vai gaitenī, dzīvojamās pusē. Priekšnams var būt gan dienvidos, gan ziemeļos.
- Loft malā augstums ≥700 (gultas mala). Kores augstums virs loft grīdas ≥1000 [MM]: māja 4000 mm no grīdas paneļa apakšas ar griestiem 2200 dod ~1029 mm, un to lietotājs pieņem. Zem 1500 `rules_check` dod tikai INFO.
- Loft gultu (1600, ja nav vietas, tad 1400) liek centrā pa kori, gala sienas pusē, ne pāri trepju atverei. Loft garums ir ≥2300.
- **Mansarda logi:**
  - Mansarda gala fasādē ir 600 logs. Palodze ir 2700, bet, ja jumts zems, 2300.
  - Ja dzīvojamā sniedzas līdz otrai gala fasādei, virs atvērtās daļas ir otrs logs. Tas ir fiksēts, garumā līdz 2200, ar palodzi 2300 (kā etalonā MM 30).
- `generate.py --mansards ja --varianti N` dod tikai variantus ar mansardu. `--mansards ne` dod variantus bez mansarda (II/L/T).

### Arhitekta vērtējums [MM]
Bots no visiem derīgajiem variantiem izvēlas **optimālo** (V01) un 1–2 **alternatīvas**. Katram ir pamatojums vienā teikumā. Kritēriji, mazāks punktu skaits ir labāks:
- **Gaiteņi un priekšnams:** līdz 8 % no telpu platības (lidz60) vai 14 % (virs60). Ja vairāk, sods ir proporcionāls pārsniegumam.
- **Dienas un nakts zona:** ja guļamistabas durvis ved tieši uz dzīvojamo, +1,5 par katru.
- **Mitrās telpas:** sanmezglam jābūt pie dzīvojamās sienas, lai virtuve būtu uz mitrās sienas. Ja nav, +1.
- **Dzīvojamās proporcijas:** ja īsākā mala ir zem 3000, +2; ja malu attiecība pārsniedz 2,2, +1.
- **Ieeja:** virs60 mājai, kurā ieeja ir tieši dzīvojamā, +1,5.
- **Konkurenti** (tās pašas klases moduļu mājas, `planojumi.json`) ir tikai kontrole. Telpu daļas novirze no vidējā dod nelielu sodu un piezīmi, ja tā ir ārpus 10.–90. procentiles. Mazāk gaiteņu vai lielāka dzīvojamā nav trūkums.
- Debespusi bots nezina, tāpēc saules bonusa nav.
- Variantus, kas ir par vairāk nekā 6 punktiem sliktāki par labāko, atmet kā "vājš plāns" un parāda iemeslu.

### Lielais stiklojums pēc mājas formas [MM]
- **Šaura II** (iekšējais dziļums < 4400): stiklojums līdz grīdai ir dzīvojamās gala fasādē, kā MM 30. Otrs logs ir garajā fasādē.
- **Plata II:** stiklojums ir garajā fasādē, tur, kur dzīvojamai ir garākā ārsiena. Tur ir vieta terasei.
- **L/T:** stiklojums ir dzīvojamās spārna galā (spārna īsajā sienā).

### Ko plānotājs pagaidām nedara [MM]
- virs60 L/T ar 2 vannasistabām.
- Logus L/T iekšējos stūros.
- L/T formu fasādes un jumtus: to dara `mm-sheet/cad.js`, un `mm-check` tur var ziņot R8.
- Normu novirzes (`planlib`) ir tikai piezīmes, nevis noraidīšanas iemesls.

### Lietotāja komentāri 05.11.2026 (/editbot) [MM]
Visi šie noteikumi ir lietotāja (EZIZ) prasība un ir saistoši. Realizēti `planner.py` (`R` vārdnīca, `std_win`, `furnish_bath`, `furnish_hall`, `furnish_liv`, `_loft_west`), `rules_check.py` un `sablons/sbe/plani/cad.js`.
1. **Maza guļamistaba (< 9 m²):** drēbju skapi neliek.
2. **Skapis priekšnamā vai gaitenī**, kas noslēdz caurgājienu (atlikušais platums < 900 mm), tiek dzēsts vai pārvietots tālāk uz dzīvojamo istabu. Dzīvojamā to liek, ja ietilpst (>= 700 mm no virtuves un dīvāna), citādi dzēš.
3. **Virtuve šaurā II mājā** (iekšējais dziļums < 4400) ir gar iekšējo galasienu (dzīvojamās siena pret priekšnamu / sanmezglu), nevis gar garo ārsienu. Priekšnama un dzīvojamās atvērumā (priekšnama platums + 1000 mm) virtuvi nelik.
4. **Dzīvojamās otrais logs pie virtuves darba virsmas:** 900 plats, fixed (neverams), palodze 900. Virtuves darba virsma drīkst atrasties zem loga ar palodzi >= 900.
5. **Logs līdz zemei un platāks par 1100:** fixed (viens stikls).
6. **Logs, kas nav līdz zemei un ir platāks par 1000:** divdaļīgs, kreisā daļa fixed, labā vērtne vēramā un gāžamā (`parts`). Šaurāks: vēramais un gāžamais (`tilt`).
7. **Standarta mansarda logs** gala fasādē: gāžamais (hopper, bottom hung) 1000 x 550, ar ārējo apmali kā parastiem logiem. Palodze 2700, zemāk, ja jumts zems.
8. **Logs virs lielā stiklojuma (mansarda otrs gala logs):** piecstūra fixed logs ar divām slīpām malām pa jumta slīpumu, tāda paša platuma kā lielais logs, palodze 2300, ar ārējo apmali. Ja lietotājs nenorāda citādi.
9. **Ieeja VIENMĒR no dienvidiem.** Ziemeļu, rietumu un austrumu ieejas neģenerē.
10. **Vienmēr sāc ar 1. variantu** (`--varianti 1`). Citus variantus ģenerē tikai tad, kad lietotājs to prasa.
11. **WC (lietotāja lēmumi):** (a) pods pēc noklusējuma centrēts zem WC loga (loga centrs = poda ass); (b) ja tas neder, pods pie sānsienas ar muguru pret sienu un 800 x 600 brīvu priekšā (sānsienas variants, `['toilet', siena_x, centra_y, 1, 'e'|'w']`); (c) starp izlietni un dušu jāvar paiet garām: atstarpe >= 600 mm, citādi izlietni pārliek (parasti stūrī pie ārsienas); (d) pods vienmēr >= 400 no sānu sienas.
12. **Izlietne WC:** ja pods ir pie sānsienas, izlietne ir gar to pašu sienu blakus podam.
13. **Logs pie virtuves:** logs nedrīkst ieiet virtuves darba virsmā. Ja virtuves rinda nav gar loga sienu, logs ir līdz zemei (fixed, 900) un >= 100 mm no virtuves rindas. Virs darba virsmas drīkst būt tikai mazs horizontāls logs: palodze 1000, augstums 600, platums parasti 1200 (tikai tad, ja rinda ir gar to sienu).
14. **Skapis dzīvojamā** nekad nav "vienkārši istabā": gar ārsienu, kreisā mala pret starpsienas galu vai virtuves rindas galu, bet ne priekšnama caurejā.
15. **Piecstūra un mansarda logi fasādē:** rāmis loga tonī (RAL 7016, ar-config win.colorOut), bez melna slāņa, ar ēnu uz stikla un ārējo apmali, kā parastie logi. Tie ir specifikācijas logi.
