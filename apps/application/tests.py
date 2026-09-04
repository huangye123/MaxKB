from pathlib import Path
from unittest import TestCase


class ApplicationChatExportPatchTest(TestCase):
    def test_export_sql_uses_chat_user_nick_name(self):
        sql_path = Path(__file__).resolve().parent / "sql" / "export_application_chat_ee.sql"
        sql = sql_path.read_text(encoding="utf-8")

        self.assertIn("chat_user.nick_name", sql)
        self.assertNotIn("chat_user.username) END)::json AS asker", sql)

    def test_export_header_uses_user_label(self):
        serializer_path = Path(__file__).resolve().parent / "serializers" / "application_chat.py"
        source = serializer_path.read_text(encoding="utf-8")

        self.assertIn("gettext('User')", source)
        self.assertNotIn("gettext('USER')", source)
