from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
import json
from app.models import (
    User, Session as DBSession, Message, Memory, Person, Chapter,
    MemoryPerson, MemoryChapter, QuestionQueue, PromptRun
)
from app.schemas import ExtractorOutput, PlannerOutput, ExtractorMemory
from app.llm_provider import get_llm_provider
from app.prompts import get_prompt
import os


class ProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_provider()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def process_message(
        self,
        session_id: int,
        message_text: str,
        extractor_version: str = "v1",
        planner_version: str = "v1"
    ) -> Dict[str, Any]:
        """Main pipeline: process user message through extractor and planner"""
        
        # 1. Create message record
        message = Message(
            session_id=session_id,
            role="user",
            content_text=message_text
        )
        self.db.add(message)
        self.db.flush()
        
        # 2. Get context for extractor
        session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        context = self._build_extractor_context(session.user_id, session_id)
        
        # 3. Run extractor
        extractor_result = await self._run_extractor(
            message_text, context, message.id, extractor_version
        )
        
        # 4. Apply extractor results
        applied = self._apply_extractor_results(
            session.user_id, session_id, message.id, extractor_result
        )
        
        # 5. Run planner
        planner_result = await self._run_planner(
            session.user_id, session_id, context, planner_version
        )
        
        # 6. Apply planner results
        self._apply_planner_results(session.user_id, session_id, planner_result)
        
        self.db.commit()
        
        return {
            "message_id": message.id,
            "extractor_run_id": extractor_result["run_id"],
            "planner_run_id": planner_result["run_id"],
            "memories_created": applied["memories"],
            "persons_created": applied["persons"],
            "chapters_created": applied["chapters"]
        }

    def _build_extractor_context(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Build context for extractor prompt"""
        # Get recent memories
        recent_memories = self.db.query(Memory).filter(
            Memory.user_id == user_id
        ).order_by(desc(Memory.created_at)).limit(10).all()
        
        # Get existing persons
        persons = self.db.query(Person).filter(Person.user_id == user_id).all()
        
        # Get existing chapters
        chapters = self.db.query(Chapter).filter(Chapter.user_id == user_id).all()
        
        return {
            "session_id": session_id,
            "message_text": "",  # Will be filled in
            "known_persons": [
                {"id": p.id, "name": p.display_name, "type": p.type}
                for p in persons
            ],
            "known_chapters": [
                {"id": c.id, "title": c.title, "status": c.status}
                for c in chapters
            ],
            "recent_memories": [
                {"summary": m.summary, "narrative": m.narrative[:200]}
                for m in recent_memories[:5]
            ]
        }

    async def _run_extractor(
        self,
        message_text: str,
        context: Dict[str, Any],
        message_id: int,
        version: str
    ) -> Dict[str, Any]:
        """Run extractor prompt and store results"""
        context["message_text"] = message_text
        prompt_text = get_prompt("extractor", version)
        
        output_text, parsed_json, token_in, token_out, latency_ms = \
            await self.llm.call_extractor(prompt_text, context, self.model)
        
        # Validate parsing
        parse_ok = False
        error_text = None
        try:
            if "error" not in parsed_json:
                ExtractorOutput(**parsed_json)
                parse_ok = True
        except Exception as e:
            error_text = str(e)
        
        # Store prompt run
        run = PromptRun(
            session_id=context.get("session_id"),
            message_id=message_id,
            prompt_name="extractor",
            prompt_version=version,
            model=self.model,
            input_json=context,
            output_text=output_text,
            output_json=parsed_json,
            parse_ok=parse_ok,
            error_text=error_text,
            token_in=token_in,
            token_out=token_out,
            latency_ms=latency_ms
        )
        self.db.add(run)
        self.db.flush()
        
        return {
            "run_id": run.id,
            "parsed": parsed_json if parse_ok else None,
            "parse_ok": parse_ok
        }

    def _apply_extractor_results(
        self,
        user_id: int,
        session_id: int,
        message_id: int,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply extractor results to database"""
        if not result["parse_ok"] or not result["parsed"]:
            return {"memories": 0, "persons": 0, "chapters": 0}
        
        extractor_output = ExtractorOutput(**result["parsed"])
        memories_created = 0
        persons_created = 0
        chapters_created = 0
        
        for mem_data in extractor_output.memories:
            # Create memory
            memory = Memory(
                user_id=user_id,
                session_id=session_id,
                source_message_id=message_id,
                summary=mem_data.summary,
                narrative=mem_data.narrative,
                time_text=mem_data.time_text,
                location_text=mem_data.location_text,
                topics=mem_data.topics,
                importance_score=mem_data.importance
            )
            self.db.add(memory)
            self.db.flush()
            memories_created += 1
            
            # Create/update persons
            for person_data in mem_data.persons:
                person = self.db.query(Person).filter(
                    Person.user_id == user_id,
                    Person.display_name.ilike(person_data.name)
                ).first()
                
                if not person:
                    person = Person(
                        user_id=user_id,
                        display_name=person_data.name,
                        type=person_data.type,
                        first_seen_memory_id=memory.id
                    )
                    self.db.add(person)
                    self.db.flush()
                    persons_created += 1
                
                # Link memory to person
                link = MemoryPerson(
                    memory_id=memory.id,
                    person_id=person.id,
                    confidence=person_data.confidence
                )
                self.db.add(link)
            
            # Handle chapter suggestions
            for chapter_suggestion in mem_data.chapter_suggestions:
                if chapter_suggestion.confidence > 0.7:
                    chapter = self.db.query(Chapter).filter(
                        Chapter.user_id == user_id,
                        Chapter.title.ilike(chapter_suggestion.title)
                    ).first()
                    
                    if not chapter:
                        # Get max order_index
                        max_order = self.db.query(Chapter).filter(
                            Chapter.user_id == user_id
                        ).count()
                        chapter = Chapter(
                            user_id=user_id,
                            title=chapter_suggestion.title,
                            order_index=max_order,
                            status="draft"
                        )
                        self.db.add(chapter)
                        self.db.flush()
                        chapters_created += 1
                    
                    # Link memory to chapter
                    link = MemoryChapter(
                        memory_id=memory.id,
                        chapter_id=chapter.id,
                        confidence=chapter_suggestion.confidence
                    )
                    self.db.add(link)
        
        return {
            "memories": memories_created,
            "persons": persons_created,
            "chapters": chapters_created
        }

    async def _run_planner(
        self,
        user_id: int,
        session_id: int,
        context: Dict[str, Any],
        version: str
    ) -> Dict[str, Any]:
        """Run planner prompt and store results"""
        # Build planner context
        recent_memories = self.db.query(Memory).filter(
            Memory.user_id == user_id
        ).order_by(desc(Memory.created_at)).limit(20).all()
        
        chapters = self.db.query(Chapter).filter(Chapter.user_id == user_id).all()
        
        planner_context = {
            "recent_memories": [
                {
                    "id": m.id,
                    "summary": m.summary,
                    "narrative": m.narrative[:300],
                    "importance": m.importance_score
                }
                for m in recent_memories
            ],
            "chapters": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "memory_count": len(c.memories)
                }
                for c in chapters
            ],
            "known_gaps": []  # Could be enhanced
        }
        
        prompt_text = get_prompt("planner", version)
        
        output_text, parsed_json, token_in, token_out, latency_ms = \
            await self.llm.call_planner(prompt_text, planner_context, self.model)
        
        parse_ok = False
        error_text = None
        try:
            if "error" not in parsed_json:
                PlannerOutput(**parsed_json)
                parse_ok = True
        except Exception as e:
            error_text = str(e)
        
        run = PromptRun(
            session_id=session_id,
            message_id=None,
            prompt_name="planner",
            prompt_version=version,
            model=self.model,
            input_json=planner_context,
            output_text=output_text,
            output_json=parsed_json,
            parse_ok=parse_ok,
            error_text=error_text,
            token_in=token_in,
            token_out=token_out,
            latency_ms=latency_ms
        )
        self.db.add(run)
        self.db.flush()
        
        return {
            "run_id": run.id,
            "parsed": parsed_json if parse_ok else None,
            "parse_ok": parse_ok
        }

    def _apply_planner_results(
        self,
        user_id: int,
        session_id: int,
        result: Dict[str, Any]
    ):
        """Apply planner results to question_queue"""
        if not result["parse_ok"] or not result["parsed"]:
            return
        
        planner_output = PlannerOutput(**result["parsed"])
        
        for question_data in planner_output.questions:
            question = QuestionQueue(
                user_id=user_id,
                session_id=session_id,
                question_text=question_data.question_text,
                reason=question_data.reason,
                confidence=question_data.confidence,
                target_type=question_data.target.type,
                target_ref=question_data.target.ref,
                status="pending"
            )
            self.db.add(question)
