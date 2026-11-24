import os
import re
import json
import glob
import pdfplumber
from datetime import datetime, timezone

PDF_DIR = "pdf_cache"
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "tp_notices.json")

# --- S6 indirme katmani ---
# Kaynak: git b64a787 scraper.py (UKHO_BASE/_download_pdf_cached/scrape_single_week/
# scrape_annual) + sorular-cevaplar.md S10(a) koordinator cevabi + Kaptan S6 karari
# (ELLE INDIRME YOK: kod haftalik indirmeleri yapip depolayacak).
# Ag yoksa dry-run raporu verip mevcut cache ile devam eder, parse akisi bozulmaz.
try:
    import requests
    from bs4 import BeautifulSoup
    from html import unescape
    _HAS_NET_LIB = True
except ImportError:
    _HAS_NET_LIB = False

UKHO_BASE = "https://msi.admiralty.co.uk"
UKHO_WEEKLY_URL = f"{UKHO_BASE}/NoticesToMariners/Weekly"
UKHO_ANNUAL_URL = f"{UKHO_BASE}/NoticesToMariners/Annual"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def _get_session():
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s

def _download_pdf_cached(session, url, cache_filename):
    """Mevcut dosya varsa atla (cache), yoksa indirip pdf_cache'e yaz."""
    cache_path = os.path.join(PDF_DIR, cache_filename)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path, False  # indirilmedi, cache kullanildi
    resp = session.get(url, timeout=120)
    resp.raise_for_status()
    with open(cache_path, 'wb') as f:
        f.write(resp.content)
    return cache_path, True

def _find_link_in_html(html, pattern):
    soup = BeautifulSoup(html, 'lxml')
    for a in soup.find_all('a', href=True):
        parent_tr = a.find_parent('tr')
        parent_text = parent_tr.get_text() if parent_tr else ""
        anchor_text = a.get_text()
        if re.search(pattern, parent_text, re.IGNORECASE) or re.search(pattern, anchor_text, re.IGNORECASE):
            return unescape(a['href'])
    return None

def _build_full_url(link):
    if link.startswith('/'):
        return f"{UKHO_BASE}{link}"
    if link.startswith('http'):
        return link
    return f"{UKHO_BASE}/{link}"

def _disk_max_week(year):
    best = 0
    for p in glob.glob(os.path.join(PDF_DIR, f"week_{year}_*.pdf")):
        m = re.search(r'week_\d{4}_(\d{2})\.pdf$', p)
        if m:
            best = max(best, int(m.group(1)))
    return best

def ensure_pdfs_cached(year=None, target_week=None):
    """Weekly (week_YYYY_WW.pdf) + annual (annual_tp_YYYY.pdf) indirme katmani.

    In-force/annual listesi S5 ile birlesik: bu katman sadece dosyayi indirir,
    parse/status karari S5'e aittir (liste kaydi haftalikta yoksa EKLEMEZ).
    Ag yoksa ya da kutuphane eksikse dry-run raporu verip cache ile devam eder.
    """
    os.makedirs(PDF_DIR, exist_ok=True)
    if year is None:
        year = datetime.now(timezone.utc).year
    if not _HAS_NET_LIB:
        print("[S6] requests/bs4 yok (dry-run): indirme atlandi, cache ile devam.")
        return {"downloaded": [], "skipped_cache": [], "dry_run": True}
    session = _get_session()
    # Hedef hafta: UKHO sayfasindaki hdnWeek/hdnYear, ulasilamazsa diskteki max hafta
    if target_week is None:
        try:
            html = session.get(UKHO_WEEKLY_URL, timeout=15).text
            wk = re.search(r'hdnWeek.*?value="(\d+)"', html)
            yr = re.search(r'hdnYear.*?value="(\d+)"', html)
            if yr:
                year = int(yr.group(1))
            target_week = int(wk.group(1)) if wk else _disk_max_week(year)
        except Exception as e:
            print(f"[S6] UKHO'ya ulasilamadi ({e}) (dry-run): indirme atlandi, cache ile devam.")
            return {"downloaded": [], "skipped_cache": [], "dry_run": True}
    downloaded, skipped = [], []
    try:
        # 1. Annual ozet (in-force sayisal indeksini icerir; S10(b) formati)
        annual_name = f"annual_tp_{year}.pdf"
        annual_path = os.path.join(PDF_DIR, annual_name)
        if os.path.exists(annual_path) and os.path.getsize(annual_path) > 0:
            skipped.append(annual_name)
        else:
            resp = session.get(UKHO_ANNUAL_URL, timeout=30)
            resp.raise_for_status()
            link = _find_link_in_html(resp.text, r'Temporary\s+and\s+Preliminary\s+Notices')
            if link:
                _, is_new = _download_pdf_cached(session, _build_full_url(link), annual_name)
                (downloaded if is_new else skipped).append(annual_name)
            else:
                print("[S6] Annual T&P linki bulunamadi, haftaliklarla devam.")
        # 2. Haftalik bultenler 1..hedef hafta (yil+hafta -> week_YYYY_WW.pdf)
        for week in range(1, target_week + 1):
            cache_name = f"week_{year}_{week:02d}.pdf"
            cache_path = os.path.join(PDF_DIR, cache_name)
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                skipped.append(cache_name)
                continue
            try:
                resp = session.post(UKHO_WEEKLY_URL, data={'year': str(year), 'week': str(week)}, timeout=30)
                resp.raise_for_status()
                link = _find_link_in_html(resp.text, r'snii')
                if not link:
                    print(f"[S6] Hafta {week}/{year}: link bulunamadi, atlandi.")
                    continue
                _, is_new = _download_pdf_cached(session, _build_full_url(link), cache_name)
                (downloaded if is_new else skipped).append(cache_name)
            except Exception as e:
                print(f"[S6] Hafta {week}/{year} indirilemedi ({e}), cache ile devam.")
    except Exception as e:
        print(f"[S6] Indirme katmani hatasi ({e}): mevcut cache ile devam.")
    print(f"[S6] Indirme ozeti: {len(downloaded)} yeni, {len(skipped)} cache'ten.")
    return {"downloaded": downloaded, "skipped_cache": skipped, "dry_run": False}

def normalize_text(txt):
    if not txt:
        return ""
    txt = re.sub(r"[\'´`’]\s*[·•\.]", ".", txt)
    txt = txt.replace('´', "'").replace('`', "'").replace('’', "'")
    txt = txt.replace('·', '.').replace('•', '.')
    txt = txt.replace('”', '"').replace('“', '"')
    
    # 1. Satır kırılmasında rakam bölünmesini onar: örn '5° 5\n5´·79W' -> '5° 55.79W'
    txt = re.sub(r'(\d+°\s*\d+)\s*\n\s*(\d+[\'\.]\d+[EWNS]\b)', r'\1\2', txt)
    
    # 2. Araya giren kelimeler (Pillar, Buoy vb.) ve satır kırılmasını onar:
    txt = re.sub(r'(\d{1,3}\s*°\s*\d+)\s*\n\s*(?:[A-Za-z\s]+)?\s*(\d+[\'\.]\d+[EWNS]\b)', r'\1\2', txt)
    
    # 3. Yön harfi eksikliği onarımı (örn '20° 57.670. has been' -> '20° 57.670E. has been')
    txt = re.sub(r'([NS]\b[\s\.,]+\d{1,3}\s*°\s*\d+(?:\.\d+)?(?:[\'\.]\d+)?)\s*[\.](?=\s+[a-z])', r'\1E.', txt)
    
    return txt

def parse_coord(lat_d, lat_m, lat_s, lat_dir, lon_d, lon_m, lon_s, lon_dir):
    try:
        la = float(lat_d) + (float(lat_m if lat_m else 0) / 60.0) + (float(lat_s if lat_s else 0) / 3600.0)
        lo = float(lon_d) + (float(lon_m if lon_m else 0) / 60.0) + (float(lon_s if lon_s else 0) / 3600.0)
        if lat_dir.upper() == 'S': la = -la
        if lon_dir.upper() == 'W': lo = -lo
        
        if -90 <= la <= 90 and -180 <= lo <= 180:
            return [round(la, 6), round(lo, 6)]
    except Exception:
        pass
    return None

def extract_coordinates(text):
    clean = normalize_text(text)
    coords = []
    
    # Doğrudan UKHO Standart Enlem / Boylam Deseni
    pattern = re.compile(
        r'(\d{1,2})\s*°\s*(\d{1,2}(?:\.\d+)?)?\s*\'?\s*(?:(\d{1,2}(?:\.\d+)?)\s*["”])?\s*([NS])\b[\s\.,]*'
        r'(\d{1,3})\s*°\s*(\d{1,2}(?:\.\d+)?)?\s*\'?\s*(?:(\d{1,2}(?:\.\d+)?)\s*["”])?\s*([EW])\b',
        re.IGNORECASE
    )
    
    for m in pattern.findall(clean):
        c = parse_coord(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7])
        if c and c not in coords:
            coords.append(c)
            
    return coords

def coord_distance_nm(c1, c2):
    """İki koordinat arasındaki yaklaşık mesafe (deniz mili)."""
    import math
    dlat = (c2[0] - c1[0]) * 60.0
    avg_lat = math.radians((c1[0] + c2[0]) / 2.0)
    dlon = (c2[1] - c1[1]) * 60.0 * math.cos(avg_lat)
    return math.sqrt(dlat**2 + dlon**2)

def split_into_segments(text, coords, gap_nm=30.0):
    """
    Evrensel Zabit Mantığı:
    1. Hiyerarşik Ana Rota Kontrolü:
       Eğer bülten 'A - Country to Country', 'B - Country to Country' gibi ana kablo/boru
       güzergahlarına ayrılmışsa, önce ana hatları bağımsız güzergahlar (routes) olarak ayırır.
       Böylece İtalya hattı, Fransa hattı ve İspanya hattı asla birbirine bağlanmaz!
    2. Derin Su vs Kıyı Sığlık Ayrımı:
       Aynı hat içinde bile aradaki derin deniz boşluğu (>80 NM) boyunca UKHO koordinat
       vermemişse, harita üzerinde boydan boya sahte deniz aşırı düz çizgi çekilmez.
       Her sığlık geçiş etabı (etap 1, etap 2...) nizami olarak gösterilir.
    3. Çoklu Alan (HPMAs / Protected Areas):
       'Dolphin Head', 'Allonby Bay' gibi farklı isimli sahalar kendi içinde bağımsız
       poligonlar olarak ayrılır.
    """
    if not coords:
        return []
        
    clean = normalize_text(text)
    
    # 1. KADEME: Çok Hatlı Büyük Kablo Güzergahları (A - Italy..., B - France...)
    major_routes = re.split(r'(?m)^\s*(?:\d+\.\s*)?([A-Z])\s*[\-–]\s+([^\n\[]+)', clean)
    if len(major_routes) > 1:
        route_segments = []
        for idx in range(1, len(major_routes), 3):
            content = major_routes[idx+2]
            r_coords = extract_coordinates(content)
            if not r_coords:
                continue
            # Bu ana hat içindeki derin su sıçramalarını (>80 NM) bölerek etapları oluştur:
            cur_patch = [r_coords[0]]
            for c in r_coords[1:]:
                dist = coord_distance_nm(cur_patch[-1], c)
                if dist > 80.0:  # Derin deniz boşluğunda yeni etaba geç
                    if len(cur_patch) >= 1:
                        route_segments.append(cur_patch)
                    cur_patch = [c]
                else:
                    cur_patch.append(c)
            if cur_patch:
                route_segments.append(cur_patch)
        if route_segments:
            return route_segments

    # 2. KADEME: İsimli Alanlar veya Madde Ayrımı (Dolphin Head, Allonby Bay, 1., 2. and...)
    split_pattern = r'(?m)(?:^\s*(?:\d+\.\s*(?:and\b|[A-Z])|[A-Z]\s*[\-–]\s+[A-Za-z]|\band\b|Area\s+[A-Z]\b|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\s*$))'
    sub_blocks = re.split(split_pattern, clean)
    
    raw_segments = []
    for sb in sub_blocks:
        sb_coords = extract_coordinates(sb)
        if sb_coords:
            raw_segments.append(sb_coords)
            
    if not raw_segments:
        raw_segments = [coords]

    # Her segment içindeki 80 NM'den büyük sıçramaları koru
    final_segments = []
    for seg in raw_segments:
        if len(seg) <= 1:
            final_segments.append(seg)
            continue
        cur = [seg[0]]
        for c in seg[1:]:
            dist = coord_distance_nm(cur[-1], c)
            if dist > 80.0:
                if len(cur) >= 1:
                    final_segments.append(cur)
                cur = [c]
            else:
                cur.append(c)
        if cur:
            final_segments.append(cur)
            
    return final_segments

def detect_geometry_type(text, coords):
    c_count = len(coords)
    if c_count < 2:
        return 'POINT'
        
    txt_low = text.lower()
    
    # Zabit Kuralı: Tablo halinde pafta veya fener/saha listesi içeren ilanlar (örn: 4233(P)/26)
    # Her satırda ayrı bir sahanın tekil mevkisi verilmişse bu kapalı poligon değildir, POINT listesidir.
    is_tabular_reference = any(k in txt_low for k in [
        'largest scale chart', 'new designation', 'details of the areas are included in the list',
        'legends', 'changes to certain charted'
    ])
    if is_tabular_reference:
        return 'POINT'

    # Açıkça geometrik sınır çizen UKHO kalıpları (geniş kapsam)
    # "bounded by the following positions", "bounded by lines joining",
    # "within an area bounded", "enclosed by", "limits defined by" vb.
    # + Zabit Kuralı: Yasak/Atış/Kısıtlı Sahalar (Restricted, Prohibited, Firing, Danger Area)
    has_restricted_area_kw = any(k in txt_low for k in [
        'restricted area', 'prohibited area', 'firing practice', 'firing exercise',
        'danger area', 'exercise area', 'spoil ground', 'dredging area', 'foul area',
        'works area', 'anchorage prohibited'
    ])

    has_explicit_area = (
        'bounded by' in txt_low or
        'within an area' in txt_low or
        'enclosed by' in txt_low or
        'limits defined by' in txt_low or
        'within an area defined' in txt_low or
        has_restricted_area_kw
    ) and c_count >= 3

    # 1. Müstakil derinlik, sığlık ve ölçüm cihazı listeleri: Kesinlikle POINT
    # Açıkça sınırlı bir alan tanımı yoksa bu tip ilanlar poligon değil nokta listesidir
    is_discrete_list = any(k in txt_low for k in [
        'scientific instruments', 'measuring instruments', 'instruments have been established',
        'depths less than charted', 'drying heights', 'numerous depths', 'shoal'
    ])
    if is_discrete_list and not has_explicit_area:
        return 'POINT'

    # 2. Hat/Çizgi Geometrisi: Kablo ve boru hatları
    # Asla koordinat sayısı veya mesafeden dolayı noktaya çevrilmez
    is_line = any(k in txt_low for k in [
        'cable', 'pipeline', 'along a line joining', 'line joining', 'track joining', 'route joining'
    ])
    if is_line and not has_explicit_area:
        return 'LINE'
        
    # 3. Alan/Poligon Geometrisi: Açıkça geometrik sınır çizen ilanlar
    if has_explicit_area:
        return 'AREA'
        
    # 4. Açık sınır içermeyen şamandıra ve fener listeleri: POINT
    if any(k in txt_low for k in ['buoy', 'light-buoy', 'light buoy', 'beacon', 'light unlit', 'fl.y', 'fl.g', 'fl.r']):
        return 'POINT'
        
    if is_line:
        return 'LINE'
        
    return 'POINT'

# K2/S1 + KAPTAN S9 (2026-11-24): iki-durumlu iptal mantigi.
# DURUM 1 (yenileme): "Former Notice NUM(T/P)/YR is/are cancelled" -> referans
# verilen eski notice iptal olur, iceren kayit AKTIF kalir.
# DURUM 2 (self-cancel): notice'in kendisi cancel mesajiysa ("this notice ...
# cancelled" vb.) iceren kayit kendisi CANCELLED olur (cancelled_by:"self").
_FORMER_RX = re.compile(
    r'[Ff]ormer [Nn]otices?\s+(.+?)\s+(?:is|are|was|has been)\s+cancell?ed')
_REF_RX = re.compile(r'(\d{1,5})\s*/?\(?\s*([TPtp])\s*\)?\s*/?\s*(\d{2,4})')
_SELF_RX = re.compile(
    r'[Tt]his notice[^.]{0,150}[Cc]ancell?ed|'
    r'[Tt]his notice and [Ff]ormer [Nn]otice[^.]{0,150}[Cc]ancell?ed')

def extract_cancel_info(text):
    """Metinden (cancels_list, is_self_cancelled) dondurur.

    Supheli/parse edilemeyen varyant S1 tutucu ilkeye gore aktif varsayilir.
    """
    flat = re.sub(r'\s+', ' ', text or '')
    # DURUM 2 oncelikli: kendisinin iptal edildigi acikca yaziyorsa
    is_self = bool(_SELF_RX.search(flat))
    cancels = []
    m = _FORMER_RX.search(flat)
    if m:
        for num, ntype, yr in _REF_RX.findall(m.group(1)):
            ntype = ntype.upper()
            yr = yr if len(yr) == 2 else yr[-2:]
            cancels.append(f"{int(num)}({ntype})/{yr}")
    return cancels, is_self

# K10 + S10(b) + S11/KAPTAN 2026-11-24 (yil filtresi): in-force numerical index dali.
# Liste SADECE annual/aylik IA PDF'indeki "NUMERICAL INDEX OF NOTICES IN FORCE ON
# <tarih>" baslikli sayfalardadir; haftalik PDF'lerde yoktur. Tarih PDF ic
# basligindan alinir, dosya adindan degil. S11: liste yilindan yeniler muaf.
_INFORCE_TITLE_RX = re.compile(
    r'NUMERICAL INDEX OF NOTICES IN FORCE ON\s+'
    r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})',
    re.IGNORECASE)
_INFORCE_ENTRY_RX = re.compile(r'(\d{1,4})\(([TP])\)/(\d{2})\s+2\.\d+')

def _norm_inforce_id(num, ntype, yy):
    return f"{int(num)}({ntype.upper()})/{yy}"

def _norm_notice_id(nid):
    m = re.match(r'(\d+)\(([TPtp])\)/(\d{2,4})', nid or '')
    if not m:
        return nid
    return f"{int(m.group(1))}({m.group(2).upper()})/{m.group(3)[-2:]}"

def is_valid_page(pdf_path, text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return False
    # Haftalık bültenlerde sadece Section II (Seyir Duyuruları) taranır
    if "week_" in pdf_path:
        if lines[0] == "II" or any("SECTION II" in l for l in lines[:3]):
            return True
        return False
    # Yıllık bültende fihrist/indeks sayfaları atlanır
    if "annual" in pdf_path:
        if any("INDEX OF NOTICES" in l for l in lines[:3]):
            return False
        return True
    return True

def process_pdfs(run_download=True):
    os.makedirs(DATA_DIR, exist_ok=True)
    if run_download:
        ensure_pdfs_cached()  # S6: once indir/depola, sonra mevcut parse akisi
    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    
    notices = []
    seen_ids = {}  # id -> index in notices list

    # Satır başında başlayan gerçek T&P başlık deseni (Örn: 52(T)/26 IRELAND - East Coast - Buoy.)
    header_pattern = re.compile(r'(?m)^(\d{1,5})\(([TP])\)/(\d{2,4})\s+(.+)$')

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] PDF dosyaları taranıyor...")

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    raw_text = page.extract_text() or ""
                    if not is_valid_page(pdf_path, raw_text):
                        continue
                        
                    # İlanları satır başındaki resmi başlıklardan böl
                    matches = list(header_pattern.finditer(raw_text))
                    if not matches:
                        continue
                        
                    for i, m in enumerate(matches):
                        start_pos = m.start()
                        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(raw_text)
                        clean_block = raw_text[start_pos:end_pos].strip()
                        
                        num = m.group(1)
                        ntype = m.group(2)
                        yr = m.group(3)
                        subject = m.group(4).strip()
                        notice_id = f"{num}({ntype})/{yr}"
                        is_continued = "(continued)" in subject.lower()
                        
                        if notice_id in seen_ids:
                            # Devam sayfası: koordinatları mevcut ilana ekle
                            extra_coords = extract_coordinates(clean_block)
                            if extra_coords:
                                idx = seen_ids[notice_id]
                                existing = notices[idx]
                                # Yinelenen koordinatları ekleme
                                existing_set = {tuple(c) for c in existing["coordinates"]}
                                for c in extra_coords:
                                    if tuple(c) not in existing_set:
                                        existing["coordinates"].append(c)
                                        existing_set.add(tuple(c))
                                existing["has_coordinates"] = len(existing["coordinates"]) > 0
                                # Metni de birleştir
                                existing["text"] += "\n" + clean_block
                                # S9 DURUM 1/2: devam blogunda gelen iptal cumlesini de isle
                                # (ilk blokta cumle yoksa cancels bos kalirdi)
                                mc, ms = extract_cancel_info(existing["text"])
                                for r in mc:
                                    if r not in existing.get("cancels", []):
                                        existing["cancels"].append(r)
                                if ms:
                                    existing["status"] = "cancelled"
                                    existing["cancelled_by"] = "self"
                                # Geometriyi ve segmentleri tüm koordinatlarla yeniden belirle
                                existing["geometry_type"] = detect_geometry_type(existing["text"], existing["coordinates"])
                                existing["segments"] = split_into_segments(existing["text"], existing["coordinates"]) if existing["geometry_type"] in ['LINE', 'AREA'] else []
                            continue
                        
                        coords = extract_coordinates(clean_block)
                        gtype = detect_geometry_type(clean_block, coords)
                        segments = split_into_segments(clean_block, coords) if gtype in ['LINE', 'AREA'] else []
                        
                        c_lat = coords[0][0] if coords else None
                        c_lon = coords[0][1] if coords else None
                        
                        cancels, is_self = extract_cancel_info(clean_block)
                        notice_obj = {
                            "id": notice_id,
                            "number": int(num),
                            "type": ntype,
                            "year": int(yr) if len(yr)==4 else int("20"+yr),
                            "status": "cancelled" if is_self else "active",
                            "cancelled_by": "self" if is_self else None,
                            "cancels": cancels,
                            "title": subject.replace(" (continued)", "").replace(" (Continued)", "").strip() or "T&P Notice",
                            "region": subject.split('-')[0].strip() if '-' in subject else "UKHO",
                            "subject": subject,
                            "text": clean_block,
                            "coordinates": coords,
                            "segments": segments,
                            "center_lat": c_lat,
                            "center_lon": c_lon,
                            "geometry_type": gtype,
                            "has_coordinates": len(coords) > 0
                        }
                        seen_ids[notice_id] = len(notices)
                        notices.append(notice_obj)
        except Exception:
            pass

    # K10 in-force dusurme (S10(b) regex + S11 yil filtresi, KAPTAN ONAYLI 2026-11-24):
    # SADECE status active VE notice yili <= liste yili olan kayitlar listede
    # aranir; listede yoksa cancelled + cancelled_by "in-force <tarih>".
    # Liste tarihinden yeniler (or. liste 2025 iken 2026 kayitlari) MUAFTIR.
    inforce_ids = set()
    inforce_date = None
    inforce_year = None
    for pdf_path in pdf_files:
        if "annual" not in pdf_path:
            continue
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    if "NUMERICAL INDEX OF NOTICES IN FORCE" not in t:
                        continue
                    mt = _INFORCE_TITLE_RX.search(re.sub(r'\s+', ' ', t))
                    if mt and inforce_date is None:
                        inforce_date = f"{mt.group(1)} {mt.group(2)} {mt.group(3)}"
                        inforce_year = int(mt.group(3))
                    for num, ntype, yy in _INFORCE_ENTRY_RX.findall(t):
                        inforce_ids.add(_norm_inforce_id(num, ntype, yy))
        except Exception:
            pass
    n_inforce_drop = 0
    n_inforce_exempt = 0
    if inforce_ids and inforce_year:
        for n in notices:
            if n.get("status") != "active":
                continue
            if n.get("year", 9999) > inforce_year:
                n_inforce_exempt += 1  # S11 muafiyeti: liste tarihinden yeni
                continue
            if _norm_notice_id(n.get("id")) not in inforce_ids:
                n["status"] = "cancelled"
                n["cancelled_by"] = f"in-force {inforce_date}"
                n_inforce_drop += 1

    # DURUM 1 cozumu (2. tur): cancels referansi JSON'da mevcutsa o kayit
    # status:"cancelled" + cancelled_by:"<bu notice id>" olur. (K2/S1 + S9)
    by_id = {n["id"]: n for n in notices}
    for n in notices:
        for ref in n.get("cancels", []):
            tgt = by_id.get(ref)
            if tgt is not None and tgt.get("cancelled_by") != "self":
                tgt["status"] = "cancelled"
                tgt["cancelled_by"] = n["id"]

    result = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_notices": len(notices),
        "notices": notices
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] İŞLEM TAMAMLANDI!")
    print(f"Toplam T&P İlanı: {len(notices)}")
    with_c = sum(1 for n in notices if n['has_coordinates'])
    print(f"Haritada Gösterilebilecek İlanlar: {with_c}")
    n_act = sum(1 for n in notices if n.get('status') == 'active')
    n_can = sum(1 for n in notices if n.get('status') == 'cancelled')
    n_cancels = sum(1 for n in notices if n.get('cancels'))
    print(f"Aktif: {n_act} / Iptal: {n_can} / cancels dolu: {n_cancels}")
    if inforce_date:
        print(f"In-force ({inforce_date}): listede {len(inforce_ids)}, dusen: {n_inforce_drop}, muaf: {n_inforce_exempt}")

if __name__ == "__main__":
    process_pdfs()
