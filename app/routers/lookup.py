from fastapi import APIRouter, Query
from db import get_conn
from services.bldg_api import get_bldg_info
from services.siga_calc import get_siga_info

router = APIRouter(prefix="/api/lookup", tags=["통합조회"])

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


@router.get("")
def lookup(
    bdong_cd: str = Query(..., description="법정동코드 10자리"),
    bun: int = Query(...),
    ji: int = Query(0),
):
    sigungu_cd = bdong_cd[:5]
    bjdong_cd  = bdong_cd[5:10]

    bldg = get_bldg_info(sigungu_cd, bjdong_cd, str(bun), str(ji))
    bldg_type = _classify(bldg.get('main_purps', '') if bldg else '')

    conn = get_conn()

    # 두 테이블 항상 모두 조회
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

    conn.close()

    gigjungsi_items = [dict(r) for r in gj_rows]
    gongdong_items  = [dict(r) for r in gd_rows]

    # 실제 데이터 기반으로 유형 재분류 (혼합 건물 포함)
    has_gj = len(gigjungsi_items) > 0
    has_gd = len(gongdong_items)  > 0

    if has_gj and has_gd:
        bldg_type = '혼합'
    elif has_gj:
        bldg_type = '오피스텔'
    elif has_gd:
        bldg_type = '공동주택'
    # else: 건축물대장 기반 유형 그대로 유지

    return {
        "bldg_type": bldg_type,
        "bldg_info": bldg,
        "gigjungsi_count": len(gigjungsi_items),
        "gongdong_count":  len(gongdong_items),
        "gigjungsi_items": gigjungsi_items,
        "gongdong_items":  gongdong_items,
    }


@router.get("/siga_info")
def siga_info_route(
    bdong_cd: str = Query(...),
    bun: int = Query(...),
    ji: int = Query(0),
    after_june: bool = Query(False),
):
    return get_siga_info(bdong_cd, bun, ji, after_june)
