import json
import itertools
import uuid
import os
import redis
import copy
from datetime import datetime
from typing import List, Dict, Any, Generator
from sqlalchemy import create_engine, desc
from celery import Celery
from celery.result import AsyncResult
from importlib import resources

from azuraforge_dbmodels import Experiment, get_session_local
from azuraforge_learner.pipelines import TimeSeriesPipeline
from azuraforge_learner import Learner, Sequential, Linear, LSTM, Adam, SGD, MSELoss
from ..core.exceptions import AzuraForgeException, ExperimentNotFoundException, PipelineNotFoundException

# --- Veritabanı Kurulumu ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("API: DATABASE_URL ortam değişkeni ayarlanmamış!")
engine = create_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# --- Celery Kurulumu ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("azuraforge_tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Redis'ten Pipeline Bilgisi Alma ---
REDIS_PIPELINES_KEY = "azuraforge:pipelines_catalog"

def get_pipelines_from_redis() -> List[Dict[str, Any]]:
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        
        official_apps_data = []
        try:
            with resources.open_text("azuraforge_applications", "official_apps.json") as f:
                official_apps_data = json.load(f)
        except (FileNotFoundError, ModuleNotFoundError):
            official_apps_data = []
        
        official_apps_map = {app['id']: app for app in official_apps_data}
        pipeline_catalog_raw = r.hgetall(REDIS_PIPELINES_KEY)
        
        if not pipeline_catalog_raw: return []

        pipelines = []
        for name, data_str in pipeline_catalog_raw.items():
            pipeline_data = json.loads(data_str)
            official_meta = official_apps_map.get(name, {})
            
            for key, value in official_meta.items():
                if key not in pipeline_data:
                    pipeline_data[key] = value
            
            pipelines.append(pipeline_data)
            
        return sorted(pipelines, key=lambda p: p.get('name', p['id']))
        
    except Exception as e:
        print(f"API Error fetching pipelines from Redis: {e}")
        return []

def _generate_config_combinations(config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    batch_params = config.pop("batch_params", None)
    if not batch_params or not isinstance(batch_params, dict):
        yield config
        return
    varying_params = {k: v if isinstance(v, list) else [v] for k, v in batch_params.items()}
    if not varying_params:
        yield config
        return
    param_names = list(varying_params.keys())
    param_values = list(varying_params.values())
    for combo_values in itertools.product(*param_values):
        new_config = copy.deepcopy(config)
        for i, key in enumerate(param_names):
            keys = key.split('.')
            d = new_config
            for k in keys[:-1]: d = d.setdefault(k, {})
            d[keys[-1]] = combo_values[i]
        yield new_config

def get_available_pipelines() -> List[Dict[str, Any]]:
    pipelines = get_pipelines_from_redis()
    for p in pipelines:
        p.pop('default_config', None)
        p.pop('form_schema', None)
    return pipelines

def get_default_pipeline_config(pipeline_id: str) -> Dict[str, Any]:
    pipelines = get_pipelines_from_redis()
    pipeline_info = next((p for p in pipelines if p['id'] == pipeline_id), None)
    if not pipeline_info:
        raise ConfigNotFoundException(pipeline_id=pipeline_id)
    return pipeline_info

def start_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    task_ids = []
    batch_id = str(uuid.uuid4())
    batch_name = config.pop("batch_name", f"Batch-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}")
    combinations = list(_generate_config_combinations(config))
    num_combinations = len(combinations)
    for single_config in combinations:
        if num_combinations > 1:
            single_config['batch_id'] = batch_id
            single_config['batch_name'] = batch_name
        else:
            single_config['batch_id'] = None
            single_config['batch_name'] = None
        task = celery_app.send_task("start_training_pipeline", args=[single_config])
        task_ids.append(task.id)
    if num_combinations > 1:
        return {"message": f"{num_combinations} experiments submitted as a batch.", "batch_id": batch_id, "task_ids": task_ids}
    else:
        return {"message": "Experiment submitted to worker.", "task_id": task_ids[0]}
        
def list_experiments() -> List[Dict[str, Any]]:
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
            summary = { "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name, "status": exp.status, "created_at": exp.created_at.isoformat() if exp.created_at else None, "completed_at": exp.completed_at.isoformat() if exp.completed_at else None, "failed_at": exp.failed_at.isoformat() if exp.failed_at else None, "batch_id": exp.batch_id, "batch_name": exp.batch_name, "config_summary": { "ticker": safe_get(exp.config, ["data_sourcing", "ticker"], "N/A"), "epochs": safe_get(exp.config, ["training_params", "epochs"], "N/A"), "lr": safe_get(exp.config, ["training_params", "lr"], "N/A"), }, "results_summary": { "final_loss": safe_get(exp.results, ["final_loss"]), "r2_score": safe_get(exp.results, ["metrics", "r2_score"]), "mae": safe_get(exp.results, ["metrics", "mae"]), }, "config": exp.config, "results": exp.results, "error": exp.error }
            all_experiments_data.append(summary)
        return all_experiments_data
    finally: db.close()

def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise ExperimentNotFoundException(experiment_id=experiment_id)
        return { "experiment_id": exp.id, "task_id": exp.task_id, "pipeline_name": exp.pipeline_name, "status": exp.status, "config": exp.config, "results": exp.results, "error": exp.error, "created_at": exp.created_at.isoformat() if exp.created_at else None, "completed_at": exp.completed_at.isoformat() if exp.completed_at else None, "failed_at": exp.failed_at.isoformat() if exp.failed_at else None, "batch_id": exp.batch_id, "batch_name": exp.batch_name, }
    finally: db.close()

def get_task_status(task_id: str) -> Dict[str, Any]:
    task_result = AsyncResult(task_id, app=celery_app)
    return {"status": task_result.state, "details": task_result.info}

# Dosyanın sonuna eklenecek yeni fonksiyon:
_pipeline_cache = {} # Basit bir in-memory cache

def _get_pipeline_instance(exp: Experiment) -> TimeSeriesPipeline:
    """
    Bir deneye ait pipeline'ı cache'den alır veya oluşturur.
    Scaler'ların eğitilmesi için bir kereye mahsus çalıştırır.
    """
    exp_id = exp.id
    if exp_id in _pipeline_cache:
        return _pipeline_cache[exp_id]

    from azuraforge_worker.tasks.training_tasks import AVAILABLE_PIPELINES
    pipeline_name = exp.pipeline_name
    if pipeline_name not in AVAILABLE_PIPELINES:
        raise PipelineNotFoundException(pipeline_id=pipeline_name)
    
    PipelineClass = AVAILABLE_PIPELINES[pipeline_name]
    pipeline_instance = PipelineClass(exp.config)
    
    # Scaler'ları eğitmek için pipeline'ı bir kere çalıştır.
    # Bu maliyetli olabilir, bu yüzden cache'liyoruz.
    pipeline_instance.run(skip_training=True)
    
    _pipeline_cache[exp_id] = pipeline_instance
    return pipeline_instance

def predict_with_model(experiment_id: str, request_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise ExperimentNotFoundException(experiment_id=experiment_id)
        if not exp.model_path or not os.path.exists(exp.model_path):
            raise AzuraForgeException(status_code=404, detail=f"No model artifact for experiment '{experiment_id}'.", error_code="MODEL_ARTIFACT_NOT_FOUND")

        # 1. Pipeline'ı (scaler'larıyla birlikte) hazırla
        pipeline_instance = _get_pipeline_instance(exp)
        
        # 2. Learner'ı oluştur ve kaydedilmiş modeli yükle
        # Input shape'i pipeline'dan al
        num_features = len(pipeline_instance.feature_cols)
        seq_len = pipeline_instance.config['model_params']['sequence_length']
        model = pipeline_instance._create_model(input_shape=(1, seq_len, num_features))
        
        learner = pipeline_instance._create_learner(model, [])
        learner.load_model(exp.model_path)

        # 3. Gelen veriyi tahmin için hazırla
        request_df = pd.DataFrame(request_data)
        prepared_data = pipeline_instance.prepare_data_for_prediction(request_df)
        
        # 4. Tahmini yap
        scaled_prediction = learner.predict(prepared_data)
        
        # 5. Tahmini orijinal ölçeğine geri döndür
        unscaled_prediction = pipeline_instance.scaler.inverse_transform(scaled_prediction)
        
        if exp.config.get("feature_engineering", {}).get("target_col_transform") == 'log':
            final_prediction = np.expm1(unscaled_prediction)
        else:
            final_prediction = unscaled_prediction

        return {
            "prediction": final_prediction.flatten()[0],
            "experiment_id": experiment_id,
        }
    finally:
        db.close()