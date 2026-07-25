"""Startup activation for database-backed learner progress and rewards."""

import save_system
from progress_store import MOVED_PROFILE_FIELDS, ProgressStore


def activate_progress_database(data, account_database):
    store = ProgressStore(account_database.engine)
    result = store.migrate_or_load(data)
    for username, profile in store.load_profiles().items():
        data.setdefault("users", {}).setdefault(username, {}).update(profile)
    data.setdefault("system", {})["progress_database_migrated"] = True
    save_system.set_profile_sync(store.save_snapshot, MOVED_PROFILE_FIELDS)
    save_system.save_save(data)
    save_system.save_save(data)
    return store, result
