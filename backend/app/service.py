from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any
import json
import asyncio
from app.models import (
    User, Session as DBSession, Message, Memory, Person, Chapter,
    MemoryPerson, MemoryChapter, QuestionQueue, PromptRun
)
from app.schemas import ExtractorOutput, PlannerOutput, ExtractorMemory, ExtractorPerson, PersonExtractorOutput
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
        """Main pipeline: process user message through two-stage extractor (person_extractor → memory_extractor) and planner"""
        
        # 1. Create message record
        message = Message(
            session_id=session_id,
            role="user",
            content_text=message_text
        )
        self.db.add(message)
        self.db.flush()
        
        # 2. Get context and session
        session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        context = self._build_extractor_context(session.user_id, session_id)
        
        # 3. Prepare message history
        message_history = context.get("message_history", [])
        
        # 4. Pipeline: Two-stage extraction (person_extractor → memory_extractor)
        # Stage 1: Extract persons
        person_result = await self._run_person_extractor_v2(
            message_text, message_history, session_id, message.id
        )
        extracted_persons = self._apply_person_extractor_results_v2(
            session.user_id, message.id, person_result
        )
        
        # Stage 2: Extract memories using found persons
        memory_result = await self._run_memory_extractor_v2(
            message_text, extracted_persons, context, message.id
        )
        applied = self._apply_memory_extractor_results_v2(
            session.user_id, session_id, message.id, memory_result, extracted_persons
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
            "person_extractor_run_id": person_result["run_id"],
            "memory_extractor_run_id": memory_result["run_id"],
            "memories_created": applied["memories"],
            "persons_created": applied["persons"],
            "chapters_created": applied["chapters"],
            "planner_run_id": planner_result["run_id"]
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
                {"summary": m.summary}  # Убрали narrative - он засоряет контекст, summary достаточно
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
            pipeline_version="v1",
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

    async def _run_person_extractor_v2(
        self,
        message_text: str,
        message_history: List[Dict[str, str]],
        session_id: int,
        message_id: int
    ) -> Dict[str, Any]:
        """Pipeline v2 - Stage 1: Extract persons from message only (no DB context)"""
        prompt_text = get_prompt("person_extractor", "v1")
        
        # Минимальный контекст - только сообщение и история
        context = {
            "message_text": message_text[:2000] if len(message_text) > 2000 else message_text,
            "message_history": message_history
        }
        
        output_text, parsed_json, token_in, token_out, latency_ms = \
            await self.llm.call_extractor(prompt_text, context, self.model)
        
        # Validate parsing
        parse_ok = False
        error_text = None
        try:
            if "error" not in parsed_json:
                PersonExtractorOutput(**parsed_json)
                parse_ok = True
        except Exception as e:
            error_text = str(e)
        
        # Store prompt run
        input_data = context.copy()
        input_data["system_prompt"] = prompt_text
        
        run = PromptRun(
            session_id=session_id,
            message_id=message_id,
            prompt_name="person_extractor",
            prompt_version="v1",
            pipeline_version="v2",
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

    def _apply_person_extractor_results_v2(
        self,
        user_id: int,
        message_id: int,
        person_result: Dict[str, Any]
    ) -> Dict[int, Person]:
        """Pipeline v2 - Apply person extractor results, return mapping of person_id -> Person"""
        if not person_result["parse_ok"] or not person_result["parsed"]:
            return {}
        
        person_output = PersonExtractorOutput(**person_result["parsed"])
        person_map = {}  # person_id -> Person
        processed_names = []  # Track names we've processed to detect duplicates
        
        for person_data in person_output.persons:
            # Find or create person
            name = person_data.name.strip()
            person_type = person_data.type
            
            # Check if this name is a variant of an already processed person in this batch
            # (e.g., "Тася" vs "Таиса Владимировна", "Витя" vs "Виктор")
            merged = False
            for processed_name, processed_person in processed_names:
                # Check if names are variants (one contains the other, or they're similar)
                name_lower = name.lower()
                processed_lower = processed_name.lower()
                
                # Check if one name is contained in another (e.g., "Тася" in "Таиса Владимировна")
                if name_lower in processed_lower or processed_lower in name_lower:
                    # Prefer longer/more formal name
                    if len(name) > len(processed_name):
                        # Update existing person with longer name
                        processed_person.display_name = name
                        self.db.flush()
                        processed_names.remove((processed_name, processed_person))
                        processed_names.append((name, processed_person))
                    # Use existing person
                    person_map[processed_person.id] = processed_person
                    merged = True
                    break
            
            if merged:
                continue
            
            # Check if person exists in database (check both v1 and v2, but prefer v2)
            existing_person = self.db.query(Person).filter(
                Person.user_id == user_id,
                Person.display_name.ilike(name),
                Person.pipeline_version == "v2"
            ).first()
            
            if not existing_person:
                # Check v1 as fallback
                existing_person = self.db.query(Person).filter(
                    Person.user_id == user_id,
                    Person.display_name.ilike(name),
                    Person.pipeline_version == "v1"
                ).first()
                
                if existing_person:
                    # Update to v2
                    existing_person.pipeline_version = "v2"
                    self.db.flush()
            
            # Also check for variant names in database (fuzzy matching)
            # НО только среди людей, извлеченных в текущем сообщении (уже в processed_names)
            # Не проверяем всех людей пользователя, чтобы не брать людей из предыдущих сообщений
            if not existing_person:
                # Проверяем только среди уже обработанных в этом сообщении
                for processed_name, processed_person in processed_names:
                    name_lower = name.lower()
                    processed_lower = processed_name.lower()
                    # Check if names are variants
                    if name_lower in processed_lower or processed_lower in name_lower:
                        # Prefer longer name
                        if len(name) > len(processed_person.display_name):
                            processed_person.display_name = name
                            self.db.flush()
                        existing_person = processed_person
                        break
            
            if existing_person:
                person_map[existing_person.id] = existing_person
                processed_names.append((name, existing_person))
            else:
                # Create new person for v2
                person = Person(
                    user_id=user_id,
                    display_name=name,
                    type=person_type,
                    pipeline_version="v2",
                    first_seen_memory_id=None  # Will be set when memory is created
                )
                self.db.add(person)
                self.db.flush()
                person_map[person.id] = person
                processed_names.append((name, person))
        
        return person_map

    async def _run_memory_extractor_v2(
        self,
        message_text: str,
        extracted_persons: Dict[int, Person],  # person_id -> Person
        context: Dict[str, Any],
        message_id: int
    ) -> Dict[str, Any]:
        """Pipeline v2 - Stage 2: Extract memories using found persons"""
        prompt_text = get_prompt("extractor", "v3")  # Use existing extractor prompt
        
        # Create a copy of context to avoid modifying original
        v2_context = context.copy()
        
        # Add extracted persons to context (these are already found, so model should use them)
        v2_context["extracted_persons"] = [
            {"id": p.id, "name": p.display_name, "type": p.type}
            for p in extracted_persons.values()
        ]
        v2_context["message_text"] = message_text[:2000] if len(message_text) > 2000 else message_text
        
        output_text, parsed_json, token_in, token_out, latency_ms = \
            await self.llm.call_extractor(prompt_text, v2_context, self.model)
        
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
        input_data = v2_context.copy()
        input_data["system_prompt"] = prompt_text
        
        run = PromptRun(
            session_id=v2_context.get("session_id"),
            message_id=message_id,
            prompt_name="memory_extractor",
            prompt_version="v1",
            pipeline_version="v2",
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
            "parse_ok": parse_ok,
            "extracted_persons": extracted_persons
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
                            first_seen_memory_id=memory_id,
                            pipeline_version="v1"
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
            first_seen_memory_id=memory_id,
            pipeline_version="v1"
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
                importance_score=mem_data.importance,
                pipeline_version="v1"
            )
            self.db.add(memory)
            self.db.flush()
            memories_created += 1
            
            # Отслеживать уже обработанные связи для этой памяти (чтобы избежать дубликатов в одной транзакции)
            processed_person_links = {}  # {(memory_id, person_id): max_confidence}
            
            # Create/update persons with improved matching
            for person_data in mem_data.persons:
                # Check if person exists before creating (только для v1)
                existing_person = self.db.query(Person).filter(
                    Person.user_id == user_id,
                    Person.display_name.ilike(person_data.name),
                    Person.pipeline_version == "v1"
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

    def _apply_memory_extractor_results_v2(
        self,
        user_id: int,
        session_id: int,
        message_id: int,
        result: Dict[str, Any],
        extracted_persons: Dict[int, Person]
    ) -> Dict[str, Any]:
        """Pipeline v2 - Apply memory extractor results with found persons"""
        if not result["parse_ok"] or not result["parsed"]:
            return {"memories": 0, "persons": 0, "chapters": 0}
        
        extractor_output = ExtractorOutput(**result["parsed"])
        memories_created = 0
        persons_created = 0
        chapters_created = 0
        
        # Map person names to Person objects (for matching by name from memory extractor output)
        person_name_map = {p.display_name.lower(): p for p in extracted_persons.values()}
        
        for mem_data in extractor_output.memories:
            # Create memory with pipeline_version="v2"
            memory = Memory(
                user_id=user_id,
                session_id=session_id,
                source_message_id=message_id,
                summary=mem_data.summary,
                narrative=mem_data.narrative,
                time_text=mem_data.time_text,
                location_text=mem_data.location_text,
                topics=mem_data.topics,
                importance_score=mem_data.importance,
                pipeline_version="v2"
            )
            self.db.add(memory)
            self.db.flush()
            memories_created += 1
            
            # Link to extracted persons (match by name from memory extractor output)
            processed_person_links = {}
            for person_data in mem_data.persons:
                person_name = person_data.name.strip().lower()
                person = person_name_map.get(person_name)
                
                if not person:
                    # Try fuzzy match (case insensitive)
                    person = next((p for p in extracted_persons.values() if p.display_name.lower() == person_name), None)
                
                if person:
                    link_key = (memory.id, person.id)
                    if link_key not in processed_person_links:
                        link = MemoryPerson(
                            memory_id=memory.id,
                            person_id=person.id,
                            confidence=person_data.confidence
                        )
                        self.db.add(link)
                        processed_person_links[link_key] = person_data.confidence
            
            # Handle chapter suggestions (same as v1)
            processed_chapter_links = {}
            for chapter_suggestion in mem_data.chapter_suggestions:
                if chapter_suggestion.confidence > 0.7:
                    chapter = self.db.query(Chapter).filter(
                        Chapter.user_id == user_id,
                        Chapter.title.ilike(chapter_suggestion.title)
                    ).first()
                    
                    if not chapter:
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
                    
                    chapter_link_key = (memory.id, chapter.id)
                    if chapter_link_key not in processed_chapter_links:
                        link = MemoryChapter(
                            memory_id=memory.id,
                            chapter_id=chapter.id,
                            confidence=chapter_suggestion.confidence
                        )
                        self.db.add(link)
                        processed_chapter_links[chapter_link_key] = chapter_suggestion.confidence
        
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
