from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any
from .scoring import score_with_llm, DIMENSIONS

app = FastAPI(title="PeerReview AI — Heurístico MVP", version="0.1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class AnalyzePayload(BaseModel):
    text: str

@app.get("/health", response_class=JSONResponse)
async def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "dimensions": DIMENSIONS})

@app.post("/analyze", response_class=JSONResponse)
async def analyze(payload: AnalyzePayload):
    try:
        result = score_with_llm(payload.text or "")
        if "error" in result:
            return JSONResponse(result, status_code=500)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": f"Erro interno na análise: {str(e)}"}, status_code=500)
