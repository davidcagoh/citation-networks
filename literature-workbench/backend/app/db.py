from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base


class Database:
    def __init__(self, url: str) -> None:
        self._sqlite_path = self._prepare_sqlite_path(url)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine_options = {"connect_args": connect_args}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            engine_options["poolclass"] = StaticPool
        self.engine = create_engine(url, **engine_options)
        if url.startswith("sqlite"):
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        if self._sqlite_path is not None and self._sqlite_path.exists():
            self._sqlite_path.chmod(0o600)

    def dispose(self) -> None:
        self.engine.dispose()

    @contextmanager
    def session(self) -> Iterator[Session]:
        db = self.session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @staticmethod
    def _prepare_sqlite_path(url: str) -> Path | None:
        parsed = make_url(url)
        if parsed.drivername != "sqlite" or parsed.database in {None, "", ":memory:"}:
            return None
        database_path = Path(parsed.database).expanduser()
        if not database_path.is_absolute():
            database_path = Path.cwd() / database_path
        parent = database_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, mode=0o700)
            parent.chmod(0o700)
        return database_path
