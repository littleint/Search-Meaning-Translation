import json
import logging
from typing import Dict, Any, Optional
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# List of preferred models available on Groq in priority order
MODEL_CANDIDATES = [
    GROQ_MODEL,
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

def get_groq_client() -> Optional[Groq]:
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        return None
    try:
        return Groq(api_key=GROQ_API_KEY.strip())
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

def lookup_with_groq(query: str, source_lang: str = "auto", target_lang: str = "English") -> Optional[Dict[str, Any]]:
    client = get_groq_client()
    if not client:
        return None

    system_prompt = """You are an expert multilingual dictionary, linguist, and translator.
Analyze the user's query (which can be a single word, phrase, idiom, sentence, or natural language question).
Extract or identify the core headword or phrase, and provide comprehensive definitions, parts of speech, synonyms, antonyms, phonetics, and translation.

You MUST respond strictly with a valid JSON object following this exact schema:
{
  "clean_word": "the base word or phrase in lowercase (e.g., 'serendipity' or 'break a leg')",
  "phonetic": "IPA or phonetic pronunciation (e.g., '/ˌsɛr.ənˈdɪp.ə.ti/') or empty string if not applicable",
  "source_lang": "detected source language name (e.g., 'English', 'French', 'Hindi')",
  "target_lang": "target translation language name (e.g., 'Spanish', 'English', 'German')",
  "translation": "accurate, context-aware translation into the target language",
  "meanings": [
    {
      "part_of_speech": "noun / verb / adjective / idiom / expression",
      "definitions": ["primary definition", "secondary definition if applicable"],
      "examples": ["example sentence showing usage in context"]
    }
  ],
  "synonyms": ["synonym1", "synonym2", "synonym3", "synonym4"],
  "antonyms": ["antonym1", "antonym2"],
  "explanation": "If the user asked a conversational question or about an idiom/nuance, provide a concise helpful explanation here; otherwise leave as empty string."
}

Important Rules:
1. Every string must be valid JSON.
2. Provide at least 2-4 synonyms and 1-3 antonyms whenever they exist conceptually.
3. If source and target language are the same, translate into Spanish or French as a secondary translation.
4. If target_lang is 'English', translate into English.
5. If the user asks a question like 'what is the meaning of serendipity in simple words?', set clean_word to 'serendipity' and provide a simple explanation in 'explanation'.
"""

    user_prompt = f"Query: {query.strip()}\nSource Language Hint: {source_lang}\nTarget Translation Language: {target_lang}"

    # Try model candidates
    for model_name in MODEL_CANDIDATES:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1500
            )
            raw_content = response.choices[0].message.content.strip()
            data = json.loads(raw_content)

            # Ensure minimal required fields
            data["clean_word"] = data.get("clean_word", query.strip()).lower()
            data["word"] = query.strip() if len(query.strip().split()) <= 4 else data["clean_word"]
            data["target_lang"] = target_lang
            data["source_lang"] = data.get("source_lang", source_lang if source_lang != "auto" else "Detected")
            data["translation"] = data.get("translation", "")
            data["phonetic"] = data.get("phonetic", "")
            data["meanings"] = data.get("meanings", [])
            data["synonyms"] = data.get("synonyms", [])
            data["antonyms"] = data.get("antonyms", [])
            data["explanation"] = data.get("explanation", "")

            return data
        except Exception as e:
            logger.warning(f"Groq lookup with model {model_name} failed: {e}")
            continue

    return None
