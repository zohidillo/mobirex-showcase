import os
from datetime import datetime
from typing import Optional

import aiosqlite


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    question TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    group_message_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_telegram_id) REFERENCES users(telegram_id)
                )
                """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS message_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    user_telegram_id INTEGER NOT NULL,
                    group_message_id INTEGER,
                    user_message_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY(user_telegram_id) REFERENCES users(telegram_id)
                )
                """
            )

            await db.commit()

    async def save_user(self, telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    updated_at=excluded.updated_at
                """,
                (telegram_id, username, first_name, last_name, now, now),
            )
            await db.commit()

    async def create_ticket(self, user_telegram_id: int, category: str, full_name: str, phone: str, question: str) -> int:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                INSERT INTO tickets (user_telegram_id, category, full_name, phone, question, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_telegram_id, category, full_name, phone, question, now, now),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def set_ticket_group_message(self, ticket_id: int, group_message_id: int) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                UPDATE tickets
                SET group_message_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (group_message_id, now, ticket_id),
            )
            await db.execute(
                """
                INSERT INTO message_links (ticket_id, user_telegram_id, group_message_id, user_message_id, created_at)
                SELECT id, user_telegram_id, ?, NULL, ? FROM tickets WHERE id = ?
                """,
                (group_message_id, now, ticket_id),
            )
            await db.commit()

    async def add_message_link(
        self,
        ticket_id: int,
        user_telegram_id: int,
        group_message_id: Optional[int] = None,
        user_message_id: Optional[int] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO message_links (ticket_id, user_telegram_id, group_message_id, user_message_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticket_id, user_telegram_id, group_message_id, user_message_id, now),
            )
            await db.commit()

    async def get_ticket_by_group_message(self, group_message_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT t.*
                FROM tickets t
                LEFT JOIN message_links ml ON ml.ticket_id = t.id
                WHERE t.group_message_id = ? OR ml.group_message_id = ?
                ORDER BY t.id DESC
                LIMIT 1
                """,
                (group_message_id, group_message_id),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_ticket_by_user_message(self, user_telegram_id: int, user_message_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT t.*
                FROM tickets t
                INNER JOIN message_links ml ON ml.ticket_id = t.id
                WHERE ml.user_telegram_id = ? AND ml.user_message_id = ?
                ORDER BY t.id DESC
                LIMIT 1
                """,
                (user_telegram_id, user_message_id),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
