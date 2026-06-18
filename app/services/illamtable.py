import xlrd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ILLAMTABLE_COM, ILLAMTABLE_RES

REGION_BREAKS = [
    (1,0,10_000),(2,10_001,30_000),(3,30_001,50_000),
    (4,50_001,100_000),(5,100_001,150_000),(6,150_001,200_000),
    (7,200_001,350_000),(8,350_001,500_000),(9,500_001,650_000),
    (10,650_001,800_000),(11,800_001,1_000_000),(12,1_000_001,1_200_000),
    (13,1_200_001,1_600_000),(14,1_600_001,2_000_000),(15,2_000_001,2_500_000),
    (16,2_500_001,3_000_000),(17,3_000_001,4_000_000),(18,4_000_001,5_000_000),
    (19,5_000_001,6_000_000),(20,6_000_001,7_000_000),(21,7_000_001,8_000_000),
    (22,8_000_001,9_000_000),(23,9_000_001,10_000_000),(24,10_000_001,20_000_000),
    (25,20_000_001,30_000_000),(26,30_000_001,40_000_000),(27,40_000_001,50_000_000),
    (28,50_000_001,60_000_000),(29,60_000_001,70_000_000),(30,70_000_001,80_000_000),
    (31,80_000_001,float('inf')),
]

def get_region_no(gongsi_price: int) -> int:
    for no, lo, hi in REGION_BREAKS:
        if lo <= gongsi_price <= hi:
            return no
    return 31


def _parse_sheet(sheet) -> dict:
    """시트 내 모든 구조번호 블록 파싱. {(strct_no, year_key, usage_no): price}"""
    # 블록 시작: col0에 '건물신축가격기준액' 포함 행
    # 구조: start+0=헤더(col2='구조번호 :X'), start+3=분류번호, start+4=위치지수, start+5~=건축년도
    block_starts = []
    for r in range(sheet.nrows):
        v = str(sheet.cell_value(r, 0))
        if '건물신축가격기준액' in v:
            block_starts.append(r)

    result = {}
    for bi, start_row in enumerate(block_starts):
        # 구조번호: col2 "구조번호 :X"에서 파싱
        strct_raw = str(sheet.cell_value(start_row, 2))
        try:
            strct_no = int(strct_raw.split(':')[-1].strip())
        except (ValueError, IndexError):
            strct_no = bi + 1

        usage_row  = start_row + 3   # 분류번호 행
        year_start = start_row + 5   # 첫 건축년도 행
        end_row = block_starts[bi+1] if bi+1 < len(block_starts) else sheet.nrows

        # 열 인덱스 → usage_no 매핑
        usage_cols = {}
        for col in range(1, sheet.ncols):
            raw = str(sheet.cell_value(usage_row, col)).strip()
            if raw.startswith('(') and ')' in raw:
                first = raw.split(')')[0].lstrip('(')
                if first.isdigit():
                    usage_cols[col] = int(first)

        for r in range(year_start, end_row):
            year_val = sheet.cell_value(r, 0)
            if year_val == '' or year_val is None:
                continue
            year_key = int(year_val) if isinstance(year_val, float) and year_val > 1900 else str(year_val).strip()
            if not year_key:
                continue
            for col, usage_no in usage_cols.items():
                v = sheet.cell_value(r, col)
                if v and isinstance(v, (int, float)) and v > 0:
                    result[(strct_no, year_key, usage_no)] = float(v)
    return result


class IllamTable:
    def __init__(self):
        self.com_table = self._load(ILLAMTABLE_COM)
        self.res_table = self._load(ILLAMTABLE_RES)

    def _load(self, path) -> dict:
        wb = xlrd.open_workbook(str(path))
        table = {}
        for sheet in wb.sheets():
            name = sheet.name  # e.g. "2-7(26.5.31이전)"
            parts = name.split('(')
            if len(parts) < 2:
                continue
            try:
                region_no = int(parts[0].split('-')[-1])
            except ValueError:
                continue
            after_june = '6.1이후' in name
            table[(region_no, after_june)] = _parse_sheet(sheet)
        return table

    def lookup_com(self, strct_no: int, region_no: int, year: int,
                   usage_no: int = 4, after_june: bool = False) -> float:
        sheet_data = self.com_table.get((region_no, after_june), {})
        key = (strct_no, year, usage_no)
        if key in sheet_data:
            return sheet_data[key]
        # 가장 오래된 '이전' 행
        for k, v in sheet_data.items():
            if k[0] == strct_no and isinstance(k[1], str) and '이전' in str(k[1]) and k[2] == usage_no:
                return v
        return 0.0

    def lookup_res(self, strct_no: int, region_no: int, year: int,
                   usage_no: int = 1, after_june: bool = False) -> float:
        sheet_data = self.res_table.get((region_no, after_june), {})
        key = (strct_no, year, usage_no)
        if key in sheet_data:
            return sheet_data[key]
        for k, v in sheet_data.items():
            if k[0] == strct_no and isinstance(k[1], str) and '이전' in str(k[1]) and k[2] == usage_no:
                return v
        return 0.0
