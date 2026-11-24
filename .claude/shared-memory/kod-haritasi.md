# Kod Haritası (tp-kodlayici keşfi, 2026-11-24 — kod yazılmadı, sadece anlama)

## tp_audit.py (148 satır, analiz betiği — JSON yazmaz, sadece konsola rapor basar)
- Görev: pdf_cache/*.pdf içindeki T&P verisini tarayıp arşiv derin-analiz raporu basar.
- Girdi: pdf_cache/*.pdf (week_* için sadece Section II sayfaları, annual için indeks hariç).
- Çıktı: stdout rapor (toplam ilan, (continued) sayısı, koordinat dağılımı, geometri sinyal kelimeleri, kaynak kurumlar, başlık kelimeleri) + durum tablosu.
- Not: (continued) sayfaları atlanır (sayaç artar, birleştirme yok); scraper.py'daki birleştirme mantığı burada yok.
- Dayandığı kural: yok (keşif/audit aracı; bilgi bankası kuralına bağlanmamış).

## scraper.py (328 satır, veri üretici)
- Görev: pdf_cache PDF'lerinden T&P notice'leri çıkarıp data/tp_notices.json yazar.
- Girdi: pdf_cache/*.pdf; başlık deseni `^NUM(T|P)/YIL` + metin; Section II filtresi (is_valid_page).
- Çıktı: data/tp_notices.json — alanlar: id, number, type, year, title, region, subject, text, coordinates, segments, center_lat/lon, geometry_type, has_coordinates (+last_updated, total_notices).
- Alt mantık: normalize_text (satır-kırığı/Yön-harfi onarımı) → extract_coordinates → split_into_segments (A/B/C ana rota + 80 NM derin-su bölmesi) → detect_geometry_type (POINT/LINE/AREA, tabular-liste ve restricted/firing anahtar kelimeleriyle).
- Devam sayfası: aynı id görülürse koordinat+metin birleştirilir, geometri yeniden hesaplanır.
- Dayandığı kural: kısmen K2 (iptal cümlesi yok — status alanı yok), K1/K3 eksik (in-force listesi ve ENC/paper ayrımı koda girmemiş).

## index.html (787 satır, istemci uygulaması)
- Görev: data/tp_notices.json + kullanıcı rotasını (RTZ/GPX) alıp CPA analizi, harita ve rapor üretir.
- Girdi: ./data/tp_notices.json; rota dosyası (parseRTZ/parseGPX → waypoints); eşikler: safety (vars. 15 NM), XTD (vars. 0.5 NM).
- Çıktı: harita (OSM + Esri Ocean/Sat, Leaflet; LINE=polyline, AREA=polygon, POINT=circleMarker) + rapor kartları (id, geometri, chart, CPA, ham metin) + kırmızı/amber rozetler.
- Mesafe: notice koordinatları ↔ rota segmentleri min CPA (ptToSegmentNM/hvNM); red = CPA ≤ XTD, amber = XTD < CPA ≤ safety.
- Rapor filtresi: severity (ALL/RED/AMBER) + metin arama; extractCharts() metinden "Charts affected" çeker.
- Dayandığı kural: yok — S3 cevapları (aktif/iptal filtresi, kaynak satırı, DOĞRULANMADI ibaresi, resmi-kaynak + ENC uyarı metni) henüz koda girmemiş. "T&P Active" rozeti tüm kaydı aktif varsayar (K2'ye aykırı varsayım riski).

## .github/workflows/scrape.yml (küçük, tamamı okundu)
- Görev: her Cuma 02:00 UTC (cron `0 2 * * 5`) + manuel tetiklemede scraper'ı çalıştırıp JSON'u commitler.
- Adımlar: checkout → Python 3.11 → requirements → `python scraper.py` → `data/tp_notices.json` + pdf_cache commit/push.
- Not: PDF indirme adımı yok; scraper da indirme yapmaz — yeni haftalık PDF'in pdf_cache'e nasıl girdiği belirsiz (bkz. S6).
- Dayandığı kural: yok (zamanlama işletmeseldir; K1'deki aylık in-force listesi akışta yok).

## requirements.txt (3 satır) + PROJECT_CONTEXT.md (2 satır)
- requirements: requests, pdfplumber, beautifulsoup4, lxml.
- PROJECT_CONTEXT: "gerçek geçmiş/kod klasörden okunur, tahmin yok" + kaptan tercümanlığı ilkesi.
- Dayandığı kural: yok.

## data/tp_notices.json (5.8M, tam okunmadı — python3 ile özet)
- Şema: {last_updated, total_notices, notices[]}; notice alanları: center_lat/lon, coordinates, geometry_type, has_coordinates, id, number, region, segments, subject, text, title, type, year.
- Durum (2026-11-16): 3022 kayıt; POINT 2225 / AREA 588 / LINE 209; T 2074 / P 948; koordinatlı 3012, koordinatsız 10.
- Dayandığı kural: kısmen K1 (T/P ayrımı type alanında var); K2/S2 alanları YOK (status, iptal referansı, etkilenen chart/ENC, kaynak belge+tarih, bitiş tarihi).

## ROUTES/ + pdf_cache/ (ls ile yapı)
- ROUTES/: ROUTE/, TAIPAN/, "THE LAST"/ alt klasörleri + .RT3 rota dosyaları (kaptanın sefer rotaları; uygulama girdisi).
- pdf_cache/: annual_tp_2026.pdf + week_2026_01..09.pdf (scraper girdisi; 10+ hafta eksik görünüyor).
- Dayandığı kural: yok.

## ANLAŞILMAYAN / EKSİK (kural karşılığı ile)
1. İptal/status: JSON'da status yok, index.html hepsini aktif sayar → K2 + S1/S2 cevabı koda girmemiş. (S4'e bak)
2. Kaynak izi: notice başına kaynak belge+tarih ve etkilenen chart/ENC no JSON'da yok (chart sadece JS regex'i) → S2 cevabı uygulanmamış. (S4'e bak)
3. In-force listesi: akışta aylık in-force kontrolü yok; format/kaynak belirsiz → K1 uygulanamaz. (S5'e bak)
4. PDF tedariği: yeni haftalık PDF'ler pdf_cache'e nasıl geliyor (manuel commit mi, indirme kodu mu lazım)? → workflow veriyi tazeleyemez görünüyor. (S6'ya bak)
5. Uyarı metinleri: resmi-kaynak + ENC uyarısı ve DOĞRULANMADI ibaresi raporda yok → S3 cevabı uygulanmamış (kodlama öncesi bilirkişi onayı gerekmez, S1-S3 cevabı var; ancak status alanı olmadan aktif/iptal filtresi yazılamaz).
