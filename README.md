# LifeBook Lab Console

A developer-facing application for debugging, observing, and iterating AI memory extraction prompts.

## Overview

LifeBook Lab Console is a **prompt laboratory** designed to provide complete transparency into:
- What the AI extracts from user text
- How it categorizes memories
- What entities it creates (people, chapters, events)
- How entities are linked
- What the AI believes is "known" about the user
- What follow-up questions the AI wants to ask and WHY

Every AI step produces artifacts stored in the database and visible in the UI.

## Tech Stack

- **Frontend**: Next.js 14 (App Router, TypeScript)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector support
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **LLM**: OpenAI GPT models (configurable)
- **Local Dev**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (or use mock provider for testing)

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd Biography
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and set your OpenAI API key:**
   ```env
   OPENAI_API_KEY=your_key_here
   OPENAI_MODEL=gpt-4o-mini
   LLM_PROVIDER=openai  # or "mock" for testing
   ```

4. **Start services:**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

6. **Seed sample data (optional):**
   ```bash
   docker-compose exec backend python seed.py
   ```

7. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
Biography/
├── backend/
│   ├── app/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py        # DB connection
│   │   ├── main.py            # FastAPI app
│   │   ├── service.py         # Core processing pipeline
│   │   ├── llm_provider.py    # OpenAI + Mock providers
│   │   ├── prompts.py         # Prompt versioning system
│   │   └── routers/           # API endpoints
│   ├── alembic/               # Database migrations
│   ├── seed.py                # Seed script
│   └── requirements.txt
├── frontend/
│   ├── app/                   # Next.js app router pages
│   ├── lib/
│   │   └── api.ts             # API client
│   └── package.json
└── docker-compose.yml
```

## Core Features

### 1. Sessions
- Create and manage conversation sessions
- View message timeline with AI processing results
- Send new messages and process through extractor/planner pipeline
- Re-run extractor with different prompt versions

### 2. Memory Inbox
- Browse all extracted memories
- Filter by user, session, importance
- View detailed memory information including:
  - Narrative and summary
  - Linked persons and chapters
  - Source message
  - Importance score

### 3. People
- View all person entities extracted by AI
- See all memories linked to each person
- Merge duplicate persons

### 4. Chapters (Outline)
- View biography chapter structure
- See coverage statistics (% of memories linked)
- Browse memories by chapter

### 5. Prompt Runs (Debug)
- **Critical for debugging**: View every LLM call
- Filter by prompt name, parse status, model
- See:
  - Input JSON sent to LLM
  - Raw output text
  - Parsed JSON (or errors)
  - Token usage and latency
- Compare different prompt versions side-by-side

### 6. Next Questions
- View AI-generated follow-up questions
- See the **reason** why each question was generated
- Mark questions as asked/dismissed
- Filter by status

## AI Pipeline

### Message Processing Flow

1. **User sends message** → Stored in `messages` table
2. **Extractor Prompt** runs:
   - Input: message text + context (known persons, chapters, recent memories)
   - Output: structured memories with persons, chapters, topics
   - Validated against strict Pydantic schema
   - Stored in `prompt_runs` table
3. **Apply Extractor Results**:
   - Create `memory` records
   - Create/update `person` records
   - Link memories ↔ persons via `memory_person`
   - Create/suggest `chapter` records
   - Link memories ↔ chapters via `memory_chapter`
4. **Planner Prompt** runs:
   - Input: recent memories + outline + known gaps
   - Output: next questions with reasons
   - Stored in `prompt_runs` table
5. **Apply Planner Results**:
   - Insert questions into `question_queue`

### Extractor Output Schema

```json
{
  "memories": [
    {
      "summary": "brief summary",
      "narrative": "full narrative text",
      "time_text": "time period or null",
      "location_text": "location or null",
      "topics": ["topic1", "topic2"],
      "importance": 0.0-1.0,
      "persons": [
        {
          "name": "person name",
          "type": "family|friend|romance|colleague|other",
          "confidence": 0.0-1.0
        }
      ],
      "chapter_suggestions": [
        {
          "title": "chapter title",
          "confidence": 0.0-1.0
        }
      ]
    }
  ],
  "unknowns": ["list of unclear things"],
  "notes": "optional notes"
}
```

### Planner Output Schema

```json
{
  "questions": [
    {
      "question_text": "the question",
      "reason": "why this question is important",
      "confidence": 0.0-1.0,
      "target": {
        "type": "person|chapter|memory|global",
        "ref": "reference id or null"
      }
    }
  ]
}
```

## Prompt Versioning

Prompts are versioned in `backend/app/prompts.py`:

- **Extractor prompts**: `v1`, `v2`, ...
- **Planner prompts**: `v1`, `v2`, ...

### Adding a New Prompt Version

1. Edit `backend/app/prompts.py`
2. Add new version to the `PROMPTS` dictionary:
   ```python
   "extractor": {
       "v1": "...",
       "v2": "...",  # Add new version
       "v3": "..."   # Or increment
   }
   ```
3. The UI will automatically show new versions in dropdowns

### Re-running with Different Versions

In the Session Detail page:
- Select different extractor/planner versions
- Process the same message again
- Compare results in Prompt Runs

## Debugging Extractor Failures

1. **Go to Prompt Runs page**
2. **Filter by `parse_ok = false`** to see failures
3. **Click "View" on a failed run** to see:
   - Input JSON sent to LLM
   - Raw output text (what LLM returned)
   - Parsed JSON attempt
   - Error message explaining why parsing failed
4. **Common issues**:
   - LLM didn't follow JSON schema
   - Missing required fields
   - Invalid enum values (e.g., person type)
   - Type mismatches (string vs number)

### Fixing Parse Errors

1. **Improve prompt**: Edit prompt in `prompts.py` to be more explicit
2. **Add validation**: Update Pydantic schema in `schemas.py` if needed
3. **Test with mock**: Use `LLM_PROVIDER=mock` for deterministic testing

## Database Schema

Key tables:
- `users` - User accounts
- `sessions` - Conversation sessions
- `messages` - User/assistant messages
- `memories` - Extracted memories
- `persons` - Person entities
- `chapters` - Biography chapters
- `memory_person` - Memory ↔ Person links
- `memory_chapter` - Memory ↔ Chapter links
- `question_queue` - AI-generated questions
- `prompt_runs` - **All LLM calls logged here**

See `backend/app/models.py` for full schema.

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://lifebook:lifebook_dev@localhost:5432/lifebook_lab

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4, etc.

# LLM Provider
LLM_PROVIDER=openai  # or "mock" for testing

# Backend
BACKEND_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

### Running Locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
- Ensure PostgreSQL is running
- Run migrations: `alembic upgrade head`
- Seed data: `python seed.py`

### Creating Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Testing with Mock Provider

Set `LLM_PROVIDER=mock` in `.env` for deterministic, fast testing without API calls.

## API Endpoints

- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}/messages` - Get messages
- `POST /api/sessions/{id}/messages` - Process message
- `GET /api/memories` - List memories
- `GET /api/persons` - List persons
- `GET /api/chapters` - List chapters
- `GET /api/prompt-runs` - List prompt runs (with filters)
- `GET /api/questions` - List questions

See http://localhost:8000/docs for full API documentation.

## Philosophy

This app exists to answer:
- **"What exactly did the AI understand?"**
- **"Why did it ask this question?"**
- **"Where did it store this memory?"**
- **"Which prompt version broke things?"**

Do NOT optimize for beauty.
Optimize for **transparency** and **iteration speed**.

## Troubleshooting

**Database connection errors:**
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in `.env`

**Frontend can't connect to backend:**
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Ensure backend is running on port 8000

**LLM calls failing:**
- Verify `OPENAI_API_KEY` is set
- Check API key has credits
- Try `LLM_PROVIDER=mock` to test without API

**Parse errors:**
- Check Prompt Runs page for detailed error messages
- Review prompt in `prompts.py`
- Validate schema in `schemas.py`

## License

MIT

## Author

Built for LifeBook Lab Console - AI Memory Extraction Debugging
