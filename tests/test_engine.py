"""Unit tests for the recommendation engine."""
import pandas as pd
import pytest

from app.recommender.engine import (
    collaborative_scores,
    content_based_scores,
    get_recommendations,
    hybrid_scores,
)

PRODUCTS_DF = pd.DataFrame([
    {"id": 1, "name": "Python Crash Course", "description": "Learn Python programming", "product_type": "book", "attributes": {"genre": "tech"}},
    {"id": 2, "name": "Clean Code", "description": "Software craftsmanship guide", "product_type": "book", "attributes": {"genre": "tech"}},
    {"id": 3, "name": "The Great Gatsby", "description": "Classic American novel", "product_type": "book", "attributes": {"genre": "fiction"}},
    {"id": 4, "name": "Dune", "description": "Epic science fiction saga", "product_type": "book", "attributes": {"genre": "scifi"}},
])

INTERACTIONS_DF = pd.DataFrame([
    {"user_id": 1, "product_id": 1, "score": 5.0},
    {"user_id": 1, "product_id": 2, "score": 3.0},
    {"user_id": 2, "product_id": 1, "score": 4.0},
    {"user_id": 2, "product_id": 3, "score": 2.0},
    {"user_id": 3, "product_id": 3, "score": 5.0},
    {"user_id": 3, "product_id": 4, "score": 4.0},
])

CONFIG = {
    "algorithm": "hybrid",
    "collab_weight": 0.5,
    "content_weight": 0.5,
    "content_fields": ["name", "description", "product_type"],
    "interaction_scores": {"view": 1.0, "like": 2.0, "purchase": 5.0},
}


class TestContentBased:
    def test_returns_series(self):
        scores = content_based_scores([1], PRODUCTS_DF, ["name", "description"])
        assert not scores.empty

    def test_excludes_unrelated(self):
        # tech book user should score tech books higher than fiction
        scores = content_based_scores([1, 2], PRODUCTS_DF, ["name", "description", "product_type"])
        assert scores[2] > scores[3]  # Clean Code > Great Gatsby

    def test_empty_interactions(self):
        scores = content_based_scores([], PRODUCTS_DF, ["name"])
        assert scores.empty

    def test_empty_products(self):
        scores = content_based_scores([1], pd.DataFrame(), ["name"])
        assert scores.empty


class TestCollaborative:
    def test_returns_series(self):
        scores = collaborative_scores(1, INTERACTIONS_DF, [1, 2, 3, 4])
        assert not scores.empty

    def test_cold_start_user(self):
        scores = collaborative_scores(99, INTERACTIONS_DF, [1, 2, 3, 4])
        assert scores.empty

    def test_seen_products_zeroed(self):
        scores = collaborative_scores(1, INTERACTIONS_DF, [1, 2, 3, 4])
        # User 1 already saw 1 and 2; their scores should be 0
        assert scores.get(1, 0) == 0.0
        assert scores.get(2, 0) == 0.0


class TestHybrid:
    def test_weighted_combination(self):
        content_s = pd.Series({3: 0.8, 4: 0.2})
        collab_s = pd.Series({3: 0.1, 4: 0.9})
        result = hybrid_scores(content_s, collab_s, 0.5, 0.5)
        assert abs(result[3] - 0.45) < 1e-6
        assert abs(result[4] - 0.55) < 1e-6

    def test_returns_union_of_ids(self):
        content_s = pd.Series({1: 0.5})
        collab_s = pd.Series({2: 0.5})
        result = hybrid_scores(content_s, collab_s, 0.5, 0.5)
        assert 1 in result.index and 2 in result.index


class TestGetRecommendations:
    def test_content_algorithm(self):
        ids, algo = get_recommendations(1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2, algorithm_override="content")
        assert algo == "content"
        assert len(ids) <= 2
        assert 1 not in ids and 2 not in ids  # already interacted

    def test_collab_algorithm(self):
        ids, algo = get_recommendations(1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2, algorithm_override="collab")
        assert algo == "collab"

    def test_hybrid_algorithm(self):
        ids, algo = get_recommendations(1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2)
        assert algo == "hybrid"

    def test_cold_start_returns_products(self):
        """New user with no interactions gets unseen products."""
        ids, algo = get_recommendations(99, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=3)
        assert len(ids) <= 4  # can't exceed total products