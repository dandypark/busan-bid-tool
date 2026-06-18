import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MOLIT_API_KEY, BLDG_API_URL
from db import get_conn

STRCT_MAP = {
    '11': 2, '12': 1, '13': 8, '14': 4, '15': 3,
    '16': 4, '17': 4, '18': 4, '19': 5, '20': 6,
    '21': 4, '22': 4,
    '42': 1,  # 철골철근콘크리트조 → 일람표 구조번호 1
}

def _illamtable_strct_no(strct_cd: str) -> int:
    return STRCT_MAP.get(str(strct_cd), 4)


def get_bldg_info(sigungu_cd: str, bjdong_cd: str, bun: str, ji: str) -> dict | None:
    conn = get_conn()
    cached = conn.execute(
        "SELECT * FROM bldg_cache WHERE sigungu_cd=? AND bjdong_cd=? AND bun=? AND ji=?",
        (sigungu_cd, bjdong_cd, bun, ji)
    ).fetchone()
    conn.close()

    if cached:
        return dict(cached)

    url = f"{BLDG_API_URL}/getBrTitleInfo"
    params = {
        "serviceKey": MOLIT_API_KEY,
        "pageNo": "1", "numOfRows": "1",
        "sigunguCd": sigungu_cd, "bjdongCd": bjdong_cd,
        "bun": bun.zfill(4), "ji": ji.zfill(4),
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        tree = ET.fromstring(resp.text)
        item = tree.find('.//item')
        if item is None:
            return None

        def t(tag): return (item.findtext(tag) or '').strip()

        result = {
            "sigungu_cd": sigungu_cd, "bjdong_cd": bjdong_cd,
            "bun": bun, "ji": ji,
            "cached_at": datetime.now().strftime('%Y-%m-%d'),
            "strct_cd": t('strctCd'),
            "strct_nm": t('strctCdNm'),
            "use_apr_day": t('useAprDay'),
            "plat_area": float(t('platArea') or 0),
            "tot_area": float(t('totArea') or 0),
            "main_purps": t('mainPurpsCdNm'),
        }
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO bldg_cache "
            "(sigungu_cd,bjdong_cd,bun,ji,cached_at,strct_cd,strct_nm,"
            "use_apr_day,plat_area,tot_area,main_purps) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            list(result.values())
        )
        conn.commit()
        conn.close()
        return result
    except Exception:
        return None


def get_illamtable_strct_no(strct_cd: str) -> int:
    return _illamtable_strct_no(strct_cd)
