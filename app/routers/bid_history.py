from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from db import get_conn, get_pg_conn, pg_available

router = APIRouter(prefix="/api/bid_history", tags=["낙찰이력"])


class BidRecord(BaseModel):
    address:    str
    bdong_cd:   Optional[str]   = None
    bun:        Optional[int]   = None
    ji:         Optional[int]   = None
    bldg_type:  Optional[str]   = None
    bldg_name:  Optional[str]   = None
    floor_no:   Optional[str]   = None
    ho_no:      Optional[str]   = None
    excl_area:  Optional[float] = None
    bid_price:  int
    ref_price:  Optional[int]   = None
    hug_limit:  Optional[int]   = None
    tax_rate:   Optional[float] = None
    tax_amount: Optional[int]   = None
    total_cost: Optional[int]   = None
    hug_rate:   Optional[float] = None
    ref_rate:   Optional[float] = None
    hug_diff:   Optional[int]   = None
    ref_diff:   Optional[int]   = None
    per_m2:     Optional[int]   = None
    note:       Optional[str]   = None


_CREATE_SQL_PG = """
CREATE TABLE IF NOT EXISTS bid_history (
    id         SERIAL PRIMARY KEY,
    saved_at   TEXT NOT NULL,
    address    TEXT NOT NULL,
    bdong_cd   TEXT, bun INTEGER, ji INTEGER,
    bldg_type  TEXT, bldg_name TEXT, floor_no TEXT, ho_no TEXT,
    excl_area  REAL,
    bid_price  INTEGER NOT NULL,
    ref_price  INTEGER, hug_limit INTEGER,
    tax_rate   REAL, tax_amount INTEGER, total_cost INTEGER,
    hug_rate   REAL, ref_rate REAL, hug_diff INTEGER, ref_diff INTEGER,
    per_m2     INTEGER, note TEXT
)
"""

_CREATE_SQL_SQLITE = _CREATE_SQL_PG.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

_INSERT_COLS = """
    (saved_at, address, bdong_cd, bun, ji, bldg_type, bldg_name,
     floor_no, ho_no, excl_area, bid_price, ref_price, hug_limit,
     tax_rate, tax_amount, total_cost, hug_rate, ref_rate,
     hug_diff, ref_diff, per_m2, note)
"""


def _row_vals(saved_at: str, r: BidRecord):
    return (saved_at, r.address, r.bdong_cd, r.bun, r.ji,
            r.bldg_type, r.bldg_name, r.floor_no, r.ho_no, r.excl_area,
            r.bid_price, r.ref_price, r.hug_limit,
            r.tax_rate, r.tax_amount, r.total_cost,
            r.hug_rate, r.ref_rate, r.hug_diff, r.ref_diff, r.per_m2,
            r.note)


# ── POST /api/bid_history ─────────────────────────────────────
@router.post("")
def save_bid(records: list[BidRecord]):
    saved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if pg_available():
        import psycopg2.extras
        conn = get_pg_conn()
        cur  = conn.cursor()
        cur.execute(_CREATE_SQL_PG)
        ph   = "(" + ",".join(["%s"] * 22) + ")"
        ids  = []
        for r in records:
            cur.execute(f"INSERT INTO bid_history {_INSERT_COLS} VALUES {ph} RETURNING id",
                        _row_vals(saved_at, r))
            ids.append(cur.fetchone()[0])
        conn.commit()
        cur.close(); conn.close()
    else:
        conn = get_conn()
        conn.execute(_CREATE_SQL_SQLITE)
        ph   = "(" + ",".join(["?"] * 22) + ")"
        ids  = []
        for r in records:
            cur = conn.execute(f"INSERT INTO bid_history {_INSERT_COLS} VALUES {ph}",
                               _row_vals(saved_at, r))
            ids.append(cur.lastrowid)
        conn.commit(); conn.close()

    return {"saved": len(ids), "ids": ids}


# ── GET /api/bid_history ──────────────────────────────────────
@router.get("")
def list_bids(
    address: Optional[str] = Query(None),
    limit:   int           = Query(200, le=500),
):
    if pg_available():
        import psycopg2.extras
        conn = get_pg_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_CREATE_SQL_PG)
        if address:
            cur.execute(
                "SELECT * FROM bid_history WHERE address LIKE %s ORDER BY saved_at DESC, id DESC LIMIT %s",
                (f"%{address}%", limit))
        else:
            cur.execute(
                "SELECT * FROM bid_history ORDER BY saved_at DESC, id DESC LIMIT %s",
                (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
    else:
        conn = get_conn()
        conn.execute(_CREATE_SQL_SQLITE)
        if address:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM bid_history WHERE address LIKE ? ORDER BY saved_at DESC, id DESC LIMIT ?",
                (f"%{address}%", limit)).fetchall()]
        else:
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM bid_history ORDER BY saved_at DESC, id DESC LIMIT ?",
                (limit,)).fetchall()]
        conn.close()

    return rows


# ── DELETE /api/bid_history/{id} ──────────────────────────────
@router.delete("/{bid_id}")
def delete_bid(bid_id: int):
    if pg_available():
        conn = get_pg_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM bid_history WHERE id=%s", (bid_id,))
        conn.commit(); cur.close(); conn.close()
    else:
        conn = get_conn()
        conn.execute("DELETE FROM bid_history WHERE id=?", (bid_id,))
        conn.commit(); conn.close()
    return {"deleted": bid_id}


# ── DELETE /api/bid_history?address=... ───────────────────────
@router.delete("")
def delete_all_bids(address: str = Query(...)):
    if pg_available():
        conn = get_pg_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM bid_history WHERE address LIKE %s", (f"%{address}%",))
        n = cur.rowcount
        conn.commit(); cur.close(); conn.close()
    else:
        conn = get_conn()
        cur = conn.execute("DELETE FROM bid_history WHERE address LIKE ?", (f"%{address}%",))
        n = cur.rowcount
        conn.commit(); conn.close()
    return {"deleted": n}
