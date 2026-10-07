"""FastAPI — 산출물 조회 + 로그 감사(POST /v1/audit) + 파일럿 계획기.

조회 엔드포인트는 미리 계산된 산출물을 돌려주고, 감사와 계획기는 요청마다 계산한다. 정적 데모(GitHub Pages)는 조회 응답을 JSON 으로 구워 둔 것이다.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import __version__
from ..audit import run_audit
from ..causal import pilot
from ..causal.data import LogSpec
from .store import Store

MAX_AUDIT_ROWS = 400_000
CONSOLE = Path(__file__).resolve().parent.parent / "console"

app = FastAPI(
    title="averted",
    version=__version__,
    description="점검 한 번이 막은 고장을 추정합니다. 모든 데이터는 합성(SYNTHETIC)입니다.",
)
store = Store()

_metrics = {"requests": 0, "audit_calls": 0, "audit_seconds": 0.0, "pilot_calls": 0}


@app.middleware("http")
async def count(request, call_next):
    _metrics["requests"] += 1
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version")
def version():
    return {"version": __version__, "manifest": store.artifact("manifest"), "scenarios": store.scenario_ids()}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    lines = [f"averted_{k} {v}" for k, v in _metrics.items()]
    return "\n".join(lines) + "\n"


@app.get("/v1/scenarios")
def scenarios():
    out = []
    for sid in store.scenario_ids():
        d = store.scenario(sid)
        out.append(
            {
                "id": sid,
                "title": d["title"],
                "world": d["world"],
                "config": d["config"],
                "verdict": d["audit"]["verdict"],
            }
        )
    return {"scenarios": out}


@app.get("/v1/scenarios/{sid}")
def scenario(sid: str):
    d = store.scenario(sid)
    if d is None:
        raise HTTPException(404, f"그런 시나리오가 없습니다: {sid}")
    return d


@app.get("/v1/scenarios/{sid}/policy")
def scenario_policy(sid: str, k: int = Query(8, ge=1, le=64)):
    d = store.scenario(sid)
    if d is None:
        raise HTTPException(404, f"그런 시나리오가 없습니다: {sid}")
    by_k = d["policy"]["by_k"]
    if str(k) not in by_k:
        raise HTTPException(400, f"미리 계산된 K 만 지원합니다: {d['policy']['ks']}")
    return {
        "k": k,
        "labels": d["policy"]["labels"],
        "values": by_k[str(k)],
        "ci": d["policy"]["ci"] if k == d["policy"]["k"] else None,
    }


@app.get("/v1/scenarios/{sid}/plan")
def scenario_plan(sid: str, site: int = Query(...), week: int = Query(...), k: int = Query(8, ge=1, le=12)):
    d = store.scenario(sid)
    if d is None:
        raise HTTPException(404, f"그런 시나리오가 없습니다: {sid}")
    for p in d["plans"]:
        if p["site"] == site and p["week"] == week:
            return {**p, "by_effect": p["by_effect"][:k], "by_risk": p["by_risk"][:k], "k": k}
    raise HTTPException(404, "그 사이트·주의 점검표는 미리 계산해 두지 않았습니다")


@app.get("/v1/artifacts/{name}")
def artifact(name: str):
    d = store.artifact(name)
    if d is None:
        raise HTTPException(404, f"그런 산출물이 없습니다: {name}")
    return d


class PilotIn(BaseModel):
    base_rate: float = Field(0.07, gt=0, lt=1, description="점검하지 않을 때 4주 안에 고장날 비율")
    averted_pp: float = Field(1.0, gt=0, le=50, description="검출하려는 효과 (%p)")
    n_assets: int = Field(500, ge=2, le=1_000_000)
    weeks: int = Field(26, ge=4, le=520)
    treat_share: float = Field(0.5, gt=0, lt=1)
    icc: float = Field(0.02, ge=0, lt=1)


@app.post("/v1/pilot/plan")
def pilot_plan(body: PilotIn):
    _metrics["pilot_calls"] += 1
    p = pilot.plan(body.base_rate, body.averted_pp, body.n_assets, body.weeks, body.treat_share, body.icc)
    return {
        "plan": p.to_dict(),
        "weeks_needed": pilot.required_weeks(
            body.base_rate, body.averted_pp, body.n_assets, body.treat_share, body.icc
        ),
        "assets_needed": pilot.required_assets(
            body.base_rate, body.averted_pp, body.weeks, body.treat_share, body.icc
        ),
    }


SCHEMA = [
    {"column": "asset", "type": "int|str", "meaning": "설비 번호"},
    {"column": "week", "type": "int", "meaning": "주 번호. 한 행은 설비 하나의 한 주입니다"},
    {"column": "site", "type": "int", "meaning": "사이트(고객사·건물) 번호. 0부터 시작합니다"},
    {
        "column": "cat",
        "type": "str",
        "meaning": "설비 종류: pump chiller ahu boiler elevator fire_pump generator switchgear",
    },
    {"column": "age", "type": "float", "meaning": "연식(년)"},
    {"column": "crit", "type": "int", "meaning": "중요도 1~3"},
    {"column": "grade_last", "type": "int", "meaning": "직전 점검 판정. 0 양호, 1 주의, 2 불량"},
    {"column": "wsv", "type": "float", "meaning": "마지막 점검 뒤 지난 주 수 (52주를 넘으면 52로 둡니다)"},
    {"column": "bd", "type": "float", "meaning": "최근 고장을 더한 값 (오래된 고장일수록 작게 셉니다)"},
    {
        "column": "cmp",
        "type": "float",
        "meaning": "최근 민원·A/S 접수를 더한 값 (오래된 접수일수록 작게 셉니다)",
    },
    {"column": "open_wo", "type": "0|1", "meaning": "수리가 접수된 결함이 남아 있는가"},
    {"column": "treated", "type": "0|1", "meaning": "그 주에 점검했는가"},
    {
        "column": "y",
        "type": "0|1|NaN",
        "meaning": "그 주부터 4주 안에 계획에 없던 고장이 있었는가. 4주가 데이터 기간을 넘으면 NaN",
    },
    {
        "column": "due",
        "type": "0|1",
        "meaning": "(선택) 법정 점검 기한이라 점검 여부가 달력으로 정해진 행. 분석에서 뺍니다",
    },
    {
        "column": "y_prev",
        "type": "0|1|NaN",
        "meaning": "(선택) 점검 이전 4주의 고장. 보정이 충분한지 확인하는 데 씁니다",
    },
]


@app.get("/v1/schema")
def schema():
    return {
        "columns": SCHEMA,
        "max_rows": MAX_AUDIT_ROWS,
        "note": "열 이름이 다르면 LogSpec 으로 맞춥니다 (docs/real-data.md)",
    }


@app.post("/v1/audit")
async def audit(
    file: UploadFile = File(...), folds: int = Query(3, ge=2, le=5), sensitivity: bool = Query(True)
):
    """CSV 한 장(위 스키마)을 올리면 점검 효과 추정과 식별 가능성 진단을 돌려준다. 데이터는 저장하지 않는다."""
    raw = await file.read()
    try:
        log = pd.read_csv(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"CSV 를 읽을 수 없습니다: {e}") from e
    if len(log) > MAX_AUDIT_ROWS:
        raise HTTPException(413, f"행이 너무 많습니다 ({len(log):,} > {MAX_AUDIT_ROWS:,})")
    spec = LogSpec(
        prior_outcome="y_prev" if "y_prev" in log.columns else None,
        due="due" if "due" in log.columns else None,
    )
    t0 = time.time()
    try:
        rep = run_audit(log, spec=spec, n_folds=folds, with_sensitivity=sensitivity)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    _metrics["audit_calls"] += 1
    _metrics["audit_seconds"] += time.time() - t0
    return JSONResponse(rep)


@app.get("/v1/sample.csv")
def sample_csv(rows: int = Query(20000, ge=1000, le=60000)):
    """감사 업로드를 시험해 볼 수 있는 합성 로그 샘플 (작은 세계를 즉석에서 만든다)."""
    from ..sim.generate import simulate
    from ..sim.world import WorldConfig

    cfg = WorldConfig(seed=3, n_sites=2, assets_min=60, assets_max=80, weeks=max(30, rows // 140), burn_in=40)
    w = simulate(cfg, truth_m=0)
    csv = w.log.drop(columns=["pilot"]).head(rows).to_csv(index=False)
    return Response(
        csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=averted_sample_log.csv"},
    )


if CONSOLE.exists():
    app.mount("/console", StaticFiles(directory=CONSOLE, html=True), name="console")

    @app.get("/")
    def root():
        index = CONSOLE / "index.html"
        return FileResponse(index) if index.exists() else {"service": "averted", "docs": "/docs"}
