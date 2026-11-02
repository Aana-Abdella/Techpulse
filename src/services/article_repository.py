"""SQLite persistence for collected news articles."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from src.services.article_service import Article, validate_article


class ChannelDestination(NamedTuple):
    chat_id: int
    title: str
    username: str | None


class ArticleRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS articles (
                        url TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        source TEXT NOT NULL,
                        fetched_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_articles_category "
                    "ON articles(category, fetched_at DESC)"
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_channels (
                        user_id INTEGER PRIMARY KEY,
                        chat_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        username TEXT
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_summaries (
                        cache_key TEXT PRIMARY KEY,
                        summary_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

    def get_cached_summary(self, cache_key: str) -> str | None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            row = connection.execute(
                "SELECT summary_json FROM ai_summaries WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        return row[0] if row is not None else None

    def save_cached_summary(self, cache_key: str, summary_json: str) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO ai_summaries (cache_key, summary_json, created_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        summary_json = excluded.summary_json,
                        created_at = excluded.created_at
                    """,
                    (cache_key, summary_json, datetime.now(timezone.utc).isoformat()),
                )

    def save_channel(
        self, user_id: int, chat_id: int, title: str, username: str | None
    ) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO user_channels (user_id, chat_id, title, username)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        chat_id = excluded.chat_id,
                        title = excluded.title,
                        username = excluded.username
                    """,
                    (user_id, chat_id, title, username),
                )

    def get_channel(self, user_id: int) -> ChannelDestination | None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            row = connection.execute(
                """
                SELECT chat_id, title, username
                FROM user_channels
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None
        return ChannelDestination(*row)

    def remove_channel(self, user_id: int) -> bool:
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM user_channels WHERE user_id = ?",
                    (user_id,),
                )
                return cursor.rowcount > 0

    def save_articles(self, articles: list[object]) -> int:
        fetched_at = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                article["url"].strip(),
                article["title"].strip(),
                article["category"].strip(),
                article["source"].strip(),
                fetched_at,
            )
            for article in articles
            if validate_article(article)
        ]
        if not rows:
            return 0

        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                cursor = connection.executemany(
                    """
                    INSERT OR IGNORE INTO articles
                        (url, title, category, source, fetched_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                return cursor.rowcount

    def get_latest(
        self,
        category: str | None = None,
        limit: int = 5,
        offset: int = 0,
    ) -> list[Article]:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                WITH ranked_articles AS (
                    SELECT title, category, source, url, fetched_at, rowid,
                        ROW_NUMBER() OVER (
                            PARTITION BY category
                            ORDER BY fetched_at DESC, rowid DESC
                        ) AS category_rank
                    FROM articles
                    WHERE ? IS NULL OR category = ? COLLATE NOCASE
                )
                SELECT title, category, source, url
                FROM ranked_articles
                ORDER BY category_rank, fetched_at DESC, rowid DESC
                LIMIT ? OFFSET ?
                """,
                (category, category, limit, offset),
            ).fetchall()

        return [
            {
                "title": row["title"],
                "category": row["category"],
                "source": row["source"],
                "url": row["url"],
            }
            for row in rows
        ]
