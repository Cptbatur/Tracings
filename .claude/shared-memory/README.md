# Ortak Hafıza — T&P Ekibi

Bu klasör 4 sub-agent'ın ortak hafızasıdır. Her agent işe başlarken ilgili dosyayı okur, iş bitince kısa not düşer.

## Dosyalar

- `tp-bilgi-bankasi.md` — tp-bilirkisi yazar, tp-kodlayici ve tp-scraper-denetci okur. Onaylı T&P kuralları.
- `kod-haritasi.md` — tp-kodlayici yazar, tp-scraper-denetci okur. Kodun işleyiş haritası.
- `scraper-denetim.md` — tp-scraper-denetci yazar, tp-kodlayici uygular. Denetim raporları (tamlık/doğruluk/format).
- `sorular-cevaplar.md` — soran sorar, bilen cevaplar. Kod yazmadan/denetimi kapatmadan önceki belirsizlikler burada çözülür.
- `gorev-log.md` — 4 agent da iş bitince 3-5 satır log düşer (tarih, ne yaptı, sonuç).

## Protokol (zorunlu)

1. İşe başlarken önce bu klasördeki ilgili dosyayı oku (tamamını değil, son 30-50 satır yeterli: `tail` ile veya Read ile son bölüm).
2. Kısa yaz: her kayıt max 5 satır, kaynak varsa belge adı + bölüm yaz.
3. `DOĞRULANMADI` etiketli bilgiyi kesin kural gibi kullanma.
4. Büyük veri dosyalarını (`data/tp_notices.json` vb.) buraya kopyalama, sadece özet + sorgu yaz.
5. AGENTS.md geçerli: dosyaları baştan sona okuma, `grep` / `python3 -c` / hedefli satır aralığı kullan.
