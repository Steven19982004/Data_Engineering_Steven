from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import load_npz, save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

from movie_intelligence_agent.exceptions import PipelineError
from movie_intelligence_agent.logger import get_logger


@dataclass
class LocalVectorStore:
    store_dir: Path

    def __post_init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.vectorizer_path = self.store_dir / "vectorizer.joblib"
        self.matrix_path = self.store_dir / "matrix.npz"
        self.metadata_path = self.store_dir / "metadata.json"

    def build_index(self, documents: list[dict[str, str]]) -> None:
        if not documents:
            raise PipelineError("Cannot build vector index with empty documents")

        texts = [doc["text"] for doc in documents]
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=6000)
        matrix = vectorizer.fit_transform(texts)

        joblib.dump(vectorizer, self.vectorizer_path)
        save_npz(self.matrix_path, matrix)

        with self.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)

        self.logger.info("Vector index built: %s docs", len(documents))

    def query(self, query_text: str, top_k: int = 5) -> list[dict[str, str | float]]:
        if not self.exists():
            raise PipelineError(
                "Vector store not found. Please run pipeline first: scripts/run_pipeline.py"
            )

        vectorizer: TfidfVectorizer = joblib.load(self.vectorizer_path)
        matrix = load_npz(self.matrix_path)
        metadata = self._load_metadata()

        q_vec = vectorizer.transform([query_text])

        dot_scores = (matrix @ q_vec.T).toarray().ravel()
        matrix_norm = np.sqrt(matrix.multiply(matrix).sum(axis=1)).A1
        query_norm = float(np.sqrt(q_vec.multiply(q_vec).sum()))
        denom = np.maximum(matrix_norm * query_norm, 1e-12)
        cosine_scores = dot_scores / denom

        top_indices = np.argsort(cosine_scores)[::-1][:top_k]

        results: list[dict[str, str | float]] = []
        for idx in top_indices:
            if idx >= len(metadata):
                continue
            doc = metadata[idx]
            results.append(
                {
                    "movie_id": doc["movie_id"],
                    "title": doc["title"],
                    "score": round(float(cosine_scores[idx]), 4),
                    "text": doc["text"][:360],
                }
            )
        return results

    def exists(self) -> bool:
        return (
            self.vectorizer_path.exists()
            and self.matrix_path.exists()
            and self.metadata_path.exists()
        )

    def _load_metadata(self) -> list[dict[str, str]]:
        with self.metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
