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
    
    # 1. Müstakil derinlik, sığlık ve ölçüm cihazı listeleri: Kesinlikle POINT
    # (Örn: Celtic Sea ölçüm cihazları, sahil boyunca derinlik sondajları)
    is_discrete_list = any(k in txt_low for k in [
        'scientific instruments', 'measuring instruments', 'instruments have been established',
        'depths less than charted', 'drying heights', 'numerous depths', 'shoal'
    ])
    has_explicit_area = any(k in txt_low for k in [
        'bounded by lines joining', 'within an area bounded', 'area bounded by',
        'within the area bounded', 'enclosed by lines joining', 'within an area joining',
        'in the area bounded'
    ])
    
    if is_discrete_list and not has_explicit_area:
        return 'POINT'

    # 2. Hat/Çizgi Geometrisi: Kablo ve boru hatları (asla mesafeden dolayı noktaya çevrilmez)
    is_line = any(k in txt_low for k in [
        'cable', 'pipeline', 'along a line joining', 'line joining', 'track joining', 'route joining'
    ])
    if is_line and not has_explicit_area:
        return 'LINE'
        
    # 3. Alan/Poligon Geometrisi: Sadece açıkça geometrik sınır bildiren ifadelerde
    if has_explicit_area and c_count >= 3:
        return 'AREA'
        
    # 4. Açık sınır içermeyen şamandıra ve fener listeleri: POINT
    if any(k in txt_low for k in ['buoy', 'light-buoy', 'light buoy', 'beacon', 'light unlit', 'fl.y', 'fl.g', 'fl.r']):
        return 'POINT'
        
    if is_line:
        return 'LINE'
        
    return 'POINT'

def process_pdfs():
    os.makedirs(DATA_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    notices = []
    seen_ids = set()

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] PDF dosyaları taranıyor...")

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    raw_text = page.extract_text() or ""
                    if "(T)/" not in raw_text and "(P)/" not in raw_text:
                        continue
                        
                    notice_blocks = re.split(r'(?=\b\d{1,5}\([TP]\)/\d{2,4}\b)', raw_text)
                    
                    for block in notice_blocks:
                        clean_block = block.strip()
                        if "(T)/" not in clean_block and "(P)/" not in clean_block:
                            continue

                        # Sadece sayfa indekslerini ele
                        if len(clean_block) < 35 and re.search(r'\d+\.\d+$', clean_block):
                            continue
                            
                        header_match = re.search(r'\b(\d{1,5})\(([TP])\)/(\d{2,4})\b\s*(.*?)(?=\n|$)', clean_block)
                        if not header_match:
                            continue
                            
                        num = header_match.group(1)
                        ntype = header_match.group(2)
                        yr = header_match.group(3)
                        subject = header_match.group(4).strip()
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
