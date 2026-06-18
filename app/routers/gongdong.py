from fastapi import APIRouter, Query
from db import get_conn

router = APIRouter(prefix="/api/gongdong", tags=["공동주택가격"])

@router.get("")
def search_gongdong(
    dong_nm: str = Query(..., description="법정동명 (예: 온천동)"),
    bun: int = Query(..., description="지번 본번"),
    ji: int = Query(0, description="지번 부번"),
    ho_nm: str = Query(None, description="호명 (예: 801)")
):
    conn = get_conn()
    sql = """
        SELECT danji_nm, dong_nm, dong, floor, ho_nm, excl_area, price
        FROM gongdong
        WHERE dong_nm LIKE ? AND bun=? AND ji=?
    """
    params = [f'%{dong_nm}%', bun, ji]
    if ho_nm:
        sql += " AND ho_nm=?"
        params.append(ho_nm)
    sql += " ORDER BY dong, floor, ho_nm LIMIT 500"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"count": len(rows), "items": [dict(r) for r in rows]}
