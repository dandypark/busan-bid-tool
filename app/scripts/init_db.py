import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS gigjungsi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bldg_no INTEGER, type_nm TEXT, bdong_cd TEXT,
    bun INTEGER, ji INTEGER, bldg_name TEXT,
    dong_nm TEXT, floor_gb TEXT, floor_no TEXT,
    ho_no TEXT, price INTEGER, excl_area REAL, share_area REAL
);
CREATE INDEX IF NOT EXISTS idx_gigjungsi_addr ON gigjungsi(bdong_cd, bun, ji);
CREATE INDEX IF NOT EXISTS idx_gigjungsi_bldg ON gigjungsi(bldg_name, ho_no);

CREATE TABLE IF NOT EXISTS gongdong (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_year INTEGER, bldg_mgmt_no TEXT, bdong_cd TEXT,
    sido TEXT, sigungu TEXT, dong_nm TEXT,
    bun INTEGER, ji INTEGER, danji_nm TEXT,
    dong TEXT, floor INTEGER, ho TEXT, ho_nm TEXT,
    excl_area REAL, price INTEGER
);
CREATE INDEX IF NOT EXISTS idx_gongdong_addr ON gongdong(bdong_cd, bun, ji);
CREATE INDEX IF NOT EXISTS idx_gongdong_danji ON gongdong(danji_nm, dong, ho_nm);

CREATE TABLE IF NOT EXISTS gongsi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_no TEXT, bdong_cd TEXT, dong_nm TEXT,
    jibun TEXT, bun INTEGER, ji INTEGER,
    base_year INTEGER, price INTEGER
);
CREATE INDEX IF NOT EXISTS idx_gongsi_addr ON gongsi(bdong_cd, bun, ji);

CREATE TABLE IF NOT EXISTS bldg_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigungu_cd TEXT, bjdong_cd TEXT, bun TEXT, ji TEXT,
    cached_at TEXT, strct_cd TEXT, strct_nm TEXT,
    use_apr_day TEXT, plat_area REAL, tot_area REAL, main_purps TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bldg_cache
    ON bldg_cache(sigungu_cd, bjdong_cd, bun, ji);
"""

if __name__ == "__main__":
    conn = get_conn()
    for stmt in DDL.strip().split(";"):
        s = stmt.strip()
        if s:
            conn.execute(s)
    conn.commit()
    conn.close()
    print("DB 스키마 생성 완료")
