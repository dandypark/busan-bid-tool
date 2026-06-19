import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from db import get_conn
from config import GIGJUNGSI_XLSX

COLS = ['bldg_no','type_nm','고시일자','bdong_cd','특수지코드','bun','ji',
        'bldg_name','dong_nm','floor_gb','floor_no','ho_no','price','excl_area','share_area']

def load():
    conn = get_conn()
    conn.execute("DELETE FROM gigjungsi")
    conn.commit()

    total = 0
    for sheet in ['1','2','3','4','5']:
        print(f"  시트 {sheet} 로딩 중...")
        df = pd.read_excel(GIGJUNGSI_XLSX, sheet_name=sheet, header=0)
        df.columns = COLS
        df['bdong_cd'] = df['bdong_cd'].astype(str).str.zfill(10)
        df = df[df['bdong_cd'].str.startswith('26')].copy()
        df['bun'] = pd.to_numeric(df['bun'], errors='coerce').fillna(0).astype(int)
        df['ji']  = pd.to_numeric(df['ji'],  errors='coerce').fillna(0).astype(int)
        rows = df[['bldg_no','type_nm','bdong_cd','bun','ji','bldg_name',
                   'dong_nm','floor_gb','floor_no','ho_no','price',
                   'excl_area','share_area']].values.tolist()
        conn.executemany(
            "INSERT INTO gigjungsi (bldg_no,type_nm,bdong_cd,bun,ji,bldg_name,"
            "dong_nm,floor_gb,floor_no,ho_no,price,excl_area,share_area) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()
        total += len(rows)
        print(f"    -> 부산 {len(rows):,}건 적재")

    conn.close()
    print(f"기준시가 적재 완료: 총 {total:,}건")

if __name__ == "__main__":
    load()
