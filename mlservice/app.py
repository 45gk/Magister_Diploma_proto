from datetime import datetime, timezone
from typing import Dict, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import sys
sys.path.append('/app')

from model_manager import (
    load_model,
    get_model_status,
    predict_single,
    predict_batch,
    validate_model
)
from train_model import train_pipeline


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MLService", version="1.0.0")

MODEL_VERSION = "v1.0.0"


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


class TrainRequest(BaseModel):
    n_iterations: Optional[int] = 1000
    dataset_path: Optional[str] = None


class TrainResponse(BaseModel):
    success: bool
    model_version: str
    metrics: Optional[Dict]
    feature_count: Optional[int]
    model_path: Optional[str]
    error: Optional[str]


class BatchPredictRequest(BaseModel):
    features_list: List[Dict[str, float]]


class BatchPredictResponse(BaseModel):
    success: bool
    total_predictions: Optional[int]
    predictions: Optional[List[Dict]]
    model_version: str
    generated_at: str
    error: Optional[str]


class ModelStatusResponse(BaseModel):
    version: str
    status: str
    last_trained: Optional[str]
    metrics: Dict
    loaded_at: str


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


@app.get("/ml/model/status", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    status = get_model_status()
    
    return ModelStatusResponse(
        version=status.get('version', MODEL_VERSION),
        status=status.get('status', 'unknown'),
        last_trained=status.get('last_trained'),
        metrics=status.get('metrics', {}),
        loaded_at=status.get('loaded_at', datetime.now(timezone.utc).isoformat())
    )


@app.post("/ml/train", response_model=TrainResponse)
def train_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    Запуск обучения модели в фоновом режиме.
    """
    try:
        # Проверяем доступность модели
        if not validate_model():
            # Если модель не загружена, запускаем обучение
            result = train_pipeline()
            
            return TrainResponse(
                success=result.get('success', False),
                model_version=result.get('model_version', MODEL_VERSION),
                metrics=result.get('metrics'),
                feature_count=result.get('feature_count'),
                model_path=result.get('model_path'),
                error=result.get('error')
            )
        else:
            # Модель уже загружена, перезапускаем обучение
            result = train_pipeline()
            
            return TrainResponse(
                success=result.get('success', False),
                model_version=result.get('model_version', MODEL_VERSION),
                metrics=result.get('metrics'),
                feature_count=result.get('feature_count'),
                model_path=result.get('model_path'),
                error=result.get('error')
            )
    
    except Exception as e:
        return TrainResponse(
            success=False,
            model_version=MODEL_VERSION,
            error=str(e)
        )


@app.post("/ml/predict", response_model=ScoreResponse)
def predict(req: ScoreRequest):
    """
    Предсказание для одной записи.
    Использует обученную CatBoost модель.
    """
    try:
        # Проверяем статус модели
        status = get_model_status()
        
        if status.get('status') == 'not_loaded':
            # Если модель не загружена, используем heuristic
            probability, importances, confidence = heuristic_score(req.features)
            return ScoreResponse(
                application_id=req.application_id,
                default_probability=probability,
                model_version=f"{MODEL_VERSION} (heuristic fallback)",
                feature_importances=importances,
                confidence=confidence,
                generated_at=datetime.now(timezone.utc).isoformat()
            )
        
        # Используем обученную модель
        result = predict_single(req.features)
        
        if not result.get('success'):
            # Если предсказание не удалось, используем heuristic
            probability, importances, confidence = heuristic_score(req.features)
            return ScoreResponse(
                application_id=req.application_id,
                default_probability=probability,
                model_version=f"{MODEL_VERSION} (fallback after error)",
                feature_importances=importances,
                confidence=confidence,
                generated_at=datetime.now(timezone.utc).isoformat()
            )
        
        return ScoreResponse(
            application_id=req.application_id,
            default_probability=result['default_probability'],
            model_version=result['model_version'],
            feature_importances=result['feature_importances'],
            confidence=result['confidence'],
            generated_at=result['generated_at']
        )
    
    except Exception as e:
        # Fallback на heuristic
        probability, importances, confidence = heuristic_score(req.features)
        return ScoreResponse(
            application_id=req.application_id,
            default_probability=probability,
            model_version=f"{MODEL_VERSION} (error fallback)",
            feature_importances=importances,
            confidence=confidence,
            generated_at=datetime.now(timezone.utc).isoformat()
        )


@app.post("/ml/predict/batch", response_model=BatchPredictResponse)
def predict_batch_endpoint(req: BatchPredictRequest):
    """
    Батч предсказания для нескольких записей.
    """
    try:
        status = get_model_status()
        
        if status.get('status') == 'not_loaded':
            return BatchPredictResponse(
                success=False,
                error="Model not loaded. Please train the model first."
            )
        
        result = predict_batch(req.features_list)
        
        return BatchPredictResponse(
            success=result.get('success', False),
            total_predictions=result.get('total_predictions'),
            predictions=result.get('predictions'),
            model_version=MODEL_VERSION,
            generated_at=datetime.now(timezone.utc).isoformat(),
            error=result.get('error')
        )
    
    except Exception as e:
        return BatchPredictResponse(
            success=False,
            error=str(e),
            model_version=MODEL_VERSION,
            generated_at=datetime.now(timezone.utc).isoformat()
        )


@app.get("/ml/train/status")
def train_status():
    """
    Проверка статуса последнего обучения.
    """
    status = get_model_status()
    
    return {
        'status': status.get('status'),
        'last_trained': status.get('last_trained'),
        'metrics': status.get('metrics'),
        'model_version': status.get('version')
    }


# Инициализация при старте
@app.on_event("startup")
async def startup_event():
    """
    Проверка модели при старте сервиса.
    """
    try:
        status = get_model_status()
        logger.info(f"MLService started. Model status: {status.get('status')}")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
