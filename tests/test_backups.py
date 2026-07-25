import datetime
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

import backup_service


class BackupTests(unittest.TestCase):
    def test_daily_backup_is_valid_and_retention_removes_old_pairs(self):
        with tempfile.TemporaryDirectory() as folder:
            database = os.path.join(folder, "edupy.db"); save = os.path.join(folder, "save.json"); backups = os.path.join(folder, "backups")
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE example (value TEXT)"); connection.execute("INSERT INTO example VALUES ('safe')")
                connection.commit()
            with open(save, "w", encoding="utf-8") as file: json.dump({"users": {}}, file)
            for day in (datetime.date(2026, 7, 12), datetime.date(2026, 7, 13), datetime.date(2026, 7, 14)):
                backup_service.create_daily_backup(database, save, backups, day, keep=2)
            self.assertFalse(os.path.exists(os.path.join(backups, "edupy-2026-07-12.db")))
            latest = os.path.join(backups, "edupy-2026-07-14.db")
            with closing(sqlite3.connect(latest)) as connection:
                self.assertEqual(connection.execute("SELECT value FROM example").fetchone()[0], "safe")
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertTrue(os.path.exists(os.path.join(backups, "edupy-2026-07-14.json")))


if __name__ == "__main__":
    unittest.main()
