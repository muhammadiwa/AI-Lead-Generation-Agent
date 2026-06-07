# Lead Gen Agent — Backend

> AI-powered lead generation, scoring, and outreach API.

## Quick Start

```bash
# Install dependencies
cd backend
pip install -e .

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Run with Docker
docker compose up -d

# Or run directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entrypoint
│   ├── config.py            # Environment-based configuration
│   ├── database.py          # SQLAlchemy async engine & session
│   ├── api/
│   │   ├── deps.py          # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── router.py    # API v1 route aggregator
│   │       ├── leads.py     # Lead CRUD endpoints
│   │       ├── discovery.py # Lead discovery/search endpoints
│   │       ├── scoring.py   # Lead scoring endpoints
│   │       ├── outreach.py  # Campaign & message endpoints
│   │       ├── icp.py       # ICP profile endpoints
│   │       └── analytics.py # Dashboard analytics endpoints
│   ├── core/
│   │   ├── errors.py        # Structured error handling
│   │   └── security.py      # JWT, password hashing
│   ├── models/
│   │   └── __init__.py      # SQLAlchemy models
│   ├── schemas/
│   │   └── __init__.py      # Pydantic request/response schemas
│   └── collectors/
│       ├── base.py          # Abstract base collector
│       ├── orchestrator.py  # Multi-source collection orchestrator
│       ├── linkedin.py      # LinkedIn search scraper
│       ├── github.py        # GitHub API explorer
│       ├── crunchbase.py    # Crunchbase API collector
│       ├── web_scraper.py   # General web scraper (Firecrawl + BS4)
│       ├── google_maps.py   # Google Maps/Business Profile scraper
│       ├── social_media.py  # Twitter/X, Reddit, Facebook monitor
│       ├── job_platforms.py # Upwork, RemoteOK, etc. monitor
│       ├── business_directories.py # Product Hunt, Yelp, directories
│       └── utils/
│           ├── rate_limiter.py   # Token bucket rate limiter
│           ├── proxy_rotator.py  # Proxy rotation
│           └── anti_block.py     # Anti-blocking strategies
├── tests/
│   ├── conftest.py          # Test fixtures
│   └── test_api.py          # API endpoint tests
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## API Endpoints

### Leads
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/leads | List/search leads |
| GET | /api/v1/leads/:id | Get lead detail |
| POST | /api/v1/leads | Create lead |
| PATCH | /api/v1/leads/:id | Update lead |
| DELETE | /api/v1/leads/:id | Soft-delete lead |
| POST | /api/v1/leads/:id/enrich | Enrich single lead |
| POST | /api/v1/leads/bulk/enrich | Batch enrich |

### Discovery
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/discovery/search | One-time search |
| POST | /api/v1/discovery/campaigns | Create recurring campaign |
| GET | /api/v1/discovery/campaigns | List campaigns |
| PATCH | /api/v1/discovery/campaigns/:id | Update campaign |
| DELETE | /api/v1/discovery/campaigns/:id | Delete campaign |

### Scoring
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/leads/:id/score | Get score breakdown |
| POST | /api/v1/scoring/recalculate | Recalculate all scores |
| PATCH | /api/v1/scoring/weights | Update scoring weights |

### Outreach
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/outreach/campaigns | Create campaign |
| GET | /api/v1/outreach/campaigns | List campaigns |
| POST | /api/v1/outreach/templates | Create template |
| GET | /api/v1/outreach/templates | List templates |
| PATCH | /api/v1/outreach/templates/:id | Update template |
| POST | /api/v1/outreach/send | Send immediately |
| POST | /api/v1/outreach/schedule | Schedule outreach |
| GET | /api/v1/outreach/:id/tracking | Get tracking data |

### ICP
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/icp | Create ICP profile |
| GET | /api/v1/icp | List profiles |
| PATCH | /api/v1/icp/:id | Update profile |
| DELETE | /api/v1/icp/:id | Delete profile |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/analytics/overview | Dashboard stats |
| GET | /api/v1/analytics/pipeline | Pipeline funnel |
| GET | /api/v1/analytics/sources | Source attribution |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | / | API info |

## Data Collection Pipeline

The backend includes 8 collector modules:

1. **LinkedIn** — Company search & decision-maker discovery
2. **GitHub** — Repo exploration by topics/language
3. **Crunchbase** — Recent funding events & company categories
4. **Web Scraper** — Firecrawl + BeautifulSoup for general scraping
5. **Google Maps** — Places API for business discovery
6. **Social Media** — Twitter/X, Reddit, Facebook monitoring
7. **Job Platforms** — RemoteOK, WeWorkRemotely, LinkedIn Jobs
8. **Business Directories** — Product Hunt, Yelp, SaaS directories

All collectors implement a common base class with:
- Rate limiting (token bucket per source)
- Proxy rotation
- Anti-blocking headers & delays
- Structured output to `CollectedLead` dataclass

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| REDIS_URL | Queue | Redis connection string |
| GITHUB_TOKEN | GitHub | GitHub API token |
| CRUNCHBASE_API_KEY | Crunchbase | Crunchbase API key |
| FIRECRAWL_API_KEY | Web scrape | Firecrawl API key |
| SECRET_KEY | Yes | JWT signing secret |

## Running Tests

```bash
cd backend
pip install -e ".[dev]"
pytest -v --cov=app
```