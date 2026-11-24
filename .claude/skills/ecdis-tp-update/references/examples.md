# Örnekler ve kontrol listesi

Notice metinleri `data/tp_notices.json`'dan (UKHO weekly NM'den derlenmiş proje verisi) olduğu gibi alınmıştır. ECDIS işlemi marka bağımsız genel ilkedir; menü adımı yoktur (open-questions.md).

## Örnek 1: Temporary (T), nokta, önceki notice'i iptal ediyor
```
146(T)/26 NORWAY - West Coast - Buoyage.
Source: Norwegian Notice 5/77238(T)/25 and Norwegian SDO T and P 18/25
1. Yellow spherical ODAS waverider buoys, Fl(5) Y 20s, have been deployed in the following positions:
65° 47´·8N., 7° 37´·7E.
65° 44´·2N., 7° 36´·4E.
2. Mariners are advised to navigate with caution in the area.
3. *Former Notice 2554(T)/25 is cancelled.
*Indicates new or revised entry
(WGS84 DATUM)
Charts affected - 1430 (INT 1404) - 4101 (INT 101)   [Wk02/26]
```
Nasıl okunur:
- "(T)" ve "/26": Temporary, 2026 yılı (rules.md A1).
- Madde 3: 2554(T)/25 iptal. Takipte 2554(T)/25 varsa kapat; ECDIS'te veya chart'ta onun için işlenmiş bir şey varsa kaldır (rules.md A4).
- "(WGS84 DATUM)": konumların datum'u; ECDIS datum'uyla uyumu kontrol et (rules.md C5).
- Charts affected: hangi paper chart'lar. ENC için karşılığı ayrıca bulunmalı (ARCS/ENC eşleşmesi notice'te yazılı değildir).

## Örnek 2: Preliminary (P), kalıcı değişikliğin önceden duyurusu
```
83(P)/26 ENGLAND - East Coast - Channel limit.
Source: Port of London Authority
1. The southern Yantlet Secondary Channel has been extended up until position 51° 28´·998N., 0° 27´·747E., maintaining a 130m width.
2. Mariners are advised to navigate with caution in the area and consult the local port authorities for the latest information.
3. These changes will be included in a New Edition of Chart 1186 to be published early 2026.
(ETRS89 DATUM)
Chart affected - 1186 (INT 1426)   [Wk01/26]
```
Nasıl okunur: değişiklik yeni baskıyla charta girecek; o zamana kadar bilgi P notice ile gelir. Datum ETRS89, WGS84'ten farklı yazılmış: konumu ECDIS'e girmeden önce datum farkı kaptana sorulur (D1).

## Doğru işlem akışı (genel ilke)
1. Notice'i weekly NM'den veya in-force listesinden al; (T)/(P), numara/yıl, chart numaraları ve datum'u not et. [rules.md A1, A3]
2. Pasaj rotasının geçtiği ENC'lerde bu notice'in ENC'ye işlenip işlenmediğine bak: UKHO "T&P NMs in ENCs" durum tablosu, ENC içeriği, AIO poligonu (Pick Report). [A6]
3. Üç durumdan biri:
   a. ENC'de var: tekrar manual update yapma, çift kayıt olmasın; yalnızca teyit et.
   b. AIO poligonu var: ECDIS'te poligon gösterilir; ek manual update gerekmez (şirket/kaptan aksini isterse o uygulanır: Q2).
   c. Hiçbirinde yok: kaptana bildir; manual update veya mariner nesnesi (MIO) kararı kaptanındır (C7, Q1).
4. Manual update yapılıyorsa: nesne turuncu manual-update tanıtıcısıyla görünmeli, orijinal ENC nesnesi silinmemeli; girilen konum ve datum notice'le karşılaştırılmalı; basit doğrulama yolu (ECDIS'in sunduğu onay/inceleme) kullanılmalı. [C1 - C3, C5]
5. Notice iptal olduğunda yapılan girişi geri al, kaydı kapat. [A4]
6. Kayıt: ne zaman, kim, hangi notice, hangi chart. Kayıt biçimi şirket prosedürüne bağlıdır (Q2).

## Kontrol listesi (pasaj planı öncesi)
- [ ] Son weekly NM ve en son aylık T&P in-force listesi alındı mı? (Tarihlerini yaz.)
- [ ] Rota boyunca tüm chart'lar için yürürlükteki T&P'ler tarandı mı?
- [ ] İptal edilen T&P'ler (in-force listesindeki "cancelled" bölümü) takipten çıkarıldı mı?
- [ ] ENC'ler son edition ve son update'te mi? Update sırası eksiksiz mi? (IMO-1503 para 10)
- [ ] AIO (GB800001) yüklü ve ECDIS'te görünür mü, yoksa kullanılmıyor mu? (AIO-UG)
- [ ] Her T&P için ENC'de/AIO'da karşılığı var mı? Yoksa kaptana bildirildi mi?
- [ ] Manual update'ler ayırt edilebilir (CHCOR turuncu) ve doğrulanmış mı? Datum ve birim kontrol edildi mi?
- [ ] Kayıt tutuldu mu?
- [ ] Belirsiz her nokta kaptana/ilgili makama danışıldı mı?

## Proje verisi hakkında (yalnızca sorgu sonucu)
`data/tp_notices.json`: 3022 notice (2074 T, 948 P); alanlar: id, number, type, year, title, region, subject, text, coordinates, segments, center_lat, center_lon, geometry_type (POINT/LINE/AREA), has_coordinates; son güncelleme 2026-11-16. Veri ADMIRALTY weekly NM'den derlenmiştir; resmi in-force listesiyle birebir eşleştiği doğrulanmamıştır (Q8).
