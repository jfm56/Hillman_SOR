# Hillmann AI System

A secure, **fully local** web application for generating Hillmann Site Observation Reports (SOR) using AI-powered image analysis, document parsing, and style-learning draft generation.

**🔒 Privacy First**: All AI processing runs locally using Ollama - no data ever leaves your network.

## Features

| Feature | Description |
|---------|-------------|
| **Local LLM (Ollama)** | 100% on-premises AI - no external API calls, PHI-safe |
| **Photo Upload & Analysis** | AI analyzes site photos for conditions, materials, and safety issues |
| **PDF Document Parsing** | Extract structured data from plans, cost reviews, change orders, and prior SORs |
| **Style Learning** | Upload past reports to teach the AI your writing style |
| **RAG Draft Generation** | Generate drafts matching Hillmann's writing style from learned reports |
| **AI Chat Assistant** | Private chat for rewriting and improving report sections |
| **Role-Based Access** | ADMIN, MANAGER, INSPECTOR roles with appropriate permissions |
| **Full Audit Logging** | Track all user actions and AI interactions for compliance |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SOR AI SYSTEM (100% Local)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │   Frontend   │    │   Backend    │    │   Database   │           │
│  │   Next.js    │◄──►│   FastAPI    │◄──►│  PostgreSQL  │           │
│  │   Port 3000  │    │   Port 8000  │    │  + pgvector  │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                             │                                        │
│                      ┌──────┴──────┐    ┌──────────────┐            │
│                      │ AI Services │◄──►│   Ollama     │            │
│                      ├─────────────┤    │  Local LLM   │            │
│                      │ • Chat      │    │  Port 11434  │            │
│                      │ • RAG       │    └──────────────┘            │
│                      │ • Draft Gen │           │                     │
│                      │ • Style     │    ┌──────┴──────┐             │
│                      │   Learning  │    │   Models    │             │
│                      └─────────────┘    │ • llama3.2  │             │
│                             │           │ • nomic-    │             │
│                      ┌──────┴──────┐    │   embed     │             │
│                      │File Storage │    └─────────────┘             │
│                      │ ./storage/  │                                 │
│                      └─────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Docker Desktop** (includes Docker Compose)
- **~6GB disk space** for AI models

### 1. Start All Services

```bash
cd sor-ai-system
docker-compose up -d --build
```

### 2. Download AI Models (One-Time Setup)

```bash
# Download chat model (~2GB)
docker exec sor_ollama ollama pull llama3.2

# Download embedding model (~274MB)
docker exec sor_ollama ollama pull nomic-embed-text
```

### 3. Verify All Services Are Running

```bash
docker-compose ps
```

Expected output:
```
NAME           SERVICE    STATUS           PORTS
sor_backend    backend    Up               0.0.0.0:8000->8000/tcp
sor_frontend   frontend   Up               0.0.0.0:3000->3000/tcp
sor_ollama     ollama     Up               0.0.0.0:11434->11434/tcp
sor_postgres   db         Up (healthy)     0.0.0.0:5432->5432/tcp
```

### 5. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application UI |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **Health Check** | http://localhost:8000/health | API health status |

## Troubleshooting

### Backend Not Starting

Check logs:
```bash
docker logs sor_backend
```

Common issues:
- **OPENAI_API_KEY not set**: Create `backend/.env` with your API key
- **Database connection failed**: Ensure PostgreSQL is healthy first

### Restart Services

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Full Rebuild

```bash
docker-compose down
docker-compose up -d --build
```

### View All Logs

```bash
docker-compose logs -f
```

## Development Setup

### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL (using Docker)
docker run -d --name sor_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=sor_ai \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Run the server
uvicorn app.main:app --reload
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your settings

# Run development server
npm run dev
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |

### File Upload
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload/images` | Upload photos |
| POST | `/api/v1/upload/documents` | Upload PDFs |

### AI Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/analyze-image` | Analyze image |
| POST | `/api/v1/ai/parse-document` | Parse PDF |
| POST | `/api/v1/ai/generate-draft` | Generate section |
| POST | `/api/v1/ai/rewrite` | Rewrite text |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports` | List reports |
| POST | `/api/v1/reports` | Create report |
| POST | `/api/v1/reports/{id}/generate` | Generate AI drafts |

See full API documentation at http://localhost:8000/docs

## Project Structure

```
sor-ai-system/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API routes
│   │   ├── core/                # Config, security
│   │   ├── db/                  # Database session
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   │   └── ai/              # AI services
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   └── lib/                 # Utilities
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_ENDPOINTS.md
│   └── AI_PIPELINE.md
├── storage/                     # File storage
└── docker-compose.yml
```

## AI Pipeline

1. **Ingestion**: Upload photos/PDFs, assign to project/building
2. **Image Analysis**: Vision model extracts conditions, materials, safety issues
3. **Document Parsing**: Extract structured data from PDFs
4. **Style Learning (RAG)**: Retrieve similar historical sections
5. **Draft Generation**: LLM synthesizes all inputs into report sections

## Security

- JWT authentication
- Role-based access control (admin, manager, inspector, reviewer)
- All AI processing on-premises (no external data exposure)
- Full audit logging for compliance
- Database encryption at rest

## Environment Variables

### Backend
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-configured |
| `SECRET_KEY` | JWT signing key | Auto-generated |
| `USE_LOCAL_LLM` | Use local Ollama instead of OpenAI | `true` |
| `OLLAMA_HOST` | Ollama server URL | `http://ollama:11434` |
| `LOCAL_MODEL` | Chat model name | `llama3.2` |
| `LOCAL_EMBEDDING_MODEL` | Embedding model name | `nomic-embed-text` |
| `STORAGE_PATH` | File storage path | `./storage` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000` |

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## Default Login

| Field | Value |
|-------|-------|
| Email | `admin@hillmann.com` |
| Password | `admin123` |

**Change the default password after first login.**

## User Roles

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full system access, user management |
| **MANAGER** | Review and approve reports |
| **INSPECTOR** | Upload photos, write narratives |

## License

Proprietary - Hillmann Consulting
