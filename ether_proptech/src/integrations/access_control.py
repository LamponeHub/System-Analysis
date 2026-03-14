import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = BASE_DIR / "docs"
REGULATIONS_DIR = DOCS_DIR / "regulations"
WORKFLOWS_DIR = DOCS_DIR / "workflows"

# Настройки LLM
LLM_CONFIG = {
    "HOST": os.getenv("LLM_HOST", "http://localhost:11434"),
    "MODEL_NAME": os.getenv("MODEL_NAME", "qwen2.5:7b-instruct"),
    "TEMPERATURE": 0.0,  # Строгая детерминированность
    "CONTEXT_WINDOW": 4096,
}

# Настройки Vector DB
VECTOR_DB_CONFIG = {
    "HOST": os.getenv("VECTOR_DB_HOST", "localhost"),
    "PORT": int(os.getenv("VECTOR_DB_PORT", "8000")),
    "COLLECTION_NAME": "ether_regulations",
}

# Пороги среды (Материальная реализация философии тишины)
# Значения основаны на ГОСТ 31319-2009 и СанПиН
ENVIRONMENT_THRESHOLDS = {
    "NOISE": {
        "DAY_LIMIT_DB": 40,      # 07:00 - 23:00
        "NIGHT_LIMIT_DB": 30,    # 23:00 - 07:00
        "CRITICAL_SPIKE_DB": 55, # Мгновенная реакция
        "DAY_START_HOUR": 7,
        "NIGHT_START_HOUR": 23,
    },
    "AIR": {
        "PM25_LIMIT_MG_M3": 0.015,
        "CO2_LIMIT_PPM": 1000,
        "SMOKE_DETECTION_THRESHOLD": 0.005, # Чувствительность к дыму
    }
}

# Настройки доступа (Блокировки)
ACCESS_CONTROL_CONFIG = {
    "AUTO_LOCK_DURATION_MINUTES": 60,  # Время блокировки гостевого доступа при нарушении
    "MAX_VIOLATIONS_BEFORE_PERMANENT_BLOCK": 3,
    "NOTIFY_ADMIN_ON_LOCK": True,
}

# API настройки
API_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 8080,
    "TITLE": "Ether PropTech API",
    "VERSION": "1.0.0"
}