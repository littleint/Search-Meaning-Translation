import logging
from typing import Dict, Any
from services.groq_service import lookup_with_groq
from services.fallback_service import lookup_with_fallback

logger = logging.getLogger(__name__)

async def get_word_details(query: str, source_lang: str = "auto", target_lang: str = "English") -> Dict[str, Any]:
    # Try Groq first
    try:
        groq_result = lookup_with_groq(query, source_lang, target_lang)
        if groq_result and groq_result.get("meanings"):
            return groq_result
    except Exception as e:
        logger.warning(f"Groq service failed or timed out: {e}")

    # Fallback to free services
    logger.info("Using free dictionary & translation fallback service.")
    return await lookup_with_fallback(query, source_lang, target_lang)
