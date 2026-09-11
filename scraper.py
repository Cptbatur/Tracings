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

def parse_coord(lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir):
    try:
        la = float(lat_deg) + (float(lat_min if lat_min else 0) / 60.0) + (float(lat_sec if lat_sec else 0) / 3600.0)
        lo = float(lon_deg) + (float(lon_min if lon_min else 0) / 60.0) + (float(lon_sec if lon_sec else 0) / 3600.0)
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
    
    pattern = re.compile(
        r'(\d{1,3})\s*°\s*(\d{1,2}(?:\.\d+)?)?\s*\'?\s*(?:(\d{1,2}(?:\.\d+)?)\s*["”])?\s*([NS])\b[\s\.,]*'
        r'(\d{1,3})\s*°\s*(\d{1,2}(?:\.\d+)?)?\s*\'?\s*(?:(\d{1,2}(?:\.\d+)?)\s*["”])?\s*([EW])\b',
        re.IGNORECASE
    )
    
    for m in pattern.findall(clean):
        if m[0] and m[3] and m[4] and m[7]:
            c = parse_coord(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7])
            if c and c not in coords:
                coords.append(c)
            
    return coords

def detect_geometry_type(text, coord_count):
    txt_low = text.lower()
    if 'area bounded' in txt_low or 'bounded by' in txt_low or 'within area' in txt_low:
        return 'AREA' if coord_count >= 3 else ('LINE' if coord_count == 2 else 'POINT')
    if 'joining' in txt_low or 'pipeline' in txt_low or 'cable' in txt_low or 'track' in txt_low:
        return 'LINE' if coord_count >= 2 else 'POINT'
    if coord_count >= 3:
        return 'AREA'
    elif coord_count == 2:
        return 'LINE'
    return 'POINT'

def process_pdfs():
    os.makedirs(DATA_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    notices = []
    seen_ids = set()

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {len(pdf_files)} PDF dosyası taranıyor...")

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
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

                        # Sadece "3852(T)/07 2.370" gibi indeks gürültülerini filtrele
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
                        gtype = detect_geometry_type(clean_block, len(coords))
                        
                        region = subject.split('-')[0].strip() if '-' in subject else "UKHO"
                        
                        c_lat = coords[0][0] if coords else None
                        c_lon = coords[0][1] if coords else None
                        
                        notices.append({
                            "id": notice_id,
                            "number": int(num),
                            "type": ntype,
                            "year": int(yr) if len(yr)==4 else int("20"+yr),
                            "title": subject or "T&P Notice",
                            "region": region,
                            "subject": subject,
                            "text": clean_block,
                            "coordinate_groups": [coords] if coords else [],
                            "coordinates": coords,
                            "center_lat": c_lat,
                            "center_lon": c_lon,
                            "geometry_type": gtype,
                            "has_coordinates": len(coords) > 0
                        })
        except Exception as e:
            print(f"Hata ({filename}): {e}")

    result = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_notices": len(notices),
        "notices": notices
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] İŞLEM TAMAMLANDI!")
    print(f"Toplam Gerçek T&P İlanı: {len(notices)}")
    with_coords = sum(1 for n in notices if n['has_coordinates'])
    text_only = len(notices) - with_coords
    print(f"📍 Coğrafi / Haritada Çizilebilir İlanlar: {with_coords}")
    print(f"📄 Bölgesel / Metinsel İlanlar: {text_only}\n")

if __name__ == "__main__":
    process_pdfs()
