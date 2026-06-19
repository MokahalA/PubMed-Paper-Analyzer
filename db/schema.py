import sqlite3
import json
from pathlib import Path

DB_PATH = Path("db/research_papers.db")


def init_db():
    """Initialize SQLite database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main papers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        pmid TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        abstract TEXT,
        authors TEXT NOT NULL,  -- JSON array
        journal TEXT,
        year INTEGER,
        keywords TEXT NOT NULL,  -- JSON array
        diseases TEXT NOT NULL,  -- JSON array
        methods TEXT NOT NULL,  -- JSON array
        organs TEXT NOT NULL,  -- JSON array
        clean_text TEXT,
        abstract_words INTEGER,
        title_words INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Index on year and title for faster queries
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_year ON papers(year)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_title ON papers(title)
    """)

    conn.commit()
    conn.close()


def get_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)
