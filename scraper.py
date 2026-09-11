import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from html import unescape

import pdfplumber
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Dizin Yapısı ve Önbellek
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_APP_DIR, "data")
CACHE_DIR = os.path.join(_APP_DIR, "pdf_cache")
DATA_FILE = os.path.join(DATA_DIR, "tp_notices.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

UKHO_BASE = "https://msi.admiralty.co.uk"
UKHO_WEEKLY_URL = f"{UKHO_BASE}/NoticesToMariners/Weekly"
UKHO_ANNUAL_URL = f"{UKHO_BASE}/NoticesToMariners/Annual"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

COORD_PATTERN = r'(\d+)\u00b0\s*(\d+)\u00b4\u00b7(\d+)\s*([NS])[.,]+\s*(\d+)\u00b0\s*(\d+)\u00b4\u00b7(\d+)\s*([EW])'

def extract_coords(text: str) -> list:
    results = []
    for m in re.finditer(COORD_PATTERN, text):
        try:
            lat_dec = m.group(3)
            lon_dec = m.group(7)
            lat = int(m.group(1)) + (int(m.group(2)) + int(lat_dec) / (10 ** len(lat_dec))) / 60
            lon = int(m.group(5)) + (int(m.group(6)) + int(lon_dec) / (10 ** len(lon_dec))) / 60
            if m.group(4) == 'S':
                lat = -lat
            if m.group(8) == 'W':
                lon = -lon
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                c = [round(lat, 6), round(lon, 6)]
                if c not in results:
                    results.append(c)
        except Exception:
            pass
    return results

def _segment_coordinates_from_text(text: str) -> list[list]:
    if not text:
        return []
    all_coords = extract_coords(text)
    if not all_coords:
        return []
    if len(all_coords) <= 1:
        return [all_coords]

    lines = text.split('\n')
    blocks: list[list[str]] = [[]]
    for line in lines:
        stripped = line.strip()
        is_sep = False
        if stripped.lower() == 'and':
            is_sep = True
        elif re.match(r'^\d+\.\s*$', stripped):
            is_sep = True
        elif re.match(r'^\w[\w\s]*(?:site|zone|area)\s*:', stripped, re.IGNORECASE):
            is_sep = True
        elif (re.match(r'^[A-Z][A-Za-z\s\'-]+$', stripped)
              and len(stripped) > 3
              and not re.search(r'\d', stripped)
              and stripped not in ('Source', 'Charts', 'DATUM', 'NOTE')):
            is_sep = True

        if is_sep:
            if blocks[-1]:
                blocks.append([])
            continue
        blocks.append(blocks.pop() + [stripped]) if blocks else blocks.append([stripped])

    blocks = [b for b in blocks if b]
    groups = []
    for block in blocks:
        block_text = '\n'.join(block)
        block_coords = extract_coords(block_text)
        if block_coords:
            groups.append(block_coords)

    if len(groups) <= 1:
        return [all_coords]
    return groups

def classify_geometry(title: str, text: str, coord_count: int) -> str:
    combined = (title + ' ' + text).lower()
    if re.search(r'bounded\s+by\s+(the\s+)?following\s+positions?', combined):
        return 'AREA'
    if re.search(r'joining\s+(the\s+)?following\s+positions?', combined):
        return 'LINE'
    if re.search(r'in\s+the\s+following\s+position\s*:', combined):
        return 'POINT'

    title_lower = title.lower()
    if any(kw in title_lower for kw in ['submarine cable', 'submarine cables', 'submarine pipeline', 'submarine pipelines', 'power cable']):
        return 'LINE'
    if any(kw in title_lower for kw in ['restricted area', 'restricted areas', 'dredging area', 'dredged area', 'reclamation area', 'anchorage area', 'anchorage areas', 'wind farm', 'exercise area']):
        return 'AREA'

    if coord_count == 1:
        return 'POINT'
    if any(kw in title_lower for kw in ['wreck', 'wrecks', 'obstruction', 'obstructions', 'light-beacon', 'light-buoy', 'platform']):
        return 'POINT' if coord_count <= 3 else 'MULTI_POINT'
    if any(kw in title_lower for kw in ['buoy', 'buoyage', 'scientific instrument', 'measuring instrument']):
        return 'POINT' if coord_count == 1 else 'MULTI_POINT'

    if coord_count <= 1:
        return 'POINT'
    if coord_count == 2:
        return 'LINE'
    if any(kw in title_lower for kw in ['works', 'depth', 'depths']):
        return 'AREA' if coord_count >= 4 else 'MULTI_POINT'
    if coord_count >= 4:
        return 'AREA'
    return 'MULTI_POINT'

_HEADER_RE = re.compile(r'^\s*(\d+)\s*\(\s*([TP])\s*\)\s*/\s*(\d+)\s+(.+)', re.IGNORECASE)
_HEADER_CONTINUED_RE = re.compile(r'^\s*(\d+)\s*\(\s*([TP])\s*\)\s*/\s*(\d+).*\(continued\)', re.IGNORECASE)
_PAGE_JUNK_RE = re.compile(r'^\s*(?:[IVX]+|\d+\.\d+|Wk\s*\d+/\d+|Section\s+II|.*Notices\s+to\s+Mariners.*)\s*$', re.IGNORECASE)

def _split_page_into_sections(text: str) -> list[tuple[str | None, str]]:
    lines = text.split('\n')
    sections: list[tuple[str | None, str]] = []
    current_id = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or _PAGE_JUNK_RE.search(stripped):
            continue

        cm = _HEADER_CONTINUED_RE.search(stripped)
        if cm:
            if current_lines:
                sections.append((current_id, '\n'.join(current_lines)))
            cont_id = f"{cm.group(1)}({cm.group(2).upper()})/{cm.group(3)}"
            current_id = f"CONT:{cont_id}"
            current_lines = []
            continue

        m = _HEADER_RE.search(stripped)
        if m and '(continued)' not in stripped.lower():
            if current_lines:
                sections.append((current_id, '\n'.join(current_lines)))
            nid = f"{m.group(1)}({m.group(2).upper()})/{m.group(3)}"
            current_id = nid
            current_lines = [stripped]
            continue

        current_lines.append(stripped)

    if current_lines:
        sections.append((current_id, '\n'.join(current_lines)))

    return sections

def parse_tp_pdf(pdf_path: str, start_page: int = 0):
    notice_map: dict[str, dict] = {}
    wk: dict = {'week': None, 'year': None}
    cancelled_ids: set = set()

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i < start_page:
                continue
            text = page.extract_text(layout=True)
            if not text:
                continue

            wk_m = re.search(r'Wk\s*(\d+)/(\d+)', text, re.IGNORECASE)
            if wk_m and not wk['week']:
                wk = {'week': int(wk_m.group(1)), 'year': 2000 + int(wk_m.group(2))}

            for cid in re.findall(r'Former\s+Notice\s+(\d+\s*\(\s*[TP]\s*\)\s*/\s*\d+)\s+is\s+cancelled', text, re.IGNORECASE):
                clean_cid = re.sub(r'\s+', '', cid).upper()
                cancelled_ids.add(clean_cid)

            sections = _split_page_into_sections(text)
            for sec_id, sec_text in sections:
                if sec_id is None:
                    if notice_map:
                        last_key = list(notice_map.keys())[-1]
                        notice_map[last_key]['text'] += '\n' + sec_text
                    continue

                if sec_id.startswith('CONT:'):
                    real_id = sec_id[5:]
                    if real_id in notice_map:
                        notice_map[real_id]['text'] += '\n' + sec_text
                    continue

                first_line = sec_text.split('\n')[0].strip()
                m = _HEADER_RE.search(first_line)
                if not m:
                    continue

                num = int(m.group(1))
                t_p = m.group(2).upper()
                yr_str = m.group(3)
                yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
                full_title = m.group(4).strip().rstrip('.')

                p = full_title.split(' - ')
                notice_map[sec_id] = {
                    'id': sec_id,
                    'number': num,
                    'type': t_p,
                    'year': yr,
                    'title': full_title,
                    'region': p[0].strip() if p else "",
                    'subject': ' - '.join(p[1:]).strip() if len(p) > 1 else "",
                    'text': sec_text,
                }

    notices = list(notice_map.values())
    for n in notices:
        txt = n.get('text', '')
        if len(txt) > 2000:
            txt = txt[:2000] + '...'
        n['text'] = txt.strip()

        n['coordinate_groups'] = _segment_coordinates_from_text(n['text'])
        n['coordinates'] = [c for g in n['coordinate_groups'] for c in g]

        coord_count = len(n['coordinates'])
        if coord_count:
            biggest = max(n['coordinate_groups'], key=len) if n['coordinate_groups'] else n['coordinates']
            n['center_lat'] = round(sum(c[0] for c in biggest) / len(biggest), 5)
            n['center_lon'] = round(sum(c[1] for c in biggest) / len(biggest), 5)
        else:
            n['center_lat'] = n['center_lon'] = None

        biggest_count = max(len(g) for g in n['coordinate_groups']) if n['coordinate_groups'] else 0
        n['geometry_type'] = classify_geometry(n['title'], n['text'], biggest_count)

    return notices, wk, cancelled_ids

def _get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s

def _download_pdf_cached(session: requests.Session, url: str, cache_filename: str) -> str:
    cache_path = os.path.join(CACHE_DIR, cache_filename)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path

    resp = session.get(url, timeout=120)
    resp.raise_for_status()
    with open(cache_path, 'wb') as f:
        f.write(resp.content)
    return cache_path

def _find_link_in_html(html: str, pattern: str) -> str | None:
    soup = BeautifulSoup(html, 'lxml')
    for a in soup.find_all('a', href=True):
        parent_tr = a.find_parent('tr')
        parent_text = parent_tr.get_text() if parent_tr else ""
        anchor_text = a.get_text()
        if re.search(pattern, parent_text, re.IGNORECASE) or re.search(pattern, anchor_text, re.IGNORECASE):
            return unescape(a['href'])
    return None

def _build_full_url(link: str) -> str:
    if link.startswith('/'):
        return f"{UKHO_BASE}{link}"
    if link.startswith('http'):
        return link
    return f"{UKHO_BASE}/{link}"

def scrape_annual(session: requests.Session | None = None) -> tuple[list, set]:
    if session is None:
        session = _get_session()
    try:
        print("🔍 Baseline: Annual T&P linki taranıyor...")
        resp = session.get(UKHO_ANNUAL_URL, timeout=30)
        resp.raise_for_status()

        link = _find_link_in_html(resp.text, r'Temporary\s+and\s+Preliminary\s+Notices')
        if not link:
            return [], set()

        pdf_url = _build_full_url(link)
        cache_name = "annual_tp_2026.pdf"
        pdf_path = _download_pdf_cached(session, pdf_url, cache_name)

        notices, _, cancelled = parse_tp_pdf(pdf_path, start_page=12)
        print(f"✅ Annual Baseline Hazır: {len(notices)} duyuru eklendi.")
        return notices, cancelled
    except Exception as e:
        print(f"⚠️ Annual PDF indirilemedi ({e}), haftalık bültenlerle devam ediliyor...")
        return [], set()

def scrape_single_week(session: requests.Session, year: int, week: int) -> tuple[list, set, bool]:
    """Haftalık bülteni çeker. Başarılıysa (notices, cancelled, True) döner."""
    cache_name = f"week_{year}_{week:02d}.pdf"
    cache_path = os.path.join(CACHE_DIR, cache_name)

    # Önce disk kontrolü
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        try:
            notices, _, cancelled = parse_tp_pdf(cache_path)
            return notices, cancelled, True
        except Exception:
            pass

    # Disk'te yoksa web'den indir
    try:
        resp = session.post(
            UKHO_WEEKLY_URL,
            data={'year': str(year), 'week': str(week)},
            timeout=30,
        ) if week > 0 else session.get(UKHO_WEEKLY_URL, timeout=30)
        
        resp.raise_for_status()
        link = _find_link_in_html(resp.text, r'snii')
        if not link:
            return [], set(), False

        pdf_url = _build_full_url(link)
        pdf_path = _download_pdf_cached(session, pdf_url, cache_name)
        notices, _, cancelled = parse_tp_pdf(pdf_path)
        return notices, cancelled, True
    except Exception:
        return [], set(), False

def save_json_file(all_notices: dict, all_cancelled: set, current_week: int, current_year: int):
    """Anlık eldeki verilerle tp_notices.json dosyasını kaydeder."""
    notices_copy = dict(all_notices)
    for cid in all_cancelled:
        notices_copy.pop(cid, None)

    final_notices = sorted(notices_copy.values(), key=lambda x: (x['year'], x['number']))
    with_coords = sum(1 for n in final_notices if n.get('coordinates'))

    data = {
        'source': 'UKHO Annual + Weekly Section II',
        'baseline': f'Annual T&P {current_year}',
        'latest_week': current_week,
        'year': current_year,
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'total': len(final_notices),
        'with_coords': with_coords,
        'cancelled_count': len(all_cancelled),
        'notices': final_notices,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data

def scrape_full() -> dict:
    session = _get_session()
    html = session.get(UKHO_WEEKLY_URL, timeout=30).text
    wk_match = re.search(r'hdnWeek.*?value="(\d+)"', html)
    yr_match = re.search(r'hdnYear.*?value="(\d+)"', html)
    current_week = int(wk_match.group(1)) if wk_match else 38
    current_year = int(yr_match.group(1)) if yr_match else 2026

    all_notices: dict[str, dict] = {}
    all_cancelled: set = set()

    # 1. Baseline
    annual_notices, annual_cancelled = scrape_annual(session)
    for n in annual_notices:
        all_notices[n['id']] = n
    all_cancelled.update(annual_cancelled)

    # 2. İlk Tarama Turu
    missing_weeks = []
    print(f"🔄 Haftalık T&P bültenleri taranıyor (1 - {current_week})...")
    for week in range(1, current_week + 1):
        w_notices, w_cancel, success = scrape_single_week(session, current_year, week)
        if success:
            for n in w_notices:
                all_notices[n['id']] = n
            all_cancelled.update(w_cancel)
        else:
            missing_weeks.append(week)

    # 3. KADEMELİ KAYIT (Anında JSON Oluştur)
    current_data = save_json_file(all_notices, all_cancelled, current_week, current_year)
    print(f"⚡ Kademeli Kayıt Yapıldı: {current_data['total']} aktif T&P harita dosyasına yazıldı.")

    # 4. İNATÇI TAKİP DÖNGÜSÜ (Eksik Haftalar Varsa Arka Plan Takibi)
    if missing_weeks:
        print(f"\n⚠️ UKHO sunucusu nedeniyle {len(missing_weeks)} hafta çekilemedi: {missing_weeks}")
        print("🎯 İnatçı Takip Başlatıldı! Eksik haftalar sökülene kadar deneniyor...")

        retry_count = 0
        while missing_weeks:
            retry_count += 1
            print(f"⏳ Deneme #{retry_count} - Kalan eksik haftalar: {missing_weeks} (5 sn bekleniyor)...")
            time.sleep(5)

            still_missing = []
            new_data_acquired = False

            for week in missing_weeks:
                w_notices, w_cancel, success = scrape_single_week(session, current_year, week)
                if success:
                    print(f"🎉 BAŞARILI! Hafta {week}/{current_year} çekildi ve eklendi.")
                    for n in w_notices:
                        all_notices[n['id']] = n
                    all_cancelled.update(w_cancel)
                    new_data_acquired = True
                else:
                    still_missing.append(week)

            missing_weeks = still_missing

            # Yeni veri alındıysa JSON'u anında tazele!
            if new_data_acquired:
                current_data = save_json_file(all_notices, all_cancelled, current_week, current_year)
                print(f"🔄 JSON Güncellendi! Yeni Toplam Aktif T&P: {current_data['total']}")

        print("✨ TEBRİKLER! Tüm haftalar %100 eksiksiz tamamlandı.")

    return current_data

if __name__ == "__main__":
    print("🚀 T&P Scraper Başlatıldı...")
    data = scrape_full()

    print("\n================ SEYİR RAPORU ================")
    print(f"✅ Toplam Aktif T&P Duyurusu : {data['total']}")
    print(f"📍 Haritada Çizilebilir     : {data['with_coords']}")
    print(f"🗑️ İptal Edilen/Kalkan      : {data['cancelled_count']}")
    print(f"💾 JSON Dosya Konumu        : {DATA_FILE}")
    print("==============================================")