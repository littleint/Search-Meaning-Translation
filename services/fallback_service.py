import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Map common language names to ISO 2-letter codes for MyMemory
LANG_CODES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "hindi": "hi",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "japanese": "ja",
    "chinese": "zh",
    "arabic": "ar",
    "korean": "ko",
    "auto": "auto"
}

def get_lang_code(lang_name: str) -> str:
    cleaned = lang_name.strip().lower()
    return LANG_CODES.get(cleaned, cleaned[:2] if len(cleaned) >= 2 else "en")

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    src = get_lang_code(source_lang)
    tgt = get_lang_code(target_lang)
    if src == "auto":
        src = "en"
    if src == tgt:
        return text

    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair={src}|{tgt}"
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText")
                if translated and not translated.startswith("MYMEMORY WARNING"):
                    return translated
    except Exception as e:
        logger.warning(f"Translation API error: {e}")
    return text

async def fetch_synonyms_antonyms(word: str) -> Dict[str, List[str]]:
    synonyms = []
    antonyms = []
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            syn_resp = await client.get(f"https://api.datamuse.com/words?rel_syn={word}&max=8")
            if syn_resp.status_code == 200:
                synonyms = [item["word"] for item in syn_resp.json() if "word" in item]

            ant_resp = await client.get(f"https://api.datamuse.com/words?rel_ant={word}&max=8")
            if ant_resp.status_code == 200:
                antonyms = [item["word"] for item in ant_resp.json() if "word" in item]
    except Exception as e:
        logger.warning(f"Datamuse API error: {e}")
    return {"synonyms": synonyms, "antonyms": antonyms}

async def lookup_with_fallback(query: str, source_lang: str = "auto", target_lang: str = "English") -> Dict[str, Any]:
    clean_word = query.strip().lower().split()[0] if len(query.strip().split()) > 0 else query.strip().lower()
    
    # 1. Translation
    translation = await translate_text(query, source_lang, target_lang)

    # 2. Dictionary API lookup (works best for English words)
    meanings = []
    phonetic = ""
    try:
        dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(dict_url)
            if resp.status_code == 200:
                entries = resp.json()
                if isinstance(entries, list) and len(entries) > 0:
                    entry = entries[0]
                    phonetic = entry.get("phonetic", "")
                    if not phonetic and "phonetics" in entry:
                        for p in entry["phonetics"]:
                            if p.get("text"):
                                phonetic = p["text"]
                                break
                    for m in entry.get("meanings", []):
                        pos = m.get("partOfSpeech", "general")
                        defs = []
                        examples = []
                        for d in m.get("definitions", [])[:3]:
                            if d.get("definition"):
                                defs.append(d["definition"])
                            if d.get("example"):
                                examples.append(d["example"])
                        meanings.append({
                            "part_of_speech": pos,
                            "definitions": defs,
                            "examples": examples
                        })
    except Exception as e:
        logger.warning(f"Dictionary API fallback error: {e}")

    # If no meanings were returned from free dictionary
    if not meanings:
        meanings.append({
            "part_of_speech": "general",
            "definitions": [f"Term: '{clean_word}'. Translated as: '{translation}'."],
            "examples": []
        })

    # 3. Datamuse synonyms and antonyms
    syn_ant = await fetch_synonyms_antonyms(clean_word)

    return {
        "word": query.strip(),
        "clean_word": clean_word,
        "source_lang": source_lang if source_lang != "auto" else "Detected",
        "target_lang": target_lang,
        "translation": translation,
        "phonetic": phonetic,
        "meanings": meanings,
        "synonyms": syn_ant["synonyms"],
        "antonyms": syn_ant["antonyms"],
        "explanation": ""
    }
