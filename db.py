"""
Shared database connection module.

- When DATABASE_URL is set (Vercel or local .env): uses Neon Postgres via psycopg2
- When DATABASE_URL is absent: falls back to local SQLite (speaker_links.db)
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

SQLITE_DB = "speaker_links.db"


def _pg_schema():
    return """
        CREATE TABLE IF NOT EXISTS speaker_links (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            token      TEXT NOT NULL,
            origin     TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL
        )
    """


def _sqlite_schema():
    return """
        CREATE TABLE IF NOT EXISTS speaker_links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            token       TEXT NOT NULL,
            origin      TEXT NOT NULL DEFAULT 'new',
            created_at  TEXT NOT NULL
        )
    """


def db_schema():
    return _pg_schema() if USE_PG else _sqlite_schema()


class DBConn:
    def __init__(self):
        if USE_PG:
            self._conn = psycopg2.connect(
                DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor
            )
            self._pg = True
        else:
            c = sqlite3.connect(SQLITE_DB)
            c.row_factory = sqlite3.Row
            self._conn = c
            self._pg = False

    def execute(self, sql, params=None):
        if self._pg:
            cur = self._conn.cursor()
            cur.execute(sql.replace("?", "%s"), params or ())
            return cur
        else:
            return self._conn.execute(sql, params or ())

    def insert_id(self, sql, params=None):
        """INSERT and return the new row's id (handles SERIAL vs AUTOINCREMENT)."""
        if self._pg:
            cur = self._conn.cursor()
            cur.execute((sql + " RETURNING id").replace("?", "%s"), params or ())
            return cur.fetchone()["id"]
        else:
            cur = self._conn.execute(sql, params or ())
            return cur.lastrowid

    def commit(self):
        self._conn.commit()

    def rollback(self):
        if self._pg:
            self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.rollback()
        self.close()


def get_db():
    return DBConn()
