"""Business configuration loading and defaults.

A business config (YAML) can override:
  - algorithm: content | collab | hybrid
  - collab_weight / content_weight  (for hybrid)
  - interaction_scores: mapping of event_type -> numeric weight
  - content_fields: product attribute keys used for content-based similarity
"""

from __future__ import annotations

from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "algorithm": "hybrid",
    "collab_weight": 0.5,
    "content_weight": 0.5,
    "interaction_scores": {
        "view": 1.0,
        "like": 2.0,
        "purchase": 5.0,
        "rate": 3.0,
    },
    "content_fields": ["name", "description", "product_type"],
}


def load_config(yaml_text: str | None) -> dict[str, Any]:
    """Merge supplied YAML with defaults; return final config dict."""
    if not yaml_text:
        return DEFAULT_CONFIG.copy()
    loaded = yaml.safe_load(yaml_text) or {}
    merged = DEFAULT_CONFIG.copy()
    # Deep-merge interaction_scores if present
    if "interaction_scores" in loaded:
        merged["interaction_scores"] = {
            **merged["interaction_scores"],
            **loaded["interaction_scores"],
        }
        loaded.pop("interaction_scores")
    merged.update(loaded)
    return merged


def get_interaction_score(event_type: str, config: dict[str, Any]) -> float:
    """Return the numeric weight for a given event_type from config."""
    return float(config["interaction_scores"].get(event_type, 1.0))
