"""Embedding-based semantic similarity with local fallback (no API required)."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from kip_core.organization.models import DocumentProfile

_WORD_RE = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)


def _tokenize_for_embedding(text: str, *, limit: int = 128) -> list[str]:
    tokens = [t.lower() for t in _WORD_RE.findall(text)]
    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
        if len(ordered) >= limit:
            break
    return ordered


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in set(a) & set(b))
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class CorpusSemanticModel:
    """TF-IDF vectors over a scan batch — lightweight local semantic embeddings."""

    vocabulary: dict[str, int]
    idf: dict[str, float]
    vectors: dict[str, dict[str, float]]
    embedder_name: str = "tfidf-local"

    def similarity(self, file_id_a: str, file_id_b: str) -> float:
        vec_a = self.vectors.get(file_id_a, {})
        vec_b = self.vectors.get(file_id_b, {})
        return round(_cosine(vec_a, vec_b), 4)


def _build_idf(doc_token_lists: list[list[str]]) -> dict[str, float]:
    doc_count = len(doc_token_lists) or 1
    df: Counter[str] = Counter()
    for tokens in doc_token_lists:
        for token in set(tokens):
            df[token] += 1
    return {token: math.log((1 + doc_count) / (1 + freq)) + 1.0 for token, freq in df.items()}


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens)
    total = sum(tf.values()) or 1
    vector: dict[str, float] = {}
    for token, count in tf.items():
        weight = (count / total) * idf.get(token, 1.0)
        if weight > 0:
            vector[token] = weight
    return vector


def fit_corpus_embeddings(profiles: list[DocumentProfile]) -> CorpusSemanticModel:
    """
    Fit batch-level TF-IDF vectors from semantic_text (content + path + role).

    Optional sentence-transformers path is attempted when installed; otherwise
    TF-IDF remains the conservative default (no external API).
    """
    st_model = _try_sentence_transformer()
    if st_model is not None:
        return _fit_sentence_transformer(profiles, st_model)

    doc_tokens: dict[str, list[str]] = {}
    for profile in profiles:
        combined = f"{profile.semantic_text} {' '.join(profile.context_tokens)}"
        doc_tokens[profile.file_id] = _tokenize_for_embedding(combined)

    idf = _build_idf(list(doc_tokens.values()))
    vocabulary = {token: idx for idx, token in enumerate(sorted(idf))}
    vectors = {
        file_id: _tfidf_vector(tokens, idf) for file_id, tokens in doc_tokens.items()
    }
    return CorpusSemanticModel(vocabulary=vocabulary, idf=idf, vectors=vectors)


def _try_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        return None


def _fit_sentence_transformer(profiles: list[DocumentProfile], model) -> CorpusSemanticModel:
    texts = [p.semantic_text or p.name for p in profiles]
    embeddings = model.encode(texts, normalize_embeddings=True)
    vectors: dict[str, dict[str, float]] = {}
    for profile, emb in zip(profiles, embeddings, strict=True):
        vectors[profile.file_id] = {f"dim_{i}": float(v) for i, v in enumerate(emb)}
    dim_keys = [f"dim_{i}" for i in range(len(embeddings[0]))] if len(embeddings) else []
    idf = {k: 1.0 for k in dim_keys}
    vocabulary = {k: i for i, k in enumerate(dim_keys)}
    return CorpusSemanticModel(
        vocabulary=vocabulary,
        idf=idf,
        vectors=vectors,
        embedder_name="sentence-transformers-MiniLM",
    )


def average_pairwise_semantic_similarity(
    model: CorpusSemanticModel,
    file_ids: list[str],
) -> float:
    if len(file_ids) < 2:
        return 1.0
    scores: list[float] = []
    for i in range(len(file_ids)):
        for j in range(i + 1, len(file_ids)):
            scores.append(model.similarity(file_ids[i], file_ids[j]))
    return round(sum(scores) / len(scores), 4) if scores else 0.0
