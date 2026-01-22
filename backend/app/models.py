from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    locale = Column(String, default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="user")
    memories = relationship("Memory", back_populates="user")
    persons = relationship("Person", back_populates="user")
    chapters = relationship("Chapter", back_populates="user")
    questions = relationship("QuestionQueue", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    memories = relationship("Memory", back_populates="session")
    prompt_runs = relationship("PromptRun", back_populates="session")
    questions = relationship("QuestionQueue", back_populates="session")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant" | "system"
    content_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")
    memories = relationship("Memory", back_populates="source_message")
    prompt_runs = relationship("PromptRun", back_populates="message")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    source_message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    summary = Column(Text, nullable=False)
    narrative = Column(Text, nullable=False)
    time_text = Column(String, nullable=True)
    location_text = Column(String, nullable=True)
    topics = Column(ARRAY(String), default=[])
    importance_score = Column(Float, default=0.5)
    pipeline_version = Column(String, default="v1")  # "v1" | "v2" - для различения подходов экстракции
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memories")
    session = relationship("Session", back_populates="memories")
    source_message = relationship("Message", back_populates="memories")
    persons = relationship("MemoryPerson", back_populates="memory")
    chapters = relationship("MemoryChapter", back_populates="memory")


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    display_name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "family" | "friend" | "romance" | "colleague" | "other"
    first_seen_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    pipeline_version = Column(String, default="v1")  # "v1" | "v2" - для различения подходов экстракции
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="persons")
    memories = relationship("MemoryPerson", back_populates="person")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    order_index = Column(Integer, default=0)
    period_text = Column(String, nullable=True)
    status = Column(String, default="draft")  # "draft" | "ready"

    user = relationship("User", back_populates="chapters")
    memories = relationship("MemoryChapter", back_populates="chapter")


class MemoryPerson(Base):
    __tablename__ = "memory_person"

    memory_id = Column(Integer, ForeignKey("memories.id"), primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), primary_key=True)
    confidence = Column(Float, default=0.5)

    memory = relationship("Memory", back_populates="persons")
    person = relationship("Person", back_populates="memories")


class MemoryChapter(Base):
    __tablename__ = "memory_chapter"

    memory_id = Column(Integer, ForeignKey("memories.id"), primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), primary_key=True)
    confidence = Column(Float, default=0.5)

    memory = relationship("Memory", back_populates="chapters")
    chapter = relationship("Chapter", back_populates="memories")


class QuestionQueue(Base):
    __tablename__ = "question_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    target_type = Column(String, nullable=False)  # "person" | "chapter" | "memory" | "global"
    target_ref = Column(String, nullable=True)
    status = Column(String, default="pending")  # "pending" | "asked" | "dismissed"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="questions")
    session = relationship("Session", back_populates="questions")


class PromptRun(Base):
    __tablename__ = "prompt_runs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    prompt_name = Column(String, nullable=False)  # "extractor" | "planner" | "writer"
    prompt_version = Column(String, nullable=False)
    pipeline_version = Column(String, default="v1")  # "v1" | "v2" - для различения подходов экстракции
    model = Column(String, nullable=False)
    input_json = Column(JSON, nullable=True)
    output_text = Column(Text, nullable=True)
    output_json = Column(JSON, nullable=True)
    parse_ok = Column(Boolean, default=False)
    error_text = Column(Text, nullable=True)
    token_in = Column(Integer, nullable=True)
    token_out = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="prompt_runs")
    message = relationship("Message", back_populates="prompt_runs")
