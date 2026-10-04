"""Neo4j connection management.

Reads credentials from environment variables (with .env file support via
python-dotenv), provides a reusable driver, and offers a connectivity
verification function.

Environment variables:
  NEO4J_URI      e.g. bolt://localhost:7687 or neo4j://127.0.0.1:7687
  NEO4J_USER     e.g. neo4j
  NEO4J_PASSWORD (required)
  NEO4J_DATABASE e.g. neo4j (optional; defaults to server default)
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ClientError as _Neo4jClientError
    _neo4j_available = True
except ImportError:  # pragma: no cover -- driver not installed
    _neo4j_available = False
    GraphDatabase = None  # type: ignore[assignment,misc]
    _Neo4jClientError = Exception  # type: ignore[assignment,misc]


def _env(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Read an environment variable, raising a clear error when required."""
    val = os.environ.get(name, default)
    if required and not val:
        raise ValueError(
            f"Environment variable {name!r} is required but not set. "
            f"See .env.example for the expected configuration."
        )
    return val


@dataclass(frozen=True)
class Neo4jSettings:
    """Immutable connection settings resolved from the environment."""
    uri: str | None
    user: str | None
    password: str | None
    database: str | None

    @classmethod
    def from_env(cls) -> Neo4jSettings:
        # Load .env from the project root (two levels up from this file).
        if load_dotenv is not None:
            env_path = Path(__file__).resolve().parents[1] / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=False)
        return cls(
            uri=_env("NEO4J_URI", "bolt://localhost:7687"),
            user=_env("NEO4J_USER", "neo4j"),
            password=_env("NEO4J_PASSWORD"),
            database=_env("NEO4J_DATABASE"),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.user and self.password)


def _require_driver() -> None:
    if not _neo4j_available:
        raise ImportError(
            "The 'neo4j' package is required for Neo4j integration. "
            "Install it with: pip install neo4j"
        )


class Neo4jConnector:
    """Reusable Neo4j connector.

    Call ``close()`` when done, or use the ``connection()`` context manager
    which closes automatically.
    """

    def __init__(self, settings: Neo4jSettings | None = None) -> None:
        _require_driver()
        self.settings = settings or Neo4jSettings.from_env()
        if not self.settings.is_configured:
            raise ValueError(
                "Neo4j is not fully configured. Set NEO4J_URI, NEO4J_USER, "
                "and NEO4J_PASSWORD. See .env.example."
            )
        self._driver = GraphDatabase.driver(
            self.settings.uri,
            auth=(self.settings.user, self.settings.password),
        )

    # -- connectivity check ---------------------------------------------------

    def verify_connectivity(self) -> dict[str, Any]:
        """Run the driver's built-in connectivity check.

        Returns a dict with ``server_version`` on success, or raises a
        descriptive error on failure.
        """
        self._ensure_open()
        try:
            self._driver.verify_connectivity()
        except Exception as exc:
            raise ConnectionError(
                f"Neo4j connectivity check failed: {exc}"
            ) from exc
        try:
            rec = self._driver.execute_query(
                "CALL dbms.components() YIELD name, versions "
                "WHERE name = 'Neo4j' RETURN versions[0] AS version"
            )
            version = rec.records[0]["version"] if rec.records else "unknown"
        except Exception:
            version = "unknown"
        return {"server_version": version}

    # -- session / transaction helpers ----------------------------------------

    def _ensure_open(self) -> None:
        if self._driver is None:
            raise ConnectionError("Neo4j driver is closed.")

    @contextmanager
    def session(self):
        self._ensure_open()
        session = self._driver.session(database=self.settings.database)
        try:
            yield session
        finally:
            session.close()

    def execute_query(self, query: str, parameters: dict | None = None) -> neo4j.ResultSummary:
        """Run a single query in an auto-committed transaction."""
        with self.session() as s:
            return s.run(query, parameters or {}).consume()

    def execute_write(self, work: Any) -> Any:
        """Run a write transaction function ``work(tx)``."""
        with self.session() as s:
            return s.execute_write(work)

    # -- schema management ----------------------------------------------------

    def ensure_schema(self) -> list[str]:
        """Create uniqueness constraints if they do not already exist.

        Returns a list of human-readable status messages.
        """
        statements = [
            (
                "CREATE CONSTRAINT account_id_unique IF NOT EXISTS "
                "FOR (a:Account) REQUIRE a.account_id IS UNIQUE"
            ),
            (
                "CREATE CONSTRAINT transfer_txn_id_unique IF NOT EXISTS "
                "FOR ()-[t:TRANSFER]-() REQUIRE t.txn_id IS UNIQUE"
            ),
        ]
        messages: list[str] = []
        for stmt in statements:
            try:
                self.execute_query(stmt)
                messages.append(f"OK: {stmt}")
            except _Neo4jClientError as exc:
                # Constraint may already exist or not be supported.
                messages.append(f"SKIP: {stmt} ({exc.message})")
        return messages

    # -- cleanup --------------------------------------------------------------

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
