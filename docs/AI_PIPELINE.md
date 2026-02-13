# AI Pipeline Flow

## Overview

The AI pipeline processes inputs through five distinct stages, each with specific responsibilities and outputs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI PIPELINE FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │  Photos  │    │   PDFs   │    │Narrative │
     └────┬─────┘    └────┬─────┘    └────┬─────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: INGESTION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Validate file types and sizes                                      │    │
│  │ • Generate unique IDs                                                │    │
│  │ • Extract EXIF metadata from photos                                  │    │
│  │ • Assign to project/building/area                                    │    │
│  │ • Queue for processing                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: IMAGE UNDERSTANDING (Vision Model)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Input: Raw photo                                                     │    │
│  │                                                                      │    │
│  │ Process:                                                             │    │
│  │   1. Send to vision model (GPT-4V / LLaVA)                          │    │
│  │   2. Extract structured observations                                 │    │
│  │   3. Classify building type                                          │    │
│  │   4. Identify conditions and materials                               │    │
│  │                                                                      │    │
│  │ Output:                                                              │    │
│  │   {                                                                  │    │
│  │     "description": "Exterior view of...",                           │    │
│  │     "building_type": "commercial",                                  │    │
│  │     "conditions": [                                                 │    │
│  │       {"category": "roof", "issue": "ponding", "severity": "mod"}   │    │
│  │     ],                                                              │    │
│  │     "materials": ["brick", "steel", "concrete"],                    │    │
│  │     "safety_issues": [],                                            │    │
│  │     "location_clues": ["loading dock visible", "north elevation"]  │    │
│  │   }                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: DOCUMENT PARSING (PDF → Structured Text)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Input: PDF documents (plans, cost reviews, prior SORs)              │    │
│  │                                                                      │    │
│  │ Process:                                                             │    │
│  │   1. Extract text with PyMuPDF                                      │    │
│  │   2. Identify document type                                          │    │
│  │   3. Parse section headers                                           │    │
│  │   4. Extract key data points                                         │    │
│  │   5. For prior SORs: extract section content for comparison         │    │
│  │                                                                      │    │
│  │ Output by Document Type:                                             │    │
│  │                                                                      │    │
│  │   Prior SOR:                                                         │    │
│  │   {                                                                  │    │
│  │     "report_date": "2026-01-15",                                    │    │
│  │     "sections": {                                                   │    │
│  │       "executive_summary": "...",                                   │    │
│  │       "building_a_status": "..."                                    │    │
│  │     },                                                              │    │
│  │     "observations": [...],                                          │    │
│  │     "recommendations": [...]                                        │    │
│  │   }                                                                  │    │
│  │                                                                      │    │
│  │   Cost Review:                                                       │    │
│  │   {                                                                  │    │
│  │     "original_budget": 15000000,                                    │    │
│  │     "current_budget": 15500000,                                     │    │
│  │     "change_orders": [...],                                         │    │
│  │     "percent_complete": 67                                          │    │
│  │   }                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: STYLE LEARNING (RAG - Retrieval Augmented Generation)               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ NOT training a new model. Using retrieval from historical SORs.     │    │
│  │                                                                      │    │
│  │ Embedding Store (ChromaDB / pgvector):                              │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │ Historical SOR Section 1 → Embedding [0.12, -0.34, ...]     │   │    │
│  │   │ Historical SOR Section 2 → Embedding [0.08, -0.21, ...]     │   │    │
│  │   │ Historical SOR Section 3 → Embedding [-0.15, 0.44, ...]     │   │    │
│  │   │ ...                                                          │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │ Process:                                                             │    │
│  │   1. Receive query context (section type, building info, issues)    │    │
│  │   2. Generate embedding for query                                    │    │
│  │   3. Find top-k similar historical sections                          │    │
│  │   4. Return examples with similarity scores                          │    │
│  │                                                                      │    │
│  │ Output:                                                              │    │
│  │   [                                                                  │    │
│  │     {                                                                │    │
│  │       "id": "uuid",                                                 │    │
│  │       "section_type": "building_status",                            │    │
│  │       "content": "Building B was observed to be...",                │    │
│  │       "similarity": 0.92                                            │    │
│  │     },                                                              │    │
│  │     ...                                                             │    │
│  │   ]                                                                  │    │
│  │                                                                      │    │
│  │ Benefits:                                                            │    │
│  │   ✅ Maintains Hillmann tone                                        │    │
│  │   ✅ Uses proper phrasing                                           │    │
│  │   ✅ Follows established structure                                  │    │
│  │   ✅ No model training required                                     │    │
│  │   ✅ Easily updated with new examples                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: DRAFT GENERATION (LLM Synthesis)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Input Combination:                                                   │    │
│  │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │   │   Image     │ │  Document   │ │    User     │ │  Retrieved  │   │    │
│  │   │Descriptions │ │   Parsed    │ │  Narrative  │ │  Examples   │   │    │
│  │   │             │ │    Data     │ │             │ │  (RAG)      │   │    │
│  │   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘   │    │
│  │          │               │               │               │          │    │
│  │          └───────────────┴───────────────┴───────────────┘          │    │
│  │                                  │                                   │    │
│  │                                  ▼                                   │    │
│  │                         ┌───────────────┐                           │    │
│  │                         │  LLM PROMPT   │                           │    │
│  │                         │               │                           │    │
│  │                         │ System: You   │                           │    │
│  │                         │ are writing   │                           │    │
│  │                         │ a Hillmann    │                           │    │
│  │                         │ SOR section   │                           │    │
│  │                         │ ...           │                           │    │
│  │                         └───────┬───────┘                           │    │
│  │                                 │                                    │    │
│  │                                 ▼                                    │    │
│  │                         ┌───────────────┐                           │    │
│  │                         │  DRAFT SOR    │                           │    │
│  │                         │   SECTION     │                           │    │
│  │                         └───────────────┘                           │    │
│  │                                                                      │    │
│  │ Output:                                                              │    │
│  │   {                                                                  │    │
│  │     "section_type": "building_status",                              │    │
│  │     "content": "Building B – Status Update\n\nDuring the...",       │    │
│  │     "evidence_references": [                                        │    │
│  │       {"type": "image", "id": "uuid", "filename": "IMG_001.jpg"},   │    │
│  │       {"type": "prior_sor", "date": "2026-01-15", "section": "..."}│    │
│  │     ],                                                              │    │
│  │     "confidence": 0.85                                              │    │
│  │   }                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Specifications

### 2.1 Vision Model Configuration

**Recommended Models:**
| Model | Deployment | Pros | Cons |
|-------|------------|------|------|
| GPT-4V | OpenAI API | Best accuracy | External API |
| LLaVA | On-prem | Full privacy | Requires GPU |
| BLIP-2 | On-prem | Good balance | Lower accuracy |

**Prompt Template for Image Analysis:**
```
You are analyzing a construction site photograph for a Site Observation Report.

Describe what you observe, focusing on:
1. Building identification (type, materials, construction phase)
2. Condition assessment (any damage, deterioration, or defects)
3. Safety observations (hazards, compliance issues)
4. Materials visible
5. Location clues (orientation, signage, landmarks)

Respond in JSON format:
{
  "description": "Detailed description in professional engineering language",
  "building_type": "residential|commercial|industrial|mixed_use",
  "conditions": [
    {
      "category": "roof|exterior|interior|structural|mechanical|electrical|plumbing|site",
      "issue": "description of condition",
      "severity": "minor|moderate|severe|critical",
      "location": "where on the building"
    }
  ],
  "materials": ["list", "of", "materials"],
  "safety_issues": ["list of safety concerns if any"],
  "location_clues": ["visual clues about location"]
}
```

### 2.2 Document Parsing Rules

**Supported Document Types:**
| Type | Key Extraction Points |
|------|----------------------|
| Prior SOR | Section content, observations, recommendations, dates |
| Cost Review | Budget figures, change orders, percent complete |
| Plans | Building names, specifications, phases |
| Change Orders | CO number, amount, description, status |
| Contracts | Parties, amounts, scope |

**PDF Processing Pipeline:**
```python
def parse_document(file_path: str, doc_type: str) -> dict:
    # 1. Extract raw text
    text = extract_text_pymupdf(file_path)
    
    # 2. Identify sections
    sections = identify_sections(text, doc_type)
    
    # 3. Type-specific parsing
    if doc_type == "prior_sor":
        return parse_prior_sor(sections)
    elif doc_type == "cost_review":
        return parse_cost_review(sections)
    # ...
```

### 4.1 RAG Implementation

**Embedding Strategy:**
- Model: `text-embedding-3-small` (OpenAI) or `all-MiniLM-L6-v2` (local)
- Chunk size: 500 tokens with 50 token overlap
- Store: pgvector extension in PostgreSQL

**Retrieval Query Construction:**
```python
def build_rag_query(section_type: str, context: dict) -> str:
    """Build query for retrieving similar historical sections."""
    query_parts = [
        f"Section type: {section_type}",
        f"Building type: {context.get('building_type', 'unknown')}",
    ]
    
    if context.get('conditions'):
        conditions = ", ".join(c['issue'] for c in context['conditions'])
        query_parts.append(f"Conditions observed: {conditions}")
    
    return " ".join(query_parts)
```

### 5.1 Draft Generation Prompt

**System Prompt:**
```
You are a professional construction consultant writing a Site Observation Report 
for Hillmann Consulting. Your writing must:

1. Use formal, technical language appropriate for engineering reports
2. Reference specific evidence (photos, documents) with citations
3. Avoid speculation - only state what was directly observed
4. Use passive voice for observations ("It was observed that...")
5. Include specific dates and locations when available
6. Follow the exact structure of the example sections provided

CRITICAL RULES:
- Never fabricate observations not supported by the input data
- Always cite the source of each observation
- Flag any uncertainty with "appears to" or "further investigation recommended"
- Use Hillmann's standard terminology from the examples provided
```

**User Prompt Template:**
```
Generate the {section_type} section for the Site Observation Report.

PROJECT CONTEXT:
- Project: {project_name}
- Site: {site_name}
- Inspection Date: {inspection_date}
- Report Number: {report_number}

PHOTO OBSERVATIONS:
{image_descriptions}

DOCUMENT DATA:
{parsed_document_data}

INSPECTOR NOTES:
{user_narrative}

EXAMPLE SECTIONS (use this style and tone):
{retrieved_examples}

Generate the {section_type} section following the exact style of the examples.
Include [Evidence: filename] citations for all observations.
```

## Building Classification System

### Auto-Suggest Workflow
```
┌──────────────────────────────────────────────────────────────────┐
│                   BUILDING CLASSIFICATION                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. User uploads image                                           │
│     │                                                            │
│     ▼                                                            │
│  2. Vision model extracts features:                              │
│     - Building materials                                          │
│     - Architectural style                                         │
│     - Location clues (signage, landmarks)                         │
│     │                                                            │
│     ▼                                                            │
│  3. Compare to existing building embeddings:                      │
│     ┌─────────────┐                                              │
│     │ Building A  │ similarity: 0.45                             │
│     │ Building B  │ similarity: 0.89 ← BEST MATCH                │
│     │ Building C  │ similarity: 0.23                             │
│     └─────────────┘                                              │
│     │                                                            │
│     ▼                                                            │
│  4. If confidence > 0.75:                                        │
│     → Auto-suggest: "This image likely belongs to Building B"    │
│     │                                                            │
│     ▼                                                            │
│  5. User confirms or corrects                                    │
│     │                                                            │
│     ▼                                                            │
│  6. System learns from correction (updates building embedding)   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Building Feature Extraction
```json
{
  "building_id": "uuid",
  "learned_features": {
    "materials": ["brick", "steel", "glass"],
    "characteristics": ["loading_dock", "rooftop_hvac", "4_stories"],
    "typical_areas": ["north_elevation", "parking_lot", "main_entrance"],
    "embedding": [0.12, -0.34, 0.56, ...]
  }
}
```

## Error Handling & Fallbacks

| Stage | Potential Error | Fallback |
|-------|----------------|----------|
| Image Analysis | Vision API timeout | Queue for retry, use basic metadata |
| PDF Parsing | Corrupted file | Manual upload request, partial extraction |
| RAG Retrieval | No similar sections | Use generic templates |
| Draft Generation | LLM error | Show partial draft with manual sections |

## Performance Targets

| Operation | Target Latency | Max Acceptable |
|-----------|----------------|----------------|
| Image upload | < 2s | 5s |
| Image analysis | < 10s | 30s |
| PDF parsing | < 15s | 60s |
| RAG retrieval | < 1s | 3s |
| Section draft | < 15s | 45s |
| Full report generation | < 2min | 5min |

## Audit Points

Every AI operation logs:
```json
{
  "operation": "draft_generation",
  "user_id": "uuid",
  "project_id": "uuid",
  "input_summary": "5 images, 2 documents, 500 char narrative",
  "model_used": "gpt-4-turbo",
  "prompt_tokens": 2500,
  "completion_tokens": 800,
  "latency_ms": 12500,
  "status": "success",
  "timestamp": "2026-02-12T20:30:00Z"
}
```
