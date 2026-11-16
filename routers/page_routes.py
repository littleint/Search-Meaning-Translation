"""
=============================================================================
HTML Page Routes
=============================================================================
Renders web pages with responsive layouts and user context.
"""

from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import SUPPORTED_LANGUAGES, DEFAULT_TARGET_LANG
from auth import get_current_user_optional

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home_search_page(request: Request, user: Optional[dict] = Depends(get_current_user_optional)):
    """Main search, dictionary, and translation dashboard."""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "active_tab": "search",
            "supported_languages": SUPPORTED_LANGUAGES,
            "default_target_lang": DEFAULT_TARGET_LANG
        }
    )

@router.get("/vocab", response_class=HTMLResponse)
async def my_vocab_page(request: Request, user: Optional[dict] = Depends(get_current_user_optional)):
    """Personal vocabulary vault library and history page."""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="vocab.html",
        context={
            "user": user,
            "active_tab": "vocab",
            "supported_languages": SUPPORTED_LANGUAGES
        }
    )

@router.get("/login", response_class=HTMLResponse)
async def authentication_page(request: Request, user: Optional[dict] = Depends(get_current_user_optional)):
    """Sign In and Create Account page."""
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={}
    )
