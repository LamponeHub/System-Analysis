
---

### 4. 🤖 Скрипт загрузки данных (Ingestion Pipeline)
Реальный Python-скрипт, который превращает PDF-файлы в базу знаний. Это показывает ваши навыки работы с данными.

**Файл:** `src/ingest_documents.py`

```python
import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, '..', 'knowledge_base')
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, '..', 'chroma_db')

def load_and_process_documents():
    print("🚀 Запуск процесса загрузки документов...")
    
    # 1. Сбор всех PDF файлов
    documents = []
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"❌ Папка {KNOWLEDGE_BASE_DIR} не найдена. Создайте её и положите туда PDF файлы.")
        return

    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"📄 Обработка файла: {file}")
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                # Добавляем метаданные об источнике
                for doc in docs:
                    doc.metadata["source"] = file
                documents.extend(docs)

    if not documents:
        print("⚠️ Документы не найдены.")
        return

    # 2. Разбиение на чанки (Chunking)
    # Важно для русского языка: разбиваем по абзацам и заголовкам
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    splits = text_splitter.split_documents(documents)
    print(f"✅ Документы разбиты на {len(splits)} чанков.")

    # 3. Векторизация и сохранение
    # Используем модель, хорошо работающую с русским языком
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    print("💾 Сохранение в векторную базу ChromaDB...")
    db = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    
    print(f"✨ Готово! База знаний обновлена в папке {CHROMA_PERSIST_DIR}")

if __name__ == "__main__":
    try:
        load_and_process_documents()
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")