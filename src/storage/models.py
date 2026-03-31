from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MovieRecord:
    movie_pk: str
    csv_movie_id: Optional[str]
    tmdb_id: Optional[int]
    title: str
    normalized_title: str
    release_date: Optional[str]
    release_year: int
    director: Optional[str]
    genres: str
    original_language: Optional[str]
    runtime_min: Optional[int]
    imdb_rating: Optional[float]
    vote_count: int
    popularity: Optional[float]
    overview: str
    tagline: Optional[str]
    review_snippet: Optional[str]
    source_flags: str


@dataclass
class MovieDocumentRecord:
    doc_id: str
    movie_pk: str
    title: str
    document_text: str
    metadata_json: str
