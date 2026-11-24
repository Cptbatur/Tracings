# Scraper Denetim Raporu (tp-scraper-denetci yazar, tp-kodlayici uygular)

> Format: Tarih | Eksen (tamlık/doğruluk/format) | Bulgu | Kanıt (dosya:satır) | Hüküm (GEÇTİ/KALDI) | Devredilen.
> Denetçi kod değiştirmez; KODLAYICIYA DEVİR etiketiyle devreder.

## Denetim 2026-11-24 (ilk denetim)

1. 2026-11-24 | tamlık | pdf_cache'te annual + week_2026_01..38 var (39 dosya); 24 Kasım itibarıyla ~39-47. hafta PDF'leri yok, JSON last_updated 2026-11-16'da kalmış. 9 haftalık kopuk tedarik. | Kanıt: pdf_cache ls (week_38 en yeni, 11 Eyl); data/tp_notices.json last_updated 2026-11-16, total 3022 | Hüküm: KALDI | KODLAYICIYA DEVİR (S6 kapsamında otomatik indirme).
2. 2026-11-24 | tamlık | scrape.yml her Cuma 02:00 UTC çalışıp scraper.py + commit yapıyor, ancak PDF indirme adımı yok; scraper da indirme yapmıyor. Workflow mevcut PDF'leri tekrar işler, yeni veri getirmez. | Kanıt: .github/workflows/scrape.yml:4-5,25-34 | Hüküm: KALDI | KODLAYICIYA DEVİR (S6).
3. 2026-11-24 | doğruluk | scraper.py'de iptal yakalama yok (cancel/former notice/superseded/in-force/status grep = 0 hit). JSON'da 569 kayıtta "former notice/cancel" cümlesi metinde geçiyor ama yapısal alana düşmemiş. Örn. 1073(T)/22 "Former Notice 4385(T)/20 is cancelled" metinde var, status key'i yok. | Kanıt: scraper.py grep boş; JSON sorgusu (569/3022); K2 + S1/S2 cevabına aykırı | Hüküm: KALDI | KODLAYICIYA DEVİR (S4 kapsamında status + iptal referansı).
4. 2026-11-24 | doğruluk | T/P ayrımı doğru: type alanında T 2074 / P 948. | Kanıt: JSON Counter sorgusu; K1 | Hüküm: GEÇTİ | Devredilen: yok.
5. 2026-11-24 | format | JSON şeması 14 key (center_lat/lon, coordinates, geometry_type, has_coordinates, id, number, region, segments, subject, text, title, type, year). S2'de istenen status, iptal referansı, chart/ENC no, kaynak belge+tarih, bitiş tarihi YOK. index.html mevcut alanları okuyor (id, geometry_type, coordinates, segments, title, text; chart JS regex extractCharts:687) ama status olmadan aktif/iptal filtresi yazılamaz. | Kanıt: JSON keys sorgusu; index.html:405,489,687-694 | Hüküm: KALDI | KODLAYICIYA DEVİR (S4).
6. 2026-11-24 | format | Bozuk/eksik oranı düşük: koordinatsız 10/3022 (%0,3), textsiz 0. Koordinatsızlar haritada atlanıyor (index.html:508 continue). | Kanıt: JSON sorgusu; index.html:508 | Hüküm: GEÇTİ (disclaimer'a not) | Devredilen: yok.

## Disclaimer'a girecek açıklar (kaptan beyanı 2026-11-24: release'de disclaimer yazılacak)
- D1: 3022 kaydın tamamı ekranda "T&P Active" sayılıyor (index.html:405); 569 iptal-cümleli + in-force'tan düşenler ayırt edilmiyor → aktif görünen kayıt iptal olabilir.
- D2: 39-47. hafta verileri yok → rota kontrolü güncel değildir; son karar kaptanındır, resmî kaynak weekly NM / in-force listesidir. [S6: DÜŞTÜ — 39-49 indirildi, JSON 3352; revize: son indirilen haftadan sonrası için rota kontrolü güncel değildir.]
- D3: Koordinatsız 10 kayıt haritada görünmez, CPA hesabı dışındadır.
- D4: "ENC güncel" demek "tüm T&P'ler ECDIS'te" demek değildir; ENC + AIO'ya ek olarak in-force listesi kontrol edilmelidir (K3).
- D5: Kayıtlarda kaynak belge+tarih izi yok → her satırın hangi belgeye dayandığı doğrulanamaz.

## Ara denetim S4 (2026-11-24, tp-scraper-denetci)
- Desen: extract_cancel_info (scraper.py:224-239) + devam-blogu merge (:310-317) + 2. tur cozum (:355-363); Durum1/Durum2 ayrimi K2/S1/S9'a uygun. | Hüküm: GEÇTİ
- JSON (python3 -c): total 3022 = total_notices; status disi 0; active 2732 / cancelled 290; cancels dolu 569; cancelled_by dolu 290 (=cancelled, tutarli); self 0. Cozulen ref 290, hedefi JSON'da olmayan uniq ref 291 (eski haftalar, dokunulmadi — S1'e uygun). | Hüküm: GEÇTİ
- Ornekler: 1073(T)/22 active + cancels [4385(T)/20] (iceren aktif — dogru); 1108(T)/22 cancelled, cancelled_by 2350(T)/26 (hedef cozumu — dogru). | Hüküm: GEÇTİ
- Not: Durum2 (self) deseni veride ornegi olmadigindan test edilemedi (self 0); ilk self-cancel gorulunce gozden gecirilsin. Cozulemeyen 291 ref + D2 (39-47. hafta yok) tamlik ekseninde acik, S5 in-force'a kaldi.
- SONUC: GEÇTİ — KODLAYICIYA DEVİR yok.

## Ara denetim S6 (2026-11-24, tp-scraper-denetci)
- Indirme katmani: ensure_pdfs_cached (scraper.py:68-131) + _download_pdf_cached (:32-41) b64a787 mantigina uygun (UKHO Weekly/Annual URL, mevcut dosya varsa atla, ag yoksa/kutuphane eksikse dry-run + cache ile devam); process_pdfs(run_download=True) (:381-384) once indirir sonra parse eder. | Hüküm: GEÇTİ
- Annual/in-force: indirme katmani dosyayi indirir, JSON'a kayit EKLEMEZ (is_valid_page annual dalinda INDEX sayfalari atlar, scraper.py:375-379; parse akisi haftalik baslik deseninden devam eder). | Hüküm: GEÇTİ
- JSON (python3 -c): total 3352 (kaptan karari: 11 yeni hafta 39-49 KALACAK, revert yok); status/cancels/cancelled_by korunmus; active 2998 / cancelled 354; cancels dolu 630, cancelled_by dolu 354 (=cancelled, firesiz); id formati disi 0. | Hüküm: GEÇTİ
- pdf_cache: week_2026_01..49 tam (49/49, eksik yok) + annual_tp_2026.pdf mevcut. | Hüküm: GEÇTİ
- D2 guncelleme: "39-47. hafta verileri yok" hukmu DUSTU (39-49 artik JSON'da); disclaimer D2 "hafta kopuklugu" degil "son hafta sonrasi guncellik" olarak revize edilmeli. | Hüküm: GEÇTİ
- SONUC: GEÇTİ — KODLAYICIYA DEVİR yok.

## Ara denetim S5 (2026-11-24, tp-scraper-denetci)
- In-force dali: _INFORCE_ENTRY_RX `(\d{1,4})\(([TP])\)/(\d{2})\s+2\.\d+` S10(b) deseniyle eslesiyor (grup ayristirmali esdeger); tarih _INFORCE_TITLE_RX ile PDF ic basligindan (19 DECEMBER 2025), dosya adindan degil; dusurme SADECE active + year<=2025 kayitlara, 2026 muaf sayacla atlaniyor. | Hüküm: GEÇTİ
- JSON (python3 -c): total 3352 = total_notices (kaptan karari: degismedi); active 2998 / cancelled 354 (S6 ile ayni); cancelled_by dagilimi: in-force 0, self 0, tamami ref-hedefi (354=354 tutarli); 2026: 1315 active muaf + 184 cancelled ref-kaynakli, in-force dokunmadi. | Hüküm: GEÇTİ
- Ornekler (bagimsiz sorgu): yil<=2025 active olup listede OLMAYAN 0 kayit (0-gecis iddiasi dogrulandi); listede olan eski 2721(T)/22 ve 5441(P)/17 active kalmis; 3852(T)/07 cancelled ama sebebi ref-cancel (3584(T)/26), in-force degil. | Hüküm: GEÇTİ
- SONUC: GEÇTİ — KODLAYICIYA DEVİR yok.

## Ara denetim S6-UI (2026-11-24, tp-scraper-denetci)
- index.html diff (62+/6-, git diff): beklenen ekler SADECE: status CSS (tag-green/grey, rpt-warn-block, src-line), 3 status filtresi cipi, uyari blogu, statusFilter state (varsayilan ACTIVE), setStatusFilter/sourceLine/statusBadge, filtre mantigi + rozet/kaynak satiri render. Baska degisiklik yok (severity cipi toggle refactor zararsiz). | Hüküm: GEÇTİ
- S3 metinleri aynen yazilmis: "Resmî kaynak ADMIRALTY weekly NM / T&P in-force listesidir; son karar kaptanındır." + "ENC güncel olması tüm T&P'lerin ECDIS'te olduğu anlamına gelmez." + belirsizde "DOĞRULANMADI - kaptana danış". Varsayılan filtre ACTIVE (S.statusFilter='ACTIVE', fs-active active). | Hüküm: GEÇTİ
- JSON eslesme (python3 -c, 1 kayit): status/cancelled_by/cancels alanlari mevcut (active/None/[]); total 3352, active 2998 / cancelled 354. HTML `(n.status||'active')` varsayimi JSON ile uyumlu. | Hüküm: GEÇTİ
- D1 DÜŞTÜ: "hepsi Active sayılıyor" açığı kapandı (rozet + sayaç "2998 Active / 354 Cancelled" + varsayılan Active filtresi). Disclaimer D1 revize edilmeli.
- SONUÇ: GEÇTİ — KODLAYICIYA DEVİR yok. (Tarayıcı testi yapılmadı, statik kontrol.)
