import os
import hashlib
from typing import List, Dict
import requests
from chromadb import HttpClient
from markdown import markdown

class RAGEngine:
    def __init__(self, db_host: str, llm_host: str, model_name: str):
        self.client = HttpClient(host=db_host, port=8000)
        self.collection = self.client.get_or_create_collection(name="regulations")
        self.llm_host = llm_host
        self.model_name = model_name

    def ingest_document(self, file_path: str, doc_id: str):
        """Читает Markdown файл и добавляет в векторную базу."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Простое разбиение по заголовкам (для MVP)
        # В продакшене лучше использовать LangChain RecursiveCharacterTextSplitter
        chunks = content.split('# ') 
        # Добавляем обратно разделитель, который lost при split
        chunks = [f"# {c}" for c in chunks if c.strip()]

        for i, chunk in enumerate(chunks):
            self.collection.add(
                documents=[chunk],
                ids=[f"{doc_id}_chunk_{i}"],
                metadatas=[{"source": os.path.basename(file_path)}]
            )
        print(f"[INFO] Документ {doc_id} индексирован ({len(chunks)} чанков).")

    def search_context(self, query: str, n_results: int = 3) -> List[str]:
        """Ищет релевантные куски регламентов."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

    def generate_response(self, context: List[str], query: str) -> str:
        """Отправляет запрос в локальную LLM с жестким системным промптом."""
        
        # Читаем мастер-промпт
        with open('src/llm/prompts/system_master.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        context_text = "\n\n".join(context)
        full_prompt = system_prompt.format(context_chunks=context_text, query=query)

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": 0.0} # Температура 0 для максимальной детерминированности
        }

        response = requests.post(f"{self.llm_host}/api/generate", json=payload)
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            raise Exception(f"LLM Error: {response.text}")