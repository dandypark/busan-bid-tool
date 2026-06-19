from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from routers import gigjungsi, gongdong, lookup

app = FastAPI(title="부산 부동산 가격 조회")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gigjungsi.router)
app.include_router(gongdong.router)
app.include_router(lookup.router)

app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "static"), html=True), name="static")
