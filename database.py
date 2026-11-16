"""
=============================================================================
Unified Database Layer (Neon PostgreSQL & Local SQLite)
=============================================================================
Automatically connects to Neon PostgreSQL when DATABASE_URL is set in .env.
Falls back to local zero-configuration SQLite when running offline.
"""

import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from config import DATABASE_URL, DATABASE_PATH

logger = logging.getLogger(__name__)

def is_postgres() -> bool:
    return bool(DATABASE_URL and DATABASE_URL.startswith("postgresql://"))

def get_db():
    if is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

def adapt_sql(sql: str) -> str:
    """Adapts query parameter placeholders (? for SQLite, %s for PostgreSQL)."""
    if is_postgres():
        return sql.replace("?", "%s")
    return sql

def init_db():
    """Initializes tables and indexes in Neon PostgreSQL or SQLite."""
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cursor:
                if is_postgres():
                    logger.info("Initializing Neon PostgreSQL database tables...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id VARCHAR(64) PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS vocabulary (
                            id VARCHAR(64) PRIMARY KEY,
                            user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            word TEXT NOT NULL,
                            clean_word TEXT NOT NULL,
                            source_lang VARCHAR(64) NOT NULL,
                            target_lang VARCHAR(64) NOT NULL,
                            translation TEXT NOT NULL,
                            phonetic TEXT,
                            meanings TEXT NOT NULL,
                            synonyms TEXT NOT NULL,
                            antonyms TEXT NOT NULL,
                            explanation TEXT,
                            is_important BOOLEAN DEFAULT FALSE,
                            notes TEXT,
                            search_count INTEGER DEFAULT 1,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, clean_word, target_lang)
                        );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_user ON vocabulary(user_id);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_important ON vocabulary(user_id, is_important);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary(user_id, clean_word);")
                else:
                    logger.info("Initializing local SQLite database tables...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id TEXT PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS vocabulary (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            word TEXT NOT NULL,
                            clean_word TEXT NOT NULL,
                            source_lang TEXT NOT NULL,
                            target_lang TEXT NOT NULL,
                            translation TEXT NOT NULL,
                            phonetic TEXT,
                            meanings TEXT NOT NULL,
                            synonyms TEXT NOT NULL,
                            antonyms TEXT NOT NULL,
                            explanation TEXT,
                            is_important BOOLEAN DEFAULT 0,
                            notes TEXT,
                            search_count INTEGER DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            UNIQUE(user_id, clean_word, target_lang)
                        );
                    """)
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_user ON vocabulary(user_id);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_important ON vocabulary(user_id, is_important);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary(user_id, clean_word);")
    finally:
        conn.close()

# ----------------- USER OPERATIONS ----------------- #

def create_user(email: str, password_hash: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    user_id = str(uuid.uuid4())
    clean_email = email.lower().strip()
    try:
        with conn:
            with conn.cursor() as cursor:
                sql = adapt_sql("INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)")
                cursor.execute(sql, (user_id, clean_email, password_hash))
        return {"id": user_id, "email": clean_email}
    except Exception as e:
        logger.warning(f"Error creating user {clean_email}: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    clean_email = email.lower().strip()
    try:
        with conn.cursor() as cursor:
            sql = adapt_sql("SELECT id, email, password_hash, created_at FROM users WHERE email = ?")
            cursor.execute(sql, (clean_email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    finally:
        conn.close()

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = adapt_sql("SELECT id, email, created_at FROM users WHERE id = ?")
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    finally:
        conn.close()

# ----------------- VOCABULARY OPERATIONS ----------------- #

def save_or_update_word(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db()
    clean_word = data.get("clean_word", data.get("word", "")).strip().lower()
    word_display = data.get("word", clean_word).strip()
    source_lang = data.get("source_lang", "auto")
    target_lang = data.get("target_lang", "English")
    translation = data.get("translation", "")
    phonetic = data.get("phonetic", "")
    meanings_json = json.dumps(data.get("meanings", []), ensure_ascii=False)
    synonyms_json = json.dumps(data.get("synonyms", []), ensure_ascii=False)
    antonyms_json = json.dumps(data.get("antonyms", []), ensure_ascii=False)
    explanation = data.get("explanation", "")

    try:
        with conn:
            with conn.cursor() as cursor:
                # Check for existing record
                check_sql = adapt_sql(
                    "SELECT id, is_important, search_count, notes FROM vocabulary WHERE user_id = ? AND clean_word = ? AND target_lang = ?"
                )
                cursor.execute(check_sql, (user_id, clean_word, target_lang))
                existing = cursor.fetchone()

                if existing:
                    existing_dict = dict(existing)
                    vocab_id = existing_dict["id"]
                    new_count = existing_dict["search_count"] + 1
                    is_important = existing_dict["is_important"]
                    notes = existing_dict["notes"]

                    update_sql = adapt_sql("""
                        UPDATE vocabulary 
                        SET word = ?, translation = ?, phonetic = ?, meanings = ?, synonyms = ?, 
                            antonyms = ?, explanation = ?, search_count = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """)
                    cursor.execute(update_sql, (
                        word_display, translation, phonetic, meanings_json, synonyms_json,
                        antonyms_json, explanation, new_count, vocab_id
                    ))
                else:
                    vocab_id = str(uuid.uuid4())
                    is_important = False
                    notes = ""
                    new_count = 1

                    insert_sql = adapt_sql("""
                        INSERT INTO vocabulary (
                            id, user_id, word, clean_word, source_lang, target_lang, translation, 
                            phonetic, meanings, synonyms, antonyms, explanation, is_important, notes, search_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """)
                    cursor.execute(insert_sql, (
                        vocab_id, user_id, word_display, clean_word, source_lang, target_lang, translation,
                        phonetic, meanings_json, synonyms_json, antonyms_json, explanation, is_important, notes, new_count
                    ))

        return {
            "id": vocab_id,
            "word": word_display,
            "clean_word": clean_word,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translation": translation,
            "phonetic": phonetic,
            "meanings": data.get("meanings", []),
            "synonyms": data.get("synonyms", []),
            "antonyms": data.get("antonyms", []),
            "explanation": explanation,
            "is_important": bool(is_important),
            "notes": notes or "",
            "search_count": new_count
        }
    finally:
        conn.close()

def get_user_vocabulary(
    user_id: str, 
    important_only: bool = False, 
    query: Optional[str] = None, 
    lang: Optional[str] = None,
    sort_by: str = "recent"
) -> List[Dict[str, Any]]:
    conn = get_db()
    params: List[Any] = [user_id]
    
    sql = "SELECT * FROM vocabulary WHERE user_id = ?"

    if important_only:
        sql += " AND is_important = TRUE" if is_postgres() else " AND is_important = 1"
    
    if lang and lang != "all":
        sql += " AND (source_lang = ? OR target_lang = ?)"
        params.extend([lang, lang])

    if query:
        search_term = f"%{query.strip().lower()}%"
        sql += " AND (clean_word LIKE ? OR translation LIKE ?)"
        params.extend([search_term, search_term])

    if sort_by == "alpha":
        sql += " ORDER BY clean_word ASC"
    elif sort_by == "searches":
        sql += " ORDER BY search_count DESC"
    else:
        sql += " ORDER BY updated_at DESC"

    try:
        with conn.cursor() as cursor:
            cursor.execute(adapt_sql(sql), tuple(params))
            rows = cursor.fetchall()
            items = []
            for row in rows:
                item = dict(row)
                item["meanings"] = json.loads(item["meanings"]) if item["meanings"] else []
                item["synonyms"] = json.loads(item["synonyms"]) if item["synonyms"] else []
                item["antonyms"] = json.loads(item["antonyms"]) if item["antonyms"] else []
                item["is_important"] = bool(item["is_important"])
                items.append(item)
            return items
    finally:
        conn.close()

def get_vocab_item(user_id: str, vocab_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = adapt_sql("SELECT * FROM vocabulary WHERE id = ? AND user_id = ?")
            cursor.execute(sql, (vocab_id, user_id))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                item["meanings"] = json.loads(item["meanings"]) if item["meanings"] else []
                item["synonyms"] = json.loads(item["synonyms"]) if item["synonyms"] else []
                item["antonyms"] = json.loads(item["antonyms"]) if item["antonyms"] else []
                item["is_important"] = bool(item["is_important"])
                return item
            return None
    finally:
        conn.close()

def toggle_important(user_id: str, vocab_id: str) -> Optional[bool]:
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cursor:
                select_sql = adapt_sql("SELECT is_important FROM vocabulary WHERE id = ? AND user_id = ?")
                cursor.execute(select_sql, (vocab_id, user_id))
                row = cursor.fetchone()
                if not row:
                    return None
                
                current = bool(dict(row)["is_important"])
                new_state = not current
                update_sql = adapt_sql("UPDATE vocabulary SET is_important = ? WHERE id = ? AND user_id = ?")
                cursor.execute(update_sql, (new_state, vocab_id, user_id))
                return new_state
    finally:
        conn.close()

def update_notes(user_id: str, vocab_id: str, notes: str) -> bool:
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cursor:
                sql = adapt_sql("UPDATE vocabulary SET notes = ? WHERE id = ? AND user_id = ?")
                cursor.execute(sql, (notes, vocab_id, user_id))
                return cursor.rowcount > 0
    finally:
        conn.close()

def delete_vocab_item(user_id: str, vocab_id: str) -> bool:
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cursor:
                sql = adapt_sql("DELETE FROM vocabulary WHERE id = ? AND user_id = ?")
                cursor.execute(sql, (vocab_id, user_id))
                return cursor.rowcount > 0
    finally:
        conn.close()

def get_vocab_stats(user_id: str) -> Dict[str, Any]:
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Total count
            cursor.execute(adapt_sql("SELECT COUNT(*) as total FROM vocabulary WHERE user_id = ?"), (user_id,))
            total = dict(cursor.fetchone())["total"]

            # Important count
            imp_sql = "SELECT COUNT(*) as important FROM vocabulary WHERE user_id = ? AND is_important = TRUE" if is_postgres() else "SELECT COUNT(*) as important FROM vocabulary WHERE user_id = ? AND is_important = 1"
            cursor.execute(adapt_sql(imp_sql), (user_id,))
            important = dict(cursor.fetchone())["important"]

            # Unique target languages
            cursor.execute(adapt_sql("SELECT DISTINCT target_lang FROM vocabulary WHERE user_id = ?"), (user_id,))
            languages = [dict(r)["target_lang"] for r in cursor.fetchall() if dict(r)["target_lang"]]

            return {
                "total_words": total,
                "important_words": important,
                "languages": languages
            }
    finally:
        conn.close()
