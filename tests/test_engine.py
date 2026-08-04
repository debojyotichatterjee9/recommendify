"""Unit tests for the recommendation engine."""
import pandas as pd
import pytest
import uuid

from app.recommender.engine import (
    collaborative_scores,
    content_based_scores,
    get_recommendations,
    hybrid_scores,
)

# Use UUIDs for IDs to match the new type hints and model changes
ID1 = uuid.uuid4()
ID2 = uuid.uuid4()
ID3 = uuid.uuid4()
ID4 = uuid.uuid4()

PRODUCTS_DF = pd.DataFrame([
    {"id": ID1, "name": "Python Crash Course", "description": "Learn Python programming", "product_type": "book", "attributes": {"genre": "tech"}},
    {"id": ID2, "name": "Clean Code", "description": "Software craftsmanship guide", "product_type": "book", "attributes": {"genre": "tech"}},
    {"id": ID3, "name": "The Great Gatsby", "description": "Classic American novel", "product_type": "book", "attributes": {"genre": "fiction"}},
    {"id": ID4, "name": "Dune", "description": "Epic science fiction saga", "product_type": "book", "attributes": {"genre": "scifi"}},
])

USER1 = uuid.uuid4()
USER2 = uuid.uuid4()
USER3 = uuid.uuid4()

INTERACTIONS_DF = pd.DataFrame([
    {"user_id": USER1, "product_id": ID1, "score": 5.0},
    {"user_id": USER1, "product_id": ID2, "score": 3.0},
    {"user_id": USER2, "product_id": ID1, "score": 4.0},
    {"user_id": USER2, "product_id": ID3, "score": 2.0},
    {"user_id": USER3, "product_id": ID3, "score": 5.0},
    {"user_id": USER3, "product_id": ID4, "score": 4.0},
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
        scores = content_based_scores([ID1], PRODUCTS_DF, ["name", "description"])
        assert not scores.empty

    def test_excludes_unrelated(self):
        # tech book user should score tech books higher than fiction
        scores = content_based_scores([ID1, ID2], PRODUCTS_DF, ["name", "description", "product_type"])
        assert scores[ID2] > scores[ID3]  # Clean Code > Great Gatsby

    def test_empty_interactions(self):
        scores = content_based_scores([], PRODUCTS_DF, ["name"])
        assert scores.empty

    def test_empty_products(self):
        scores = content_based_scores([ID1], pd.DataFrame(), ["name"])
        assert scores.empty


class TestCollaborative:
    def test_returns_series(self):
        scores = collaborative_scores(USER1, INTERACTIONS_DF, [ID1, ID2, ID3, ID4])
        assert not scores.empty

    def test_cold_start_user(self):
        scores = collaborative_scores(uuid.uuid4(), INTERACTIONS_DF, [ID1, ID2, ID3, ID4])
        assert scores.empty

    def test_seen_products_zeroed(self):
        scores = collaborative_scores(USER1, INTERACTIONS_DF, [ID1, ID2, ID3, ID4])
        # User 1 already saw ID1 and ID2; their scores should be 0
        assert scores.get(ID1, 0) == 0.0
        assert scores.get(ID2, 0) == 0.0


class TestHybrid:
    def test_weighted_combination(self):
        content_s = pd.Series({ID3: 0.8, ID4: 0.2})
        collab_s = pd.Series({ID3: 0.1, ID4: 0.9})
        result = hybrid_scores(content_s, collab_s, 0.5, 0.5)
        assert abs(result[ID3] - 0.45) < 1e-6
        assert abs(result[ID4] - 0.55) < 1e-6

    def test_returns_union_of_ids(self):
        content_s = pd.Series({ID1: 0.5})
        collab_s = pd.Series({ID2: 0.5})
        result = hybrid_scores(content_s, collab_s, 0.5, 0.5)
        assert ID1 in result.index and ID2 in result.index


class TestGetRecommendations:
    def test_content_algorithm(self):
        recs, algo = get_recommendations(USER1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2, algorithm_override="content")
        assert algo == "content"
        assert len(recs) <= 2
        ids = [r[0] for r in recs]
        assert ID1 not in ids and ID2 not in ids  # already interacted
        assert isinstance(recs[0][1], float) # Score is present

    def test_collab_algorithm(self):
        recs, algo = get_recommendations(USER1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2, algorithm_override="collab")
        assert algo == "collab"
        assert len(recs) > 0
        assert isinstance(recs[0][1], float)

    def test_hybrid_algorithm(self):
        recs, algo = get_recommendations(USER1, PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=2)
        assert algo == "hybrid"
        assert len(recs) > 0

    def test_cold_start_returns_products(self):
        """New user with no interactions gets unseen products."""
        recs, algo = get_recommendations(uuid.uuid4(), PRODUCTS_DF, INTERACTIONS_DF, CONFIG, top_n=3)
        assert len(recs) <= 4  # can't exceed total products
        assert recs[0][1] == 0.5 # Cold start score
