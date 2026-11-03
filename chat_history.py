import sqlite3
import json
from datetime import datetime
from pathlib import Path


# =========================================================
# 1. DATABASE CONFIGURATION
# =========================================================

DB_PATH = Path(__file__).resolve().parent / "nova_chats.db"


def get_connection():
    """Open a SQLite connection with foreign keys enabled."""

    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row

    # Enable foreign-key enforcement on EVERY connection.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def current_timestamp():
    """Return the current local timestamp."""
    return datetime.now().isoformat(timespec="seconds")


# =========================================================
# 2. INITIALIZE DATABASE
# =========================================================

def initialize_database():
    """Create NOVA's conversation and message tables if needed."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                chat_type TEXT NOT NULL DEFAULT 'interview',
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)


# =========================================================
# 3. CREATE A CONVERSATION
# =========================================================

def create_conversation(
    title="New Chat",
    chat_type="interview",
    metadata=None,
):
    """Create a conversation and return its unique ID."""

    now = current_timestamp()

    with get_connection() as connection:

        cursor = connection.execute("""
            INSERT INTO conversations (
                title,
                chat_type,
                metadata,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            chat_type,
            json.dumps(metadata or {}),
            now,
            now,
        ))

        return cursor.lastrowid


# =========================================================
# 4. LIST SAVED CONVERSATIONS
# =========================================================

def list_conversations(chat_type=None):
    """
    Return saved conversations, newest activity first.

    Optional:
        chat_type='general'
        chat_type='rag'
        chat_type='interview'
    """

    with get_connection() as connection:

        if chat_type is not None:
            rows = connection.execute("""
                SELECT
                    id,
                    title,
                    chat_type,
                    metadata,
                    created_at,
                    updated_at
                FROM conversations
                WHERE chat_type = ?
                ORDER BY updated_at DESC, id DESC
            """, (chat_type,)).fetchall()

        else:
            rows = connection.execute("""
                SELECT
                    id,
                    title,
                    chat_type,
                    metadata,
                    created_at,
                    updated_at
                FROM conversations
                ORDER BY updated_at DESC, id DESC
            """).fetchall()

        results = []

        for row in rows:
            item = dict(row)

            try:
                item["metadata"] = json.loads(
                    item["metadata"] or "{}"
                )
            except (json.JSONDecodeError, TypeError):
                item["metadata"] = {}

            results.append(item)

        return results


# =========================================================
# 5. GET ONE CONVERSATION
# =========================================================

def get_conversation(conversation_id):
    """Return one conversation, or None if it does not exist."""

    with get_connection() as connection:

        row = connection.execute("""
            SELECT
                id,
                title,
                chat_type,
                metadata,
                created_at,
                updated_at
            FROM conversations
            WHERE id = ?
        """, (conversation_id,)).fetchone()

        if row is None:
            return None

        conversation = dict(row)

        try:
            conversation["metadata"] = json.loads(
                conversation["metadata"] or "{}"
            )
        except (json.JSONDecodeError, TypeError):
            conversation["metadata"] = {}

        return conversation


# =========================================================
# 6. GET MESSAGES FOR ONE CONVERSATION ONLY
# =========================================================

def get_messages(conversation_id):
    """Load messages in chronological order."""

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT
                id,
                conversation_id,
                role,
                content,
                created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,)).fetchall()

        return [dict(row) for row in rows]


# =========================================================
# 7. SAVE A MESSAGE
# =========================================================

def add_message(conversation_id, role, content):
    """Save a message and update the conversation activity time."""

    if role not in ("user", "assistant"):
        raise ValueError(
            "Message role must be 'user' or 'assistant'."
        )

    if not isinstance(content, str):
        raise TypeError("Message content must be a string.")

    now = current_timestamp()

    with get_connection() as connection:

        # Verify that the conversation exists.
        conversation = connection.execute("""
            SELECT id
            FROM conversations
            WHERE id = ?
        """, (conversation_id,)).fetchone()

        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} does not exist."
            )

        connection.execute("""
            INSERT INTO messages (
                conversation_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            conversation_id,
            role,
            content,
            now,
        ))

        connection.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """, (now, conversation_id))


# =========================================================
# 8. UPDATE CONVERSATION TITLE OR METADATA
# =========================================================

def update_conversation(
    conversation_id,
    title=None,
    metadata=None,
):
    """Update the title and/or metadata of a conversation."""

    now = current_timestamp()

    with get_connection() as connection:

        if title is not None:
            connection.execute("""
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
            """, (
                title,
                now,
                conversation_id,
            ))

        if metadata is not None:
            connection.execute("""
                UPDATE conversations
                SET metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                json.dumps(metadata),
                now,
                conversation_id,
            ))


# =========================================================
# 9. DELETE ONE CONVERSATION
# =========================================================

def delete_conversation(conversation_id):
    """
    Delete one conversation and its messages.

    Other conversations remain untouched.
    """

    with get_connection() as connection:

        connection.execute("""
            DELETE FROM conversations
            WHERE id = ?
        """, (conversation_id,))


# =========================================================
# 10. INITIALIZE ON IMPORT
# =========================================================

initialize_database()
