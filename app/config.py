import os
from pathlib import Path

# ── 로컬 경로 (개발 환경에서만 사용) ─────────────────────────────
_LOCAL_ROOT = Path(r"E:\경공매 프로그램\기준시가,공동주택,시가표준액 조회")

GIGJUNGSI_XLSX = _LOCAL_ROOT / "기준시가_전국" / "상업용건물 및 오피스텔 기준시가(2026년 1월 1일 기준).xlsx"
GONGDONG_DIR   = _LOCAL_ROOT / "공동주택가격_부산"
GONGSI_CSV     = _LOCAL_ROOT / "토지개별공시지가_부산" / "AL_D151_26_20260526.csv"
ILLAMTABLE_RES = _LOCAL_ROOT / "시가표준액_부산" / "1. 2026년 건축물 시가표준액 일람표(주거용).xls"
ILLAMTABLE_COM = _LOCAL_ROOT / "시가표준액_부산" / "2. 2026년 건축물 시가표준액 일람표(상업용).xls"
OFFICETEL_STD  = _LOCAL_ROOT / "시가표준액_부산" / "오피스텔_표준가격기준액_2026.xlsx"

# SQLite (가격 참조 데이터)
DB_PATH = Path(__file__).parent / "data" / "busan.db"

# API 키
MOLIT_API_KEY = os.environ.get("MOLIT_API_KEY", "2029d62769afe70bb952f9205fc01b69572f7b9c217f39f0082f956ca6308ec6")
BLDG_API_URL  = "https://apis.data.go.kr/1613000/BldRgstHubService"

