"""Recommendation engine.

Three strategies:
  - content_based  : TF-IDF on product text fields → cosine similarity
  - collaborative  : User-item score matrix → cosine similarity between users
  - hybrid         : Weighted combination of both

All functions are pure / stateless; they receive data frames built from DB rows.
"""

from __future__ import annotations

import uuid

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# ── helpers ────────────────────────────────────────────────────────────────


def _build_product_corpus(
    products_df: pd.DataFrame, content_fields: list[str]
) -> list[str]:
    """Concatenate selected attribute fields into one text string per product."""
    corpus = []
    for _, row in products_df.iterrows():
        parts = []
        for field in content_fields:
            if field in row and pd.notna(row[field]):
                parts.append(str(row[field]))
            # also check inside the attributes dict
            attrs = row.get("attributes", {}) or {}
            if field in attrs:
                parts.append(str(attrs[field]))
        corpus.append(" ".join(parts))
    return corpus


# ── content-based ──────────────────────────────────────────────────────────


def content_based_scores(
    target_product_ids: list[uuid.UUID],
    products_df: pd.DataFrame,
    content_fields: list[str],
) -> pd.Series:
    """Return a Series of {product_id: similarity_score} for all products.

    Similarity is averaged over the target_product_ids the user interacted with.
    """
    if products_df.empty or not target_product_ids:
        return pd.Series(dtype=float)

    corpus = _build_product_corpus(products_df, content_fields)
    try:
        tfidf = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf_matrix = tfidf.fit_transform(corpus)
    except ValueError:
        return pd.Series(dtype=float)

    product_ids = products_df["id"].tolist()
    id_to_idx = {pid: i for i, pid in enumerate(product_ids)}

    query_indices = [id_to_idx[pid] for pid in target_product_ids if pid in id_to_idx]
    if not query_indices:
        return pd.Series(dtype=float)

    query_matrix = tfidf_matrix[query_indices]
    sims = cosine_similarity(query_matrix, tfidf_matrix).mean(axis=0)
    return pd.Series(sims, index=product_ids)


# ── collaborative ──────────────────────────────────────────────────────────


def collaborative_scores(
    target_user_id: uuid.UUID,
    interactions_df: pd.DataFrame,
    all_product_ids: list[uuid.UUID],
) -> pd.Series:
    """Return a Series of {product_id: predicted_score} via user-based CF.

    Builds a user×product matrix, finds similar users, and aggregates their
    weighted scores for unseen products.
    """
    if interactions_df.empty:
        return pd.Series(dtype=float)

    # Pivot: rows=users, cols=products, values=cumulative interaction score
    matrix = interactions_df.pivot_table(
        index="user_id",
        columns="product_id",
        values="score",
        aggfunc="sum",
        fill_value=0,
    )

    if target_user_id not in matrix.index:
        return pd.Series(dtype=float)

    # Ensure all product columns present
    for pid in all_product_ids:
        if pid not in matrix.columns:
            matrix[pid] = 0.0
    matrix = matrix[sorted(matrix.columns)]

    norm_matrix = normalize(matrix.values, norm="l2")
    user_idx = list(matrix.index).index(target_user_id)
    user_vec = norm_matrix[user_idx].reshape(1, -1)
    sims = cosine_similarity(user_vec, norm_matrix).flatten()

    # Zero out self-similarity
    sims[user_idx] = 0.0

    # Weighted sum of other users' scores
    weighted_scores = sims @ norm_matrix
    predicted = pd.Series(weighted_scores, index=matrix.columns)

    # Zero out products the user already interacted with
    seen = interactions_df[interactions_df["user_id"] == target_user_id][
        "product_id"
    ].unique()
    predicted[predicted.index.isin(seen)] = 0.0

    return predicted


# ── hybrid ─────────────────────────────────────────────────────────────────


def hybrid_scores(
    content_s: pd.Series,
    collab_s: pd.Series,
    content_weight: float,
    collab_weight: float,
) -> pd.Series:
    """Combine content and collaborative scores with configurable weights."""
    all_ids = set(content_s.index) | set(collab_s.index)
    result = {}
    for pid in all_ids:
        c = content_s.get(pid, 0.0)
        k = collab_s.get(pid, 0.0)
        # Normalise each to [0,1] range before combining
        result[pid] = content_weight * c + collab_weight * k
    return pd.Series(result)


# ── dispatcher ─────────────────────────────────────────────────────────────


def get_recommendations(
    target_user_id: uuid.UUID,
    products_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    config: dict,
    top_n: int = 10,
    algorithm_override: str | None = None,
) -> tuple[list[tuple[uuid.UUID, float]], str]:
    """Return (list of (product_id, score), algorithm_name_used).

    products_df columns : id, name, description, product_type, attributes
    interactions_df cols: user_id, product_id, score
    """
    algorithm = algorithm_override or config.get("algorithm", "hybrid")
    content_fields: list[str] = config.get(
        "content_fields", ["name", "description", "product_type"]
    )
    content_weight: float = config.get("content_weight", 0.5)
    collab_weight: float = config.get("collab_weight", 0.5)

    all_product_ids = products_df["id"].tolist()
    user_interactions = interactions_df[interactions_df["user_id"] == target_user_id]
    interacted_ids = user_interactions["product_id"].tolist()

    scores: pd.Series

    if algorithm == "content":
        scores = content_based_scores(interacted_ids, products_df, content_fields)

    elif algorithm == "collab":
        scores = collaborative_scores(target_user_id, interactions_df, all_product_ids)

    else:  # hybrid
        content_s = content_based_scores(interacted_ids, products_df, content_fields)
        collab_s = collaborative_scores(
            target_user_id, interactions_df, all_product_ids
        )
        scores = hybrid_scores(content_s, collab_s, content_weight, collab_weight)

    if scores.empty:
        # Cold-start: return random products the user hasn't seen
        unseen_ids = [pid for pid in all_product_ids if pid not in interacted_ids]
        if not unseen_ids:
            return [], algorithm

        # Use random choice for discovery
        selected_ids = np.random.choice(
            unseen_ids, size=min(len(unseen_ids), top_n), replace=False
        ).tolist()
        # Cold start items get a neutral score
        return [(pid, 0.5) for pid in selected_ids], algorithm

    # Exclude already-interacted products
    scores = scores.drop(
        index=[p for p in interacted_ids if p in scores.index], errors="ignore"
    )
    top = scores.nlargest(top_n)
    return list(top.items()), algorithm
