"""Integration tests for the API endpoints."""
import io
import pytest


BUSINESS_ID = "test-bookshop"


def _create_user(client, ext_id="user-1"):
    return client.post("/users/", json={"external_id": ext_id, "business_id": BUSINESS_ID})


def _create_product(client, ext_id="book-1", name="Python Crash Course"):
    return client.post("/products/", json={
        "external_id": ext_id,
        "business_id": BUSINESS_ID,
        "product_type": "book",
        "name": name,
        "description": "Learn Python",
        "attributes": {"genre": "tech", "author": "Eric Matthes"},
    })


class TestUsers:
    def test_create_user(self, client):
        r = _create_user(client, "u-api-1")
        assert r.status_code == 201
        assert r.json()["external_id"] == "u-api-1"

    def test_duplicate_user_409(self, client):
        _create_user(client, "u-dup")
        r = _create_user(client, "u-dup")
        assert r.status_code == 409

    def test_get_user(self, client):
        _create_user(client, "u-get-1")
        r = client.get(f"/users/{BUSINESS_ID}/u-get-1")
        assert r.status_code == 200
        assert r.json()["external_id"] == "u-get-1"

    def test_get_missing_user_404(self, client):
        r = client.get(f"/users/{BUSINESS_ID}/nobody")
        assert r.status_code == 404


class TestProducts:
    def test_create_product(self, client):
        r = _create_product(client, "p-api-1", "Clean Code")
        assert r.status_code == 201
        assert r.json()["name"] == "Clean Code"
        assert r.json()["attributes"]["genre"] == "tech"

    def test_list_products(self, client):
        _create_product(client, "p-list-1", "Book A")
        _create_product(client, "p-list-2", "Book B")
        r = client.get(f"/products/{BUSINESS_ID}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_delete_product(self, client):
        _create_product(client, "p-del-1", "Delete Me")
        r = client.delete(f"/products/{BUSINESS_ID}/p-del-1")
        assert r.status_code == 204
        r2 = client.get(f"/products/{BUSINESS_ID}/p-del-1")
        assert r2.status_code == 404


class TestInteractions:
    def test_log_interaction(self, client):
        _create_user(client, "u-int-1")
        _create_product(client, "p-int-1", "Interacted Book")
        r = client.post("/interactions/", json={
            "user_external_id": "u-int-1",
            "product_external_id": "p-int-1",
            "business_id": BUSINESS_ID,
            "event_type": "purchase",
        })
        assert r.status_code == 201
        assert r.json()["score"] == 5.0  # default purchase score

    def test_missing_user_404(self, client):
        _create_product(client, "p-int-2", "Another Book")
        r = client.post("/interactions/", json={
            "user_external_id": "ghost",
            "product_external_id": "p-int-2",
            "business_id": BUSINESS_ID,
            "event_type": "view",
        })
        assert r.status_code == 404


class TestRecommend:
    def test_recommend_cold_start(self, client):
        """New user should still receive a response (cold start)."""
        _create_user(client, "u-rec-cold")
        _create_product(client, "p-rec-1", "Rec Book 1")
        _create_product(client, "p-rec-2", "Rec Book 2")
        r = client.post("/recommend/", json={
            "user_external_id": "u-rec-cold",
            "business_id": BUSINESS_ID,
            "top_n": 5,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["user_external_id"] == "u-rec-cold"
        assert isinstance(data["recommendations"], list)

    def test_recommend_with_interactions(self, client):
        _create_user(client, "u-rec-warm")
        _create_product(client, "p-rec-w1", "Python Book")
        _create_product(client, "p-rec-w2", "JavaScript Book")
        _create_product(client, "p-rec-w3", "Gatsby Novel")
        client.post("/interactions/", json={
            "user_external_id": "u-rec-warm",
            "product_external_id": "p-rec-w1",
            "business_id": BUSINESS_ID,
            "event_type": "purchase",
        })
        r = client.post("/recommend/", json={
            "user_external_id": "u-rec-warm",
            "business_id": BUSINESS_ID,
            "top_n": 5,
        })
        assert r.status_code == 200
        recs = r.json()["recommendations"]
        # Purchased product should NOT appear in recommendations
        ext_ids = [rec["external_id"] for rec in recs]
        assert "p-rec-w1" not in ext_ids


class TestAdminConfig:
    def test_upload_valid_config(self, client):
        yaml_content = b"algorithm: content\ncontent_weight: 0.9\ncollab_weight: 0.1\n"
        r = client.post(
            f"/admin/config/{BUSINESS_ID}",
            files={"file": ("config.yaml", io.BytesIO(yaml_content), "text/yaml")},
        )
        assert r.status_code == 200
        assert r.json()["business_id"] == BUSINESS_ID

    def test_upload_invalid_yaml_400(self, client):
        bad_yaml = b"algorithm: [\nnot: valid: yaml:::"
        r = client.post(
            f"/admin/config/{BUSINESS_ID}",
            files={"file": ("bad.yaml", io.BytesIO(bad_yaml), "text/yaml")},
        )
        assert r.status_code == 400

    def test_get_config(self, client):
        yaml_content = b"algorithm: collab\n"
        client.post(
            f"/admin/config/{BUSINESS_ID}",
            files={"file": ("config.yaml", io.BytesIO(yaml_content), "text/yaml")},
        )
        r = client.get(f"/admin/config/{BUSINESS_ID}")
        assert r.status_code == 200
        assert "collab" in r.json()["config_yaml"]