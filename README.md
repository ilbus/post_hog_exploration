# Post Hog Exploartion Pipeline 


A production-ready data pipeline designed to transform raw user clickstreams (PostHog events) into semantic "User Context" for AI Chatbots.

## ⚡ Key Features

* **Real-Time Ingestion:** High-throughput FastAPI endpoint secured via API Key.
* **Async Processing:** Decoupled architecture using Redis as a message broker.
* **Semantic Enrichment:** Translates technical events (e.g., `.btn-primary click`) into natural language (e.g., "Clicked Upgrade Plan").
* **RAG-Ready:** Provides a structured history API for LLM context injection.
* **Production Grade:** Includes Docker infrastructure, connection pooling, and strict Pydantic validation.

## 🏗 Architecture

The system follows a **Producer-Consumer** pattern to ensure the API never blocks, even during traffic spikes.

```mermaid
graph LR
    subgraph "Write Path (Ingestion)"
        Client[PostHog / Client] -- JSON --> API[FastAPI]
        API -- LPUSH --> Queue[(Redis)]
        Queue -- BLPOP --> Worker[Python Worker]
        Worker -- Enrich --> DB[(Postgres)]
    end

    subgraph "Read Path (Retrieval)"
        Chatbot[AI Agent] -- GET /context --> API
        API -- Query --> DB
    end
```
## 🚀 How to Run Locally

### 1. Prerequisites
* **Docker Desktop** installed & running (for Database & Queue).
* **[uv](https://github.com/astral-sh/uv)** installed (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`).

### 2. Infrastructure Setup
Start the required services (Postgres & Redis) using Docker. This creates the "Skeleton" of your system.

```bash
docker-compose up -d
```
*Verify they are running:*
```bash
docker ps
# Output should list: 'postgres:15-alpine' and 'redis:alpine'
```

### 3. Configuration (Critical)
Create a `.env` file in the project root. This file is **required** for the system to start securely.

```bash
# Create a file named .env and paste this content:

ENVIRONMENT=development
PROJECT_NAME="PostHog LLM Pipeline"

# 🔑 Security Key (Must match in your scripts)
API_SECRET_KEY=local_dev_secret_key_12345

# 🗄️ Database & Queue Config
DB_USER=user
DB_PASS=password
DB_NAME=pipeline_db
DATABASE_URL=postgresql://user:password@localhost:5432/pipeline_db
REDIS_URL=redis://localhost:6379/0
QUEUE_NAME=event_stream
```

### 4. Running the System
The system architecture requires three simultaneous processes. Open **3 separate terminal windows** in the project root:

**Terminal 1: The API (Ingestion Layer)**
*Listens for incoming webhooks and pushes them to the Queue.*
```bash
uv run uvicorn src.api.main:app --reload
```

**Terminal 2: The Worker (Processing Layer)**
*Pulls events from Redis, enriches them, and saves to Postgres.*
```bash
uv run python -m src.worker.main
```

**Terminal 3: Traffic Generator (Simulation)**
*Simulates a user clicking buttons to generate load.*
```bash
# Explicitly loads .env to ensure the API Key is found
uv run --env-file .env scripts/mock_traffic.py
```

---

## ✅ Verification: How to know it works

1.  **Check Traffic (Terminal 3):**
    * You should see symbols like `P` (Pageview), `C` (Click), or `.` (Success).
    * *If you see `403 Forbidden` or `x`:* Your `.env` key does not match the application key. Restart Terminal 1 after checking `.env`.

2.  **Check Logs (Terminal 2):**
    * The worker should be printing logs indicating success:
        > `INFO:worker:✅ Processed: Clicked 'Upgrade Plan' Button`

3.  **Check Data (Browser / Curl):**
    * Verify the data is ready for the LLM by querying the context endpoint.
    * *Command:*
        ```bash
        curl -X GET "http://localhost:8000/context/user/user_1" \
             -H "X-API-Key: local_dev_secret_key_12345"
        ```
    * *Expected Output:*
        ```json
        {
          "user_id": "user_1",
          "summary": "User showing Purchase Intent.",
          "recent_history": [...]
        }
        ```