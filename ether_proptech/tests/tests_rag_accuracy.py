import pytest
from src.core.rag_engine import RAGEngine
from src.core.validator import ResponseValidator
import os

# Моковые данные для теста (в реальном тесте поднимается тестовый контенер)
@pytest.fixture
def engine():
    # Подключение к тестовой БД
    return RAGEngine(db_host="localhost", llm_host="http://localhost:11434", model_name="qwen2.5:7b-instruct")

@pytest.fixture
def validator():
    return ResponseValidator()

def test_noise_regulation_citation(engine, validator):
    """Проверка: вопрос про шум должен вернуть ответ со ссылкой на ГОСТ."""
    query = "До скольки можно шуметь ночью?"
    
    # Эмуляция поиска (предполагаем, что база уже наполнена файлом gost_noise_control.md)
    context = engine.search_context(query)
    
    assert len(context) > 0, "Контекст не найден. Проверьте индексацию документов."
    
    response = engine.generate_response(context, query)
    
    # Главная проверка: есть ли ссылка?
    is_valid = validator.validate(response, context)
    
    assert is_valid, f"Галлюцинация обнаружена! Ответ без ссылки на документ: {response}"
    assert "[ГОСТ" in response or "[СанПиН" in response, "Ответ не содержит названия нормативного документа."

def test_unknown_question_handling(engine, validator):
    """Проверка: на вопрос вне темы система должна сказать, что не знает."""
    query = "Какой рецепт борща лучший?"
    
    context = engine.search_context(query)
    # Если контекст пустой или нерелевантный, промпт должен заставить модель молчать
    response = engine.generate_response(context, query)
    
    assert "отсутствует регламентация" in response.lower() or "нет информации" in response.lower(), \
        f"Система выдумала ответ на нерелевантный вопрос: {response}"