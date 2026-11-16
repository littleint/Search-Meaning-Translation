"""
=============================================================================
Authentication API Router
=============================================================================
Endpoints for User Registration, Login, Logout, and Profile queries.
"""

from fastapi import APIRouter, Response, HTTPException, Depends
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import AuthRequest
from database import create_user, get_user_by_email, get_vocab_stats
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(auth_req: AuthRequest, response: Response):
    """Register a new user account with secure password hashing."""
    email = auth_req.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(auth_req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    hashed = hash_password(auth_req.password)
    user = create_user(email, hashed)
    if not user:
        raise HTTPException(status_code=500, detail="Could not create user account.")
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    return {"success": True, "user": {"id": user["id"], "email": user["email"]}}

@router.post("/login")
async def login_user(auth_req: AuthRequest, response: Response):
    """Authenticate an existing user and issue a secure session cookie."""
    email = auth_req.email.strip().lower()
    user = get_user_by_email(email)
    if not user or not verify_password(auth_req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    return {"success": True, "user": {"id": user["id"], "email": user["email"]}}

@router.post("/logout")
async def logout_user(response: Response):
    """Clear session cookie and log the user out."""
    response.delete_cookie("access_token")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """Fetch profile data and vocabulary summary statistics for the active user."""
    stats = get_vocab_stats(user["id"])
    return {
        "id": user["id"],
        "email": user["email"],
        "stats": stats
    }
