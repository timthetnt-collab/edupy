"""Startup activation for database-backed classes and assignments."""

import save_system
from education_store import EducationStore


def activate_education_database(data, account_database):
    store = EducationStore(account_database.engine)
    result = store.migrate_or_load(data)
    snapshot = store.load_snapshot()
    data.update(snapshot)
    data.setdefault("system", {})["education_database_migrated"] = True
    save_system.set_education_sync(store.save_snapshot)
    # Clean the active JSON file and its rolling backup after verification.
    save_system.save_save(data)
    save_system.save_save(data)
    return store, result
