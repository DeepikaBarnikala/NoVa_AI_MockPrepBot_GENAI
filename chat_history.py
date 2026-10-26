
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Store the database beside this file.
DB_PATH = Path(__file__).resolve().parent / "nova_chats.db"


def get_connection():
    """Open a connection to NOVA's local database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the required tables if they do not exist."""
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
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        # Ensure deleting a conversation also deletes its messages.
        connection.execute("PRAGMA foreign_keys = ON")


def create_conversation(title="New Chat", chat_type="interview",
                        metadata=None):
    """Create a conversation and return its ID."""
    now = datetime.now().isoformat(timespec="seconds")
    metadata_json = json.dumps(metadata or {})

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO conversations
                (title, chat_type, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, chat_type, metadata_json, now, now))

        return cursor.lastrowid


def list_conversations():
    """Return conversations with the newest activity first."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, title, chat_type, metadata,
                   created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_conversation(conversation_id):
    """Get one conversation by its ID."""
    with get_connection() as connection:
        row = connection.execute("""
            SELECT id, title, chat_type, metadata,
                   created_at, updated_at
            FROM conversations
            WHERE id = ?
        """, (conversation_id,)).fetchone()

        if row is None:
            return None

        conversation = dict(row)
        conversation["metadata"] = json.loads(
            conversation["metadata"] or "{}"
        )
        return conversation


def get_messages(conversation_id):
    """Load all messages in chronological order."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,)).fetchall()

        return [dict(row) for row in rows]


def add_message(conversation_id, role, content):
    """Save a user or assistant message."""
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO messages
                (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (conversation_id, role, content, now))

        connection.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """, (now, conversation_id))


def update_conversation(conversation_id, title=None, metadata=None):
    """Update a conversation title and/or metadata."""
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        if title is not None:
            connection.execute("""
                UPDATE conversations
                SET title = ?, updated_at = ?
                WHERE id = ?
            """, (title, now, conversation_id))

        if metadata is not None:
            connection.execute("""
                UPDATE conversations
                SET metadata = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(metadata), now, conversation_id))


def delete_conversation(conversation_id):
    """Delete one conversation and all its messages."""
    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
        """, (conversation_id,))
        connection.execute("""
            DELETE FROM conversations
            WHERE id = ?
        """, (conversation_id,))


# Initialize the database when this module is imported.
initialize_database()
