import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=== 부산 부동산 가격 조회 DB 초기화 ===\n")

print("[1/4] DB 스키마 생성...")
import scripts.init_db as init_db_mod
import importlib
importlib.reload(init_db_mod)
exec(open(Path(__file__).parent / 'init_db.py').read(), {'__name__': '__main__', '__file__': str(Path(__file__).parent / 'init_db.py')})

print("\n[2/4] 기준시가 적재 (약 5분)...")
from scripts.load_gigjungsi import load as load_gj
load_gj()

print("\n[3/4] 공동주택가격 적재...")
from scripts.load_gongdong import load as load_gd
load_gd()

print("\n[4/4] 토지공시지가 적재...")
from scripts.load_gongsi import load as load_gs
load_gs()

print("\n=== 셋업 완료 ===")
print("서버 실행: uvicorn main:app --reload --port 8000")
