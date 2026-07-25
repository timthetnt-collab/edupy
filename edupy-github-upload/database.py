"""SQLite account database access for EduPy."""

import os
from typing import Optional

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from models import Account, utc_now


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATABASE_PATH = os.path.join(BASE_DIR, "edupy.db")


class AccountDatabase:
    def __init__(self, path=DEFAULT_DATABASE_PATH):
        self.path = os.path.abspath(path)
        self.engine = create_engine(
            f"sqlite:///{self.path}",
            connect_args={"check_same_thread": False},
        )
        event.listen(self.engine, "connect", self._enable_foreign_keys)

    @staticmethod
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_account(self, username: str) -> Optional[Account]:
        with Session(self.engine) as session:
            return session.exec(select(Account).where(Account.username == username)).first()

    def create_account(self, account: Account) -> Optional[Account]:
        with Session(self.engine) as session:
            try:
                session.add(account)
                session.commit()
                session.refresh(account)
                return account
            except IntegrityError:
                session.rollback()
                return None

    def update_account(self, username: str, **changes) -> Optional[Account]:
        with Session(self.engine) as session:
            account = session.exec(select(Account).where(Account.username == username)).first()
            if not account:
                return None
            for key, value in changes.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            account.updated_at = utc_now()
            session.add(account)
            session.commit()
            session.refresh(account)
            return account

    def delete_account(self, username: str) -> bool:
        with Session(self.engine) as session:
            account = session.exec(select(Account).where(Account.username == username)).first()
            if not account:
                return False
            session.delete(account)
            session.commit()
            return True

    def usernames(self):
        with Session(self.engine) as session:
            return set(session.exec(select(Account.username)).all())

    def count_accounts(self) -> int:
        return len(self.usernames())
