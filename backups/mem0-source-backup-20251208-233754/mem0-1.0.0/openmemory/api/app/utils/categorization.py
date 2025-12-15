import json
import logging
from typing import List

from app.utils.prompts import MEMORY_CATEGORIZATION_PROMPT
from mem0.memory.utils import extract_json, remove_code_blocks
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential


class MemoryCategories(BaseModel):
    categories: List[str]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
def get_categories_for_memory(memory: str) -> List[str]:
    """
    Get categories for a memory using the configured LLM provider.
    
    This function uses the Memory client's LLM (which respects the UI configuration),
    ensuring consistency with the rest of the system (Gemini, OpenAI, Ollama, etc.).
    """
    try:
        # Lazy import to avoid circular dependency with models.py
        from app.utils.memory import get_memory_client
        
        # Get Memory client with configured LLM provider
        memory_client = get_memory_client()
        if not memory_client:
            logging.warning("[WARNING] Memory client not available. Categorization disabled.")
            return []
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": MEMORY_CATEGORIZATION_PROMPT},
            {"role": "user", "content": memory}
        ]

        # Use the configured LLM to generate response with JSON format
        # Following SDK pattern: generate_response() always returns a string
        response = memory_client.llm.generate_response(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0
        )

        # Clean up response (remove code blocks if any)
        # Following SDK pattern from memory/main.py:434-453
        response = remove_code_blocks(response)
        
        if not response.strip():
            logging.warning("[WARNING] Empty response from LLM for categorization")
            return []

        # Extract and parse JSON following SDK pattern
        try:
            # First try direct JSON parsing
            response_json = json.loads(response)
        except json.JSONDecodeError:
            # Try extracting JSON from code blocks or text
            extracted_json = extract_json(response)
            response_json = json.loads(extracted_json)

        # Validate with Pydantic model
        parsed = MemoryCategories(**response_json)
        return [cat.strip().lower() for cat in parsed.categories]

    except ValidationError as ve:
        logging.error(f"[ERROR] Failed to validate categories response: {ve}")
        return []
    except json.JSONDecodeError as je:
        logging.error(f"[ERROR] Failed to parse JSON response: {je}")
        return []
    except Exception as e:
        logging.error(f"[ERROR] Failed to get categories: {e}")
        logging.debug(f"[DEBUG] Exception type: {type(e).__name__}")
        return []