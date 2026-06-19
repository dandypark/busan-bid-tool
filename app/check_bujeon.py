import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from db import get_conn

conn = get_conn()

print("=== 온천동 SK 오피스텔 샘플 ===")
rows = conn.execute("""
    SELECT floor_no, ho_no, excl_area, share_area,
           ROUND(share_area/excl_area, 3) as share_ratio
    FROM gigjungsi WHERE bdong_cd='2626010800' AND bun=1410 AND ji=5
    ORDER BY CAST(floor_no AS INT) LIMIT 10
""").fetchall()
for r in rows:
    print(f"  {r['floor_no']}층 {r['ho_no']}호: 전용={r['excl_area']}, 공용={r['share_area']}, 공용비율={r['share_ratio']}")

print("\n=== 삼정그린코아더시티 샘플 ===")
rows2 = conn.execute("""
    SELECT floor_no, ho_no, excl_area, share_area,
           ROUND(share_area/excl_area, 3) as share_ratio
    FROM gigjungsi WHERE bdong_cd='2623010300' AND bun=18 AND ji=0
    ORDER BY CAST(floor_no AS INT), ho_no LIMIT 10
""").fetchall()
for r in rows2:
    print(f"  {r['floor_no']}층 {r['ho_no']}호: 전용={r['excl_area']}, 공용={r['share_area']}, 공용비율={r['share_ratio']}")

conn.close()
