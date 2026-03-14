import requests
import time
import logging
from src.core.config import LLM_CONFIG

logger = logging.getLogger("ether.llm")

def check_model_availability(retries: int = 5, delay: int = 5) -> bool:
    """
    Проверяет, запущена ли локальная LLM и загружена ли нужная модель.
    """
    url = f"{LLM_CONFIG['HOST']}/api/tags"
    
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = [m['name'] for m in models_data.get('models', [])]
                
                if any(LLM_CONFIG['MODEL_NAME'] in m for m in models):
                    logger.info(f"✅ Модель {LLM_CONFIG['MODEL_NAME']} готова к работе.")
                    return True
                else:
                    logger.warning(f"⚠️ Модель {LLM_CONFIG['MODEL_NAME']} не найдена. Доступные: {models}")
                    logger.info("💡 Запустите 'ollama pull qwen2.5:7b-instruct' или проверьте docker-compose.")
            else:
                logger.warning(f"Сервер LLM ответил кодом {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Попытка {i+1}/{retries}: Сервер LLM недоступен. Ожидание...")
        
        time.sleep(delay)
    
    logger.error("❌ Не удалось подключиться к локальной LLM после нескольких попыток.")
    return False

def get_embedding_model_info():
    # Заглушка для будущего расширения, если потребуется отдельная эмбеддинг-модель
    return {"provider": "local", "model": "all-minilm"}