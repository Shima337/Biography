# LifeBook Lab Console - Setup Guide

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your OpenAI API key:**
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Seed sample data (optional):**
   ```bash
   docker-compose exec backend python seed.py
   ```

6. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Testing Without OpenAI

Set in `.env`:
```env
LLM_PROVIDER=mock
```

This uses a deterministic mock provider that doesn't make API calls.

## Troubleshooting

- **Port conflicts**: Change ports in `docker-compose.yml`
- **Database errors**: Check PostgreSQL logs: `docker-compose logs postgres`
- **Backend errors**: Check backend logs: `docker-compose logs backend`
- **Frontend errors**: Check frontend logs: `docker-compose logs frontend`

## Development Mode

To run without Docker:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Make sure PostgreSQL is running and `DATABASE_URL` in `.env` points to it.
