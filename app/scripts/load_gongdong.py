import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_conn
from config import GONGDONG_DIR

def load():
    conn = get_conn()
    conn.execute("DELETE FROM gongdong")
    conn.commit()

    txt_files = sorted(Path(GONGDONG_DIR).glob("공동주택가격_부산_*.txt"))
    total = 0
    for fpath in txt_files:
        rows = []
        with open(fpath, encoding='cp949') as f:
            for line in f:
                c = line.rstrip('\n').split('|')
                if len(c) < 23:
                    continue
                try:
                    rows.append((
                        int(c[0]),
                        c[2],
                        c[5].zfill(10),
                        c[7],
                        c[8],
                        c[9],
                        int(c[13]) if c[13].strip().isdigit() else 0,
                        int(c[14]) if c[14].strip().isdigit() else 0,
                        c[16],
                        c[17],
                        int(c[18]) if c[18].strip().lstrip('-').isdigit() else 0,
                        c[19],
                        c[20],
                        float(c[21]) if c[21].strip() else 0.0,
                        int(c[22])   if c[22].strip().isdigit() else 0,
                    ))
                except Exception:
                    continue
        conn.executemany(
            "INSERT INTO gongdong (base_year,bldg_mgmt_no,bdong_cd,sido,sigungu,"
            "dong_nm,bun,ji,danji_nm,dong,floor,ho,ho_nm,excl_area,price) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        total += len(rows)
        print(f"  {fpath.name}: {len(rows):,}건")

    conn.close()
    print(f"공동주택가격 적재 완료: 총 {total:,}건")

if __name__ == "__main__":
    load()
