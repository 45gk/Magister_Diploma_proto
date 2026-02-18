from typing import Any, Dict

import requests
from django.conf import settings


def call_ml_score(application_id: int, features: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        f"{settings.ML_SERVICE_URL}/ml/score",
        json={"application_id": application_id, "features": features},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def call_agent_explain(application_id: int, features: Dict[str, Any], scoring_data: Dict[str, Any], mode: str) -> Dict[str, Any]:
    payload = {
        "application_id": application_id,
        "features": features,
        "scoring_result": {
            "default_probability": scoring_data["default_probability"],
            "model_version": scoring_data["model_version"],
        },
        "explain_data": {"feature_importances": scoring_data.get("feature_importances", {})},
        "mode": mode,
    }
    response = requests.post(f"{settings.AGENT_SERVICE_URL}/agent/explain", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
