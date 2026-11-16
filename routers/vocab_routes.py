"""
=============================================================================
Vocabulary & Dictionary API Router
=============================================================================
Endpoints for searching words/translations (with automatic saving),
filtering vocabulary, inspecting word dossiers, toggling stars, and managing notes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import LookupRequest, NotesRequest
from database import (
    save_or_update_word, get_user_vocabulary, get_vocab_item,
    toggle_important, update_notes, delete_vocab_item, get_vocab_stats
)
from auth import get_current_user
from services.dictionary_manager import get_word_details

router = APIRouter(prefix="/api", tags=["Vocabulary & Dictionary"])

@router.post("/lookup")
async def lookup_and_autosave(payload: LookupRequest, user: dict = Depends(get_current_user)):
    """
    Search definitions, synonyms, antonyms, and translations.
    AUTOMATICALLY saves the word and all details to the authenticated user's private vault.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    
    source_lang = payload.source_lang or "auto"
    target_lang = payload.target_lang or "English"

    # 1. Fetch linguistic & translation data (Groq AI with Fallback)
    word_details = await get_word_details(query, source_lang=source_lang, target_lang=target_lang)

    # 2. Automatically save to private database for this user
    saved_item = save_or_update_word(user["id"], word_details)

    return {
        "success": True,
        "auto_saved": True,
        "data": saved_item
    }

@router.get("/vocab")
async def list_user_vocabulary(
    important: bool = False,
    query: Optional[str] = None,
    lang: Optional[str] = None,
    sort_by: str = "recent",
    user: dict = Depends(get_current_user)
):
    """List saved words for the current user with flexible filtering and sorting."""
    items = get_user_vocabulary(
        user_id=user["id"],
        important_only=important,
        query=query,
        lang=lang,
        sort_by=sort_by
    )
    stats = get_vocab_stats(user["id"])
    return {
        "items": items,
        "stats": stats
    }

@router.get("/vocab/{vocab_id}")
async def get_word_details_by_id(vocab_id: str, user: dict = Depends(get_current_user)):
    """Retrieve full details, definitions, synonyms, and antonyms for a specific saved word."""
    item = get_vocab_item(user["id"], vocab_id)
    if not item:
        raise HTTPException(status_code=404, detail="Word not found in your vocabulary.")
    return item

@router.patch("/vocab/{vocab_id}/important")
async def toggle_word_importance(vocab_id: str, user: dict = Depends(get_current_user)):
    """Toggle the ⭐ Important status of a word."""
    new_state = toggle_important(user["id"], vocab_id)
    if new_state is None:
        raise HTTPException(status_code=404, detail="Word not found.")
    return {"success": True, "is_important": new_state}

@router.patch("/vocab/{vocab_id}/notes")
async def update_word_notes(vocab_id: str, payload: NotesRequest, user: dict = Depends(get_current_user)):
    """Update personal memory notes for a specific word."""
    success = update_notes(user["id"], vocab_id, payload.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found.")
    return {"success": True}

@router.delete("/vocab/{vocab_id}")
async def remove_word_from_vault(vocab_id: str, user: dict = Depends(get_current_user)):
    """Remove a word from the user's vocabulary vault."""
    success = delete_vocab_item(user["id"], vocab_id)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found.")
    return {"success": True}
