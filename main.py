"""
=============================================================================
LinguaVault - Main Application Entrypoint
=============================================================================
Starts the FastAPI ASGI application, mounts static assets, initializes
the SQLite database, and includes routers for Auth, Vocabulary, and Pages.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers.auth_routes import router as auth_router
from routers.vocab_routes import router as vocab_router
from routers.page_routes import router as page_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on application startup."""
    init_db()
    yield

app = FastAPI(
    title="LinguaVault - Dictionary & Vocabulary",
    description="Multilingual dictionary, translation, and vocabulary intelligence web application.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static asset directory (CSS, JavaScript, Icons)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register feature routers
app.include_router(page_router)
app.include_router(auth_router)
app.include_router(vocab_router)

if __name__ == "__main__":
    import os
    import threading
    import webbrowser
    import uvicorn

    # Support dynamic PORT assigned by cloud hosts like Render
    port = int(os.environ.get("PORT", 8000))
    is_production = bool(os.environ.get("PORT"))
    host = "0.0.0.0" if is_production else "127.0.0.1"

    # In local development, automatically open the browser
    if not is_production:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        print(f"🚀 Opening http://127.0.0.1:{port} in your browser...")

    uvicorn.run("main:app", host=host, port=port, reload=not is_production)
