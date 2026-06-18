import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_conn
from services.illamtable import IllamTable, get_region_no
from services.bldg_api import get_bldg_info, get_illamtable_strct_no

# 경과연수별 잔가율 — [별표 7] 제19조 관련
# strct_cd → 매년 상각률 (내용연수 끝 최솟값 10%)
_DEPRECIATION_RATE = {
    '11': 0.018,   # 철골(철골철근)콘크리트조
    '12': 0.018,   # 통나무조
    '13': 0.018,   # (철골철근콘크리트 계열)
    '42': 0.018,   # 철골철근콘크리트조
    '21': 0.0225,  # 철근콘크리트조
    '15': 0.0225,  # 라멘조
    '14': 0.0225,  # 석조
    '22': 0.0225,  # 프리캐스트콘크리트조
    '16': 0.030,   # 철골조
    '17': 0.030,   # 연와조
    '18': 0.030,   # 보강콘크리트/블록조
    '19': 0.030,   # 목조/ALC조
    '20': 0.045,   # 시멘트블록조/경량철골조
}

def _get_depreciation_rate(strct_cd: str) -> float:
    return _DEPRECIATION_RATE.get(str(strct_cd), 0.0225)

def _calc_잔가율(strct_cd: str, build_year: int, base_year: int = 2026) -> float:
    rate = _get_depreciation_rate(strct_cd)
    elapsed = max(base_year - build_year, 0)
    return max(round(1.0 - rate * elapsed, 4), 0.10)


# 오피스텔 층지수 — [별표 2] 제18조 관련
# 상대층수 = (당해층 - 최저층) / (최고층 - 최저층)
# 주거용: 0.2이하=0.999, ~0.4=1.000, ~0.6=1.001, ~0.8=1.002, ~1=1.003, 지하=0.9
# 사무용: 지상 모두=1.000, 지하=0.9
def _calc_층지수(floor_no, min_floor: int = None, max_floor: int = None,
                is_residential: bool = False) -> float:
    """층지수 계산. 상대층수 기반 [별표 2]."""
    try:
        floor = int(str(floor_no).replace('B', '-').replace('b', '-'))
    except (ValueError, TypeError):
        floor = 1

    if floor <= 0:  # 지하층
        return 0.9

    if not is_residential:  # 사무용: 지상 항상 1.0
        return 1.0

    # 주거용: 상대층수 계산
    if min_floor is None or max_floor is None or max_floor == min_floor:
        return 1.0
    rel = (floor - min_floor) / (max_floor - min_floor)
    if rel <= 0.2:   return 0.999
    if rel <= 0.4:   return 1.000
    if rel <= 0.6:   return 1.001
    if rel <= 0.8:   return 1.002
    return 1.003


def _get_floor_range(bdong_cd: str, bun: int, ji: int) -> tuple[int, int]:
    """건물의 오피스텔 최저층/최고층 조회."""
    conn = get_conn()
    row = conn.execute(
        "SELECT MIN(CAST(floor_no AS INT)) as min_f, MAX(CAST(floor_no AS INT)) as max_f "
        "FROM gigjungsi WHERE bdong_cd=? AND bun=? AND ji=? AND CAST(floor_no AS INT) > 0",
        (bdong_cd, bun, ji)
    ).fetchone()
    conn.close()
    if row and row['min_f'] is not None:
        return int(row['min_f']), int(row['max_f'])
    return 1, 1


# 오피스텔 가감산율 — [별표 3] 제18조 관련 (전용+공용 합계면적 기준)
def _calc_가감산율(total_area: float) -> float:
    """면적별 가감산율 [별표 3]."""
    if total_area <= 50:    return 1.000
    if total_area <= 100:   return 0.999
    if total_area <= 150:   return 0.998
    if total_area <= 200:   return 0.997
    if total_area <= 250:   return 0.996
    if total_area <= 300:   return 0.995
    if total_area <= 350:   return 0.994
    if total_area <= 400:   return 0.993
    if total_area <= 450:   return 0.992
    return 0.991

_illamtable = None

def _get_illamtable() -> IllamTable:
    global _illamtable
    if _illamtable is None:
        _illamtable = IllamTable()
    return _illamtable


def _get_gongsi(bdong_cd: str, bun: int, ji: int) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT price FROM gongsi WHERE bdong_cd=? AND bun=? AND ji=? "
        "ORDER BY base_year DESC LIMIT 1",
        (bdong_cd, bun, ji)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def _get_otel_stdprice(bdong_cd: str, bun: int, ji: int) -> int:
    """오피스텔 표준가격기준액(원/㎡) 조회."""
    conn = get_conn()
    row = conn.execute(
        "SELECT std_price FROM otel_stdprice WHERE bdong_cd=? AND bun=? AND ji=?",
        (bdong_cd, bun, ji)
    ).fetchone()
    conn.close()
    return row[0] if row else 0


# 용도지수 — [별표 1] 제18조 관련
# 별도 신청 없음=1.000, 주택으로 신청=1.050
# 주거용(주택신청) 여부는 gigjungsi 건물의 공용비율로 추정
# 평균 공용비율 < 0.7 → 주거용(용도지수 1.05 가능), >= 0.7 → 사무용(1.0)
_SHARE_RATIO_THRESHOLD = 0.7

def _is_residential_otel(bdong_cd: str, bun: int, ji: int) -> bool:
    """건물 평균 공용비율 기반 주거용 오피스텔 여부 판단."""
    conn = get_conn()
    row = conn.execute(
        "SELECT AVG(share_area * 1.0 / excl_area) as avg_ratio "
        "FROM gigjungsi WHERE bdong_cd=? AND bun=? AND ji=? AND excl_area > 0",
        (bdong_cd, bun, ji)
    ).fetchone()
    conn.close()
    avg_ratio = row['avg_ratio'] if row and row['avg_ratio'] is not None else 0.0
    return avg_ratio < _SHARE_RATIO_THRESHOLD


def get_siga_info(bdong_cd: str, bun: int, ji: int, after_june: bool = False) -> dict:
    """시가표준액 계산에 필요한 기본 정보 반환.
    오피스텔이면 표준가격기준액 방식, 그 외엔 상업용 일람표 방식.
    """
    gongsi_price = _get_gongsi(bdong_cd, bun, ji)

    # 오피스텔 표준가격기준액 우선 조회 (잔가율 미적용 — 고시가격에 이미 반영)
    otel_std = _get_otel_stdprice(bdong_cd, bun, ji)
    if otel_std > 0:
        return {
            "mode": "오피스텔",
            "unit_price_per_m2": otel_std,
            "gongsi_price": gongsi_price,
            "otel_std_price": otel_std,
        }
        # 층지수는 calc_siga에서 floor_no별로 적용

    # 일반 건축물 — 상업용 일람표
    region_no = get_region_no(gongsi_price) if gongsi_price > 0 else 1
    sigungu_cd = bdong_cd[:5]
    bjdong_cd_5 = bdong_cd[5:10]
    bldg = get_bldg_info(sigungu_cd, bjdong_cd_5, str(bun), str(ji))

    strct_no = 4
    build_year = 2000
    if bldg:
        strct_no = get_illamtable_strct_no(bldg.get("strct_cd", "21"))
        apr_day = bldg.get("use_apr_day", "")
        if apr_day and len(apr_day) >= 4:
            build_year = int(apr_day[:4])

    unit_price = _get_illamtable().lookup_com(
        strct_no=strct_no, region_no=region_no, year=build_year,
        usage_no=4, after_june=after_june
    )

    return {
        "mode": "일람표",
        "gongsi_price": gongsi_price,
        "region_no": region_no,
        "strct_no": strct_no,
        "build_year": build_year,
        "unit_price_per_m2": unit_price * 1000,
    }


def calc_siga(bdong_cd: str, bun: int, ji: int,
              excl_area: float, share_area: float, daejijibun: float,
              after_june: bool = False, floor_no=None) -> dict:
    """오피스텔 or 일반 건축물 시가표준액 계산."""
    gongsi_price = _get_gongsi(bdong_cd, bun, ji)
    land_price = int(gongsi_price * daejijibun)

    # 오피스텔 표준가격기준액 방식 — 제18조
    # 공식: 표준가격기준액 × 면적 × 용도지수[별표1] × 층지수[별표2] × 가감산율[별표3]
    otel_std = _get_otel_stdprice(bdong_cd, bun, ji)
    if otel_std > 0:
        bldg_area = excl_area + share_area
        is_res = _is_residential_otel(bdong_cd, bun, ji)
        용도지수 = 1.050 if is_res else 1.000  # 별표1: 주거용(주택신청)=1.05, 사무용=1.0
        용도분류 = "주거용" if is_res else "사무용"
        min_f, max_f = _get_floor_range(bdong_cd, bun, ji)
        층지수 = _calc_층지수(floor_no, min_f, max_f, is_res) if floor_no is not None else (0.9 if not is_res else 1.0)
        가감산율 = _calc_가감산율(bldg_area)
        bldg_price = int(otel_std * bldg_area * 용도지수 * 층지수 * 가감산율)
        return {
            "mode": "오피스텔",
            "bldg_price": bldg_price,
            "land_price": land_price,
            "total_price": bldg_price + land_price,
            "gongsi_price": gongsi_price,
            "unit_price_per_m2": otel_std,
            "otel_std_price": otel_std,
            "용도지수": 용도지수,
            "용도분류": 용도분류,
            "층지수": 층지수,
            "가감산율": 가감산율,
        }

    # 일반 건축물 — 상업용 일람표
    region_no = get_region_no(gongsi_price) if gongsi_price > 0 else 1
    sigungu_cd = bdong_cd[:5]
    bjdong_cd_5 = bdong_cd[5:10]
    bldg = get_bldg_info(sigungu_cd, bjdong_cd_5, str(bun), str(ji))

    strct_no = 4
    build_year = 2000
    if bldg:
        strct_no = get_illamtable_strct_no(bldg.get("strct_cd", "21"))
        apr_day = bldg.get("use_apr_day", "")
        if apr_day and len(apr_day) >= 4:
            build_year = int(apr_day[:4])

    unit_price = _get_illamtable().lookup_com(
        strct_no=strct_no, region_no=region_no, year=build_year,
        usage_no=4, after_june=after_june
    )

    bldg_price = int(unit_price * 1000 * (excl_area + share_area))
    return {
        "mode": "일람표",
        "bldg_price": bldg_price,
        "land_price": land_price,
        "total_price": bldg_price + land_price,
        "gongsi_price": gongsi_price,
        "region_no": region_no,
        "strct_no": strct_no,
        "build_year": build_year,
        "unit_price_per_m2": unit_price * 1000,
    }
