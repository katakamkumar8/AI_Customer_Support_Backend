# 🤖 AI Customer Support Agent — Backend

A production-ready multi-agent AI customer support backend built with **FastAPI**, **LangGraph**, **Groq LLM**, **Zilliz Cloud (Milvus)**, and **PostgreSQL**.

---

## 🏗️ Architecture

```
User Request
     │
     ▼
POST /chat
     │
     ▼
┌─────────────────────────────────────────┐
│            LangGraph Workflow           │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  A. Intent Classifier Agent      │   │
│  │  (Groq LLM zero-shot)            │   │
│  └────────────┬─────────────────────┘   │
│               │                         │
│    ┌──────────▼──────────────┐          │
│    │  Human Escalation?      │          │
│    └──────┬──────────┬───────┘          │
│           │No        │Yes               │
│  ┌────────▼───────┐  │                  │
│  │ B. Knowledge   │  │                  │
│  │    Agent (RAG) │  │                  │
│  └────────┬───────┘  │                  │
│           │          │                  │
│  ┌────────▼───────┐  │                  │
│  │ C. Ticket      │  │                  │
│  │    Agent       │  │                  │
│  └────────┬───────┘  │                  │
│           └────┬─────┘                  │
│  ┌─────────────▼──────────────────┐     │
│  │ D. Escalation Agent            │     │
│  │ (low-confidence / dissatisfied)│     │
│  └─────────────┬──────────────────┘     │
│  ┌─────────────▼──────────────────┐     │
│  │ E. Response Agent              │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
     │
     ▼
JSON Response
```

---

## 📁 Folder Structure

```
backend/
├── app/
│   ├── api/                   # FastAPI routers
│   │   ├── chat.py            # POST /chat
│   │   ├── tickets.py         # CRUD /tickets
│   │   ├── knowledge.py       # PDF upload & KB search
│   │   └── health.py          # GET /health
│   ├── agents/                # LangGraph agent nodes
│   │   ├── intent_agent.py    # A – Intent Classifier
│   │   ├── knowledge_agent.py # B – RAG Knowledge Agent
│   │   ├── ticket_agent.py    # C – Ticket Creator
│   │   ├── escalation_agent.py# D – Escalation Agent
│   │   └── response_agent.py  # E – Response Composer
│   ├── graph/
│   │   ├── state.py           # AgentState TypedDict
│   │   └── workflow.py        # LangGraph StateGraph
│   ├── rag/
│   │   ├── embeddings.py      # SentenceTransformer wrapper
│   │   ├── chunker.py         # PDF extractor + text splitter
│   │   ├── vector_store.py    # Zilliz Cloud client
│   │   └── retriever.py       # RAG pipeline (retrieve + generate)
│   ├── database/
│   │   └── engine.py          # Async SQLAlchemy engine
│   ├── models/
│   │   ├── ticket.py          # Ticket ORM model
│   │   └── conversation.py    # ConversationMessage ORM model
│   ├── schemas/
│   │   ├── ticket.py          # Ticket Pydantic schemas
│   │   ├── chat.py            # Chat Pydantic schemas
│   │   └── knowledge.py       # KB Pydantic schemas
│   ├── services/
│   │   ├── chat_service.py    # Orchestrates the full graph
│   │   ├── knowledge_service.py # PDF ingestion pipeline
│   │   ├── ticket_service.py  # Ticket CRUD
│   │   └── memory_service.py  # Conversation history
│   ├── utils/
│   │   └── logging.py         # Structured JSON logging
│   ├── config.py              # Pydantic Settings
│   └── main.py                # FastAPI app factory
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- PostgreSQL 15+
- [Groq API Key](https://console.groq.com)
- [Zilliz Cloud account](https://cloud.zilliz.com) (free tier works)

### 2. Clone & Install

```bash
git clone <repo>
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

Required variables:
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq LLM API key |
| `ZILLIZ_URI` | Your Zilliz Cloud cluster URI |
| `ZILLIZ_TOKEN` | Zilliz API token |
| `POSTGRES_PASSWORD` | PostgreSQL password |

### 4. Start PostgreSQL

Run PostgreSQL 15+ locally (or use a managed instance) and ensure the connection settings in `.env` match your instance.

### 5. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📡 API Reference

### Chat

```http
POST /chat
Content-Type: application/json

{
  "session_id": "user-session-123",
  "message": "I want a refund for order #9921",
  "customer_name": "Jane Doe",
  "email": "jane@example.com"
}
```

**Response:**
```json
{
  "session_id": "user-session-123",
  "intent": "Refund Request",
  "answer": "I've raised a refund ticket for you. Our team will process it within 3-5 business days.",
  "ticket_created": true,
  "ticket_id": "SUP-A1B2C3",
  "escalated": false,
  "sources": ["returns_policy.pdf"],
  "confidence": 0.87
}
```

### Knowledge Base

```http
# Upload a PDF
POST /knowledge/upload
Content-Type: multipart/form-data
file=@returns_policy.pdf

# Semantic search
POST /knowledge/search
{"query": "how do I return a product?", "top_k": 5}

# Delete document
DELETE /knowledge/{filename}
```

### Tickets

```http
POST   /tickets          # Create ticket
GET    /tickets          # List all tickets
GET    /tickets/{id}     # Get ticket by ID
PATCH  /tickets/{id}     # Update status/priority
```

### Health

```http
GET /health
```

---

## 🤖 Agent Intents

| Intent | Triggers Ticket | Escalation Risk |
|---|---|---|
| FAQ Query | ❌ | Low |
| Technical Issue | ✅ Medium | Medium |
| Refund Request | ✅ High | Low |
| Order Tracking | ✅ Low | Low |
| Human Escalation | ✅ Critical | **Always escalates** |

Escalation also triggers automatically when:
- Groq RAG confidence < 45%
- User message contains dissatisfaction keywords

---

## 🧪 Testing the Pipeline

```bash
# Upload knowledge base
curl -X POST http://localhost:8000/knowledge/upload \
  -F "file=@your_docs.pdf"

# Chat with agent
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-1","message":"How do I reset my password?","customer_name":"Alice"}'
```

---

## 🔒 Production Checklist

- [ ] Set `CORS` origins to your frontend domain
- [ ] Use secrets manager for API keys (AWS Secrets Manager, Vault)
- [ ] Add rate limiting (e.g. `slowapi`)
- [ ] Configure Alembic for schema migrations
- [ ] Set up PostgreSQL connection pooling (PgBouncer)
- [ ] Enable HTTPS / TLS termination
- [ ] Add Prometheus metrics (`prometheus-fastapi-instrumentator`)

---

## 📄 License

MIT
