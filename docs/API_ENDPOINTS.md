# API Endpoint Structure

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### Auth Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user (admin only) |
| POST | `/auth/login` | Login, returns JWT token |
| POST | `/auth/refresh` | Refresh JWT token |
| POST | `/auth/logout` | Invalidate token |
| GET | `/auth/me` | Get current user profile |
| PUT | `/auth/me` | Update current user profile |
| POST | `/auth/change-password` | Change password |

### Request/Response Examples

**POST /auth/login**
```json
// Request
{
  "email": "inspector@hillmann.com",
  "password": "securepassword123"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "inspector@hillmann.com",
    "full_name": "John Smith",
    "role": "inspector"
  }
}
```

---

## Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create new project |
| GET | `/projects/{id}` | Get project details |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Archive project |
| GET | `/projects/{id}/sites` | List sites in project |
| GET | `/projects/{id}/reports` | List reports in project |
| GET | `/projects/{id}/images` | List all project images |
| GET | `/projects/{id}/documents` | List all project documents |

**POST /projects**
```json
// Request
{
  "name": "Harbor View Condos",
  "client_name": "ABC Development Corp",
  "client_contact": "John Doe",
  "address": "123 Harbor Way, Boston MA",
  "description": "Multi-building residential development"
}

// Response
{
  "id": "uuid",
  "name": "Harbor View Condos",
  "client_name": "ABC Development Corp",
  "status": "active",
  "created_at": "2026-02-12T20:00:00Z"
}
```

---

## Sites

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sites` | List all sites (with filters) |
| POST | `/sites` | Create new site |
| GET | `/sites/{id}` | Get site details |
| PUT | `/sites/{id}` | Update site |
| DELETE | `/sites/{id}` | Delete site |
| GET | `/sites/{id}/buildings` | List buildings at site |

---

## Buildings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/buildings` | List all buildings (with filters) |
| POST | `/buildings` | Create new building |
| GET | `/buildings/{id}` | Get building details |
| PUT | `/buildings/{id}` | Update building |
| DELETE | `/buildings/{id}` | Delete building |
| GET | `/buildings/{id}/images` | List building images |

**POST /buildings**
```json
// Request
{
  "site_id": "uuid",
  "name": "Building A",
  "building_type": "residential",
  "floors": 4,
  "year_built": 2020,
  "square_footage": 45000,
  "description": "Main residential tower"
}
```

---

## File Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/images` | Upload photos (multipart) |
| POST | `/upload/documents` | Upload PDFs (multipart) |
| GET | `/files/{id}` | Get file metadata |
| GET | `/files/{id}/download` | Download file |
| DELETE | `/files/{id}` | Delete file |

**POST /upload/images**
```
Content-Type: multipart/form-data

Fields:
- files: File[] (multiple images)
- project_id: string (required)
- building_id: string (optional)
- area: string (optional)
- tags: string[] (optional)
```

```json
// Response
{
  "uploaded": [
    {
      "id": "uuid",
      "filename": "IMG_001_abc123.jpg",
      "original_filename": "IMG_001.jpg",
      "file_path": "/storage/photos/project-id/building-id/IMG_001_abc123.jpg",
      "file_size": 2048576,
      "width": 4032,
      "height": 3024,
      "ai_processing_queued": true
    }
  ],
  "failed": []
}
```

---

## AI Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/analyze-image` | Analyze single image |
| POST | `/ai/analyze-images` | Batch analyze images |
| POST | `/ai/parse-document` | Parse PDF document |
| POST | `/ai/classify-building` | Suggest building for image |
| POST | `/ai/generate-draft` | Generate report section draft |
| POST | `/ai/rewrite` | Rewrite text in Hillmann style |
| GET | `/ai/similar-sections` | Find similar historical sections |

**POST /ai/analyze-image**
```json
// Request
{
  "image_id": "uuid"
}

// Response
{
  "image_id": "uuid",
  "analysis": {
    "description": "Exterior view of Building B showing brick facade with visible mortar deterioration at northwest corner. Metal flashing appears intact. No immediate safety hazards observed.",
    "building_type": "commercial",
    "conditions": [
      {
        "category": "exterior",
        "condition": "mortar_deterioration",
        "severity": "moderate",
        "location": "northwest corner"
      }
    ],
    "materials": ["brick", "metal_flashing", "concrete_foundation"],
    "safety_issues": [],
    "suggested_building_id": "uuid",
    "confidence": 0.87
  },
  "tokens_used": 450,
  "model": "gpt-4-vision"
}
```

**POST /ai/generate-draft**
```json
// Request
{
  "report_id": "uuid",
  "section_type": "building_status",
  "building_id": "uuid",
  "include_images": true,
  "include_prior_sor": true
}

// Response
{
  "section_type": "building_status",
  "draft": "Building B – Status Update\n\nDuring the February 12, 2026 site observation, Building B was observed to be approximately 67% complete. The exterior brick facade installation continues with work progressing on the north elevation. Mortar deterioration was noted at the northwest corner, consistent with observations from the prior report dated January 15, 2026.\n\n[Evidence: IMG_001.jpg, IMG_002.jpg]\n\nRecommendation: Continue monitoring mortar condition; consider remediation during spring weather window.",
  "evidence_references": [
    {"type": "image", "id": "uuid", "filename": "IMG_001.jpg"},
    {"type": "image", "id": "uuid", "filename": "IMG_002.jpg"},
    {"type": "prior_sor", "section": "building_status", "date": "2026-01-15"}
  ],
  "similar_historical_sections": [
    {"id": "uuid", "similarity": 0.89, "preview": "Building C - Status..."}
  ]
}
```

**POST /ai/rewrite**
```json
// Request
{
  "text": "The roof has some water pooling issues that need to be fixed.",
  "style": "formal_sor",
  "context": {
    "section_type": "building_status",
    "building_name": "Building A"
  }
}

// Response
{
  "original": "The roof has some water pooling issues that need to be fixed.",
  "rewritten": "Ponding water was observed on the Building A rooftop membrane. This condition warrants attention to prevent potential membrane degradation. Recommend drainage assessment and remediation as weather permits."
}
```

---

## Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports` | List all reports |
| POST | `/reports` | Create new report |
| GET | `/reports/{id}` | Get report with sections |
| PUT | `/reports/{id}` | Update report metadata |
| DELETE | `/reports/{id}` | Delete report |
| POST | `/reports/{id}/generate` | Generate all AI drafts |
| POST | `/reports/{id}/approve` | Approve report |
| GET | `/reports/{id}/export` | Export to DOCX/PDF |
| GET | `/reports/{id}/versions` | Get version history |

**POST /reports**
```json
// Request
{
  "project_id": "uuid",
  "site_id": "uuid",
  "report_number": 5,
  "report_date": "2026-02-12",
  "inspection_date": "2026-02-10",
  "weather_conditions": "Clear, 45°F",
  "personnel_on_site": "Site superintendent, 12 workers observed"
}
```

**POST /reports/{id}/generate**
```json
// Request
{
  "sections": ["executive_summary", "budget", "schedule", "building_status", "recommendations"],
  "options": {
    "include_images": true,
    "include_prior_sor": true,
    "use_rag": true
  }
}

// Response
{
  "report_id": "uuid",
  "sections_generated": 5,
  "sections": [
    {
      "section_type": "executive_summary",
      "status": "completed",
      "draft_preview": "During the February 10, 2026 site observation..."
    }
  ],
  "total_tokens_used": 4500,
  "generation_time_ms": 12500
}
```

---

## Report Sections

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/{id}/sections` | List all sections |
| GET | `/reports/{id}/sections/{section_id}` | Get section detail |
| PUT | `/reports/{id}/sections/{section_id}` | Update section content |
| POST | `/reports/{id}/sections/{section_id}/regenerate` | Regenerate AI draft |
| POST | `/reports/{id}/sections/{section_id}/approve` | Approve section |

**PUT /reports/{id}/sections/{section_id}**
```json
// Request
{
  "human_content": "Updated content with human edits...",
  "is_final": false
}
```

---

## Chat (AI Assistant)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/chat/sessions` | List user's chat sessions |
| POST | `/chat/sessions` | Create new chat session |
| GET | `/chat/sessions/{id}` | Get session with messages |
| DELETE | `/chat/sessions/{id}` | Delete chat session |
| POST | `/chat/sessions/{id}/messages` | Send message, get AI response |

**POST /chat/sessions/{id}/messages**
```json
// Request
{
  "content": "Rewrite this in Hillmann report language: The building looks mostly done but there's some stuff that needs work.",
  "context": {
    "report_id": "uuid",
    "section_type": "building_status"
  }
}

// Response
{
  "id": "uuid",
  "role": "assistant",
  "content": "Here's a revised version in Hillmann's formal SOR style:\n\n\"The building was observed to be substantially complete during the site visit. However, several punch list items remain outstanding and require attention prior to final completion. These items have been documented in the attached photograph log and are detailed in the Recommendations section below.\"",
  "tokens_used": 180
}
```

---

## Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit/logs` | List audit logs (admin) |
| GET | `/audit/logs/{object_type}/{object_id}` | Get logs for object |
| GET | `/audit/ai-logs` | List AI interaction logs |
| GET | `/audit/export` | Export audit logs (CSV) |

**GET /audit/logs**
```
Query Parameters:
- user_id: uuid (optional)
- object_type: string (optional)
- action: string (optional)
- start_date: date (optional)
- end_date: date (optional)
- limit: int (default 100)
- offset: int (default 0)
```

---

## Health & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ai` | AI services status |
| GET | `/system/stats` | System statistics (admin) |

---

## Error Responses

All errors follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `AI_SERVICE_ERROR` | 503 | AI service unavailable |
| `RATE_LIMITED` | 429 | Too many requests |
