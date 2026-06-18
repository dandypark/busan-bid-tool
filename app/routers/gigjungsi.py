from fastapi import APIRouter, Query
from db import get_conn

router = APIRouter(prefix="/api/gigjungsi", tags=["기준시가"])

@router.get("")
def search_gigjungsi(
    dong_nm: str = Query(..., description="법정동명 (예: 온천동)"),
    bun: int = Query(..., description="지번 본번"),
    ji: int = Query(0, description="지번 부번"),
    ho_no: str = Query(None, description="호 (예: 801)")
):
    conn = get_conn()
    sql = """
        SELECT g.bldg_name, g.dong_nm, g.floor_no, g.ho_no, g.price,
               g.excl_area, g.share_area,
               g.excl_area + g.share_area as bldg_area,
               CAST(g.price * (g.excl_area + g.share_area) AS INTEGER) as total_price
        FROM gigjungsi g
        WHERE g.bun=? AND g.ji=?
          AND g.bdong_cd IN (
              SELECT bdong_cd FROM gongsi WHERE dong_nm LIKE ?
              UNION
              SELECT bdong_cd FROM gongdong WHERE dong_nm LIKE ?
          )
    """
    params = [bun, ji, f'%{dong_nm}%', f'%{dong_nm}%']
    if ho_no:
        sql += " AND g.ho_no=?"
        params.append(ho_no)
    sql += " ORDER BY g.floor_no, g.ho_no"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"count": len(rows), "items": [dict(r) for r in rows]}


@router.get("/search")
def search_by_name(
    bldg_name: str = Query(..., description="건물명 검색어"),
    ho_no: str = Query(None, description="호수")
):
    conn = get_conn()
    sql = ("SELECT bldg_name, dong_nm, floor_no, ho_no, price, excl_area, share_area, "
           "excl_area+share_area as bldg_area, "
           "CAST(price*(excl_area+share_area) AS INTEGER) as total_price "
           "FROM gigjungsi WHERE bldg_name LIKE ? AND type_nm='오피스텔'")
    params = [f'%{bldg_name}%']
    if ho_no:
        sql += " AND ho_no=?"
        params.append(ho_no)
    sql += " ORDER BY floor_no, ho_no LIMIT 200"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"count": len(rows), "items": [dict(r) for r in rows]}
