# Integration Platform Framework & App Marketplace Engine

[![CI Pipeline](https://github.com/awanish5101/integration-platform-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/awanish5101/integration-platform-framework/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, high-leverage Integration Platform and App Marketplace engine built with Python 3.11, FastAPI, and Pydantic v2. Designed to power the software development lifecycle (SDLC) for unified SaaS platforms, standardize API V2 endpoints, automate third-party app installations, and enforce "Zero KTLO" (Keep The Lights On) operational resilience through AI-assisted connector synthesis and dead-letter queue (DLQ) recovery.

---

## Key Capabilities

1. **Standardized API V2 Framework:**
   - Uniform JSON:API REST envelopes across all entity mutations and queries.
   - Deterministic cursor-based pagination for high-volume datasets.
   - Atomic distributed idempotency via `X-Idempotency-Key` headers with SHA-256 payload hashing and 409 conflict detection for in-flight requests.
   - Sliding-window token bucket rate limiting with automated `Retry-After` throttling headers.

2. **Marketplace & App Shop Lifecycle:**
   - Declarative App Manifests defining OAuth permission scopes, configuration JSON schemas, and webhook topics.
   - Tenant-isolated installation workflows supporting state machine transitions (`PENDING_AUTH` -> `CONFIGURED` -> `SUSPENDED` -> `UNINSTALLED`).
   - Granular credential encryption and validation against declared JSON schemas.

3. **AI-Driven Tooling for Third-Party Connectivity:**
   - Semantic connector synthesizer inferring field mappings from arbitrary third-party payloads to standardized schemas (e.g. mapping `work_email` -> `email`, `given_name` -> `first_name`).
   - Proactive schema drift analyzer identifying breaking changes, type conflicts, and unmapped attributes.
   - Automated Python connector adapter stub generator.

4. **"Zero KTLO" Automation & Resilient Webhook Dispatcher:**
   - Reliable webhook delivery engine with exponential backoff retries (0.5s, 1s, 2s).
   - Automated Dead-Letter Queue (DLQ) quarantine for permanently failing endpoints, preventing pipeline stalls.
   - Bulk DLQ replay API for zero-data-loss recovery once upstream third-party services recover.
   - Structured telemetry middleware capturing request IDs, p95/p99 execution latencies, and tenant context.

---

## Architectural Overview

```mermaid
flowchart TD
    subgraph Clients["Clients & Developers"]
        APIClient["SaaS Admin / API Client"]
        ThirdParty["Third-Party App / Webhook Receiver"]
    end

    subgraph Gateway["Integration Platform Gateway"]
        AuthLayer["Tenant Resolution & Auth<br/>(X-Tenant-ID & Bearer)"]
        RateLimiter["Token Bucket Rate Limiter<br/>(Tenant Throttling & Burst)"]
        Idempotency["Distributed Idempotency Guard<br/>(SHA-256 Digest & Replay)"]
        Telemetry["Structured Telemetry & Latency Profiling"]
    end

    subgraph CoreEngine["Platform Services"]
        APIV2["Standardized API V2<br/>(Employee Records & Pagination)"]
        Marketplace["App Shop / Marketplace Engine<br/>(Manifests & Lifecycle)"]
        AIEngine["AI Connector Synthesizer<br/>(Schema Inference & Drift)"]
        WebhookEngine["Webhook Dispatcher & DLQ<br/>(Backoff Retries & Replay)"]
    end

    subgraph Storage["Storage & Isolation"]
        Repo["Tenant-Isolated Storage<br/>(Employees, Apps, Installations)"]
        DLQ["Dead-Letter Queue Quarantine"]
    end

    APIClient --> Telemetry
    Telemetry --> AuthLayer
    AuthLayer --> RateLimiter
    RateLimiter --> Idempotency
    Idempotency --> APIV2
    Idempotency --> Marketplace

    Marketplace --> Repo
    APIV2 --> Repo
    AIEngine --> Marketplace

    APIV2 -->|Events| WebhookEngine
    WebhookEngine -->|Dispatch Retries| ThirdParty
    WebhookEngine -->|Exhausted Failures| DLQ
```

---

## Project Structure

```text
integration-platform-framework/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, middleware, probe routes
│   ├── config.py                # Environment configuration & limits
│   ├── api/
│   │   └── v2/
│   │       ├── endpoints.py     # API V2 Employee records (CRUD, pagination, idempotency)
│   │       ├── marketplace.py   # App Shop discovery, install, configure, uninstall
│   │       └── ai_tools.py      # AI connector synthesis, schema drift, DLQ replay
│   ├── core/
│   │   ├── idempotency.py       # Distributed idempotency engine with SHA-256 caching
│   │   ├── rate_limiter.py      # Token bucket rate limiter with sliding window
│   │   ├── security.py          # Tenant resolution and header extraction
│   │   └── telemetry.py         # Request ID tracking and latency profiling
│   ├── models/
│   │   ├── app_manifest.py      # App Shop manifest schema
│   │   ├── installation.py      # Tenant app installation state machine
│   │   ├── employee.py          # Standardized HRIS employee model
│   │   └── webhook.py           # Webhook event and DLQ models
│   ├── services/
│   │   ├── marketplace_service.py # App installation and configuration business logic
│   │   ├── webhook_dispatcher.py  # Async dispatcher with exponential backoff and DLQ
│   │   └── ai_connector_service.py# AI schema inference and connector generation
│   └── storage/
│       └── repository.py        # Thread-safe in-memory datastore with tenant isolation
├── tests/
│   ├── conftest.py              # Test fixtures and state resets
│   ├── test_api_v2.py           # Employee CRUD, multi-tenancy, and pagination tests
│   ├── test_marketplace.py      # App Shop lifecycle tests
│   ├── test_idempotency.py      # Idempotent retry and conflict tests
│   ├── test_rate_limiter.py     # Throttling and HTTP 429 tests
│   ├── test_ai_connector.py     # AI schema matching and drift detection tests
│   └── test_webhook_dlq.py      # Webhook retries, DLQ quarantine, and replay tests
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated GitHub Actions test pipeline
├── Dockerfile                   # Production container definition
├── docker-compose.yml           # Local composition orchestration
├── pytest.ini                   # Pytest runner configuration
└── requirements.txt             # Project dependencies
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Virtualenv or Pipenv

### 2. Installation
```bash
git clone https://github.com/awanish5101/integration-platform-framework.git
cd integration-platform-framework

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Access the interactive OpenAPI Swagger UI at `http://localhost:8000/docs`.

---

## Running the Automated Test Suite

The test suite runs with `pytest` and covers API contracts, edge-cases, concurrency, and error handling:

```bash
pytest -v
```

Expected output:
```text
tests/test_api_v2.py::test_health_and_readiness PASSED
tests/test_api_v2.py::test_create_and_get_employee PASSED
tests/test_api_v2.py::test_cursor_pagination PASSED
tests/test_api_v2.py::test_update_and_delete_employee PASSED
tests/test_marketplace.py::test_browse_apps_and_search PASSED
tests/test_marketplace.py::test_app_install_lifecycle PASSED
tests/test_idempotency.py::test_idempotent_retry_returns_cached_response PASSED
tests/test_idempotency.py::test_idempotent_key_conflict_different_payload PASSED
tests/test_rate_limiter.py::test_rate_limiter_throttling_and_headers PASSED
tests/test_ai_connector.py::test_ai_connector_synthesis PASSED
tests/test_ai_connector.py::test_schema_drift_detection PASSED
tests/test_webhook_dlq.py::test_webhook_successful_dispatch PASSED
tests/test_webhook_dlq.py::test_webhook_quarantine_to_dlq PASSED
```

---

## Docker Deployment

Build and run via Docker:
```bash
docker build -t integration-platform-framework .
docker run -p 8000:8000 integration-platform-framework
```
Or via Docker Compose:
```bash
docker-compose up -d
```

---

## API Documentation Highlights

### 1. Standardized API V2 Onboarding
`POST /api/v2/employees`
- **Headers:**
  - `X-Tenant-ID`: Organization tenant identifier (e.g. `tenant_corp`)
  - `X-Idempotency-Key`: UUIDv4 ensuring mutation idempotency
- **Payload:**
```json
{
  "first_name": "Awanish",
  "last_name": "Chaurasiya",
  "email": "avanish84ya@gmail.com",
  "department": "Platform Engineering",
  "title": "Software Engineer",
  "employment_status": "ACTIVE"
}
```

### 2. App Shop Installation
`POST /api/v2/marketplace/install`
```json
{
  "app_id": "slack-enterprise",
  "config_values": {
    "api_token": "xoxb-verified-secret"
  }
}
```

### 3. AI Connector Synthesis
`POST /api/v2/tools/synthesize-connector`
Ingests unformatted third-party JSON payloads and automatically produces high-confidence mapping rules and transformation adapters to normalize SaaS integrations.

---

## License
MIT
