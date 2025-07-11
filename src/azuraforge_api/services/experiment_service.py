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
import asyncio

from azuraforge_dbmodels import Experiment, sa_create_engine, get_session_local
from ..core.exceptions import AzuraForgeException, ExperimentNotFoundException, PipelineNotFoundException, ConfigNotFoundException

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL: raise ValueError("API: DATABASE_URL ortam değişkeni ayarlanmamış!")
engine = sa_create_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("azuraforge_tasks", broker=REDIS_URL, backend=REDIS_URL)

REDIS_PIPELINES_KEY = "azuraforge:pipelines_catalog"

# ... (list_experiments, get_default_pipeline_config vb. fonksiyonlar yukarıdaki gibi aynı kalıyor) ...
def get_pipelines_from_redis() -> List[Dict[str, Any]]:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        official_apps_data = []
        try:
            with resources.open_text("azuraforge_applications", "official_apps.json") as f: official_apps_data = json.load(f)
        except Exception: official_apps_data = []
        official_apps_map = {app['id']: app for app in official_apps_data}; pipeline_catalog_raw = r.hgetall(REDIS_PIPELINES_KEY)
        if not pipeline_catalog_raw: return []
        pipelines = [json.loads(data_str) for name, data_str in pipeline_catalog_raw.items()]; [p.update(official_apps_map.get(p['id'], {})) for p in pipelines]; return sorted(pipelines, key=lambda p: p.get('name', p['id']))
    except Exception as e: print(f"API Error fetching pipelines from Redis: {e}"); return []
def _parse_value(value: Union[str, list, int, float]) -> list:
    if isinstance(value, list): return value
    if isinstance(value, str):
        items = [item.strip() for item in value.split(',')]; processed_items = []
        for item in items:
            try: processed_items.append(float(item))
            except (ValueError, TypeError): processed_items.append(item)
        return processed_items
    return [value]
def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    static_params, varying_params = {}, {};
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
    task_ids, batch_name = [], config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    combinations = list(_generate_config_combinations(config)); num_combinations = len(combinations)
    batch_id, batch_name = (str(uuid.uuid4()) if num_combinations > 1 else None), (batch_name if num_combinations > 1 else None)
    for single_config in combinations:
        single_config.update({'batch_id': batch_id, 'batch_name': batch_name})
        task = celery_app.send_task("start_training_pipeline", args=[single_config]); task_ids.append(task.id)
    if num_combinations > 1: return {"message": f"{num_combinations} experiments submitted as batch '{batch_name}'.", "batch_id": batch_id, "task_ids": task_ids}
    else: return {"message": "Experiment submitted to worker.", "task_id": task_ids[0]}
def get_available_pipelines() -> List[Dict[str, Any]]:
    pipelines = get_pipelines_from_redis()
    for p in pipelines: p.pop('default_config', None); p.pop('form_schema', None)
    return pipelines
def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    pipelines = get_pipelines_from_redis(); pipeline_info = next((p for p in pipelines if p['id'] == pipeline_id), None)
    if not pipeline_info: raise ConfigNotFoundException(pipeline_id=pipeline_id)
    return pipeline_info
def list_experiments() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        experiments_from_db = db.query(Experiment).order_by(desc(Experiment.created_at)).all(); all_experiments_data = []
        for exp in experiments_from_db:
            def safe_get(d, keys, default=None):
                if not isinstance(d, dict): return default
                for key in keys:
                    if not isinstance(d, dict) or key not in d: return default
                    d = d[key]
                return d
            config_summary = {"ticker": safe_get(exp.config, ["data_sourcing", "ticker"]),"location": f"{safe_get(exp.config, ['data_sourcing', 'latitude'])}, {safe_get(exp.config, ['data_sourcing', 'longitude'])}" if safe_get(exp.config, ['data_sourcing', 'latitude']) else None,"epochs": safe_get(exp.config, ["training_params", "epochs"]),"lr": safe_get(exp.config, ["training_params", "lr"])}
            config_summary = {k: v for k, v in config_summary.items() if v is not None}
            summary = {"experiment_id": exp.id,"task_id": exp.task_id,"pipeline_name": exp.pipeline_name,"status": exp.status,"created_at": exp.created_at.isoformat() if exp.created_at else None,"completed_at": exp.completed_at.isoformat() if exp.completed_at else None,"failed_at": exp.failed_at.isoformat() if exp.failed_at else None,"batch_id": exp.batch_id,"batch_name": exp.batch_name,"model_path": exp.model_path,"config_summary": config_summary,"results_summary": {"final_loss": safe_get(exp.results, ["final_loss"]),"r2_score": safe_get(exp.results, ["metrics", "r2_score"]),"mae": safe_get(exp.results, ["metrics", "mae"]),"accuracy": safe_get(exp.results, ["metrics", "accuracy"])},"config": exp.config,"results": exp.results,"error": exp.error}
            all_experiments_data.append(summary)
        return all_experiments_data
    finally: db.close()
def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp: raise ExperimentNotFoundException(experiment_id=experiment_id)
        return { "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name, "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error, "created_at": exp.created_at.isoformat() if exp.created_at else None, "completed_at": exp.completed_at.isoformat() if exp.completed_at else None, "failed_at": exp.failed_at.isoformat() if exp.failed_at else None, "batch_id": exp.batch_id, "batch_name": exp.batch_name, }
    finally: db.close()
def get_task_status(task_id: str) -> Dict[str, Any]:
    task_result = AsyncResult(task_id, app=celery_app); return {"status": task_result.state, "details": task_result.info}
def get_experiment_report_path(experiment_id: str) -> str:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp: raise ExperimentNotFoundException(experiment_id=experiment_id)
        report_dir = exp.config.get('experiment_dir')
        if not report_dir or not os.path.isdir(report_dir): raise AzuraForgeException(status_code=404, detail=f"Report directory for experiment '{experiment_id}' not found.", error_code="REPORT_NOT_FOUND")
        return report_dir
    finally: db.close()

async def predict_with_model(experiment_id: str, request_data: Optional[List[Dict[str, Any]]], prediction_steps: Optional[int]) -> Dict[str, Any]:
    """
    Worker'a bir tahmin görevi gönderir ve sonucunu bekler.
    prediction_steps ek parametresi iletilir.
    """
    task = None
    try:
        task = celery_app.send_task(
            "predict_from_model_task",
            args=[experiment_id, request_data, prediction_steps] # prediction_steps eklendi
        )
        result = await asyncio.to_thread(task.get, timeout=60)
        return result

    except Exception as e:
        error_message = f"Prediction task failed: {str(e)}"
        if task and task.failed():
             original_exception = task.result
             error_message = f"Prediction task failed: {str(original_exception)}"

        print(f"API Error during prediction task: {error_message}")
        if task and task.traceback:
            print(f"Worker Traceback:\n{task.traceback}")

        raise AzuraForgeException(
            status_code=500,
            detail=error_message,
            error_code="PREDICTION_TASK_FAILED"
        )