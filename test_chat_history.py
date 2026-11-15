import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chat_history


class FakeCursor:
    def __init__(self):
        self.query = None
        self.parameters = None
        self.closed = False

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters

    def close(self):
        self.closed = True


class FakeMySQLConnection:
    def __init__(self):
        self.cursors = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, dictionary=False):
        if not dictionary:
            raise AssertionError("MySQL cursors must return dictionary rows.")
        cursor = FakeCursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class ChatHistoryTests(unittest.TestCase):
    def setUp(self):
        self.original_db_path = chat_history.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        chat_history.DB_PATH = Path(self.temp_dir.name) / "test_chats.db"
        chat_history.initialize_database()

    def tearDown(self):
        chat_history.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_sqlite_conversation_lifecycle(self):
        conversation_id = chat_history.create_conversation(
            title="Deployment test",
            chat_type="general",
            metadata={"mode": "general_chat"},
        )
        chat_history.add_message(conversation_id, "user", "Hello")
        chat_history.add_message(conversation_id, "assistant", "Hi there")

        conversation = chat_history.get_conversation(conversation_id)
        messages = chat_history.get_messages(conversation_id)

        self.assertEqual(conversation["metadata"], {"mode": "general_chat"})
        self.assertEqual(
            [message["content"] for message in messages],
            ["Hello", "Hi there"],
        )

        chat_history.delete_conversation(conversation_id)
        self.assertIsNone(chat_history.get_conversation(conversation_id))
        self.assertEqual(chat_history.get_messages(conversation_id), [])

    def test_mysql_adapter_translates_placeholders_and_commits(self):
        raw_connection = FakeMySQLConnection()
        connection = chat_history._MySQLConnection(raw_connection)

        with connection as database:
            cursor = database.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (7,),
            )

        self.assertEqual(
            raw_connection.cursors[0].query,
            "SELECT id FROM conversations WHERE id = %s",
        )
        self.assertEqual(raw_connection.cursors[0].parameters, (7,))
        self.assertTrue(raw_connection.committed)
        self.assertFalse(raw_connection.rolled_back)
        self.assertTrue(raw_connection.cursors[0].closed)
        self.assertTrue(raw_connection.closed)

    def test_mysql_initialization_creates_both_tables(self):
        raw_connection = FakeMySQLConnection()
        settings = {
            "MYSQL_HOST": "db.example.test",
            "MYSQL_PORT": "3306",
            "MYSQL_DATABASE": "nova",
            "MYSQL_USER": "nova_app",
            "MYSQL_PASSWORD": "test-password",
        }

        with patch.dict("os.environ", settings), patch(
            "mysql.connector.connect",
            return_value=raw_connection,
        ) as connect:
            chat_history.initialize_database()

        connect.assert_called_once_with(
            host="db.example.test",
            port=3306,
            database="nova",
            user="nova_app",
            password="test-password",
            connection_timeout=15,
        )
        self.assertEqual(len(raw_connection.cursors), 2)
        self.assertIn(
            "CREATE TABLE IF NOT EXISTS conversations",
            raw_connection.cursors[0].query,
        )
        self.assertIn(
            "CREATE TABLE IF NOT EXISTS messages",
            raw_connection.cursors[1].query,
        )
        self.assertTrue(raw_connection.committed)
        self.assertTrue(raw_connection.closed)

    def test_mysql_adapter_rolls_back_errors(self):
        raw_connection = FakeMySQLConnection()
        connection = chat_history._MySQLConnection(raw_connection)

        with self.assertRaisesRegex(ValueError, "test failure"):
            with connection:
                raise ValueError("test failure")

        self.assertFalse(raw_connection.committed)
        self.assertTrue(raw_connection.rolled_back)
        self.assertTrue(raw_connection.closed)


if __name__ == "__main__":
    unittest.main()
