# Architecture

## 1. End-to-End Flow

This project implements a full local workflow from data ingestion to grounded agent answers:

1. Ingestion layer
- `src/ingestion/csv_loader.py` loads local structured fixture CSV.
- `src/ingestion/tmdb_client.py` loads TMDB-style fixture JSON, with optional TMDB API path.
- `src/ingestion/ingest_pipeline.py` orchestrates both sources.

2. Processing layer
- `src/processing/clean_movies.py` standardizes title/year/genres and removes duplicates.
- `src/processing/merge_sources.py` merges sources by `(normalized_title, release_year)`.
- `src/processing/build_documents.py` creates embedding-ready text documents.
- `src/processing/validate_schema.py` validates canonical output before loading.

3. Storage layer
- `src/storage/db.py` creates SQLite schema (`movies`, `movie_documents`).
- `src/storage/repository.py` upserts canonical movies and documents.

4. Retrieval layer
- `src/retrieval/retriever.py` reads `movie_documents` from SQLite.
- `src/retrieval/embedder.py` builds embeddings.
- `src/retrieval/vector_store.py` persists vectors locally (Chroma preferred, JSON fallback).

5. Tool + Agent layer
- Structured tools: `search_movies_by_filters`, `get_top_rated_movies`, `compare_movies_or_directors`.
- Semantic tool: `semantic_movie_search`.
- Router (`src/agent/router.py`) selects structured/semantic/hybrid execution path.
- Agent service (`src/agent/agent_service.py`) composes tool outputs into grounded response.

## 2. Why SQLite + Local Vector Store

SQLite is selected because:
- zero service deployment
- one file DB suitable for coursework submission
- deterministic local reproducibility
- strong enough SQL expressiveness for filter/sort/aggregation tasks

Local vector store is selected because:
- enables semantic retrieval without cloud infrastructure
- supports RAG-style evidence retrieval for text similarity/theme queries
- can run fully offline using deterministic fallback

## 3. Prototype and Extensibility

This is intentionally a coursework-friendly prototype, but architecture is extendable:
- replace fixtures with production ETL/API ingestion
- swap SQLite with PostgreSQL
- swap fallback embedding with full sentence-transformer pipeline
- expose tools via REST API for external agent frameworks
- add evaluation dashboards and richer quality metrics
