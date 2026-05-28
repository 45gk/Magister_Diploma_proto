from datetime import datetime
import json

def print_agent_result(result: dict, scenario_name: str = ""):
    print("\n" + "=" * 60)
    print(f"🤖 CREDIT AI AGENT RESPONSE {f'— {scenario_name}' if scenario_name else ''}")
    print("=" * 60)

    print(f"⏱ Timestamp: {datetime.now()}")
    print(f"📄 Application ID: {result.get('application_id', 'N/A')}")

    print("\n📊 DECISION:")
    print(f"  Decision: {result.get('decision', 'N/A')} ({result.get('decision_label', 'N/A')})")
    print(f"  Default Probability: {result.get('default_probability', 'N/A')}")
    print(f"  Credit Rating: {result.get('credit_rating', 'N/A')}")

    print("\n📈 IMPORTANT FEATURES:")
    important_features = result.get("important_features", [])
    if isinstance(important_features, dict):
        for feature, value in important_features.items():
            print(f"  - {feature}: {value}")
    elif isinstance(important_features, list):
        for item in important_features:
            feature = item.get("feature", "unknown")
            value = item.get("importance", "N/A")
            print(f"  - {feature}: {value}")
    else:
        print("  Нет данных по признакам")

    print("\n🧠 EXPLANATION:")
    explanation = result.get("explanation") or result.get("explanation_text") or "Нет объяснения"
    print(explanation)

    print("\n💡 RECOMMENDATIONS:")
    recommendations = result.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            print(f"  - {rec}")
    else:
        print("  Рекомендации отсутствуют")

    print("\n🔧 Model version:", result.get("model_version", "N/A"))
    print("=" * 60 + "\n")


def demo_different_scenarios():
    scenarios = [
        {
            "name": "Одобрение заявки",
            "data": {
                "application_id": "APP-2026-00123",
                "decision": 1,
                "decision_label": "Approved",
                "default_probability": 0.18,
                "credit_rating": 82.0,
                "important_features": [
                    {"feature": "income", "importance": 0.42},
                    {"feature": "credit_history_length", "importance": 0.31},
                    {"feature": "debt_to_income", "importance": -0.27},
                ],
                "explanation_text": (
                    "Заявка одобрена: у клиента стабильный доход, хорошая кредитная история "
                    "и умеренная долговая нагрузка."
                ),
                "recommendations": [
                    "Сохранить текущий уровень финансовой дисциплины",
                    "Не увеличивать долговую нагрузку без необходимости",
                ],
                "model_version": "v1.2.0",
            },
        },
        {
            "name": "Отказ по риску дефолта",
            "data": {
                "application_id": "APP-2026-00124",
                "decision": 0,
                "decision_label": "Rejected",
                "default_probability": 0.73,
                "credit_rating": 27.0,
                "important_features": [
                    {"feature": "debt_to_income", "importance": -0.51},
                    {"feature": "late_payments", "importance": -0.38},
                    {"feature": "income", "importance": 0.12},
                ],
                "explanation_text": (
                    "Заявка отклонена из-за высокой долговой нагрузки, просрочек "
                    "и повышенной вероятности дефолта."
                ),
                "recommendations": [
                    "Снизить текущую долговую нагрузку",
                    "Закрыть просроченные обязательства",
                    "Подать заявку повторно после улучшения кредитной истории",
                ],
                "model_version": "v1.2.0",
            },
        },
        {
            "name": "Недостаточно данных",
            "data": {
                "application_id": "APP-2026-00125",
                "decision": "N/A",
                "decision_label": "Insufficient data",
                "default_probability": "N/A",
                "credit_rating": "N/A",
                "important_features": [],
                "explanation_text": (
                    "Недостаточно данных для принятия надёжного решения. "
                    "Необходимо предоставить сведения о доходе, текущих обязательствах "
                    "и кредитной истории."
                ),
                "recommendations": [
                    "Добавить подтверждённый доход",
                    "Указать информацию о действующих кредитах",
                    "Предоставить историю платежей",
                ],
                "model_version": "v1.2.0",
            },
        },
        {
            "name": "Пограничный случай",
            "data": {
                "application_id": "APP-2026-00126",
                "decision": 1,
                "decision_label": "Approved with caution",
                "default_probability": 0.49,
                "credit_rating": 51.0,
                "important_features": [
                    {"feature": "income", "importance": 0.26},
                    {"feature": "employment_stability", "importance": 0.19},
                    {"feature": "credit_utilization", "importance": -0.24},
                ],
                "explanation_text": (
                    "Заявка находится в пограничной зоне: формально может быть одобрена, "
                    "но риск остаётся повышенным из-за кредитной нагрузки."
                ),
                "recommendations": [
                    "Снизить использование кредитного лимита",
                    "Подтвердить стабильность занятости",
                    "Рассмотреть меньшую сумму кредита",
                ],
                "model_version": "v1.2.0",
            },
        },
    ]

    for scenario in scenarios:
        print_agent_result(scenario["data"], scenario_name=scenario["name"])


# запуск демонстрации
demo_different_scenarios()