"""Private, rotating local backups for EduPy's database and small JSON shell."""

import datetime
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing


def create_daily_backup(database_path, save_path, backup_dir, today=None, keep=7):
    date = today or datetime.date.today()
    date_text = date.isoformat()
    os.makedirs(backup_dir, exist_ok=True)
    database_backup = os.path.join(backup_dir, f"edupy-{date_text}.db")
    json_backup = os.path.join(backup_dir, f"edupy-{date_text}.json")
    if not (os.path.exists(database_backup) and os.path.exists(json_backup)):
        handle, temporary = tempfile.mkstemp(prefix="edupy-backup-", suffix=".db", dir=backup_dir)
        os.close(handle)
        try:
            with closing(sqlite3.connect(database_path)) as source, closing(sqlite3.connect(temporary)) as destination:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("Backup integrity check failed")
            os.replace(temporary, database_backup)
            shutil.copy2(save_path, json_backup)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    keep = max(1, int(keep))
    database_files = sorted(
        (name for name in os.listdir(backup_dir) if name.startswith("edupy-") and name.endswith(".db")),
        reverse=True,
    )
    for old_name in database_files[keep:]:
        stem = os.path.splitext(old_name)[0]
        for extension in (".db", ".json"):
            path = os.path.join(backup_dir, stem + extension)
            if os.path.exists(path): os.remove(path)
    return {"database": database_backup, "json": json_backup, "date": date_text}
