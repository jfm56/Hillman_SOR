# Database Schema

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │   projects  │       │    sites    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ email       │  │    │ name        │  │    │ project_id  │──┐
│ password    │  │    │ client      │  │    │ name        │  │
│ full_name   │  │    │ address     │  │    │ address     │  │
│ role        │  │    │ created_by  │──┘    │ lat/lng     │  │
│ created_at  │  │    │ created_at  │       │ created_at  │  │
└─────────────┘  │    └─────────────┘       └─────────────┘  │
                 │           │                     │          │
                 │           │                     │          │
                 │    ┌──────┴──────┐              │          │
                 │    ▼             ▼              ▼          │
          ┌─────────────┐   ┌─────────────┐  ┌─────────────┐ │
          │   reports   │   │  buildings  │  │   images    │ │
          ├─────────────┤   ├─────────────┤  ├─────────────┤ │
          │ id (PK)     │   │ id (PK)     │  │ id (PK)     │ │
          │ project_id  │   │ site_id     │──┤ building_id │─┘
          │ site_id     │   │ name        │  │ filename    │
          │ created_by  │──┐│ type        │  │ file_path   │
          │ status      │  ││ description │  │ ai_analysis │
          │ version     │  │└─────────────┘  │ uploaded_by │──┐
          │ created_at  │  │                 │ created_at  │  │
          └─────────────┘  │                 └─────────────┘  │
                 │         │                                   │
                 │         └───────────────────────────────────┘
                 │
          ┌──────┴──────┐
          ▼             ▼
   ┌─────────────┐  ┌─────────────┐
   │report_sections│ │ audit_logs │
   ├─────────────┤  ├─────────────┤
   │ id (PK)     │  │ id (PK)     │
   │ report_id   │  │ user_id     │
   │ section_type│  │ action      │
   │ content     │  │ object_type │
   │ ai_draft    │  │ object_id   │
   │ human_edit  │  │ before_data │
   │ is_approved │  │ after_data  │
   │ version     │  │ ip_address  │
   │ updated_at  │  │ created_at  │
   └─────────────┘  └─────────────┘
```

## Table Definitions

### users
Stores all system users with authentication and role information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'inspector',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles: admin, manager, inspector, reviewer
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### projects
Top-level container for all work related to a client engagement.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_contact VARCHAR(255),
    address TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status: active, completed, archived
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_client ON projects(client_name);
```

### sites
Physical locations within a project (a project may have multiple sites).

```sql
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sites_project ON sites(project_id);
```

### buildings
Individual structures at a site for classification and organization.

```sql
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    building_type VARCHAR(100),
    floors INTEGER,
    year_built INTEGER,
    square_footage INTEGER,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- building_type: residential, commercial, industrial, mixed_use, etc.
CREATE INDEX idx_buildings_site ON buildings(site_id);
CREATE INDEX idx_buildings_type ON buildings(building_type);
```

### images
Uploaded photos with AI analysis metadata.

```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    area VARCHAR(255),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    
    -- AI Analysis Results
    ai_description TEXT,
    ai_analysis JSONB DEFAULT '{}',
    ai_building_suggestion UUID REFERENCES buildings(id),
    ai_confidence DECIMAL(3, 2),
    ai_processed_at TIMESTAMP,
    
    -- Metadata
    exif_data JSONB DEFAULT '{}',
    tags TEXT[],
    is_featured BOOLEAN DEFAULT false,
    
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_project ON images(project_id);
CREATE INDEX idx_images_building ON images(building_id);
CREATE INDEX idx_images_tags ON images USING GIN(tags);
```

### documents
Uploaded PDFs and other documents.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Parsed Content
    extracted_text TEXT,
    parsed_data JSONB DEFAULT '{}',
    page_count INTEGER,
    is_processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- document_type: plan, cost_review, prior_sor, contract, change_order, other
CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_type ON documents(document_type);
```

### reports
Site Observation Reports with versioning.

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    site_id UUID REFERENCES sites(id),
    
    report_number INTEGER NOT NULL,
    report_date DATE NOT NULL,
    inspection_date DATE NOT NULL,
    
    -- Report Metadata
    status VARCHAR(50) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    parent_version_id UUID REFERENCES reports(id),
    
    -- Summary Fields
    weather_conditions TEXT,
    personnel_on_site TEXT,
    executive_summary TEXT,
    
    -- AI Generation Tracking
    ai_generated_at TIMESTAMP,
    ai_model_used VARCHAR(100),
    
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status: draft, in_review, approved, final, archived
CREATE INDEX idx_reports_project ON reports(project_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE UNIQUE INDEX idx_reports_number ON reports(project_id, report_number, version);
```

### report_sections
Individual sections of a report with AI and human content tracking.

```sql
CREATE TABLE report_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    
    section_type VARCHAR(100) NOT NULL,
    section_order INTEGER NOT NULL,
    title VARCHAR(255),
    
    -- Content Versions
    ai_draft TEXT,
    ai_generated_at TIMESTAMP,
    ai_prompt_used TEXT,
    
    human_content TEXT,
    human_edited_by UUID REFERENCES users(id),
    human_edited_at TIMESTAMP,
    
    -- Final Content
    final_content TEXT,
    is_approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    
    -- Related Data
    related_images UUID[],
    related_documents UUID[],
    evidence_references JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- section_type: executive_summary, budget, schedule, building_status, safety, recommendations, etc.
CREATE INDEX idx_sections_report ON report_sections(report_id);
CREATE INDEX idx_sections_type ON report_sections(section_type);
```

### historical_sors
Historical SOR content for style learning (RAG).

```sql
CREATE TABLE historical_sors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source Info
    source_filename VARCHAR(255),
    source_date DATE,
    project_type VARCHAR(100),
    
    -- Section Content
    section_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    
    -- Embeddings for RAG
    embedding VECTOR(1536),
    
    -- Metadata
    quality_score DECIMAL(3, 2),
    is_exemplar BOOLEAN DEFAULT false,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historical_section ON historical_sors(section_type);
CREATE INDEX idx_historical_embedding ON historical_sors USING ivfflat (embedding vector_cosine_ops);
```

### audit_logs
Complete audit trail for compliance.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    
    object_type VARCHAR(100) NOT NULL,
    object_id UUID NOT NULL,
    
    before_data JSONB,
    after_data JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actions: create, update, delete, view, export, approve, generate_ai, etc.
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_object ON audit_logs(object_type, object_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_time ON audit_logs(created_at);
```

### ai_interaction_logs
Track all AI model interactions.

```sql
CREATE TABLE ai_interaction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID REFERENCES users(id),
    interaction_type VARCHAR(100) NOT NULL,
    
    -- Request
    model_name VARCHAR(100) NOT NULL,
    prompt TEXT NOT NULL,
    input_tokens INTEGER,
    
    -- Response
    response TEXT,
    output_tokens INTEGER,
    latency_ms INTEGER,
    
    -- Context
    project_id UUID REFERENCES projects(id),
    report_id UUID REFERENCES reports(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- interaction_type: image_analysis, draft_generation, rewrite, chat, classification
CREATE INDEX idx_ai_logs_user ON ai_interaction_logs(user_id);
CREATE INDEX idx_ai_logs_type ON ai_interaction_logs(interaction_type);
CREATE INDEX idx_ai_logs_project ON ai_interaction_logs(project_id);
```

### chat_sessions
Private AI chat sessions.

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    report_id UUID REFERENCES reports(id),
    
    title VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_user ON chat_sessions(user_id);
```

### chat_messages
Individual messages in chat sessions.

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    
    -- AI Metadata
    tokens_used INTEGER,
    model_used VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- role: user, assistant, system
CREATE INDEX idx_messages_session ON chat_messages(session_id);
```

## Extensions Required

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable vector similarity search for RAG
CREATE EXTENSION IF NOT EXISTS "vector";
```

## Migration Strategy

1. Create base tables in dependency order
2. Add indexes after initial data load
3. Enable vector extension before historical_sors
4. Seed with initial user and example data
