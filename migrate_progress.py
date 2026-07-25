"""Manual migration/check for learner progress, rewards, mastery, and themes."""

import account_service
import education_service
import progress_service
import save_system


def main():
    data = save_system.load_save()
    database = account_service.create_default_database()
    account_service.migrate_legacy_accounts(data, database)
    education_service.activate_education_database(data, database)
    _store, result = progress_service.activate_progress_database(data, database)
    print("Progress and rewards database verified successfully.")
    for name, count in result.actual.items():
        print(f"{name.replace('_', ' ').title()}: {count}")


if __name__ == "__main__":
    main()
