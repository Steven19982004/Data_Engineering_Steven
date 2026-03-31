# Movie Intelligence Agent

A local-first **Data Engineering + Tool-based Agent** coursework prototype for movie discovery, comparison, and text analysis.

## 1. Project Overview

This project builds an end-to-end workflow that:
- ingests movie data from multiple sources
- cleans and merges data into a canonical dataset
- stores structured data in SQLite
- builds document-level semantic retrieval
- routes user questions to structured tools, semantic retrieval, or both
- returns grounded answers with evidence titles

The system is intentionally designed to be:
- easy to run locally
- easy to explain in a report
- modular enough to extend

## 2. Assignment Alignment (MSIN0166)

This submission aligns with core Data Engineering + Agent requirements:

1. Multiple data sources
- local CSV fixture + TMDB-style JSON fixture (optional live TMDB API)

2. Data cleaning and merge pipeline
- title normalization, year harmonization, genre normalization, null handling, dedupe, source merge

3. Structured storage
- SQLite tables: `movies`, `movie_documents`

4. Vector retrieval / RAG
- local semantic retriever with persistent vector store (Chroma preferred, JSON fallback)

5. Tool-based agent
- SQL tools + semantic search tool + lightweight router

6. Logging and error handling
- consistent stage-level logging and defensive fallback logic

7. Simple evaluation
- query-level evaluation with expected vs actual tool path and groundedness checks

8. Security
- `.env`-based configuration, no hardcoded API keys

## 3. Architecture Summary

Pipeline:
1. ingest (`csv_loader`, `tmdb_client`)
2. clean (`clean_movies`)
3. merge (`merge_sources`)
4. document build (`build_documents`)
5. store in SQLite (`movies`, `movie_documents`)
6. embed + vector index (`retriever`)
7. agent router/tool execution (`structured`, `semantic`, `hybrid`)

See:
- `docs/architecture.md`
- `docs/data_lineage.md`

## 4. Repository Structure

```text
Movie-Intelligence-Agent/
├── data/
│   ├── fixtures/
│   ├── raw/
│   └── processed/
├── docs/
├── logs/
├── scripts/
├── src/
│   ├── config.py
│   ├── ingestion/
│   ├── processing/
│   ├── storage/
│   ├── retrieval/
│   ├── tools/
│   ├── agent/
│   └── evaluation/
└── tests/
```

## 5. Data Sources

This prototype uses two local-first sources by default:
- `data/fixtures/sample_movies.csv` (structured movie records)
- `data/fixtures/tmdb_sample_movies.json` (TMDB-style JSON fixture)

Optional:
- live TMDB API (`ENABLE_TMDB_API=true` + `TMDB_API_KEY`)

## 6. Installation

```bash
cd /Users/cai/Desktop/Movie-Intelligence-Agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 7. Environment Variables

Configured via `.env` (template in `.env.example`):

- Runtime:
  - `APP_ENV`, `LOG_LEVEL`, `LOG_PATH`
- Keys:
  - `OPENAI_API_KEY`, `TMDB_API_KEY`
- Agent/LLM:
  - `USE_REAL_LLM`, `LLM_PROVIDER`, `LLM_MODEL`
- Data source:
  - `ENABLE_TMDB_API`, `FIXTURE_MOVIES_CSV`, `FIXTURE_TMDB_JSON`
- Storage:
  - `SQLITE_PATH`, `VECTOR_DB_BACKEND`, `VECTOR_DB_PATH`
- Retrieval:
  - `EMBEDDING_MODEL`, `DEFAULT_TOP_K`
- Business thresholds:
  - `MIN_VOTE_COUNT`, `HIGH_RATING_THRESHOLD`, `YEAR_FILTER_DEFAULT`

## 8. Run Pipeline

```bash
python3 scripts/seed_sample_data.py
python3 scripts/run_pipeline.py
```

Outputs:
- `data/processed/01_ingested_csv.csv`
- `data/processed/02_ingested_tmdb.csv`
- `data/processed/03_cleaned_csv.csv`
- `data/processed/04_cleaned_tmdb.csv`
- `data/processed/05_merged_movies.csv`
- `data/processed/06_movie_documents.csv`
- `storage/movie_agent.db`
- local vector index under `storage/` (Chroma or JSON fallback)

## 9. Run Agent

```bash
python3 scripts/run_agent.py --query "找出 2015 年后的高评分科幻片"
python3 scripts/run_agent.py --query "找出与 Interstellar 风格相似的电影"
python3 scripts/run_agent.py --query "比较 Christopher Nolan 和 Denis Villeneuve 的电影表现"
```

Optional:
```bash
python3 scripts/run_agent.py --query "..." --json
python3 scripts/run_agent.py --query "..." --rebuild-index
```

## 10. Run Evaluation

```bash
python3 scripts/run_evaluation.py
```

Saved reports:
- `data/processed/evaluation_results.json`
- `data/processed/evaluation_results.md`

Each evaluation case records:
- query
- expected tool path
- actual tool path
- retrieved movie titles
- final answer
- grounded/basic reasonableness

## 11. Example Queries

See `docs/sample_queries.md` for 10 representative queries.

## 12. Limitations

- Dataset is fixture-sized, not full production scale.
- Router is heuristic keyword-based (lightweight by design).
- Semantic quality depends on embedding backend:
  - best with `sentence-transformers`
- deterministic fallback available if dependency missing
- If LLM/API dependencies are unavailable, deterministic responder is used.

## 13. Privacy and Security

- Keys are environment-managed only.
- No key values in source files.
- Default setup supports local-only operation without sending data to external LLM.
- Responses are grounded in indexed local data and explicitly state evidence boundaries.

## 14. Why This Fits Individual Coursework

This repository provides a complete, coherent, and local-runnable prototype that demonstrates core data engineering competencies plus practical agent behavior without overengineering.

It is intentionally scoped for:
- fast implementation
- robust demo
- transparent report writing
- clear appendices with readable code
