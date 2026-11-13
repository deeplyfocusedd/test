from contextlib import asynccontextmanager
import json
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.init_db import init_db
from app import queries


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Initializing database...")
    init_db()
    print("[startup] Database ready.")
    yield


app = FastAPI(title="Справочник крепёжных изделий", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def catalog_page(request: Request):
    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "stats": queries.get_stats(),
            "types": queries.get_type_list(),
            "gost_numbers": queries.get_gost_numbers(),
        },
    )


@app.get("/gosts", response_class=HTMLResponse)
async def gosts_page(request: Request):
    return templates.TemplateResponse(
        "gosts.html",
        {
            "request": request,
            "gosts": queries.get_all_gosts(),
        },
    )


@app.get("/schema", response_class=HTMLResponse)
async def schema_page(request: Request):
    return templates.TemplateResponse("schema.html", {"request": request})


@app.get("/queries", response_class=HTMLResponse)
async def queries_page(request: Request):
    return templates.TemplateResponse("sql_queries.html", {"request": request})


@app.get("/api/fasteners")
async def api_fasteners(
    type_name: Optional[str] = Query(None),
    d: Optional[float] = Query(None, description="Диаметр резьбы, мм"),
    d1: Optional[float] = Query(None, description="Диаметр стержня, мм"),
    l_min: Optional[float] = Query(None),
    l_max: Optional[float] = Query(None),
    gost_number: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Текстовый поиск"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows, total = queries.search_fasteners(
        type_name=type_name,
        d=d,
        d1=d1,
        l_min=l_min,
        l_max=l_max,
        gost_number=gost_number,
        q=q,
        limit=limit,
        offset=offset,
    )
    for row in rows:
        if isinstance(row.get("params"), str):
            row["params"] = json.loads(row["params"])
    return {"total": total, "items": rows}


@app.get("/api/stats")
async def api_stats():
    return queries.get_stats()
