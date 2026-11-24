# UI Envanteri — index.html (tp-ui-developer keşfi, 2026-11-25 — kod yazılmadı, hedefli tarama)

## Sekmeler (4 section + 4 dock butonu, switchTab jenerik id-birleştirme)
- tab-import / n-import: rota yükleme (RTZ/GPX) + eşikler + EXECUTE
- tab-convert / n-convert: format çevirici (RTZ/GPX/RT3/CVT/CSV/RTE/NMEA)
- tab-map / n-map: Leaflet harita (lmap, map-wrap)
- tab-report / n-report: rapor + filtreler + GENEL BİLGİ

## Tüm id'ler (48, JS ile birebir eşleşmeli)
hdr, hdr-logo, hdr-stats, stat-red, stat-amber, stat-notices, app, tab-wrap,
tab-import, drop-zone, file-inp, file-info, inp-safety, inp-xtd, analyze-btn,
tab-convert, conv-drop, conv-inp, conv-fmt, conv-info, conv-prev-card, conv-count,
conv-table, conv-tbody, dl-rtz, dl-gpx,
tab-map, map-wrap, lmap,
tab-report, print-meta, rpt-filter-input, f-all, f-red, f-amber,
fs-active, fs-cancelled, fs-all, rpt-warn-block, rpt-list, rpt-gen-list,
bnav, n-import, n-convert, n-map, n-report

## Fonksiyonlar (32, gövde mantığına DOKUNULMAZ)
- switchTab(t, autoFit) — sekme geçiş + harita invalidateSize
- fetchStatusAndData() — JSON çek, Active/Cancelled sayaç, renderGeneralInfo
- detectRouteFormat(txt, filename, buf) — RTZ/GPX/RT3/CVT/RTE/DOCUMENT/NMEA/CSV/BILINMIYOR
- parseRoute(txt, filename) — yönlendirici (RTE hariç; RTE ArrayBuffer ister)
- parseRT3, parseRTE(buf), parseDMM, parseCVT, parseCSV, parseRTZ, parseGPX
- escXml, buildRTZ, buildGPX, downloadConv(kind), previewOnMap
- file-inp change handler (DOCUMENT uyarısı + RTE/ArrayBuffer + CVT windows-1252)
- conv-inp change handler (DOCUMENT/BILINMIYOR dalları + önizleme tablosu)
- toR, hvNM, ptToSegmentNM, getNoticeDistance, runAnalysis (has_coordinates atlama satırı KORUNUR)
- initMap (OSM+Esri Ocean+Esri Sat, layer control), renderRoute (mavi rota #0284c7), renderMarkers (LINE polyline / AREA polygon / POINT circleMarker; hex #f43f5e red / #f59e0b amber)
- extractCharts, renderReport→filterReport, setSeverityFilter, setStatusFilter (varsayılan ACTIVE),
  sourceLine (İptal:/Kaynak:/DOĞRULANMADI), statusBadge (tag-green Active / tag-grey Cancelled),
  toggleCard, renderGeneralInfo (Show on Map YOK, 5 çağrı noktası), locateOnMap, escapeHtml, exportPrintableReport

## JSON alanları (S.tpRaw üzerinden)
id, type(T/P), year, title, subject, text, region, coordinates, segments, geometry_type,
center_lat/lon, has_coordinates, status(active/cancelled), cancelled_by, cancels

## Kritik mantık (BOZULMAMALI)
- runAnalysis: has_coordinates=false atlanır; red = dist<=xtd, amber = xtd<dist<=safety
- statusFilter varsayılan ACTIVE (KAPTAN S4); severity varsayılan ALL
- conv-inp/file-inp ArrayBuffer okuma (RTE binary + OLE DOCUMENT magic D0CF11E0)
- CVT windows-1252 decode; parseDMM'e dokunulmaz
- Uyarı bloğu S3 metinleri aynen: "Resmî kaynak ADMIRALTY weekly NM / T&P in-force listesidir; son karar kaptanındır." + "ENC güncel olması tüm T&P'lerin ECDIS'te olduğu anlamına gelmez."
- renderGeneralInfo harita/CPA'ya girmez, GENEL kartta Show on Map yok
- Leaflet akışı korunur (kütüphane değişmez); tile URL'leri OSM/Esri aynen kalır

## K7/K8 renk kontrolü (soruya gerek YOK)
Uygulamada manual-update girişi yok (S7 kapsam dışı); turuncu/amber yalnızca CPA caution bandını gösterir, CHCOR sembolü çizilmez. Kırmızı=XTD Conflict (tehlike), mavi=bilgi/rota hattı — ayrım korunacak.

## Harici bağımlılıklar (mevcut)
Google Fonts (Plus Jakarta Sans + JetBrains Mono) + Leaflet 1.9.4 CDN + OSM/Esri tile. Yeniden yazımda: fontlar sistem stack'ine alınır (işlevsiz, gemi interneti), Leaflet + tile korunur (kaptan emri).
