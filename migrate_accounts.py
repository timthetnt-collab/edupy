"""Manual account migration/check command. Run with the EduPy virtual environment."""

import account_service
import save_system


def main():
    data = save_system.load_save()
    database = account_service.create_default_database()
    result = account_service.migrate_legacy_accounts(data, database)
    print(f"Profiles checked: {result.total_profiles}")
    print(f"Secure accounts created: {result.created_accounts}")
    print(f"Secure accounts already present: {result.existing_accounts}")
    if result.missing_passwords:
        print("Could not migrate: " + ", ".join(result.missing_passwords))
        print("Readable passwords were not removed.")
    else:
        print("Migration verified successfully.")
        print("Readable passwords were removed from the active save and rolling backup.")


if __name__ == "__main__":
    main()
