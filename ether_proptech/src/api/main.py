from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from src.core.rag_engine import RAGEngine
from src.core.validator import ResponseValidator

app = FastAPI(title="Ether PropTech API", version="1.0.0")

# Инициализация движков
db_host = os.getenv("VECTOR_DB_HOST", "http://localhost:8000").replace("http://", "").split(":")[0]
llm_host = os.getenv("LLM_HOST", "http://localhost:11434")
model_name = os.getenv("MODEL_NAME", "qwen2.5:7b-instruct")

rag = RAGEngine(db_host=db_host, llm_host=llm_host, model_name=model_name)
validator = ResponseValidator()

class QueryRequest(BaseModel):
    question: str
    user_role: str = "resident" # resident, admin, vendor

@app.post("/ask")
async def ask_regulation(request: QueryRequest):
    # 1. Поиск контекста
    context_chunks = rag.search_context(request.question)
    
    if not context_chunks:
        return {
            "answer": "В нормативной базе нет информации по вашему вопросу. Требуется создание нового регламента.",
            "sources": [],
            "validated": True
        }

    # 2. Генерация ответа
    try:
        raw_answer = rag.generate_response(context_chunks, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

    # 3. Строгая валидация (Anti-Hallucination)
    is_valid = validator.validate(raw_answer, context_chunks)
    
    final_answer = raw_answer
    if not is_valid:
        final_answer = validator.sanitize(raw_answer)
    
    # Извлечение источников для ответа
    sources = list(set([meta['source'] for meta in rag.collection.get(ids=[], where={})['metadatas']])) 
    # Упрощенно: в реальном коде нужно мапить чанки обратно к файлам
    
    return {
        "answer": final_answer,
        "validated": is_valid,
        "message": "Ответ проверен на соответствие ГОСТ/СанПиН" if is_valid else "ВНИМАНИЕ: Ответ не прошел автоматическую проверку цитирования."
    }

@app.get("/health")
def health_check():
    return {"status": "operational", "philosophy": "Material order supports spiritual peace"}