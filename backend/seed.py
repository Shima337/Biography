#!/usr/bin/env python3
"""
Seed script for LifeBook Lab Console
Creates sample data for development and testing
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    User, Session, Message, Memory, Person, Chapter,
    MemoryPerson, MemoryChapter, QuestionQueue, PromptRun
)
from app.database import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lifebook:lifebook_dev@localhost:5432/lifebook_lab")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed_database():
    db = SessionLocal()
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create user
        user = db.query(User).filter(User.name == "Test User").first()
        if not user:
            user = User(name="Test User", locale="en")
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {user.id}")
        else:
            print(f"User already exists: {user.id}")
        
        # Create session
        session = db.query(Session).filter(Session.user_id == user.id).first()
        if not session:
            session = Session(user_id=user.id)
            db.add(session)
            db.commit()
            db.refresh(session)
            print(f"Created session: {session.id}")
        else:
            print(f"Session already exists: {session.id}")
        
        # Create sample messages
        sample_messages = [
            "I grew up in a small town in Ohio. My parents were both teachers.",
            "In college, I met my best friend Sarah. We studied computer science together.",
            "After graduation, I moved to San Francisco to work at a tech startup.",
        ]
        
        for msg_text in sample_messages:
            existing = db.query(Message).filter(
                Message.session_id == session.id,
                Message.content_text == msg_text
            ).first()
            if not existing:
                message = Message(
                    session_id=session.id,
                    role="user",
                    content_text=msg_text
                )
                db.add(message)
                db.commit()
                db.refresh(message)
                print(f"Created message: {message.id}")
        
        # Create sample memory
        message = db.query(Message).filter(Message.session_id == session.id).first()
        if message:
            memory = db.query(Memory).filter(Memory.source_message_id == message.id).first()
            if not memory:
                memory = Memory(
                    user_id=user.id,
                    session_id=session.id,
                    source_message_id=message.id,
                    summary="Childhood in Ohio",
                    narrative="I grew up in a small town in Ohio. My parents were both teachers.",
                    time_text="Childhood",
                    location_text="Ohio",
                    topics=["childhood", "family"],
                    importance_score=0.8
                )
                db.add(memory)
                db.commit()
                db.refresh(memory)
                print(f"Created memory: {memory.id}")
        
        # Create sample person
        person = db.query(Person).filter(Person.user_id == user.id).first()
        if not person:
            person = Person(
                user_id=user.id,
                display_name="Sarah",
                type="friend",
                first_seen_memory_id=memory.id if 'memory' in locals() else None,
                notes="Met in college"
            )
            db.add(person)
            db.commit()
            db.refresh(person)
            print(f"Created person: {person.id}")
        
        # Create sample chapter
        chapter = db.query(Chapter).filter(Chapter.user_id == user.id).first()
        if not chapter:
            chapter = Chapter(
                user_id=user.id,
                title="Early Years",
                order_index=0,
                period_text="Childhood to College",
                status="draft"
            )
            db.add(chapter)
            db.commit()
            db.refresh(chapter)
            print(f"Created chapter: {chapter.id}")
        
        # Create sample prompt run
        prompt_run = db.query(PromptRun).filter(
            PromptRun.session_id == session.id
        ).first()
        if not prompt_run:
            prompt_run = PromptRun(
                session_id=session.id,
                message_id=message.id if 'message' in locals() else None,
                prompt_name="extractor",
                prompt_version="v1",
                model="gpt-4o-mini",
                input_json={"message_text": "Sample input"},
                output_text='{"memories": []}',
                output_json={"memories": []},
                parse_ok=True,
                token_in=100,
                token_out=50,
                latency_ms=200
            )
            db.add(prompt_run)
            db.commit()
            db.refresh(prompt_run)
            print(f"Created prompt run: {prompt_run.id}")
        
        # Create sample question
        question = db.query(QuestionQueue).filter(
            QuestionQueue.user_id == user.id
        ).first()
        if not question:
            question = QuestionQueue(
                user_id=user.id,
                session_id=session.id,
                question_text="What was your favorite subject in school?",
                reason="To understand educational background",
                confidence=0.8,
                target_type="global",
                target_ref=None,
                status="pending"
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            print(f"Created question: {question.id}")
        
        print("\n✅ Seed completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
