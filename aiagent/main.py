import json
import os
from typing import Any, Dict, List, Optional

import requests
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph import tool


SYSTEM_PROMPT = (
    "Ты — кредитный советник банка. Оценивай заявителя и кредитную заявку на основе доступных признаков, "
    "поясняй решение модели, давай понятные рекомендации и не добавляй вымышленные данные. "
    "Если данных недостаточно, укажи, какие признаки нужно предоставить дополнительно."
)

TOOL_PROMPTS = {
    "score_credit_application": (
        "Оцени кредитную заявку и верни JSON с полями: application_id, decision (1 или 0), "
        "decision_label, default_probability, credit_rating, important_features и model_version. "
        "Используй переданные features и application_id."
    ),
    "advise_credit_improvement": (
        "Сформируй рекомендации по улучшению кредитного профиля клиента. "
        "Основано на результатах скоринга и ключевых факторах риска. "
        "Укажи конкретные шаги, которые можно предпринять, чтобы снизить вероятность дефолта."
    ),
    "explain_credit_decision": (
        "Объясни, почему модель согласилась или отклонила заявку. "
        "Опиши, как вычислен default_probability, как сформирован кредитный рейтинг, "
        "и какой вклад внесли ключевые признаки."
    ),
}


ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8002")

memory = MemorySaver()
model = GigaChat(
    credentials="ключ_авторизации",
    scope="GIGACHAT_API_PERS",
    model="GigaChat-Pro",
    verify_ssl_certs=False,
)

def parse_tool_input(input_text: str) -> Dict[str, Any]:
    input_text = input_text.strip()
    if not input_text:
        return {}

    try:
        parsed = json.loads(input_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    result: Dict[str, Any] = {}
    parts = [part.strip() for part in input_text.split("|") if part.strip()]
    if parts:
        if parts[0].isdigit():
            result["application_id"] = int(parts[0])
            parts = parts[1:]

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    result.setdefault("features", {})[key] = float(value)
                except ValueError:
                    result.setdefault("features", {})[key] = value
    return result


def flatten_features(input_data: Dict[str, Any]) -> Dict[str, float]:
    features = input_data.get("features", {})
    if isinstance(features, dict):
        return {k: float(v) for k, v in features.items() if v is not None}
    return {}


def call_ml_score(application_id: Optional[int], features: Dict[str, float]) -> Dict[str, Any]:
    response = requests.post(
        f"{ML_SERVICE_URL}/ml/score",
        json={"application_id": application_id, "features": features},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def call_agent_explain(application_id: Optional[int], features: Dict[str, float], scoring_data: Dict[str, Any], mode: str = "detailed") -> Dict[str, Any]:
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
    response = requests.post(f"{AGENT_SERVICE_URL}/agent/explain", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def format_feature_importances(importances: Dict[str, float], top_k: int = 5) -> List[Dict[str, Any]]:
    ordered = sorted(importances.items(), key=lambda item: abs(item[1]), reverse=True)[:top_k]
    return [{"feature": key, "importance": value} for key, value in ordered]


def binary_decision(default_probability: float, threshold: float = 0.5) -> int:
    return 1 if default_probability <= threshold else 0


def credit_rating(default_probability: float) -> float:
    return round(max(0.0, min(100.0, (1.0 - default_probability) * 100)), 2)


@tool("score_credit_application")
def score_credit_application(agent, input: str) -> str:
    """Оценивает заявку по кредиту и возвращает решение 1/0, важные признаки и рейтинг."""
    input_data = parse_tool_input(input)
    if not input_data:
        return "Нужно передать application_id или features для оценки заявки."

    application_id = input_data.get("application_id")
    features = flatten_features(input_data)

    try:
        scoring_data = call_ml_score(application_id, features)
    except Exception as exc:
        return f"Ошибка при вызове сервиса скоринга: {exc}"

    probability = float(scoring_data.get("default_probability", 0.0))
    decision = binary_decision(probability)
    rating = credit_rating(probability)
    top_features = format_feature_importances(scoring_data.get("feature_importances", {}))
    label = "выдавать кредит" if decision == 1 else "не выдавать кредит"

    return json.dumps(
        {
            "application_id": application_id,
            "decision": decision,
            "decision_label": label,
            "default_probability": probability,
            "credit_rating": rating,
            "important_features": top_features,
            "model_version": scoring_data.get("model_version"),
        },
        ensure_ascii=False,
    )


@tool("advise_credit_improvement")
def advise_credit_improvement(agent, input: str) -> str:
    """Дает рекомендации, как улучшить ситуацию клиента до выдачи кредита."""
    input_data = parse_tool_input(input)
    if not input_data:
        return "Нужно передать application_id или features для рекомендации улучшений."

    application_id = input_data.get("application_id")
    features = flatten_features(input_data)

    try:
        scoring_data = call_ml_score(application_id, features)
        explanation = call_agent_explain(application_id, features, scoring_data, mode="detailed")
    except Exception as exc:
        return f"Ошибка при формировании рекомендаций: {exc}"

    return json.dumps(
        {
            "application_id": application_id,
            "decision": explanation.get("scoring", {}).get("decision"),
            "default_probability": explanation.get("scoring", {}).get("default_probability"),
            "recommendations": explanation.get("recommendations", []),
            "key_factors": explanation.get("key_factors", []),
            "confidence": explanation.get("confidence"),
        },
        ensure_ascii=False,
    )


@tool("explain_credit_decision")
def explain_credit_decision(agent, input: str) -> str:
    """Объясняет, почему модель приняла решение 1 или 0 и как вычислил рейтинг."""
    input_data = parse_tool_input(input)
    if not input_data:
        return "Нужно передать application_id или features для объяснения решения."

    application_id = input_data.get("application_id")
    features = flatten_features(input_data)

    try:
        scoring_data = call_ml_score(application_id, features)
        explanation = call_agent_explain(application_id, features, scoring_data, mode="policy")
    except Exception as exc:
        return f"Ошибка при получении объяснения: {exc}"

    probability = float(scoring_data.get("default_probability", 0.0))
    decision = binary_decision(probability)
    rating = credit_rating(probability)

    return json.dumps(
        {
            "application_id": application_id,
            "decision": decision,
            "default_probability": probability,
            "credit_rating": rating,
            "explanation_text": explanation.get("explanation_text"),
            "key_factors": explanation.get("key_factors", []),
            "recommendations": explanation.get("recommendations", []),
            "model_version": scoring_data.get("model_version"),
        },
        ensure_ascii=False,
    )


agent = create_react_agent(model=model, memory=memory)
tools = [score_credit_application, advise_credit_improvement, explain_credit_decision]


def main():
    while True:
        user_input = input("Введите запрос: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Завершение работы агента.")
            break

        response = agent.run(user_input, tools=tools)
        print(f"Ответ агента: {response}")

