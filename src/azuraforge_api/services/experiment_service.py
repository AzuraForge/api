import json
import itertools
import uuid
from datetime import datetime
from importlib import resources
from typing import List, Dict, Any, Generator
from fastapi import HTTPException
from celery.result import AsyncResult
from sqlalchemy import desc

from ..database import SessionLocal # DOĞRU IMPORT
from azuraforge_worker.database import Experiment 

from azuraforge_worker import celery_app
from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES_AND_CONFIGS

def get_available_pipelines() -> List[Dict[str, Any]]:
    official_apps_data = []
    try:
        with resources.open_text("azuraforge_applications", "official_apps.json") as f:
            official_apps_data = json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        pass
    available_pipelines = [app for app in official_apps_data if app.get("id") in AVAILABLE_PIPELINES_AND_CONFIGS]
    return available_pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    pipeline_info = AVAILABLE_PIPELINES_AND_CONFIGS.get(pipeline_id)
    if not pipeline_info:
        raise ValueError(f"Pipeline '{pipeline_id}' not found.")
    get_config_func = pipeline_info.get('get_config_func')
    if not get_config_func:
        return {"message": "No specific default configuration available."}
    return get_config_func()

def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    varying_params, static_params = {}, {}
    def _traverse_and_split(conf, path=""):
        for key, value in conf.items():
            new_path = f"{path}.{key}" if path else key
            if isinstance(value, list): varying_params[new_path] = value
            elif isinstance(value, dict): _traverse_and_split(value, new_path)
            else: static_params[new_path] = value
    _traverse_and_split(config)
    if not varying_params:
        yield config
        return
    param_names, param_values = list(varying_params.keys()), list(varying_params.values())
    for combo in itertools.product(*param_values):
        new_config = {}
        for key_path, value in static_params.items():
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]: d = d.setdefault(k, {})
            d[keys[-1]] = value
        for i, key_path in enumerate(param_names):
            keys = key_path.split('.')
            d = new_config
            for k in keys[:-1]: d = d.setdefault(k, {})
            d[keys[-1]] = combo[i]
        yield new_config

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    task_ids = []
    batch_id, batch_name = str(uuid.uuid4()), config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y-%m-%d-%H%M')}")
    combinations = list(_generate_config_combinations(config))
    num_combinations = len(combinations)
    for single_config in combinations:
        single_config['batch_id'] = batch_id if num_combinations > 1 else None
        single_config['batch_name'] = batch_name if num_combinations > 1 else None
        task = celery_app.send_task("start_training_pipeline", args=[single_config])
        task_ids.append(task.id)
    if num_combinations > 1:
        return {"message": f"{num_combinations} experiments submitted as a batch.", "batch_id": batch_id, "task_ids": task_ids}
    else:
        return {"message": "Experiment submitted to worker.", "task_id": task_ids[0]}

def list_experiments() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        experiments = db.query(Experiment).order_by(desc(Experiment.created_at)).all()
        return [{
            "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
            "status": exp.status,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
            "batch_id": exp.batch_id, "batch_name": exp.batch_name,
            "config_summary": {
                "ticker": exp.config.get("data_sourcing", {}).get("ticker", "N/A") if exp.config else "N/A",
                "epochs": exp.config.get("training_params", {}).get("epochs", "N/A") if exp.config else "N/A",
                "lr": exp.config.get("training_params", {}).get("lr", "N/A") if exp.config else "N/A",
            },
            "results_summary": {"final_loss": exp.results.get("final_loss") if exp.results else None}
        } for exp in experiments]
    finally:
        db.close()

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
        return {
            "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name,
            "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "failed_at": exp.failed_at.isoformat() if exp.failed_at else None,
            "batch_id": exp.batch_id, "batch_name": exp.batch_name,
        }
    finally:
        db.close()

def get_task_status(task_id: str) -> Dict[str, Any]:
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}