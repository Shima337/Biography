from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
import json
from app.models import (
    User, Session as DBSession, Message, Memory, Person, Chapter,
    MemoryPerson, MemoryChapter, QuestionQueue, PromptRun
)
from app.schemas import ExtractorOutput, PlannerOutput, ExtractorMemory, ExtractorPerson
from app.llm_provider import get_llm_provider
from app.prompts import get_prompt
import os


class ProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_provider()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.2")

    async def process_message(
        self,
        session_id: int,
        message_text: str,
        extractor_version: str = "v3",
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
        """Build context for extractor prompt - ограниченный размер для предотвращения превышения лимитов токенов"""
        # Get recent messages from this session for context (ограничить до 3)
        recent_messages = self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(desc(Message.created_at)).limit(3).all()
        
        # Get recent memories (ограничить до 3)
        recent_memories = self.db.query(Memory).filter(
            Memory.user_id == user_id
        ).order_by(desc(Memory.created_at)).limit(3).all()
        
        # ОГРАНИЧИТЬ количество персон (последние 20)
        persons = self.db.query(Person).filter(
            Person.user_id == user_id
        ).order_by(desc(Person.id)).limit(20).all()
        
        # ОГРАНИЧИТЬ количество глав (последние 15)
        chapters = self.db.query(Chapter).filter(
            Chapter.user_id == user_id
        ).order_by(desc(Chapter.id)).limit(15).all()
        
        return {
            "session_id": session_id,
            "message_text": "",  # Will be filled in
            "message_history": [
                {"role": m.role, "text": m.content_text[:500]}  # Ограничить длину сообщений до 500 символов
                for m in reversed(recent_messages[:-1])  # All except the last (current) message
            ],
            "known_persons": [
                {"id": p.id, "name": p.display_name, "type": p.type}
                for p in persons
            ],
            "known_chapters": [
                {"id": c.id, "title": c.title, "status": c.status}
                for c in chapters
            ],
            "recent_memories": [
                {"summary": m.summary, "narrative": m.narrative[:100]}  # Уменьшить до 100 символов
                for m in recent_memories[:3]  # Уменьшить до 3
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
        # Ограничить длину message_text до 2000 символов для предотвращения превышения лимитов
        context["message_text"] = message_text[:2000] if len(message_text) > 2000 else message_text
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
        
        # Store prompt run with full prompt text in input_json
        input_data = context.copy()
        input_data["system_prompt"] = prompt_text  # Сохранить полный system prompt
        
        run = PromptRun(
            session_id=context.get("session_id"),
            message_id=message_id,
            prompt_name="extractor",
            prompt_version=version,
            model=self.model,
            input_json=input_data,
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

    def _find_or_create_person(
        self,
        user_id: int,
        person_data: ExtractorPerson,
        message_id: int,
        memory_id: int
    ) -> Person:
        """Smart person finding/creation with role and name matching"""
        import re
        
        name = person_data.name.strip()
        person_type = person_data.type
        
        # Get the source message for context
        message = self.db.query(Message).filter(Message.id == message_id).first()
        message_text = message.content_text.lower() if message else ""
        
        # 1. Exact match by name
        person = self.db.query(Person).filter(
            Person.user_id == user_id,
            Person.display_name.ilike(name)
        ).first()
        
        if person:
            return person
        
        # 2. For family members: check if role and name appear together in message
        if person_type == "family":
            # Family role mappings
            family_roles = {
                "папа": ["отец", "dad", "папочка", "пап"],
                "мама": ["мать", "mother", "мамочка", "мам"],
                "брат": ["brother"],
                "сестра": ["sister", "сестренка"]
            }
            
            # Check if message contains both role and a name
            # Pattern: "роль ИМЯ" or "ИМЯ, мой роль"
            name_pattern = r'\b([А-ЯЁ][а-яё]+)\b'
            names_in_message = re.findall(name_pattern, message_text)
            
            # If we have a role and a name in the message, try to link them
            role_lower = name.lower()
            for found_name in names_in_message:
                # Check if this name is close to the role in text
                role_pos = message_text.find(role_lower)
                name_pos = message_text.find(found_name.lower())
                
                if role_pos != -1 and name_pos != -1 and abs(role_pos - name_pos) < 30:
                    # Check if there's already a person with this name
                    existing_person = self.db.query(Person).filter(
                        Person.user_id == user_id,
                        Person.display_name.ilike(found_name)
                    ).first()
                    
                    if existing_person and existing_person.type == "family":
                        # Use the existing person with the name
                        return existing_person
                    elif not existing_person:
                        # Create new person with the name (not the role)
                        person = Person(
                            user_id=user_id,
                            display_name=found_name,
                            type=person_type,
                            first_seen_memory_id=memory_id
                        )
                        self.db.add(person)
                        self.db.flush()
                        return person
            
            # 3. Check if there's a person of the same type that might be the same
            same_type_persons = self.db.query(Person).filter(
                Person.user_id == user_id,
                Person.type == person_type
            ).all()
            
            # If only one person of this type exists, might be the same
            if len(same_type_persons) == 1:
                return same_type_persons[0]
        
        # 4. Create new person
        person = Person(
            user_id=user_id,
            display_name=name,
            type=person_type,
            first_seen_memory_id=memory_id
        )
        self.db.add(person)
        self.db.flush()
        return person

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
            
            # Отслеживать уже обработанные связи для этой памяти (чтобы избежать дубликатов в одной транзакции)
            processed_person_links = {}  # {(memory_id, person_id): max_confidence}
            
            # Create/update persons with improved matching
            for person_data in mem_data.persons:
                # Check if person exists before creating
                existing_person = self.db.query(Person).filter(
                    Person.user_id == user_id,
                    Person.display_name.ilike(person_data.name)
                ).first()
                
                person = self._find_or_create_person(
                    user_id=user_id,
                    person_data=person_data,
                    message_id=message_id,
                    memory_id=memory.id
                )
                
                # Check if this is a new person (wasn't in DB before)
                if not existing_person:
                    # Check if person was just created (has the memory_id we passed)
                    if person.first_seen_memory_id == memory.id:
                        persons_created += 1
                
                # Проверить, не обрабатывали ли мы уже эту связь в текущей транзакции
                link_key = (memory.id, person.id)
                if link_key in processed_person_links:
                    # Обновить confidence, если новая выше
                    if person_data.confidence > processed_person_links[link_key]:
                        processed_person_links[link_key] = person_data.confidence
                    continue
                
                # Проверить, не существует ли уже связь в базе данных
                existing_link = self.db.query(MemoryPerson).filter(
                    MemoryPerson.memory_id == memory.id,
                    MemoryPerson.person_id == person.id
                ).first()
                
                if not existing_link:
                    # Link memory to person
                    link = MemoryPerson(
                        memory_id=memory.id,
                        person_id=person.id,
                        confidence=person_data.confidence
                    )
                    self.db.add(link)
                    processed_person_links[link_key] = person_data.confidence
                else:
                    # Обновить confidence, если новая выше
                    if person_data.confidence > existing_link.confidence:
                        existing_link.confidence = person_data.confidence
                    processed_person_links[link_key] = max(person_data.confidence, existing_link.confidence)
            
            # Отслеживать уже обработанные связи глав для этой памяти
            processed_chapter_links = {}  # {(memory_id, chapter_id): max_confidence}
            
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
                    
                    # Проверить, не обрабатывали ли мы уже эту связь в текущей транзакции
                    chapter_link_key = (memory.id, chapter.id)
                    if chapter_link_key in processed_chapter_links:
                        # Обновить confidence, если новая выше
                        if chapter_suggestion.confidence > processed_chapter_links[chapter_link_key]:
                            processed_chapter_links[chapter_link_key] = chapter_suggestion.confidence
                        continue
                    
                    # Проверить, не существует ли уже связь в базе данных
                    existing_chapter_link = self.db.query(MemoryChapter).filter(
                        MemoryChapter.memory_id == memory.id,
                        MemoryChapter.chapter_id == chapter.id
                    ).first()
                    
                    if not existing_chapter_link:
                        # Link memory to chapter
                        link = MemoryChapter(
                            memory_id=memory.id,
                            chapter_id=chapter.id,
                            confidence=chapter_suggestion.confidence
                        )
                        self.db.add(link)
                        processed_chapter_links[chapter_link_key] = chapter_suggestion.confidence
                    else:
                        # Обновить confidence, если новая выше
                        if chapter_suggestion.confidence > existing_chapter_link.confidence:
                            existing_chapter_link.confidence = chapter_suggestion.confidence
                        processed_chapter_links[chapter_link_key] = max(chapter_suggestion.confidence, existing_chapter_link.confidence)
        
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
        """Run planner prompt and store results - ограниченный контекст"""
        # Build planner context (ограничить размер)
        recent_memories = self.db.query(Memory).filter(
            Memory.user_id == user_id
        ).order_by(desc(Memory.created_at)).limit(10).all()  # Было 20
        
        chapters = self.db.query(Chapter).filter(
            Chapter.user_id == user_id
        ).order_by(desc(Chapter.id)).limit(15).all()  # Ограничить вместо .all()
        
        planner_context = {
            "recent_memories": [
                {
                    "id": m.id,
                    "summary": m.summary,
                    "narrative": m.narrative[:150],  # Было 300, уменьшить до 150
                    "importance": m.importance_score
                }
                for m in recent_memories[:5]  # Ограничить до 5
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
        
        # Store prompt run with full prompt text in input_json
        input_data = planner_context.copy()
        input_data["system_prompt"] = prompt_text  # Сохранить полный system prompt
        
        run = PromptRun(
            session_id=session_id,
            message_id=None,
            prompt_name="planner",
            prompt_version=version,
            model=self.model,
            input_json=input_data,
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
