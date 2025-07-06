# api/src/azuraforge_api/services/experiment_service.py

import json
import itertools
import uuid
import os
import redis
import copy
from datetime import datetime
from typing import List, Dict, Any, Generator, Union, Optional
from fastapi import HTTPException
from sqlalchemy import desc
from celery import Celery
from celery.result import AsyncResult
from importlib import resources
import pandas as pd
import numpy as np

from azuraforge_dbmodels import Experiment, sa_create_engine, get_session_local
from azuraforge_learner import Learner, Sequential
from azuraforge_learner.pipelines import TimeSeriesPipeline
from ..core.exceptions import AzuraForgeException, ExperimentNotFoundException, PipelineNotFoundException, ConfigNotFoundException

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL: raise ValueError("API: DATABASE_URL ortam değişkeni ayarlanmamış!")
engine = sa_create_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("azuraforge_tasks", broker=REDIS_URL, backend=REDIS_URL)

REDIS_PIPELINES_KEY = "azuraforge:pipelines_catalog"
_pipeline_cache: Dict[str, Any] = {}
_model_cache: Dict[str, Learner] = {}

def get_pipelines_from_redis() -> List[Dict[str, Any]]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        official_apps_data = []
        try:
            with resources.open_text("azuraforge_applications", "official_apps.json") as f:
                official_apps_data = json.load(f)
        except Exception: official_apps_data = []
        official_apps_map = {app['id']: app for app in official_apps_data}
        pipeline_catalog_raw = r.hgetall(REDIS_PIPELINES_KEY)
        if not pipeline_catalog_raw: return []
        pipelines = []
        for name, data_str in pipeline_catalog_raw.items():
            pipeline_data = json.loads(data_str)
            official_meta = official_apps_map.get(name, {})
            for key, value in official_meta.items():
                if key not in pipeline_data: pipeline_data[key] = value
            pipelines.append(pipeline_data)
        return sorted(pipelines, key=lambda p: p.get('name', p['id']))
    except Exception as e:
        print(f"API Error fetching pipelines from Redis: {e}")
        return []

def _parse_value(value: Union[str, list, int, float]) -> list:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    if isinstance(value, list): return value
    if isinstance(value, str):
        items = [item.strip() for item in value.split(',')]
        processed_items = []
        for item in items:
            try: processed_items.append(float(item))
            except (ValueError, TypeError): processed_items.append(item)
        return processed_items
    return [value]

def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    static_params, varying_params = {}, {}
    def find_varying_params(d, path=""):
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict): find_varying_params(value, current_path)
            elif (isinstance(value, str) and ',' in value) or (isinstance(value, list) and len(value) > 1): varying_params[current_path] = _parse_value(value)
    find_varying_params(config)
    if not varying_params: yield config; return
    param_names, param_values = list(varying_params.keys()), list(varying_params.values())
    for combo_values in itertools.product(*param_values):
        new_config = copy.deepcopy(config)
        for i, key_path in enumerate(param_names):
            keys = key_path.split('.'); d = new_config
            for k in keys[:-1]: d = d.setdefault(k, {})
            d[keys[-1]] = combo_values[i]
        yield new_config

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    task_ids, batch_name = [], config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    combinations, num_combinations = list(_generate_config_combinations(config)), len(list(_generate_config_combinations(config)))
    batch_id = str(uuid.uuid4()) if num_combinations > 1 else None
    batch_name = batch_name if num_combinations > 1 else None
    for single_config in combinations:
        single_config.update({'batch_id': batch_id, 'batch_name': batch_name})
        task = celery_app.send_task("start_training_pipeline", args=[single_config]); task_ids.append(task.id)
    if num_combinations > 1: return {"message": f"{num_combinations} experiments submitted as batch '{batch_name}'.", "batch_id": batch_id, "task_ids": task_ids}
    else: return {"message": "Experiment submitted to worker.", "task_id": task_ids[0]}

def get_available_pipelines() -> List[Dict[str, Any]]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    pipelines = get_pipelines_from_redis()
    for p in pipelines: p.pop('default_config', None); p.pop('form_schema', None)
    return pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    pipelines = get_pipelines_from_redis()
    pipeline_info = next((p for p in pipelines if p['id'] == pipeline_id), None)
    if not pipeline_info: raise ConfigNotFoundException(pipeline_id=pipeline_id)
    return pipeline_info

def list_experiments() -> List[Dict[str, Any]]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    db = SessionLocal()
    try:
        experiments_from_db = db.query(Experiment).order_by(desc(Experiment.created_at)).all()
        all_experiments_data = []
        for exp in experiments_from_db:
            def safe_get(d, keys, default=None):
                if not isinstance(d, dict): return default
                for key in keys:
                    if not isinstance(d, dict) or key not in d: return default
                    d = d[key]
                return d

            config_summary = {
                "ticker": safe_get(exp.config, ["data_sourcing", "ticker"]),
                "location": f"{safe_get(exp.config, ['data_sourcing', 'latitude'])}, {safe_get(exp.config, ['data_sourcing', 'longitude'])}" if safe_get(exp.config, ['data_sourcing', 'latitude']) else None,
                "epochs": safe_get(exp.config, ["training_params", "epochs"]),
                "lr": safe_get(exp.config, ["training_params", "lr"]),
            }
            config_summary = {k: v for k, v in config_summary.items() if v is not None}

            summary = {
                "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
                "status": exp.status, "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
                "batch_id": exp.batch_id, "batch_name": exp.batch_name, "model_path": exp.model_path,
                "config_summary": config_summary,
                "results_summary": {
                    "final_loss": safe_get(exp.results, ["final_loss"]),
                    "r2_score": safe_get(exp.results, ["metrics", "r2_score"]),
                    "mae": safe_get(exp.results, ["metrics", "mae"]),
                    "accuracy": safe_get(exp.results, ["metrics", "accuracy"])
                },
                "config": exp.config, "results": exp.results, "error": exp.error
            }
            all_experiments_data.append(summary)
        return all_experiments_data
    finally:
        db.close()

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp: raise ExperimentNotFoundException(experiment_id=experiment_id)
        return { "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name, "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error, "created_at": exp.created_at.isoformat() if exp.created_at else None, "completed_at": exp.completed_at.isoformat() if exp.completed_at else None, "failed_at": exp.failed_at.isoformat() if exp.failed_at else None, "batch_id": exp.batch_id, "batch_name": exp.batch_name, }
    finally: db.close()

def get_task_status(task_id: str) -> Dict[str, Any]:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}

def get_experiment_report_path(experiment_id: str) -> str:
    # ... (Bu fonksiyonun içeriği aynı kalıyor, değişiklik yok) ...
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp: raise ExperimentNotFoundException(experiment_id=experiment_id)
        report_dir = exp.config.get('experiment_dir')
        if not report_dir or not os.path.isdir(report_dir): raise AzuraForgeException(status_code=404, detail=f"Report directory for experiment '{experiment_id}' not found.", error_code="REPORT_NOT_FOUND")
        return report_dir
    finally: db.close()

# === DEĞİŞİKLİK BURADA BAŞLIYOR ===
def predict_with_model(experiment_id: str, request_data: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp: raise ExperimentNotFoundException(experiment_id=experiment_id)
        if not exp.model_path or not os.path.exists(exp.model_path): raise AzuraForgeException(status_code=404, detail=f"No model artifact for experiment '{experiment_id}'.", error_code="MODEL_ARTIFACT_NOT_FOUND")
        
        from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES
        PipelineClass = AVAILABLE_PIPELINES.get(exp.pipeline_name)
        if not PipelineClass: raise PipelineNotFoundException(pipeline_id=exp.pipeline_name)
        
        pipeline_instance = PipelineClass(exp.config)
        is_timeseries = isinstance(pipeline_instance, TimeSeriesPipeline)

        # Scaler'ların eğitim verisine göre fit edilmesi gerekiyor
        if is_timeseries:
            from azuraforge_worker.tasks.training_tasks import get_shared_data
            full_config_json = json.dumps(exp.config, sort_keys=True)
            historical_data = get_shared_data(exp.pipeline_name, full_config_json)
            pipeline_instance._fit_scalers(historical_data)

        # Modelin beklediği girdi şeklini hazırla
        num_features = len(exp.results.get('feature_cols', [])) if exp.results else 1
        seq_len = exp.config.get('model_params', {}).get('sequence_length', 60)
        model_input_shape = (1, seq_len, num_features) if is_timeseries else (1, 3, 32, 32)
        model = pipeline_instance._create_model(model_input_shape)
        learner = pipeline_instance._create_learner(model, [])
        learner.load_model(exp.model_path)

        # Tahmin için kullanılacak veriyi belirle
        request_df = None
        if request_data:
            # Durum 1: Kullanıcı özel veri sağladı
            request_df = pd.DataFrame(request_data)
        elif is_timeseries:
            # Durum 2: Kullanıcı veri sağlamadı, zaman serisi için son veriyi kullan
            if 'historical_data' not in locals(): # Eğer daha önce yüklenmediyse tekrar yükle
                from azuraforge_worker.tasks.training_tasks import get_shared_data
                full_config_json = json.dumps(exp.config, sort_keys=True)
                historical_data = get_shared_data(exp.pipeline_name, full_config_json)
            
            if len(historical_data) < seq_len:
                raise AzuraForgeException(status_code=400, detail=f"Not enough historical data ({len(historical_data)}) to form a sequence of length {seq_len}.", error_code="INSUFFICIENT_DATA")
            
            request_df = historical_data.tail(seq_len)
        else:
            # Durum 3: Veri yok ve zaman serisi değil, hata ver
            raise AzuraForgeException(status_code=400, detail="Prediction data is required for non-time-series models.", error_code="PREDICTION_DATA_REQUIRED")
        
        # Veriyi tahmin için hazırla ve tahmini yap
        if not hasattr(pipeline_instance, 'prepare_data_for_prediction'): raise NotImplementedError("The pipeline does not implement 'prepare_data_for_prediction'.")
        
        prepared_data = pipeline_instance.prepare_data_for_prediction(request_df)
        scaled_prediction = learner.predict(prepared_data)
        
        if not hasattr(pipeline_instance, 'target_scaler'): raise RuntimeError("The pipeline's target_scaler is not available.")
        
        unscaled_prediction = pipeline_instance.target_scaler.inverse_transform(scaled_prediction)
        
        if exp.config.get("feature_engineering", {}).get("target_col_transform") == 'log':
            final_prediction = np.expm1(unscaled_prediction)
        else:
            final_prediction = unscaled_prediction
            
        return {"prediction": final_prediction.flatten()[0], "experiment_id": experiment_id}
    finally:
        db.close()
# === DEĞİŞİKLİK BURADA BİTİYOR ===