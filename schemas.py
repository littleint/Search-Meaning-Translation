from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AuthRequest(BaseModel):
    """Payload for User Registration and Login."""
    email: str
    password: str

class LookupRequest(BaseModel):
    """Payload for Word/Phrase/Question search."""
    query: str
    source_lang: Optional[str] = "auto"
    target_lang: Optional[str] = "English"

class NotesRequest(BaseModel):
    """Payload for updating personal vocabulary notes."""
    notes: str

class MeaningBlock(BaseModel):
    """Structure of definition block by part of speech."""
    part_of_speech: str
    definitions: List[str]
    examples: List[str]

class WordDetailsResponse(BaseModel):
    """Structured response for dictionary & translation result."""
    id: Optional[str] = None
    word: str
    clean_word: str
    source_lang: str
    target_lang: str
    translation: str
    phonetic: Optional[str] = ""
    meanings: List[MeaningBlock]
    synonyms: List[str]
    antonyms: List[str]
    explanation: Optional[str] = ""
    is_important: Optional[bool] = False
    notes: Optional[str] = ""
    search_count: Optional[int] = 1
