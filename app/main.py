from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from routers import gigjungsi, gongdong, lookup, bid_history
from db import get_conn

app = FastAPI(title="부산 부동산 가격 조회")


@app.on_event("startup")
def build_search_index():
    """건물명 요약 테이블 생성 — 첫 기동 시 1회만 수행"""
    conn = get_conn()
    exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='buildings_idx'"
    ).fetchone()[0]
    if not exists:
        print("buildings_idx 생성 중...")
        conn.execute("""
            CREATE TABLE buildings_idx AS
            SELECT danji_nm AS name, sigungu, dong_nm,
                   bdong_cd, MIN(bun) AS bun, MIN(ji) AS ji,
                   '공동주택' AS btype
            FROM gongdong
            GROUP BY danji_nm, sigungu, dong_nm, bdong_cd
            UNION ALL
            SELECT bldg_name AS name, '' AS sigungu, '' AS dong_nm,
                   bdong_cd, MIN(bun) AS bun, MIN(ji) AS ji,
                   '오피스텔' AS btype
            FROM gigjungsi
            GROUP BY bldg_name, bdong_cd
        """)
        conn.execute("CREATE INDEX idx_bidx_name ON buildings_idx(name)")
        conn.commit()
        print("buildings_idx 완료")
    conn.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gigjungsi.router)
app.include_router(gongdong.router)
app.include_router(lookup.router)
app.include_router(bid_history.router)

app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
