# Kurallar (marka ve şirket bağımsız)

Doğrulama tarihi: 22 Kasım 2026. Durum etiketleri: [DOĞRULANDI] birincil/resmi metinden okundu; [İKİNCİL] resmi kurumun dolaylı ya da taslak belgesi, yardımcı kaynak; DOĞRULANMADI olanlar open-questions.md'dedir ve kural olarak yazılmamıştır.

Kaynak kısaltmaları:
- UKHO-WK36: ADMIRALTY Notices to Mariners Weekly Edition 36/2026 (3 Eylül 2026), "Explanatory Notes" bölümü ve T&P in-force listesi (msi.admiralty.co.uk/NoticesToMariners).
- UKHO-GUIDE: "Guidance notes for accessing ADMIRALTY Notice to Mariners" (revised Eylül 2015), msi.admiralty.co.uk/nms/about.
- UKHO-ABOUT: msi.admiralty.co.uk/NoticesToMariners/About.
- AIO-UG: ADMIRALTY Information Overlay (AIO) User Guide, V2.0, Aralık 2022 (assets.admiralty.co.uk).
- IMO-1503: MSC.1/Circ.1503/Rev.2, "ECDIS - Guidance for Good Practice", 28 Kasım 2022.
- S-52: IHO S-52 Edition 6.1.1 (Haziran 2015); PresLib Annex A Ed. 4.0.3 Part I Addendum (Aralık 2020).

---
## A. T&P nedir

A1. Tanım ve gösterim. UKHO weekly NM'de T&P notice'ler numaranın arkasındaki (T) veya (P) ile gösterilir; Section II'nin sonunda yer alır, yıl numaradan sonra yazılır (ör. 146(T)/26), her ay bir "in force" listesi yayınlanır. [DOĞRULANDI] Kaynak: UKHO-WK36, Explanatory Notes, Section II, "T&P Notices".

A2. Temporary (T) ve Preliminary (P) farkı.
- Temporary (T): geçici nitelikte değişiklik bilgisi (ör. şamandıranın yerinde olmaması, ışığın geçici sönük olması); kalıcı olması beklenmez.
- Preliminary (P): yakın gelecekte olması beklenen değişikliğin önceden duyurusu; çoğu zaman sonradan kalıcı olur.
Durum: [İKİNCİL]. Kaynak: Danimarka Hidrografi Ofisi (GST), "P- og T-notices and ENC updates" sayfası (UKHO değil); IHO çalışma grubu belgeleri tanımların IHO S-4 bölüm B-600'de (P için B-634) olduğunu belirtir (EUWG L03/L04-09, taslak). UKHO'nun kendi T/P tanım cümlesi ve S-4 metni okunamadı: DOĞRULANMADI, bkz. open-questions.md Q5. Uygulamada tutucu ol: iki türü de "uygulanması gereken geçerli bilgi" say; P'yi "henüz olmadı, olacak" diye yok sayma.

A3. NtM içindeki yeri. Weekly NM: Section IA = T&P in-force listesi (ayda bir, bir önceki ay iptal edilenlerle birlikte); Section II = standart chart düzeltme notice'leri, T&P'ler bunun sonunda; Section IB = güncel yayın listesi. [DOĞRULANDI] Kaynak: UKHO-WK36, Explanatory Notes, Section I, IA, IB, II.
Yıllık özet NP247(1): her yıl 1 Ocak itibarıyla yürürlükteki tüm T&P notice'lerin yeniden basımını içerir. [DOĞRULANDI] Kaynak: UKHO-GUIDE ("NP247(1) ... Temporary and Preliminary Notices").

A4. Geçerlilik ve iptal mantığı.
- Bir T&P kendiliğinden "bitti" sayılmaz; iptal edildiği bir notice'te yazılır (ör. "Former Notice 2554(T)/25 is cancelled"). Bu cümle gerçek notice metninde görülür (bkz. examples.md). [DOĞRULANDI: gerçek notice metni, proje verisi]
- Aylık in-force listesi hangi T&P'lerin yürürlükte olduğunu, önceki listenin iptal edildiğini ve önceki ay iptal edilenleri gösterir. [DOĞRULANDI] Kaynak: UKHO-WK36, Section IA ve in-force liste başlığı ("Former In Force List ... is cancelled").
- Web arama aracı, seçilen chart için "şu an yürürlükteki" T&P'leri ayrıca getirebilir. [DOĞRULANDI] Kaynak: UKHO-GUIDE, "ADMIRALTY NM Web Search".
- Notice metninde yazan bitiş tarihi tek başına güvenilir iptal sayılmaz; iptal notice'i veya in-force listesiyle teyit et (tutucu ilke, Kaptan onayına açık; bkz. open-questions.md Q7).

A5. Paper chart için uygulama. T&P bilgisi chart basılmadan önce charta işlenmez; "charts should be updated in pencil on receipt" (kurşun kalemle). [DOĞRULANDI] Kaynak: UKHO-WK36, Section II, "T&P Notices". Kalemin P/T iptalinde silinmesi: [İKİNCİL] (IHO'ya Fransa'nın sunduğu belge: P NM iptal edilince silinir) ve kalıcı düzeltmenin farklı mürekkeple yapıldığı bilgisi UKHO NP294'ten okunamadı: Q6.

A6. ENC için uygulama (kritik).
- T&P'ler paper chart için derlenir ve ENC'deki geçici bilgiyle uyuşmayabilir. [DOĞRULANDI] Kaynak: UKHO-WK36, ADMIRALTY dijital servisler/ENC notu (hangi bölüm başlığı altında olduğu metinden kesin okunamadı) ("T&P NMs are compiled for paper charts and may not align with any temporary information that is compiled into ENCs").
- Her ENC üreticisi T&P bilgisini ENC'ye koymaz. Güncel durum tablosu UKHO'nun "T&P NMs in ENCs" sayfasında. [DOĞRULANDI] Kaynak: UKHO-WK36, aynı bölüm; ayrıca Nautical Institute "T&P Notices on ENCs" (2010, tarihli, yardımcı).
- ADMIRALTY Information Overlay (AIO): ENC üreticisi geçici bilgiyi ENC'ye koymamışsa, paper chart için yayınlanan ADMIRALTY T&P NM'leri poligon olarak ENC üzerinde gösterir; poligon, orijinal NM numarasını taşır; tam metin ECDIS Pick Report'tan okunur. AIO haftalık güncellenir; ulusal T&P ile AIO arasında zaman farkı olabilir; çift kayıt olabilir. AIO yalnızca paper'a ait bilgiyi ve ENC üreticisinin ENC'ye koyduğunu doğruladığı bilgiyi dışarıda bırakır. AIO uyumlu ECDIS gerekir. [DOĞRULANDI] Kaynak: AIO-UG, "Overview", "Content", "Managing temporary information with AIO".
- Dolayısıyla "ENC güncel" demek "tüm T&P'ler ECDIS'te var" demek değildir. Tutucu kural: ENC ve AIO'ya ek olarak weekly NM T&P in-force listesi, pasaj planındaki chart'lar için ayrıca kontrol edilir. Gerekçe: UKHO-WK36 "Mariners should take temporary information into account when planning and executing a passage with ENCs" der (cümlenin devamı okunamadı) ve T&P'lerin ENC ile uyuşmayabileceğini söyler; Nautical Institute sayfası paper NM'yi T&P için "tek garantili kaynak" olarak anar (2010, tarihli, yardımcı). Güncel UKHO tavrı için Q4.

---
## B. Düzeltme yükümlülüğü

B1. SOLAS V/27: pasaj için gerekli chart ve nautical publication'lar (sailing directions, list of lights, notices to mariners vb.) "adequate and up to date" olmalıdır. Durum: [İKİNCİL] metin IHO ve bayrak devleti belgelerinde alıntılanmış; resmi SOLAS konsolide metninden okunamadı. Aynı zamanda IMO-1503 paragraf 10 bu düzenlemeye atıf yapar [DOĞRULANDI].

B2. ECDIS'i chart carriage için kullanan gemide: tüm ENC/RNC'ler son baskıda olmalı ve hem elektronik chart güncellemeleri (ENC updates) hem de en son mevcut notices to mariners ile güncel tutulmalıdır. Yedek (backup) düzenlemeleri için de aynı güncellik şartı geçerlidir. [DOĞRULANDI] Kaynak: IMO-1503, Annex paragraf 10 ve 11.

B3. SOLAS V/19.2.1.4: gemide pasajı planlamak, göstermek ve konum izlemek için chart ve nautical publication bulunmalıdır; MCA, UKHO weekly NM'nin kâğıt ve dijital halinin NtM taşıma gereğini karşıladığını kabul eder. [DOĞRULANDI: MCA kabulü, UKHO-GUIDE "Official Status"; V/19.2.1.4 metni İKİNCİL]

B4. UKHO, NM'lere göre düzeltilen chart'larda kayıt tutmak için NP133A (Paper Chart Maintenance Record) önerir. [DOĞRULANDI] Kaynak: UKHO-ABOUT. NP133A'nın ayrıntılı kullanımı ve NP294 metni okunamadı: Q6.

B5. Gözlem bildirimi: yeni/şüpheli tehlike veya chart/ENC eksikleri UKHO'ya H102 formuyla bildirilir. [DOĞRULANDI] Kaynak: UKHO-WK36, Section I girişi (H102/H102B).

---
## C. ECDIS'te manual update (genel ilkeler, markadan bağımsız)

C1. ECDIS, mariner'ın elle girdiği ENC güncellemelerini kabul edebilmeli; kesin kabulden önce doğrulamak için basit bir yol sunmalı; bu girişler ENC bilgisinden ve resmi güncellemelerinden ayırt edilebilir olmalı ve ekran okunabilirliğini bozmamalı. Durum: [İKİNCİL]. Kaynak: MSC.232(82) taslak metni (IMO NAV 52/18, Annex 6, paragraf 4.6; NOAA sitesindeki kopya). Kabul edilmiş son metindeki paragraf numarası ve tam sözcükler doğrulanmadı; ayrıca MSC.530(106) (2022) yeni standardı mevcut. Q3.

C2. S-52, IMO standardının manual update maddesini (S-52'de "IMO PS 4.6") şöyle karşılar: manual update'ler standart renk ve sembollerle gösterilir ve Presentation Library'de tarif edildiği gibi ayırt edilir; inceleme için tüm SENC bilgisi gösterilebilmelidir. [DOĞRULANDI] Kaynak: S-52 Ed. 6.1.1, bölüm 2.3.4 (IMO PS 4.6 ve 4.8).

C3. Elle yapılan chart düzeltmeleri küçük turuncu tanıtıcılarla (colour token CHCOR, "manual chart corrections made by the mariner") gösterilir; amaç insan hatasına açık elle girişleri otomatik girişten ayırmaktır. Orijinal chart nesnesi silinmez veya değiştirilmez. [DOĞRULANDI] Kaynak: S-52 Ed. 6.1.1, "Manual chart correction" maddesi ve renk tablosu (CHCOR); sembol adları CHCRID01 ("manually updated"), CHCRDEL1 ("manually deleted or modified"), LC(CHCRID01), LC(CHCRDEL1), PresLib Ed. 4.0.3 Part I Addendum, bölüm 8.7.1 atfıyla.

C4. Çizim önceliği: resmi ENC verisi ve resmi güncellemeler, NtM/manual input ve radyo navigasyon uyarılarından daha yüksek önceliklidir (katman 2 ve 3); mariner'ın kendi nesneleri daha düşük (katman 8). [DOĞRULANDI] Kaynak: S-52 Ed. 6.1.1, "10 priority layers" listesi.

C5. Eğitim ilkesi: manual update'te koordinat referans elipsoidine ve ölçü birimlerine (derinlik m/ft/fathom; konum datum'u) uyum özellikle gözetilmelidir. [DOĞRULANDI] Kaynak: IMO-1503, eğitim/bilgi bölümü "Chart updating" tablosu, madde 22 (.1). (Notice'lerde datum bu yüzden yazılıdır, ör. "(WGS84 DATUM)", "(ETRS89 DATUM)": examples.md.)

C6. Dikkat: IMO-1503'teki "Onboard ECDIS updates" bölümü yazılım/donanım güncellemesidir (type approval), chart manual update'i DEĞİL. İkisini karıştırma. [DOĞRULANDI] Kaynak: IMO-1503, "Onboard ECDIS updates" bölümü ve Appendix 4.

C7. Mariner-bilgisi nesneleri (MIO): geçici kısa süreli uyarılar ECDIS'te Mariner's Information Objects ile işaretlenebilir. [İKİNCİL] Kaynak: Nautical Institute, "T&P Notices on ENCs" (2010). Bunun bir "ENC manual update" ile ve şirket prosedürüyle ilişkisi Kaptan kararıdır: Q1, Q2.

C8. Markaya özel menü adımları: bu skill'de YOK. Bkz. open-questions.md, "Kaptandan alınacak bilgi".

---
## D. Skill'in tutucu davranış kuralları
D1. Notice metninde konum, datum veya birim belirsizse manual update önerme; kaptana sor.
D2. Pasaj planı T&P kontrolünde, şüpheli durumda "etkilenmiş say" ve kaptana bildir.
D3. Kaynağı olmayan kuralı "kural" diye yazma.
