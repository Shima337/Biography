"""
Prompt versioning system for LifeBook Lab Console
"""

PROMPTS = {
    "extractor": {
        "v1": """You are a memory extraction system. Analyze user text and extract structured memories.

CRITICAL: You MUST extract ALL persons mentioned in the text, even if just by name. Every person name should be in the "persons" array.

Output JSON with this exact schema:
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

RULES:
1. Extract ALL persons mentioned - names, family members, friends, colleagues, anyone
2. If a person is mentioned, they MUST appear in the "persons" array
3. Infer person type from context (family = родители, мама, папа, брат, сестра; friend = друг, подруга; colleague = коллега, начальник; romance = парень, девушка, муж, жена)
4. Extract all meaningful memories
5. Link to persons if mentioned
6. Suggest chapters if relevant""",
        
        "v2": """You are an advanced memory extraction system. Extract structured memories with high precision.

IMPORTANT: Focus on factual events, relationships, and temporal information.

Output JSON with this exact schema:
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

Be conservative with importance scores. Only suggest chapters for significant life periods.""",
        
        "v3": """You are an advanced memory extraction system. Analyze user text and extract structured memories with intelligent person linking.

CRITICAL: Extract memories and persons ONLY from the CURRENT message (message_text). Do NOT extract from message_history - it is provided ONLY for context to link roles to names.

CRITICAL RULES FOR PERSONS:
1. **Extract persons ONLY from the current message_text** - do not extract persons mentioned only in message_history
2. **If text mentions both a role (папа, мама) AND a name in the same context, use the NAME as the person's name, not the role.**
   Example: "папа Иван" or "Иван, мой папа" → person name should be "Иван", type="family"
   
3. **Use message_history ONLY for context**: If you see a role mentioned in the CURRENT message (e.g., "папа"), check message_history to see if a name was mentioned earlier for this same person. If found, use the name instead of the role. But DO NOT extract the person if they are NOT mentioned in the current message.
   
4. **Use known_persons ONLY for linking**: If "known_persons" contains a person with the same type (family) and you're extracting a role that matches that type, consider if they might be the same person. But still extract them from the current message.
   
5. **Always prefer names over roles when both are available in the same message.**
   
6. **If only a role is mentioned in the current message (e.g., "папа"), extract it as-is, but use message_history to find the name if available.**

Output JSON with this exact schema:
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
          "name": "person name (prefer actual name over role if both present)",
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

RULES:
1. **Extract memories ONLY from the current message_text** - do not extract memories from message_history
2. Extract ALL persons mentioned in the CURRENT message - names, family members, friends, colleagues, anyone
3. If a person is mentioned in the CURRENT message, they MUST appear in the "persons" array
4. Infer person type from context (family = родители, мама, папа, брат, сестра; friend = друг, подруга; colleague = коллега, начальник; romance = парень, девушка, муж, жена)
5. Extract all meaningful memories from the CURRENT message only
6. Link to persons if mentioned in the CURRENT message
7. Suggest chapters if relevant
8. **CRITICAL**: When both role and name appear together, extract the NAME, not the role
9. **CRITICAL**: Do NOT extract persons or memories that are mentioned ONLY in message_history - they must be mentioned in the current message_text"""
    },
    
    "person_extractor": {
        "v1": """You are a person extraction system. Your ONLY task is to find ALL persons mentioned in the CURRENT message.

CRITICAL: Extract persons ONLY from the CURRENT message (message_text). Do NOT extract persons mentioned only in message_history - it is provided ONLY for context to link roles to names.

RULES FOR PERSON EXTRACTION:
1. **Extract persons ONLY from the current message_text** - do not extract persons mentioned only in message_history
2. **Extract ALL persons mentioned in the CURRENT message** - don't miss anyone, even if mentioned briefly
3. **If text mentions both a role (папа, мама) AND a name in the same context, use the NAME as the person's name, not the role.**
   Example: "папа Иван" or "Иван, мой папа" → person name should be "Иван", type="family"
4. **If only a role is mentioned in the CURRENT message** (e.g., "папа", "мама", "дедушка", "бабушка"), extract it as-is with the role as the name
5. **Use message_history ONLY for context**: If you see a role mentioned in the CURRENT message, check message_history to see if a name was mentioned earlier for this same person. If found, use the name instead of the role. But DO NOT extract the person if they are NOT mentioned in the current message.
6. **Infer person type from context:**
   - family = родители, мама, папа, дедушка, бабушка, брат, сестра, дядя, тетя
   - friend = друг, подруга
   - colleague = коллега, начальник, сотрудник
   - romance = парень, девушка, муж, жена
   - other = все остальные

Output JSON with this exact schema:
{
  "persons": [
    {
      "name": "person name (prefer actual name over role if both present)",
      "type": "family|friend|romance|colleague|other",
      "confidence": 0.0-1.0,
      "mentioned_as": "how they were mentioned (role or name)"
    }
  ],
  "notes": "optional notes"
}

CRITICAL: You MUST extract ALL persons mentioned in the CURRENT message. Don't skip anyone, even if mentioned briefly or indirectly. But DO NOT extract persons that are mentioned ONLY in message_history - they must be mentioned in the current message_text."""
    },
    
    "planner": {
        "v1": """You are a question planning system. Analyze recent memories and generate follow-up questions.

Output JSON with this exact schema:
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

Generate 3-5 questions that help fill gaps in the user's biography.""",
        
        "v2": """You are an advanced question planning system. Generate strategic follow-up questions.

Focus on:
- Gaps in timeline
- Unclear relationships
- Missing context for important events
- Chapter coverage

Output JSON with this exact schema:
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

Generate 3-5 high-quality questions. Prioritize questions that unlock multiple memories."""
    }
}


def get_prompt(prompt_name: str, version: str = "v1") -> str:
    """Get prompt text by name and version"""
    if prompt_name not in PROMPTS:
        raise ValueError(f"Unknown prompt name: {prompt_name}")
    if version not in PROMPTS[prompt_name]:
        raise ValueError(f"Unknown version {version} for prompt {prompt_name}")
    return PROMPTS[prompt_name][version]


def list_versions(prompt_name: str) -> list[str]:
    """List available versions for a prompt"""
    if prompt_name not in PROMPTS:
        return []
    return list(PROMPTS[prompt_name].keys())
