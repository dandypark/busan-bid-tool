import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from db import get_conn

conn = get_conn()

# gongsi 1410-5
rows = conn.execute("SELECT bdong_cd, bun, ji, price FROM gongsi WHERE bun=1410 AND ji=5 LIMIT 5").fetchall()
print("gongsi 1410-5:", [dict(r) for r in rows])

# otel_stdprice 1410-5
rows2 = conn.execute("SELECT * FROM otel_stdprice WHERE bun=1410 AND ji=5 LIMIT 5").fetchall()
print("otel_stdprice 1410-5:", [dict(r) for r in rows2])

# gigjungsi 1410-5 샘플 (501호, 201호, 701호)
rows3 = conn.execute("SELECT bdong_cd, bun, ji, floor_no, ho_no, excl_area, share_area FROM gigjungsi WHERE bun=1410 AND ji=5 AND ho_no IN ('201','501','701') LIMIT 10").fetchall()
print("gigjungsi 1410-5 target units:", [dict(r) for r in rows3])

conn.close()
