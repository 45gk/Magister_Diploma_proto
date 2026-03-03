from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="MLService", version="1.0.0")

MODEL_VERSION = "v1.0-kaggle-proto"


class ScoreRequest(BaseModel):
    application_id: Optional[int] = None
    features: Dict[str, float] = Field(default_factory=dict)


class ScoreResponse(BaseModel):
    application_id: Optional[int]
    default_probability: float
    model_version: str
    feature_importances: Dict[str, float]
    confidence: float
    generated_at: str


def heuristic_score(features: Dict[str, float]) -> tuple[float, Dict[str, float], float]:
    income = float(features.get("income", 50000))
    age = float(features.get("age", 35))
    debt_to_income = float(features.get("debt_to_income", 0.3))
    bki_requests = float(features.get("bki_request_cnt", 1))

    linear = 0.45 + (debt_to_income * 0.7) + (bki_requests * 0.04) - (income / 300000) - (age / 400)
    probability = max(0.01, min(0.99, linear))

    feature_importances = {
        "debt_to_income": round(min(0.35, debt_to_income * 0.5), 4),
        "bki_request_cnt": round(min(0.2, bki_requests * 0.03), 4),
        "income": round(max(-0.25, -(income / 500000)), 4),
        "age": round(max(-0.1, -(age / 1000)), 4),
    }
    confidence = round(0.65 + (0.3 * abs(0.5 - probability)), 4)
    return round(probability, 4), feature_importances, min(0.98, confidence)


@app.get("/ml/health")
def health() -> dict:
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.post("/ml/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    if not req.application_id and not req.features:
        raise HTTPException(status_code=400, detail="application_id or features must be provided")

    probability, importances, confidence = heuristic_score(req.features)
    return ScoreResponse(
        application_id=req.application_id,
        default_probability=probability,
        model_version=MODEL_VERSION,
        feature_importances=importances,
        confidence=confidence,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
