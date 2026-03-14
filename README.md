# SRS/SDD RAG Document Generator v2

## Complete Offline Pipeline: HRS → SRS → SDD with Traceability

```
┌──────────────────────────────────────────────────────────────────┐
│                        PIPELINE FLOW                             │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌────────┐ │
│  │  Upload   │───>│  Extract &   │───>│ Generate│───>│Generate│ │
│  │  HRS Doc  │    │  Classify    │    │  SRS    │    │  SDD   │ │
│  └──────────┘    │  Requirements│    └────┬────┘    └───┬────┘ │
│                  └──────────────┘         │              │      │
│                                          └──────┬───────┘      │
│                                                 │              │
│                                    ┌────────────▼────────────┐ │
│                                    │  Traceability Matrix    │ │
│                                    │  HRS → SRS → SDD       │ │
│                                    └─────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│  KNOWLEDGE BASE (ChromaDB)           LLM (Ollama 70B)          │
│  ├── Your SRS templates              100% local inference      │
│  ├── Your SDD templates                                        │
│  ├── Past SRS/SDD documents          Embeddings                │
│  └── Stored requirements             all-MiniLM-L6-v2 (local) │
└──────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Mixed-Format HRS Parsing
Handles any requirement format automatically:
- Numbered IDs: `REQ-001`, `HRS-042`, `FR-003`
- Natural language: "The system shall..."
- Numbered lists: "1.1 Support real-time processing"
- Bullets: "- Handle 100MHz sampling rate"
- Tables with requirement columns

### 2. Auto-Classification
Requirements are classified into 5 types using keyword analysis:
- **Functional** — what the system does
- **Performance** — speed, throughput, capacity
- **Interface** — protocols, connectors, APIs
- **Safety** — fault tolerance, redundancy, standards
- **Constraint** — environmental, physical, regulatory

You can override any classification in the review step.

### 3. Traceability Matrix
Automatic mapping: HRS-ID → SRS-ID → SDD Module → Verification Method

### 4. Section-by-Section Regeneration
After generating an SRS, click any section to regenerate it with specific feedback.
The model sees the full document context and only regenerates the target section.

### 5. Chained SRS → SDD Pipeline
SDD is generated directly from the SRS, ensuring every requirement has a 
corresponding design element. No manual copy-paste needed.

### 6. Template Matching
Upload your company's templates once. The system learns your:
- Document structure (section ordering, numbering)
- Writing style (formal, technical, specific terminology)
- Formatting conventions

## Setup

### Prerequisites
- Python 3.10+
- Ollama with your 70B model running
- ~2GB disk for embeddings + ChromaDB

### Install & Run

```bash
cd srs_sdd_rag_v2
pip install -r requirements.txt

# First run downloads embedding model (~80MB) — needs internet once
# After that, everything is 100% offline

python app.py
# → Open http://localhost:5000
```

### Configure Model (if your Ollama tag differs)

Edit `app.py` line 18, or use environment variables:
```bash
export OLLAMA_MODEL="llama3.1:70b"
export OLLAMA_URL="http://localhost:11434"
python app.py
```

## Workflow

### One-Time Setup (Knowledge Base)

1. **Upload your SRS template** → Sidebar → Select "SRS Templates" → Drop file
2. **Upload your SDD template** → Select "SDD Templates" → Drop file
3. **Upload past SRS/SDD docs** → Select "Reference SRS/SDD" → Drop files
4. **Upload any existing HRS/reqs** → Select "Requirements / HRS" → Drop files

### Per-Project Generation

**Step 1:** Enter project name + upload HRS document (or paste requirements)

**Step 2:** Review auto-extracted requirements — fix any misclassifications

**Step 3:** Generate SRS → Review → Optionally regenerate specific sections

**Step 4:** Generate SDD from SRS (chained — one click)

**Step 5:** Generate traceability matrix (HRS → SRS → SDD)

**Download** .docx files at any step.

## Project Persistence

Each project is saved to `./projects/` as JSON. Reopen past projects from 
the sidebar to continue editing, regenerate sections, or generate SDD.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Ollama status + collection stats |
| `/api/ingest` | POST | Upload doc to knowledge base |
| `/api/extract-requirements` | POST | Parse HRS and classify requirements |
| `/api/generate` | POST | Generate SRS or SDD |
| `/api/generate-sdd-from-srs` | POST | Chained SRS→SDD pipeline |
| `/api/regenerate-section` | POST | Regenerate single section |
| `/api/traceability` | POST | Build traceability matrix |
| `/api/download/<file>` | GET | Download .docx |
| `/api/projects` | GET | List all projects |
| `/api/project/<id>` | GET | Get project details |
| `/api/search` | POST | Search knowledge base |
| `/api/sections/<type>` | GET | Get SRS/SDD section definitions |

## Tips

- **More reference docs = better output.** Ingest 3-5 past SRS/SDD documents.
- **Template quality matters.** Include example content in templates, not just headings.
- **Use section regeneration** instead of regenerating the entire document.
- **Expect 2-5 min per generation** with a 70B model — this is normal.
- **For faster iteration:** temporarily switch to an 8B model during development.
