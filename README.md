# 📖 LinguaVault — Multilingual Dictionary, Translation & Vocabulary Bank

A modern, private web application built with **FastAPI**, **SQLite**, **Tailwind CSS**, and **Groq AI**. 

Look up any word, phrase, idiom, or question in any language to get instant definitions, translations, parts of speech, synonyms, antonyms, and pronunciation. Every search is automatically saved to your private vocabulary bank, which you can filter, mark as important (⭐), and review in full detail.

---

## 🚀 Quick Start

### 1. Start the Web Server (Auto-Opens Browser)
In your PowerShell terminal:
```powershell
python main.py
```
*(or `uv run python main.py`)*

This starts the server **and** immediately opens the app in your browser!

---

## 📂 Clean & Modular Codebase Structure

Everything is neatly organized into clear, single-responsibility modules:

```text
transhlation_in_any_language/
│
├── .env                       # API keys and secret configuration
├── config.py                  # Central configuration (Languages, AI models, JWT settings)
├── schemas.py                 # Central Pydantic request & response data models
├── database.py                # SQLite database models, queries, and migrations
├── auth.py                    # Bcrypt password hashing & JWT cookie authentication
├── main.py                    # FastAPI entrypoint (mounts static files & routes)
│
├── routers/                   # Modular API & Page Route Handlers
│   ├── auth_routes.py         # Sign in, Sign up, Logout, Profile routes
│   ├── vocab_routes.py        # Search, auto-save, vocabulary library, star toggle
│   └── page_routes.py         # HTML pages (Search dashboard, My Vocab, Login)
│
├── services/                  # AI & Fallback Linguistic Engines
│   ├── groq_service.py        # Groq Llama/Qwen structured multilingual dictionary & Q&A
│   ├── fallback_service.py    # Free Dictionary & Translation API fallback
│   └── dictionary_manager.py  # Coordinates AI and fallback gracefully
│
├── static/                    # Frontend Client Scripts & Assets
│   └── js/
│       ├── app.js             # Shared helpers (toast notifications, pronunciation TTS)
│       ├── search.js          # Search bar, results card, and star toggle logic
│       ├── vocab.js           # My Vocab library, instant filters, detail modal, notes
│       └── auth.js            # Sign In & Registration form controller
│
├── templates/                 # Clean, Responsive HTML5 Templates (Tailwind CSS)
│   ├── base.html              # Base layout with navbar, counters & toasts
│   ├── index.html             # Search, dictionary & translation page
│   ├── vocab.html             # Personal vocabulary bank & detail modal
│   └── auth.html              # Login & Registration page
│
└── tests/
    └── test_app.py            # Automated end-to-end test suite
```

---

## 🛠️ How to Customize Anything Easily

### 1. Want to Add or Remove Languages?
Open **`config.py`** and simply edit the `SUPPORTED_LANGUAGES` list:
```python
SUPPORTED_LANGUAGES = [
    "English", "Spanish", "French", "German", "Hindi",
    "Japanese", "Chinese", "Arabic", "Italian", "Portuguese",
    "Korean", "Dutch", "Russian", "Swedish", "YourNewLanguage"
]
```
*The dropdowns on the search page will update automatically!*

### 2. Want to Change the AI Prompt or Model?
Open **`services/groq_service.py`**:
* Change `MODEL_CANDIDATES` or `GROQ_MODEL` in `config.py`.
* Adjust `system_prompt` to customize the definitions, tone, or linguistic formatting.

### 3. Want to Change the Database Schema or Add New Fields?
Open **`database.py`**:
* All database queries and table definitions are centralized here with clean docstrings.

### 4. Want to Adjust Frontend Colors or Layout?
* **Colors & Themes:** Open `templates/base.html` to adjust the Tailwind theme colors.
* **Search Page UI:** Open `templates/index.html`.
* **Vocabulary Cards & Modal:** Open `templates/vocab.html`.

---

## 🧪 Running Automated Tests

Run the complete automated test suite anytime to verify authentication, dictionary lookups, auto-save, and privacy isolation:

```powershell
uv run python tests/test_app.py
```
