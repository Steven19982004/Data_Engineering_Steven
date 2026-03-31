from __future__ import annotations

from datetime import datetime, timezone

from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.data.extract import DataExtractor
from movie_intelligence_agent.data.load import SQLiteLoader
from movie_intelligence_agent.data.transform import DataTransformer
from movie_intelligence_agent.exceptions import PipelineError
from movie_intelligence_agent.logger import configure_logging, get_logger
from movie_intelligence_agent.retrieval.vector_store import LocalVectorStore


def run_data_pipeline(settings: Settings) -> dict[str, int | str]:
    settings.ensure_directories()
    configure_logging(settings.log_path)
    logger = get_logger("pipeline")

    extractor = DataExtractor(settings)
    transformer = DataTransformer()
    loader = SQLiteLoader(settings.sqlite_path)
    vector_store = LocalVectorStore(settings.vector_store_dir)

    try:
        movies_raw = extractor.load_movies_catalog()
        ratings_raw = extractor.load_ratings_snapshot()
        reviews_raw = extractor.load_reviews_corpus()

        movies_clean = transformer.clean_movies(movies_raw)
        ratings_clean = transformer.clean_ratings(ratings_raw)
        reviews_clean = transformer.clean_reviews(reviews_raw)

        movies_merged = transformer.merge_movies_and_ratings(movies_clean, ratings_clean)

        enrichment_df = extractor.get_omdb_enrichment(movies_merged["title"].tolist())
        movies_enriched = transformer.attach_enrichment(movies_merged, enrichment_df)

        reviews_mapped = transformer.attach_movie_ids_to_reviews(reviews_clean, movies_enriched)

        loader.load_all(movies_enriched, reviews_mapped)

        documents = transformer.build_movie_documents(movies_enriched, reviews_mapped)
        vector_store.build_index(documents)

        lineage_payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "sources": [
                "data/raw/movies_catalog.csv",
                "data/raw/ratings_snapshot.csv",
                "data/raw/reviews_corpus.jsonl",
                "data/raw/omdb_fixture.json (or OMDb API if enabled)",
            ],
            "transformations": [
                "title normalization",
                "date parsing",
                "type casting",
                "deduplication",
                "movies-ratings merge",
                "reviews-to-movie mapping",
                "OMDb enrichment",
                "document build for vector retrieval",
            ],
            "storage": {
                "sqlite": str(settings.sqlite_path),
                "vector_store": str(settings.vector_store_dir),
            },
        }

        transformer.write_processed_files(
            merged_movies_df=movies_enriched,
            processed_dir=settings.processed_data_dir,
            lineage_payload=lineage_payload,
        )

        summary = {
            "movies_loaded": int(len(movies_enriched)),
            "reviews_loaded": int(len(reviews_mapped)),
            "documents_indexed": int(len(documents)),
            "sqlite_path": str(settings.sqlite_path),
            "vector_store_dir": str(settings.vector_store_dir),
        }
        logger.info("Pipeline summary: %s", summary)
        return summary
    except Exception as exc:
        logger.exception("Pipeline failed")
        raise PipelineError(str(exc)) from exc
