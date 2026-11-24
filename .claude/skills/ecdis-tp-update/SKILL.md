---
name: ecdis-tp-update
description: ADMIRALTY T&P (Temporary & Preliminary) Notices to Mariners nasıl okunur, takip edilir, iptal edilir ve ECDIS'te (ENC) ya da paper chart'ta nasıl uygulanır. T&P notice, NtM, chart/ENC düzeltmesi, manual update, pasaj planı T&P kontrolü veya tp_notices.json verisiyle ilgili soru ve işlerde kullan. Marka bağımsız genel kuraldır; marka menü adımı ve şirket SMS prosedürü içermez.
---

# ecdis-tp-update

Bu skill, T&P notice konusunda IMO/IHO/UKHO düzeyinde genel kuralları verir. Kullanıcı bir kaptandır ve kodlama bilmez: Türkçe, sade yaz; T&P, NtM, ENC, ARCS, manual update terimlerini İngilizce bırak.

## Nasıl çalış
1. T&P'nin ne olduğu veya T ile P farkı sorulursa: `references/rules.md` Bölüm A.
2. Düzeltme, ENC/paper uygulaması ve manual update sorulursa: `references/rules.md` Bölüm B ve C.
3. Gerçek örnek ve kontrol listesi gerekirse: `references/examples.md`.
4. Bir kuralın kaynağı `rules.md`'de yoksa kural gibi sunma. `references/open-questions.md`'ye bak; orada "DOĞRULANMADI" olanı kesin bilgi gibi söyleme.

## Değişmez ilkeler
- Her kural kaynağıyla verilir. Kaynağı olmayan bilgi "DOĞRULANMADI" diye işaretlenir.
- Seyir emniyetinde belirsizlik varsa tutucu davran: notice'i uygulanmış/yok hükmünde sayma; "kaptana / ilgili makama (UKHO, şirket) danış" de.
- ECDIS marka/modeline özel menü adımı YAZMA. Marka bilinmiyor (bkz. open-questions.md, "Kaptandan alınacak bilgi").
- Şirket SMS prosedürü bilinmiyor; kaptan beyanı gelirse en yüksek öncelikli kaynak sayılır, "Kaptan beyanı" diye işaretlenir.
- Bu projenin verisi (`data/tp_notices.json`) büyüktür: baştan sona okuma, `python3 -c` ile sadece ilgili notice'i sorgula (AGENTS.md).
- Uygulama sadece bilgilendirme aracıdır. Resmi kaynak ADMIRALTY weekly NM / T&P in-force listesidir; son karar kaptanındır.
