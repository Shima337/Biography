from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import sessions, memories, persons, chapters, prompt_runs, questions, users

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LifeBook Lab Console API",
    description="Developer-facing API for debugging AI memory extraction",
    version="1.0.0",
    # Max request body size is controlled by uvicorn --limit-max-requests
    # We set it in docker-compose.yml via uvicorn command
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(memories.router, prefix="/api/memories", tags=["memories"])
app.include_router(persons.router, prefix="/api/persons", tags=["persons"])
app.include_router(chapters.router, prefix="/api/chapters", tags=["chapters"])
app.include_router(prompt_runs.router, prefix="/api/prompt-runs", tags=["prompt-runs"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])


@app.get("/")
async def root():
    return {"message": "LifeBook Lab Console API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
