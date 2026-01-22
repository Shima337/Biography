import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
from app.schemas import ExtractorOutput, PlannerOutput


class LLMProvider(ABC):
    @abstractmethod
    async def call_extractor(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        """Returns: (output_text, parsed_json, token_in, token_out, latency_ms)"""
        pass

    @abstractmethod
    async def call_planner(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        """Returns: (output_text, parsed_json, token_in, token_out, latency_ms)"""
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)

    async def call_extractor(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": json.dumps(context, indent=2)}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                timeout=120.0,  # 120 секунд таймаут для длинных запросов
                max_tokens=4000,  # Ограничение выходных токенов для предотвращения превышения лимитов
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            output_text = response.choices[0].message.content
            token_in = response.usage.prompt_tokens
            token_out = response.usage.completion_tokens
            
            try:
                parsed_json = json.loads(output_text)
                # Validate against schema
                ExtractorOutput(**parsed_json)
            except Exception as e:
                parsed_json = {"error": str(e)}
            
            return output_text, parsed_json, token_in, token_out, latency_ms
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"OpenAI API error: {str(e)}"
            parsed_json = {"error": error_msg, "type": type(e).__name__}
            return error_msg, parsed_json, 0, 0, latency_ms

    async def call_planner(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": json.dumps(context, indent=2)}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                timeout=120.0,  # 120 секунд таймаут для длинных запросов
                max_tokens=2000,  # Ограничение выходных токенов для planner (меньше, так как генерирует только вопросы)
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            output_text = response.choices[0].message.content
            token_in = response.usage.prompt_tokens
            token_out = response.usage.completion_tokens
            
            try:
                parsed_json = json.loads(output_text)
                # Validate against schema
                PlannerOutput(**parsed_json)
            except Exception as e:
                parsed_json = {"error": str(e)}
            
            return output_text, parsed_json, token_in, token_out, latency_ms
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"OpenAI API error: {str(e)}"
            parsed_json = {"error": error_msg, "type": type(e).__name__}
            return error_msg, parsed_json, 0, 0, latency_ms


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for testing"""
    
    async def call_extractor(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        # Mock deterministic response
        output_json = {
            "memories": [
                {
                    "summary": f"Extracted memory from: {context.get('message_text', '')[:50]}",
                    "narrative": context.get("message_text", ""),
                    "time_text": "2024",
                    "location_text": None,
                    "topics": ["test"],
                    "importance": 0.7,
                    "persons": [],
                    "chapter_suggestions": []
                }
            ],
            "unknowns": [],
            "notes": "Mock extraction"
        }
        output_text = json.dumps(output_json, indent=2)
        return output_text, output_json, 100, 50, 200

    async def call_planner(
        self,
        prompt_text: str,
        context: Dict[str, Any],
        model: str,
    ) -> tuple[str, Dict[str, Any], int, int, int]:
        output_json = {
            "questions": [
                {
                    "question_text": "Can you tell me more about this?",
                    "reason": "Mock question for testing",
                    "confidence": 0.8,
                    "target": {"type": "global", "ref": None}
                }
            ]
        }
        output_text = json.dumps(output_json, indent=2)
        return output_text, output_json, 100, 30, 150


def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "openai")
    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")
