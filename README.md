# Recommendation Service

A **product-agnostic** recommendation engine built with FastAPI. Drop in any business domain — books, clothing, food, movies, cars — with minimal configuration.

---

## Features

| Capability | Detail |
|---|---|
| **Algorithms** | Content-based (TF-IDF + cosine), Collaborative filtering (user-based cosine), Hybrid (weighted blend) |
| **Product-agnostic** | Generic JSON `attributes` column; any domain works without schema changes |
| **Per-business config** | Upload a YAML file to override algorithm, weights, event scores, and content fields |
| **Cold-start handling** | New users receive unseen products when no interaction history exists |
| **Auto-docs** | Swagger UI at `/docs`, ReDoc at `/redoc` |
| **Free stack** | SQLite · FastAPI · scikit-learn · pandas · pytest |

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| Framework | FastAPI | High performance, auto OpenAPI docs |
| Database | SQLite (local) | Zero config, free, file-based |
| ORM | SQLAlchemy 2.x | Pythonic, DB-agnostic |
| Validation | Pydantic v2 | Fast, type-safe |
| ML | scikit-learn + pandas | TF-IDF, cosine similarity, matrix ops |
| Config | PyYAML | Human-readable business configs |
| Testing | pytest + httpx | Unit + integration via TestClient |
| Container | Docker / Compose | Optional, fully free locally |

---

## Project Structure

```
recommendation-service/
├── app/
│   ├── main.py                  # FastAPI app, router registration, DB init
│   ├── database.py              # SQLite engine + session dependency
│   ├── models.py                # SQLAlchemy: User, Product, Interaction, BusinessConfig
│   ├── schemas.py               # Pydantic request/response models
│   ├── config/
│   │   ├── loader.py            # YAML merge + defaults
│   │   ├── ecommerce.yaml       # Sample: e-commerce
│   │   ├── restaurant.yaml      # Sample: restaurant/food delivery
│   │   └── streaming.yaml       # Sample: streaming/media
│   ├── recommender/
│   │   └── engine.py            # Content, collaborative, hybrid algorithms
│   └── routes/
│       ├── users.py             # POST/GET /users
│       ├── products.py          # Full CRUD /products
│       ├── interactions.py      # POST /interactions
│       ├── recommendations.py   # POST /recommend
│       └── admin.py             # POST/GET /admin/config/{business_id}
├── tests/
│   ├── conftest.py              # TestClient + in-memory SQLite fixtures
│   ├── test_engine.py           # Pure unit tests for recommender logic
│   ├── test_api.py              # Integration tests for all endpoints
│   └── test_config.py           # Config loader unit tests
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### 1. Local (no Docker)

```bash
# Clone / create venv
python -m venv venv && source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

### 2. Docker

```bash
docker compose up --build
```

---

## API Overview

### Users
| Method | Path | Description |
|---|---|---|
| `POST` | `/users/` | Register a user |
| `GET` | `/users/{business_id}/{external_id}` | Fetch a user |

### Products
| Method | Path | Description |
|---|---|---|
| `POST` | `/products/` | Add a product |
| `GET` | `/products/{business_id}` | List all products for a business |
| `GET` | `/products/{business_id}/{external_id}` | Get one product |
| `PUT` | `/products/{business_id}/{external_id}` | Update a product |
| `DELETE` | `/products/{business_id}/{external_id}` | Delete a product |

### Interactions
| Method | Path | Description |
|---|---|---|
| `POST` | `/interactions/` | Log a user-product event (view, like, purchase, …) |

### Recommendations
| Method | Path | Description |
|---|---|---|
| `POST` | `/recommend/` | Get personalised recommendations for a user |

### Admin
| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/config/{business_id}` | Upload a YAML config file |
| `GET` | `/admin/config/{business_id}` | Retrieve current config |

---

## End-to-End Example (curl)

```bash
# 1. Register a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"external_id": "alice", "business_id": "bookshop"}'

# 2. Add products
curl -X POST http://localhost:8000/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "book-1", "business_id": "bookshop",
    "product_type": "book", "name": "Python Crash Course",
    "description": "Beginner Python programming guide",
    "attributes": {"author": "Eric Matthes", "genre": "tech"}
  }'

# 3. Log an interaction
curl -X POST http://localhost:8000/interactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_external_id": "alice", "product_external_id": "book-1",
    "business_id": "bookshop", "event_type": "purchase"
  }'

# 4. Get recommendations
curl -X POST http://localhost:8000/recommend/ \
  -H "Content-Type: application/json" \
  -d '{"user_external_id": "alice", "business_id": "bookshop", "top_n": 5}'

# 5. Upload a business config
curl -X POST http://localhost:8000/admin/config/bookshop \
  -F "file=@app/config/ecommerce.yaml"
```

---

## Business Configuration

Upload any YAML with a subset of these keys; unset keys fall back to defaults.

```yaml
# All keys optional — shown here with their defaults
algorithm: hybrid          # content | collab | hybrid
collab_weight: 0.5
content_weight: 0.5

interaction_scores:
  view: 1.0
  like: 2.0
  purchase: 5.0
  rate: 3.0

content_fields:            # product fields used for TF-IDF similarity
  - name
  - description
  - product_type
```

Three ready-made sample configs ship in `app/config/`:

- **`ecommerce.yaml`** — heavier collaborative weighting; `brand`, `category`, `tags` in content fields
- **`restaurant.yaml`** — content-only default; `cuisine`, `dietary_tags`, `spice_level`
- **`streaming.yaml`** — balanced hybrid; `genre`, `director`, `cast`, `release_year`

---

## Running Tests

```bash
pytest tests/ -v
```

Test coverage:
- `test_engine.py` — pure unit tests for content-based, collaborative, hybrid, and cold-start logic
- `test_api.py` — full HTTP integration tests using `TestClient` and an isolated in-memory DB
- `test_config.py` — YAML loading, merging, and score resolution

---

## Extending the Service

| Goal | How |
|---|---|
| Add a new event type | Add it to `interaction_scores` in a business YAML |
| New product domain | Register products with domain-specific `attributes` JSON; list relevant keys in `content_fields` |
| Swap to PostgreSQL | Change `SQLALCHEMY_DATABASE_URL` in `database.py`; remove `check_same_thread` arg |
| Add auth | Add FastAPI OAuth2/JWT middleware to `main.py`; protect routes with `Depends(verify_token)` |
| Improve algorithms | Drop in ALS/SVD in `engine.py`; expose via `algorithm` override field |
| Production deploy | Swap SQLite for PostgreSQL; deploy container to Railway / Render (free tiers available) |

---

## Out of Scope (POC)

- Paid cloud services or hosting
- Real-time streaming pipelines
- A/B testing framework
- User authentication (hooks exist in schema but not enforced)