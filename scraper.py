import os
import re
import json
import glob
import pdfplumber
from datetime import datetime, timezone

PDF_DIR = "pdf_cache"
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "tp_notices.json")

def normalize_text(txt):
    if not txt:
        return ""
    txt = re.sub(r"[\'´`’]\s*[·•\.]", ".", txt)
    txt = txt.replace('´', "'").replace('`', "'").replace('’', "'")
    txt = txt.replace('·', '.').replace('•', '.')
    txt = txt.replace('”', '"').replace('“', '"')
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

def detect_geometry_type(text, coords):
    c_count = len(coords)
    if c_count < 2:
        return 'POINT'
        
    txt_low = text.lower()
    
    # Açıkça geometrik sınır çizen UKHO kalıpları (geniş kapsam)
    # "bounded by the following positions", "bounded by lines joining",
    # "within an area bounded", "enclosed by", "limits defined by" vb.
    has_explicit_area = (
        'bounded by' in txt_low or
        'within an area' in txt_low or
        'enclosed by' in txt_low or
        'limits defined by' in txt_low or
        'within an area defined' in txt_low
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

def process_pdfs():
    os.makedirs(DATA_DIR, exist_ok=True)
    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    
    notices = []
    seen_ids = set()

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
                        
                        if notice_id in seen_ids:
                            continue
                        seen_ids.add(notice_id)
                        
                        coords = extract_coordinates(clean_block)
                        gtype = detect_geometry_type(clean_block, coords)
                        
                        c_lat = coords[0][0] if coords else None
                        c_lon = coords[0][1] if coords else None
                        
                        notices.append({
                            "id": notice_id,
                            "number": int(num),
                            "type": ntype,
                            "year": int(yr) if len(yr)==4 else int("20"+yr),
                            "title": subject or "T&P Notice",
                            "region": subject.split('-')[0].strip() if '-' in subject else "UKHO",
                            "subject": subject,
                            "text": clean_block,
                            "coordinates": coords,
                            "center_lat": c_lat,
                            "center_lon": c_lon,
                            "geometry_type": gtype,
                            "has_coordinates": len(coords) > 0
                        })
        except Exception:
            pass

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

if __name__ == "__main__":
    process_pdfs()
