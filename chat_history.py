import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# =========================================================
# 1. DATABASE CONFIGURATION
# =========================================================

DB_PATH = Path(__file__).resolve().parent / "nova_chats.db"
MYSQL_ENV_KEYS = (
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DATABASE",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
)


def _get_mysql_config():
    """Read hosted MySQL settings from environment or Streamlit secrets."""

    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        try:
            secrets = st.secrets["mysql"]
        except KeyError:
            secrets = {}
        except StreamlitSecretNotFoundError:
            secrets = {}
    except ImportError:
        secrets = {}

    config = {
        "host": os.getenv("MYSQL_HOST") or secrets.get("host"),
        "port": os.getenv("MYSQL_PORT") or secrets.get("port", 3306),
        "database": (
            os.getenv("MYSQL_DATABASE") or secrets.get("database")
        ),
        "user": os.getenv("MYSQL_USER") or secrets.get("user"),
        "password": (
            os.getenv("MYSQL_PASSWORD") or secrets.get("password")
        ),
    }

    mysql_configured = any(
        os.getenv(key)
        for key in MYSQL_ENV_KEYS
        if key != "MYSQL_PORT"
    )
    mysql_configured = mysql_configured or bool(secrets)

    if not mysql_configured:
        return None

    missing = [
        key
        for key in ("host", "database", "user", "password")
        if not config[key]
    ]

    if missing:
        raise RuntimeError(
            "MySQL is partially configured. Provide host, database, user, "
            "and password in the [mysql] Streamlit secrets section or "
            "MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, and MYSQL_PASSWORD "
            "environment variables."
        )

    try:
        config["port"] = int(config["port"])
    except (TypeError, ValueError) as error:
        raise RuntimeError("MYSQL_PORT must be a valid port number.") from error

    if not 1 <= config["port"] <= 65535:
        raise RuntimeError("MYSQL_PORT must be between 1 and 65535.")

    return config


class _SQLiteConnection:
    def __init__(self, path):
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def __enter__(self):
        return self.connection

    def __exit__(self, *exception_info):
        try:
            if exception_info[0] is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()

        return False


class _MySQLConnection:
    def __init__(self, connection):
        self.connection = connection
        self.cursors = []

    def __enter__(self):
        return self

    def __exit__(self, *exception_info):
        try:
            if exception_info[0] is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            for cursor in self.cursors:
                cursor.close()
            self.connection.close()

        return False

    def execute(self, query, parameters=()):
        cursor = self.connection.cursor(dictionary=True)
        self.cursors.append(cursor)
        cursor.execute(query.replace("?", "%s"), parameters)
        return cursor


def get_connection():
    """Open the configured MySQL database or the local SQLite database."""

    config = _get_mysql_config()

    if config is None:
        return _SQLiteConnection(DB_PATH)

    try:
        import mysql.connector
    except ImportError as error:
        raise RuntimeError(
            "MySQL support is missing. Install the project dependencies "
            "from requirements.txt."
        ) from error

    connection = mysql.connector.connect(
        **config,
        connection_timeout=15,
    )
    return _MySQLConnection(connection)


def current_timestamp():
    """Return the current local timestamp."""
    return datetime.now().isoformat(timespec="seconds")


# =========================================================
# 2. INITIALIZE DATABASE
# =========================================================

def initialize_database():
    """Create NOVA's conversation and message tables if needed."""

    with get_connection() as connection:

        if isinstance(connection, _MySQLConnection):
            connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    title VARCHAR(255) NOT NULL,
                    chat_type VARCHAR(32) NOT NULL DEFAULT 'interview',
                    metadata LONGTEXT NOT NULL,
                    created_at VARCHAR(32) NOT NULL,
                    updated_at VARCHAR(32) NOT NULL,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    conversation_id BIGINT UNSIGNED NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    content LONGTEXT NOT NULL,
                    created_at VARCHAR(32) NOT NULL,
                    PRIMARY KEY (id),
                    INDEX messages_conversation_id_id (
                        conversation_id, id
                    ),
                    CONSTRAINT messages_conversation_fk
                        FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
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
