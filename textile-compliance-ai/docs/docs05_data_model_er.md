# Модель данных (Entity-Relationship)

База знаний системы построена на векторном хранилище, но логическая структура метаданных описывается следующей схемой.

## Сущности

1.  **Document**: Represents a source file (PDF/DOCX).
    *   `id`: UUID
    *   `title`: String (e.g., "ГОСТ 31396-2018")
    *   `type`: Enum (GOST, GRANT_RULE, MARKETPLACE_RULE)
    *   `version`: String (e.g., "2025-edition")
    *   `upload_date`: Timestamp
    *   `file_path`: String

2.  **Chunk**: A segment of text extracted from a Document for vectorization.
    *   `id`: UUID
    *   `document_id`: FK -> Document.id
    *   `content`: Text (the actual text segment)
    *   `chunk_index`: Integer (order in document)
    *   `metadata`: JSON (page_number, section_header)
    *   `embedding`: Vector (stored in ChromaDB, not SQL)

3.  **QueryLog**: History of user interactions for analytics.
    *   `id`: UUID
    *   `session_id`: String
    *   `query_text`: Text
    *   `response_text`: Text
    *   `sources_used`: Array of Document IDs
    *   `feedback_score`: Integer (1-5, optional)

## Диаграмма (PlantUML)

Вы можете сгенерировать визуальную схему, используя код ниже в любом редакторе PlantUML или онлайн (plantuml.com).

```plantuml
@startuml
entity "Document" as D {
    *id : UUID <<PK>>
    --
    title : VARCHAR
    type : ENUM
    version : VARCHAR
    upload_date : TIMESTAMP
}

entity "Chunk" as C {
    *id : UUID <<PK>>
    --
    document_id : UUID <<FK>>
    content : TEXT
    chunk_index : INT
    metadata : JSON
}

entity "QueryLog" as Q {
    *id : UUID <<PK>>
    --
    session_id : VARCHAR
    query_text : TEXT
    response_text : TEXT
    feedback_score : INT
}

D ||--o{ C : contains
Q ..> C : references (via metadata)
@enduml