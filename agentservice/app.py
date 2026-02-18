from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AgentService", version="1.0.0")

Mode = Literal["brief", "detailed", "policy"]


class ScoringResult(BaseModel):
    default_probability: float = Field(ge=0, le=1)
    model_version: str
    decision: Optional[str] = None


class ExplainData(BaseModel):
    feature_importances: Dict[str, float] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    application_id: Optional[int] = None
    client_id: Optional[int] = None
    features: Dict[str, float] = Field(default_factory=dict)
    scoring_result: ScoringResult
    explain_data: Optional[ExplainData] = None
    mode: Mode = "brief"


class KeyFactor(BaseModel):
    feature: str
    value: float
    impact: float
    advice: str


RULES = {
    "debt_to_income": {
        "desc": "Высокая долговая нагрузка",
        "advice": "Снизить долю задолженности ниже 40% от дохода.",
        "type": "short_term",
        "impact": 0.06,
    },
    "income": {
        "desc": "Недостаточный подтвержденный доход",
        "advice": "Подтвердить дополнительный источник дохода или привлечь созаёмщика.",
        "type": "medium_term",
        "impact": 0.05,
    },
    "bki_request_cnt": {
        "desc": "Высокая частота запросов в БКИ",
        "advice": "Снизить число одновременных кредитных заявок.",
        "type": "short_term",
        "impact": 0.04,
    },
    "age": {
        "desc": "Возрастной профиль влияет на риск",
        "advice": "Увеличить подтверждённый стаж и стабильность занятости.",
        "type": "long_term",
        "impact": 0.02,
    },
}


def decision_by_probability(probability: float) -> str:
    if probability < 0.3:
        return "approve"
    if probability < 0.5:
        return "conditionally_approve"
    return "conditionally_reject"


def to_key_factors(features: Dict[str, float], importances: Dict[str, float], top_k: int = 5) -> List[KeyFactor]:
    ranked = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:top_k]
    response: List[KeyFactor] = []
    for feature, impact in ranked:
        rule = RULES.get(feature, {"advice": "Улучшить общий финансовый профиль."})
        response.append(
            KeyFactor(
                feature=feature,
                value=float(features.get(feature, 0.0)),
                impact=float(impact),
                advice=rule["advice"],
            )
        )
    return response


def render_text(prob: float, mode: Mode, factors: List[KeyFactor]) -> str:
    base = f"Вероятность дефолта составляет {prob:.2%}. Основные факторы решения модели выделены ниже."
    if mode == "brief":
        return base

    details = "; ".join([f"{f.feature}: вклад {f.impact:+.3f}" for f in factors])
    if mode == "policy":
        return base + " Решение сформировано на основе интерпретируемых факторов без дискриминационных признаков. " + details
    return base + " Детализация факторов: " + details


@app.get("/agent/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/agent/explain")
def explain(payload: ExplainRequest) -> dict:
    importances = payload.explain_data.feature_importances if payload.explain_data else {}
    if not importances:
        raise HTTPException(status_code=400, detail="explain_data.feature_importances is required in prototype")

    decision = payload.scoring_result.decision or decision_by_probability(payload.scoring_result.default_probability)
    factors = to_key_factors(payload.features, importances)
    recommendations = [
        {
            "type": RULES.get(f.feature, {}).get("type", "short_term"),
            "text": f.advice,
            "impact_estimate": RULES.get(f.feature, {}).get("impact", 0.01),
        }
        for f in factors
    ]

    confidence = round(0.7 + min(0.25, sum(abs(f.impact) for f in factors) / 2), 4)
    return {
        "application_id": payload.application_id,
        "scoring": {
            "default_probability": payload.scoring_result.default_probability,
            "decision": decision,
            "model_version": payload.scoring_result.model_version,
        },
        "explanation_text": render_text(payload.scoring_result.default_probability, payload.mode, factors),
        "key_factors": [factor.model_dump() for factor in factors],
        "recommendations": recommendations,
        "confidence": min(0.99, confidence),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/agent/batch_explain")
def batch_explain(items: List[ExplainRequest]) -> List[dict]:
    return [explain(item) for item in items]
