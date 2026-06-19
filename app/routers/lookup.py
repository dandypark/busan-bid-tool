from fastapi import APIRouter, Query
from db import get_conn
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MOLIT_API_KEY, BLDG_API_URL

router = APIRouter(prefix="/api/lookup", tags=["통합조회"])

BUSAN_GU = {
    '26110': '중구', '26140': '서구', '26170': '동구', '26200': '영도구',
    '26230': '부산진구', '26260': '동래구', '26290': '남구', '26320': '북구',
    '26350': '해운대구', '26380': '사하구', '26410': '금정구', '26440': '강서구',
    '26470': '연제구', '26500': '수영구', '26530': '사상구', '26710': '기장군',
}

OFFICETEL_KW = ['오피스텔', '업무시설']
GONGDONG_KW  = ['다세대', '연립', '아파트', '공동주택']

def _classify(main_purps: str) -> str:
    for k in OFFICETEL_KW:
        if k in main_purps:
            return '오피스텔'
    for k in GONGDONG_KW:
        if k in main_purps:
            return '공동주택'
    return '기타'


def _get_bldg_info(sigungu_cd: str, bjdong_cd: str, bun: str, ji: str) -> dict | None:
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
        resp = requests.get(url, params=params, timeout=3)
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


@router.get("/search")
def search_building(q: str = Query(..., min_length=1)):
    """건물명으로 검색 — 자동완성용"""
    conn = get_conn()
    kw = f'%{q}%'
    starts = f'{q}%'

    def jibun(bun, ji): return f'{bun}-{ji}' if ji else str(bun)

    # 공동주택 — idx_gongdong_danji 인덱스 활용 (prefix LIKE)
    gd = conn.execute("""
        SELECT danji_nm AS name, sigungu, dong_nm,
               bdong_cd, bun, ji, '공동주택' AS btype
        FROM gongdong
        WHERE danji_nm LIKE ?
        GROUP BY danji_nm, sigungu, dong_nm, bdong_cd, bun, ji
        ORDER BY danji_nm
        LIMIT 10
    """, (starts,)).fetchall()

    # 오피스텔 — idx_gigjungsi_bldg 인덱스 활용 (prefix LIKE)
    gj = conn.execute("""
        SELECT bldg_name AS name, bdong_cd, bun, ji, '오피스텔' AS btype
        FROM gigjungsi
        WHERE bldg_name LIKE ?
        GROUP BY bldg_name, bdong_cd, bun, ji
        ORDER BY bldg_name
        LIMIT 10
    """, (starts,)).fetchall()

    # prefix로 결과 부족하면 중간 포함 검색 추가
    if len(gd) < 5:
        gd2 = conn.execute("""
            SELECT danji_nm AS name, sigungu, dong_nm,
                   bdong_cd, bun, ji, '공동주택' AS btype
            FROM gongdong
            WHERE danji_nm LIKE ? AND danji_nm NOT LIKE ?
            GROUP BY danji_nm, sigungu, dong_nm, bdong_cd, bun, ji
            ORDER BY danji_nm
            LIMIT ?
        """, (kw, starts, 10 - len(gd))).fetchall()
        gd = list(gd) + list(gd2)

    if len(gj) < 5:
        gj2 = conn.execute("""
            SELECT bldg_name AS name, bdong_cd, bun, ji, '오피스텔' AS btype
            FROM gigjungsi
            WHERE bldg_name LIKE ? AND bldg_name NOT LIKE ?
            GROUP BY bldg_name, bdong_cd, bun, ji
            ORDER BY bldg_name
            LIMIT ?
        """, (kw, starts, 10 - len(gj))).fetchall()
        gj = list(gj) + list(gj2)

    conn.close()

    gd_list = []
    for r in gd:
        d = dict(r)
        sg = d.pop('sigungu', '')
        dn = d.pop('dong_nm', '')
        d['addr'] = ' '.join(p for p in [sg, dn, jibun(d['bun'], d['ji'])] if p)
        gd_list.append(d)

    gj_list = []
    for r in gj:
        d = dict(r)
        gu = BUSAN_GU.get(d['bdong_cd'][:5], '')
        d['addr'] = ' '.join(p for p in [gu, jibun(d['bun'], d['ji'])] if p)
        gj_list.append(d)

    results = gd_list + gj_list
    results.sort(key=lambda x: (0 if x['bdong_cd'].startswith('26') else 1, x['name']))
    return {"results": results[:20]}


@router.get("")
def lookup(
    bdong_cd: str = Query(..., description="법정동코드 10자리"),
    bun: int = Query(...),
    ji: int = Query(0),
):
    sigungu_cd = bdong_cd[:5]
    bjdong_cd  = bdong_cd[5:10]

    bldg = _get_bldg_info(sigungu_cd, bjdong_cd, str(bun), str(ji))
    bldg_type = _classify(bldg.get('main_purps', '') if bldg else '')

    conn = get_conn()

    gj_rows = conn.execute(
        "SELECT bldg_name, dong_nm, floor_no, ho_no, price, excl_area, share_area, "
        "excl_area + share_area as bldg_area, "
        "CAST(price * (excl_area + share_area) AS INTEGER) as total_price "
        "FROM gigjungsi WHERE bdong_cd=? AND bun=? AND ji=? ORDER BY floor_no, ho_no",
        (bdong_cd, bun, ji)
    ).fetchall()

    gd_rows = conn.execute(
        "SELECT danji_nm, dong_nm, dong, floor, ho_nm, excl_area, price "
        "FROM gongdong WHERE bdong_cd=? AND bun=? AND ji=? ORDER BY dong, floor, ho_nm",
        (bdong_cd, bun, ji)
    ).fetchall()

    gongsi_row = conn.execute(
        "SELECT price FROM gongsi WHERE bdong_cd=? AND bun=? AND ji=? ORDER BY base_year DESC LIMIT 1",
        (bdong_cd, bun, ji)
    ).fetchone()

    conn.close()

    gigjungsi_items = [dict(r) for r in gj_rows]
    gongdong_items  = [dict(r) for r in gd_rows]
    gongsi_price    = gongsi_row['price'] if gongsi_row else None

    has_gj = len(gigjungsi_items) > 0
    has_gd = len(gongdong_items)  > 0

    if has_gj and has_gd:
        bldg_type = '혼합'
    elif has_gj:
        bldg_type = '오피스텔'
    elif has_gd:
        bldg_type = '공동주택'

    return {
        "bldg_type": bldg_type,
        "bldg_info": bldg,
        "gongsi_price": gongsi_price,
        "gigjungsi_count": len(gigjungsi_items),
        "gongdong_count":  len(gongdong_items),
        "gigjungsi_items": gigjungsi_items,
        "gongdong_items":  gongdong_items,
    }
