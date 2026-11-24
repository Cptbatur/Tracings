# Token / Kredi Tasarrufu ve Dosya Okuma Kuralları

Bu projede token/kredi tüketimini en aza indirmek ve gereksiz context şişmesini önlemek için aşağıdaki kurallar zorunludur:

1. **Dosyaları Baştan Sona Okuma Yasağı:**
   - Kod ve veri dosyalarını (`.py`, `.html`, `.json`, `.csv`, `.log`, vb.) gerekmedikçe asla baştan sona (tüm satırları) okuma.
   - Her zaman hedeflenen satır aralığını (`StartLine`, `EndLine`) veya `grep` / `find` gibi filtreleme araçlarını kullanarak sadece ilgili bloğu incele.
   - Büyük veri dosyalarını (ör. `data/tp_notices.json`) doğrudan metin olarak okumak yerine Python tek satırlık scriptler (`python3 -c "..."`) ile sorgula ve özetle.

2. **Gereksiz Context ve Çıktı Kısıtlaması:**
   - Komut çıktılarında binlerce satır basılmasına izin verme (`head`, `tail`, `grep` ile sınırla).
   - Tam dosya içeriğini tekrar tekrar modele yükleme; sadece değiştirilecek fonksiyonu veya bloğu gör ve düzenle (`edit_file` / `replace_file_content`).

3. **Önce Düşün, Hedefli İncele:**
   - Bir sorunu ararken tüm dosyayı okumak yerine dosya yapısını, fonksiyon başlıklarını veya hata veren satır numarasını tespit edip yalnızca o aralığa odaklan.
