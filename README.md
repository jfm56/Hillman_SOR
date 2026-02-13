# SOR AI System

A secure, server-hosted web application for generating Hillmann Site Observation Reports (SOR) using AI-powered image analysis, document parsing, and style-learning draft generation.

## Features

| Feature | Description |
|---------|-------------|
| **Photo Upload & Analysis** | GPT-4 Vision analyzes site photos for conditions, materials, and safety issues |
| **PDF Document Parsing** | Extract structured data from plans, cost reviews, change orders, and prior SORs |
| **Building Classification** | Auto-suggest building assignments using embedding similarity |
| **RAG Style Learning** | Generate drafts matching Hillmann's writing style from historical reports |
| **AI-Assisted Editing** | Private chat assistant for rewriting and improving report sections |
| **Full Audit Logging** | Track all user actions and AI interactions for compliance |
| **Version History** | Maintain complete revision history for all reports |

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      SOR AI SYSTEM                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Frontend   │    │   Backend    │    │   Database   │     │
│  │   Next.js    │◄──►│   FastAPI    │◄──►│  PostgreSQL  │     │
│  │   Port 3000  │    │   Port 8000  │    │  + pgvector  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                                  │
│         │            ┌──────┴──────┐                          │
│         │            │ AI Services │                          │
│         │            ├─────────────┤                          │
│         │            │ • Vision    │                          │
│         │            │ • PDF Parse │                          │
│         │            │ • RAG       │                          │
│         │            │ • Draft Gen │                          │
│         │            │ • Chat      │                          │
│         │            └─────────────┘                          │
│         │                   │                                  │
│         └───────────────────┼──────────────────────────────►  │
│                      File Storage                              │
│                      ./storage/                                │
└────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Docker Desktop** (includes Docker Compose)
- **OpenAI API Key** (for AI features)

### 1. Configure Environment

```bash
cd sor-ai-system

# Create backend environment file
cat > backend/.env << EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sor_ai
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=sk-your-openai-api-key-here
STORAGE_PATH=/app/storage
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
```

### 2. Start with Docker Compose

```bash
docker-compose up -d --build
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
sor_postgres   db         Up (healthy)     0.0.0.0:5432->5432/tcp
```

### 4. Access the Application

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
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `STORAGE_PATH` | File storage path | `./storage` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000` |

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## License

Proprietary - Hillmann Consulting
