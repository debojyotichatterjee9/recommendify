"""Unit tests for the config loader."""
import pytest

from app.config.loader import DEFAULT_CONFIG, get_interaction_score, load_config


class TestLoadConfig:
    def test_none_returns_defaults(self):
        config = load_config(None)
        assert config == DEFAULT_CONFIG

    def test_override_algorithm(self):
        config = load_config("algorithm: content\n")
        assert config["algorithm"] == "content"
        # Other defaults remain
        assert "interaction_scores" in config

    def test_merge_interaction_scores(self):
        config = load_config("interaction_scores:\n  purchase: 10.0\n  custom_event: 4.0\n")
        assert config["interaction_scores"]["purchase"] == 10.0
        assert config["interaction_scores"]["custom_event"] == 4.0
        # Defaults retained
        assert config["interaction_scores"]["view"] == 1.0

    def test_empty_yaml(self):
        config = load_config("")
        assert config["algorithm"] == DEFAULT_CONFIG["algorithm"]


class TestGetInteractionScore:
    def test_known_event(self):
        config = load_config(None)
        assert get_interaction_score("purchase", config) == 5.0

    def test_unknown_event_defaults_to_one(self):
        config = load_config(None)
        assert get_interaction_score("mystery_event", config) == 1.0