from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from db import get_pg_conn, pg_available

router = APIRouter(prefix="/api/bid_history", tags=["낙찰이력"])


# ── 테이블 초기화 ──────────────────────────────────────────────
def ensure_table():
    conn = get_pg_conn()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bid_history (
                    id          SERIAL PRIMARY KEY,
                    saved_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    address     TEXT NOT NULL,
                    bldg_type   TEXT,
                    bldg_name   TEXT,
                    floor_no    TEXT,
                    ho_no       TEXT,
                    excl_area   REAL,
                    bid_price   BIGINT,
                    ref_price   BIGINT,
                    hug_limit   BIGINT,
                    tax_rate    REAL,
                    tax_amount  BIGINT,
                    total_cost  BIGINT,
                    hug_rate    REAL,
                    ref_rate    REAL,
                    hug_diff    BIGINT,
                    ref_diff    BIGINT,
                    per_m2      BIGINT,
                    note        TEXT
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_bh_address ON bid_history(address)"
            )
        conn.commit()
    finally:
        conn.close()


# ── 스키마 ─────────────────────────────────────────────────────
class BidRecord(BaseModel):
    address: str
    bldg_type: Optional[str] = None
    bldg_name: Optional[str] = None
    floor_no: Optional[str] = None
    ho_no: Optional[str] = None
    excl_area: Optional[float] = None
    bid_price: Optional[int] = None
    ref_price: Optional[int] = None
    hug_limit: Optional[int] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[int] = None
    total_cost: Optional[int] = None
    hug_rate: Optional[float] = None
    ref_rate: Optional[float] = None
    hug_diff: Optional[int] = None
    ref_diff: Optional[int] = None
    per_m2: Optional[int] = None
    note: Optional[str] = None


# ── 저장 ───────────────────────────────────────────────────────
@router.post("", status_code=201)
def save_bids(records: list[BidRecord]):
    if not pg_available():
        raise HTTPException(503, detail="DB 미설정 — DATABASE_URL 환경변수를 확인하세요")
    if not records:
        raise HTTPException(400, detail="저장할 데이터가 없습니다")

    conn = get_pg_conn()
    if conn is None:
        raise HTTPException(503, detail="DB 연결 실패")
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO bid_history
                    (address, bldg_type, bldg_name, floor_no, ho_no, excl_area,
                     bid_price, ref_price, hug_limit, tax_rate, tax_amount, total_cost,
                     hug_rate, ref_rate, hug_diff, ref_diff, per_m2, note)
                VALUES
                    (%(address)s, %(bldg_type)s, %(bldg_name)s, %(floor_no)s, %(ho_no)s,
                     %(excl_area)s, %(bid_price)s, %(ref_price)s, %(hug_limit)s,
                     %(tax_rate)s, %(tax_amount)s, %(total_cost)s,
                     %(hug_rate)s, %(ref_rate)s, %(hug_diff)s, %(ref_diff)s,
                     %(per_m2)s, %(note)s)
                """,
                [r.model_dump() for r in records],
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=f"저장 중 오류: {e}")
    finally:
        conn.close()

    return {"saved": len(records)}


# ── 조회 ───────────────────────────────────────────────────────
@router.get("")
def list_bids(
    address: str = Query(""),
    limit: int = Query(300, le=1000),
):
    if not pg_available():
        raise HTTPException(503, detail="DB 미설정")

    conn = get_pg_conn()
    if conn is None:
        raise HTTPException(503, detail="DB 연결 실패")
    try:
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if address:
                cur.execute(
                    "SELECT * FROM bid_history WHERE address ILIKE %s ORDER BY saved_at DESC LIMIT %s",
                    (f"%{address}%", limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM bid_history ORDER BY saved_at DESC LIMIT %s",
                    (limit,),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [dict(r) for r in rows]


# ── 단건 삭제 ──────────────────────────────────────────────────
@router.delete("/{record_id}", status_code=204)
def delete_bid(record_id: int):
    if not pg_available():
        raise HTTPException(503, detail="DB 미설정")

    conn = get_pg_conn()
    if conn is None:
        raise HTTPException(503, detail="DB 연결 실패")
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bid_history WHERE id = %s", (record_id,))
        conn.commit()
    finally:
        conn.close()


# ── 주소별 전체 삭제 ───────────────────────────────────────────
@router.delete("", status_code=204)
def delete_by_address(address: str = Query(...)):
    if not pg_available():
        raise HTTPException(503, detail="DB 미설정")

    conn = get_pg_conn()
    if conn is None:
        raise HTTPException(503, detail="DB 연결 실패")
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bid_history WHERE address = %s", (address,))
        conn.commit()
    finally:
        conn.close()
