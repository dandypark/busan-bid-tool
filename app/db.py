import sqlite3
from contextlib import contextmanager
from config import DB_PATH, DATABASE_URL

# ── SQLite (가격 참조 데이터) ─────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()

# ── PostgreSQL (낙찰이력 — Supabase) ─────────────────────────
def get_pg_conn():
    """Supabase PostgreSQL 연결. DATABASE_URL 없으면 None 반환."""
    if not DATABASE_URL:
        return None
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def pg_available():
    return bool(DATABASE_URL)
