import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from db import get_conn
from config import GONGSI_CSV

def load():
    conn = get_conn()
    conn.execute("DELETE FROM gongsi")
    conn.commit()

    df = pd.read_csv(GONGSI_CSV, encoding='cp949', dtype=str)
    rows = []
    for _, r in df.iterrows():
        jibun = str(r['지번']).strip()
        parts = jibun.replace('-', ' ').split()
        bun = int(parts[0]) if parts and parts[0].isdigit() else 0
        ji  = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        rows.append((
            r['고유번호'],
            str(r['법정동코드']).zfill(10),
            r['법정동명'],
            jibun,
            bun, ji,
            int(r['기준연도']),
            int(float(r['공시지가']))
        ))

    conn.executemany(
        "INSERT INTO gongsi (unique_no,bdong_cd,dong_nm,jibun,bun,ji,base_year,price) "
        "VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"공시지가 적재 완료: 총 {len(rows):,}건")

if __name__ == "__main__":
    load()
