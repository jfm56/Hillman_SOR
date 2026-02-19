# Hillmann AI System Architecture

## System Overview

A secure, server-hosted web application for generating Hillmann Site Observation Reports (SOR) using AI-powered image analysis, document parsing, and style-learning draft generation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOR AI SYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    WEB APPLICATION (Next.js)                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐   │   │
│  │  │ Upload  │ │ Upload  │ │Narrative │ │ AI Chat  │ │   Report    │   │   │
│  │  │ Photos  │ │  PDFs   │ │  Input   │ │Assistant │ │   Editor    │   │   │
│  │  └─────────┘ └─────────┘ └──────────┘ └──────────┘ └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      BACKEND API (FastAPI)                            │   │
│  │  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ ┌───────────┐   │   │
│  │  │   Auth   │ │   File    │ │    AI     │ │ Report │ │   Audit   │   │   │
│  │  │  Module  │ │Processing │ │ Pipeline  │ │  Gen   │ │  Logging  │   │   │
│  │  └──────────┘ └───────────┘ └───────────┘ └────────┘ └───────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│         ┌────────────────────────────┼────────────────────────────┐         │
│         ▼                            ▼                            ▼         │
│  ┌─────────────┐            ┌─────────────────┐           ┌─────────────┐   │
│  │  AI SERVICES │            │    DATABASE     │           │FILE STORAGE │   │
│  │  (On-Prem)   │            │  (PostgreSQL)   │           │   (Local)   │   │
│  │              │            │                 │           │             │   │
│  │ ┌──────────┐ │            │ • Users         │           │ • Photos    │   │
│  │ │  Vision  │ │            │ • Projects      │           │ • PDFs      │   │
│  │ │  Model   │ │            │ • Sites         │           │ • Reports   │   │
│  │ └──────────┘ │            │ • Buildings     │           │ • Exports   │   │
│  │ ┌──────────┐ │            │ • Reports       │           │             │   │
│  │ │   PDF    │ │            │ • Images        │           └─────────────┘   │
│  │ │  Parser  │ │            │ • Audit Logs    │                             │
│  │ └──────────┘ │            │ • AI Logs       │                             │
│  │ ┌──────────┐ │            │ • Embeddings    │                             │
│  │ │   RAG    │ │            │                 │                             │
│  │ │  Engine  │ │            └─────────────────┘                             │
│  │ └──────────┘ │                                                            │
│  │ ┌──────────┐ │                                                            │
│  │ │   LLM    │ │                                                            │
│  │ │Generator │ │                                                            │
│  │ └──────────┘ │                                                            │
│  └─────────────┘                                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Web Application (Next.js Frontend)

| Component | Purpose |
|-----------|---------|
| **Upload Photos** | Drag-drop interface for site images with building/area assignment |
| **Upload PDFs** | Document ingestion for plans, cost reviews, prior reports |
| **Narrative Input** | Rich text editor for inspector observations |
| **AI Chat Assistant** | Private chat for style rewrites and clarifications |
| **Report Editor** | Section-by-section editing with AI suggestions |

### 2. Backend API (FastAPI)

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| **Auth** | `/auth/*` | JWT authentication, role-based access |
| **File Processing** | `/files/*` | Upload, validate, store files |
| **AI Pipeline** | `/ai/*` | Image analysis, parsing, generation |
| **Report Generator** | `/reports/*` | CRUD, draft generation, export |
| **Audit Logging** | `/audit/*` | Track all system actions |

### 3. AI Services (On-Premises)

| Service | Model Options | Purpose |
|---------|---------------|---------|
| **Vision Model** | GPT-4V, LLaVA, BLIP-2 | Image understanding and description |
| **PDF Parser** | PyMuPDF + LLM | Extract structured text from documents |
| **RAG Engine** | ChromaDB + OpenAI Embeddings | Style learning from historical SORs |
| **LLM Generator** | GPT-4, Claude, or local LLM | Draft report sections |

### 4. Database (PostgreSQL)

Core tables for managing users, projects, reports, and audit trails. See `DATABASE_SCHEMA.md` for full details.

### 5. File Storage

```
/storage/
├── photos/
│   └── {project_id}/
│       └── {building_id}/
│           └── {image_uuid}.{ext}
├── pdfs/
│   └── {project_id}/
│       └── {document_uuid}.pdf
├── reports/
│   └── {project_id}/
│       └── {report_uuid}/
│           ├── draft_v1.docx
│           └── final.pdf
└── exports/
    └── {export_uuid}.{ext}
```

## Security Architecture

### Authentication Flow
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  FastAPI │────▶│PostgreSQL│
│          │     │   Auth   │     │  Users   │
└──────────┘     └──────────┘     └──────────┘
      │                │
      │    JWT Token   │
      ◀────────────────┘
      │
      ▼ (All subsequent requests)
┌──────────┐     ┌──────────┐
│  Client  │────▶│  FastAPI │
│  + JWT   │     │ Verified │
└──────────┘     └──────────┘
```

### Data Isolation
- All AI processing on-premises
- No external API calls with sensitive data
- Database encryption at rest
- Audit logging for compliance

## Scalability Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| Frontend | Static export + CDN |
| Backend | Horizontal scaling with load balancer |
| Database | Read replicas for reporting |
| AI Services | GPU cluster for vision models |
| Storage | Distributed file system (later phase) |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React, TailwindCSS, shadcn/ui |
| Backend | FastAPI, Python 3.11+, Pydantic |
| Database | PostgreSQL 15+, SQLAlchemy |
| AI/ML | OpenAI API (or local LLM), ChromaDB, LangChain |
| File Storage | Local filesystem (S3-compatible later) |
| Auth | JWT, bcrypt, OAuth2 |
| Deployment | Docker, Docker Compose |
