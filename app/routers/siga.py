from fastapi import APIRouter
from pydantic import BaseModel
from services.siga_calc import calc_siga

router = APIRouter(prefix="/api/siga", tags=["시가표준액"])

class SigaRequest(BaseModel):
    bdong_cd: str
    bun: int
    ji: int
    excl_area: float
    share_area: float = 0.0
    daejijibun: float
    after_june: bool = False
    floor_no: str | None = None

@router.post("")
def calc_siga_route(req: SigaRequest):
    return calc_siga(
        bdong_cd=req.bdong_cd,
        bun=req.bun,
        ji=req.ji,
        excl_area=req.excl_area,
        share_area=req.share_area,
        daejijibun=req.daejijibun,
        after_june=req.after_june,
        floor_no=req.floor_no,
    )
