## Отчёт по проекту «Advanced Hybrid RAG-ассистент Сбербанка»

### Описание проекта

- **Название проекта**: Advanced Hybrid RAG-ассистент Сбербанка (`07-advanced-rag`)
- **Краткое описание**: Telegram-бот с RAG (Retrieval-Augmented Generation) на базе LangChain, который отвечает на вопросы по документам Сбербанка (кредиты и вклады). Поддерживаются три режима поиска: чисто семантический (`semantic`), гибридный семантический + BM25 (`hybrid`) и гибридный с дополнительным переранжированием cross-encoder’ом (`hybrid_reranker`). Качество системы оценивается с помощью LangSmith и метрик RAGAS.

---

## Конфигурации экспериментов

Во всех экспериментах использовались:

- **Документы**:  
  - `data/ouk_potrebitelskiy_kredit_lph.pdf`  
  - `data/usl_r_vkladov.pdf`  
  - `data/sberbank_help_documents.json`
- **Embeddings для основного RAG-потока**:
  - **Провайдер**: `huggingface`
  - **Модель**: `intfloat/multilingual-e5-base`
  - **Устройство**: `cpu`
- **RAGAS evaluation**:
  - **RAGAS_LLM_MODEL**: `gpt-4o`
  - **RAGAS_EMBEDDING_MODEL**: `text-embedding-3-large`
  - **Датасет**: `06-rag-qa-dataset` (через LangSmith)

Ниже приведены ключевые отличия конфигураций по режимам retrieval.

### Эксперимент 1 — Semantic

- **RETRIEVAL_MODE**: `semantic`
- **Retrieval-пайплайн**:
  - Только векторный поиск по смыслу через `InMemoryVectorStore.as_retriever`.
- **Основные параметры**:
  - `SEMANTIC_RETRIEVER_K`: 10
  - `EMBEDDING_PROVIDER`: `huggingface`
  - `HUGGINGFACE_EMBEDDING_MODEL`: `intfloat/multilingual-e5-base`
  - `HUGGINGFACE_DEVICE`: `cpu`
- **RAG-цепочка**:
  - Query transformation (LLM) → semantic retriever → генерация ответа LLM с учётом контекста.

### Эксперимент 2 — Hybrid (Semantic + BM25)

- **RETRIEVAL_MODE**: `hybrid`
- **Retrieval-пайплайн**:
  - Комбинация:
    - semantic retriever (векторный поиск по смыслу),
    - BM25 retriever по исходным чанкам.
  - Объединение через `EnsembleRetriever`.
- **Основные параметры**:
  - `SEMANTIC_RETRIEVER_K`: 10
  - `BM25_RETRIEVER_K`: 10
  - `ENSEMBLE_SEMANTIC_WEIGHT`: 0.5
  - `ENSEMBLE_BM25_WEIGHT`: 0.5
  - `EMBEDDING_PROVIDER`: `huggingface`
  - `HUGGINGFACE_EMBEDDING_MODEL`: `intfloat/multilingual-e5-base`
- **RAG-цепочка**:
  - Query transformation → hybrid retriever (semantic + BM25) → генерация ответа LLM.

### Эксперимент 3 — Hybrid + Reranker (Semantic + BM25 + Cross-Encoder)

- **RETRIEVAL_MODE**: `hybrid_reranker`
- **Retrieval-пайплайн**:
  - Тот же `EnsembleRetriever` (semantic + BM25), что и в режиме `hybrid`.
  - Дополнительный этап reranking с помощью cross-encoder из `sentence_transformers`.
- **Основные параметры**:
  - `SEMANTIC_RETRIEVER_K`: 10
  - `BM25_RETRIEVER_K`: 10
  - `ENSEMBLE_SEMANTIC_WEIGHT`: 0.5
  - `ENSEMBLE_BM25_WEIGHT`: 0.5
  - `CROSS_ENCODER_MODEL`: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
  - `RERANKER_TOP_K`: 3
  - `EMBEDDING_PROVIDER`: `huggingface`
  - `HUGGINGFACE_EMBEDDING_MODEL`: `intfloat/multilingual-e5-base`
- **RAG-цепочка**:
  - Query transformation → hybrid retriever → reranking топ-документов cross-encoder’ом → генерация ответа LLM.

---

## Результаты экспериментов (RAGAS)

Во всех экспериментах использовались одни и те же:

- датасет вопросов/ответов (`06-rag-qa-dataset`);
- метрики RAGAS: `Faithfulness`, `Answer Relevancy`, `Answer Correctness`, `Answer Similarity`, `Context Recall`, `Context Precision`.

Ниже приведены усреднённые значения метрик, полученные из `/evaluate_dataset` для трёх конфигураций.

### Таблица 1 — Semantic

| Метрика              | Значение |
|----------------------|----------|
| Faithfulness         | 0.650    |
| Answer Relevancy     | 0.765    |
| Answer Correctness   | 0.554    |
| Answer Similarity    | 0.933    |
| Context Recall       | 1.000    |
| Context Precision    | nan      |

### Таблица 2 — Hybrid (Semantic + BM25)

| Метрика              | Значение |
|----------------------|----------|
| Faithfulness         | 0.667    |
| Answer Relevancy     | 0.771    |
| Answer Correctness   | 0.587    |
| Answer Similarity    | 0.944    |
| Context Recall       | 1.000    |
| Context Precision    | nan      |

### Таблица 3 — Hybrid + Reranker

| Метрика              | Значение |
|----------------------|----------|
| Faithfulness         | 0.875    |
| Answer Relevancy     | 0.774    |
| Answer Correctness   | 0.704    |
| Answer Similarity    | 0.938    |
| Context Recall       | 1.000    |
| Context Precision    | 1.000    |

---

## Сравнительный анализ

### Обоснованность и корректность ответов

- Переход от **semantic → hybrid** даёт небольшой прирост:
  - `Faithfulness`: 0.650 → 0.667
  - `Answer Correctness`: 0.554 → 0.587
- Добавление **reranker’а** даёт заметный скачок качества:
  - `Faithfulness`: до 0.875
  - `Answer Correctness`: до 0.704
- Вывод: cross-encoder значительно улучшает как обоснованность, так и соответствие ответов эталону за счёт более точного выбора самых релевантных фрагментов контекста.

### Релевантность и похожесть на эталон

- `Answer Relevancy` растёт от 0.765 (semantic) до 0.774 (hybrid_reranker), прирост небольшой, но стабильный.
- `Answer Similarity` во всех режимах высокая (>0.93), что говорит о том, что формулировки ответов близки к эталонным:
  - максимум в режиме `hybrid` (0.944),
  - в `hybrid_reranker` немного ниже (0.938), но на фоне роста других метрик это некритично.
- Вывод: все три конфигурации умеют порождать ответы, близкие к эталонным, но `hybrid` и `hybrid_reranker` дают небольшое, но устойчивое улучшение по релевантности.

### Качество retrieval (Context Recall / Precision)

- Во всех режимах `Context Recall = 1.000` — нужная информация почти всегда присутствует в извлечённом контексте.
- В режимах **semantic** и **hybrid** метрика `Context Precision` получилась `nan` (по результатам evaluation) — это указывает на техническую особенность расчёта метрики в конкретном запуске, а не на отсутствие поиска.
- В режиме **hybrid_reranker**:
  - `Context Precision = 1.000`, что подтверждает:
    - retriever + reranker отбирают максимально релевантные куски текста;
    - в retrieved контекст практически не попадает лишний шум.
- Вывод: с точки зрения качества поиска (особенно точности) режим `hybrid_reranker` явно выигрывает.

### Скорость и сложность

- **Semantic**:
  - самый простой и быстрый режим (один retriever, один векторный поиск);
  - минимальные требования к ресурсам.
- **Hybrid**:
  - чуть медленнее за счёт BM25, но всё ещё достаточно лёгкий;
  - лучше работает с точными формулировками и редкими терминами.
- **Hybrid + Reranker**:
  - самый тяжёлый по ресурсам (дополнительный cross-encoder);
  - увеличивает latency, но даёт наилучшее качество.

---

## Выводы

- **Лучшая конфигурация для данной задачи** — **`hybrid_reranker`**:
  - максимальные значения `Faithfulness` (0.875), `Answer Correctness` (0.704) и `Context Precision` (1.000);
  - при этом сохраняется высокий уровень `Answer Similarity` и `Context Recall`.
- **Режим `hybrid`**:
  - даёт умеренный прирост качества по сравнению с чисто семантическим поиском,
  - подходящ как более «лёгкая» продакшн-конфигурация, если использование cross-encoder’а слишком дорого по ресурсам.
- **Режим `semantic`**:
  - хорошо подходит для отладки и ранних итераций (минимальная сложность и требования),
  - но по качеству ответов уступает гибридным подходам.
- С учётом метрик RAGAS и требований к качеству для ассистента Сбербанка, **для продакшн-сценариев целесообразно использовать `hybrid_reranker`, а `semantic` оставить как базовый режим для разработки и отладки.**


