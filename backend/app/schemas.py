from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# Person Extractor Output Schema (для Pipeline v2)
class PersonExtractorPerson(BaseModel):
    name: str
    type: Literal["family", "friend", "romance", "colleague", "other"]
    confidence: float = Field(ge=0.0, le=1.0)
    mentioned_as: Optional[str] = None  # Как упомянут в тексте (роль или имя)


class PersonExtractorOutput(BaseModel):
    persons: List[PersonExtractorPerson] = []
    notes: Optional[str] = None


# Extractor Output Schema
class ExtractorPerson(BaseModel):
    name: str
    type: Literal["family", "friend", "romance", "colleague", "other"]
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractorChapterSuggestion(BaseModel):
    title: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractorMemory(BaseModel):
    summary: str
    narrative: str
    time_text: Optional[str] = None
    location_text: Optional[str] = None
    topics: List[str] = []
    importance: float = Field(ge=0.0, le=1.0)
    persons: List[ExtractorPerson] = []
    chapter_suggestions: List[ExtractorChapterSuggestion] = []


class ExtractorOutput(BaseModel):
    memories: List[ExtractorMemory] = []
    unknowns: List[str] = []
    notes: Optional[str] = None


# Planner Output Schema
class PlannerTarget(BaseModel):
    type: Literal["person", "chapter", "memory", "global"]
    ref: Optional[str] = None


class PlannerQuestion(BaseModel):
    question_text: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    target: PlannerTarget


class PlannerOutput(BaseModel):
    questions: List[PlannerQuestion] = []


# API Request/Response Schemas
class MessageCreate(BaseModel):
    text: str


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryResponse(BaseModel):
    id: int
    user_id: int
    session_id: int
    source_message_id: int
    summary: str
    narrative: str
    time_text: Optional[str]
    location_text: Optional[str]
    topics: List[str]
    importance_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class PersonResponse(BaseModel):
    id: int
    user_id: int
    display_name: str
    type: str
    first_seen_memory_id: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    id: int
    user_id: int
    title: str
    order_index: int
    period_text: Optional[str]
    status: str

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    user_id: int
    session_id: int
    question_text: str
    reason: str
    confidence: float
    target_type: str
    target_ref: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PromptRunResponse(BaseModel):
    id: int
    session_id: int
    message_id: Optional[int]
    prompt_name: str
    prompt_version: str
    model: str
    input_json: Optional[dict]
    output_text: Optional[str]
    output_json: Optional[dict]
    parse_ok: bool
    error_text: Optional[str]
    token_in: Optional[int]
    token_out: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
