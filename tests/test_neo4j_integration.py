"""Neo4j integration tests.

Unit tests use a mocked driver and always run.  Live integration tests are
marked ``neo4j_live`` and skipped automatically when Neo4j is not configured.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from neo4j_db.connector import Neo4jConnector, Neo4jSettings
from neo4j_db.loader import LoadReport, _prepare_accounts, _prepare_txns, _validate_txns, load_sample, readback_counts

T0 = pd.Timestamp("2022-09-01 10:00")


def _settings(**overrides) -> Neo4jSettings:
    defaults = dict(uri="bolt://localhost:7687", user="neo4j", password="x", database=None)
    defaults.update(overrides)
    return Neo4jSettings(**defaults)


def _txns_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"txn_id": "t1", "ts": T0, "src": "A", "dst": "B", "amount": 100.0,
         "type": "transfer", "channel": "NEFT", "ext_bank": False, "currency": "USD"},
        {"txn_id": "t2", "ts": T0, "src": "B", "dst": "A", "amount": 50.0,
         "type": "transfer", "channel": "UPI", "ext_bank": True, "currency": "USD"},
    ])


def _accounts_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"account_id": "A", "role": "SOURCE"},
        {"account_id": "B", "role": "MULE"},
    ])


# ---------------------------------------------------------------------------
# Environment and configuration tests
# ---------------------------------------------------------------------------


class TestNeo4jSettings:

    def test_from_env_reads_variables(self):
        env = {"NEO4J_URI": "bolt://h:7687", "NEO4J_USER": "u", "NEO4J_PASSWORD": "p", "NEO4J_DATABASE": "db"}
        with patch.dict(os.environ, env, clear=False):
            s = Neo4jSettings.from_env()
        assert s.uri == "bolt://h:7687"
        assert s.user == "u"
        assert s.password == "p"
        assert s.database == "db"

    @patch("neo4j_db.connector.load_dotenv")
    def test_defaults_when_env_missing(self, _mock_dotenv):
        env = {k: v for k, v in os.environ.items() if not k.startswith("NEO4J_")}
        with patch.dict(os.environ, env, clear=True):
            s = Neo4jSettings.from_env()
        assert s.uri == "bolt://localhost:7687"
        assert s.user == "neo4j"
        assert s.password is None

    def test_is_configured_true(self):
        assert _settings().is_configured is True

    def test_is_configured_false_when_password_missing(self):
        assert _settings(password=None).is_configured is False


# ---------------------------------------------------------------------------
# Connector tests (mocked driver)
# ---------------------------------------------------------------------------


class TestNeo4jConnector:

    @patch("neo4j_db.connector.GraphDatabase")
    def test_constructs_driver_with_settings(self, mock_gdb):
        Neo4jConnector(_settings())
        mock_gdb.driver.assert_called_once_with(
            "bolt://localhost:7687", auth=("neo4j", "x")
        )

    @patch("neo4j_db.connector.GraphDatabase")
    def test_raises_when_not_configured(self, mock_gdb):
        with pytest.raises(ValueError, match="not fully configured"):
            Neo4jConnector(_settings(password=None))

    @patch("neo4j_db.connector.GraphDatabase")
    def test_verify_connectivity_success(self, mock_gdb):
        driver = MagicMock()
        mock_gdb.driver.return_value = driver
        result_mock = MagicMock()
        result_mock.records = [{"version": "5.13.0"}]
        driver.execute_query.return_value = result_mock
        conn = Neo4jConnector(_settings())
        info = conn.verify_connectivity()
        driver.verify_connectivity.assert_called_once()
        assert info["server_version"] == "5.13.0"
        conn.close()

    @patch("neo4j_db.connector.GraphDatabase")
    def test_verify_connectivity_failure(self, mock_gdb):
        driver = MagicMock()
        mock_gdb.driver.return_value = driver
        driver.verify_connectivity.side_effect = Exception("AuthError")
        conn = Neo4jConnector(_settings())
        with pytest.raises(ConnectionError, match="AuthError"):
            conn.verify_connectivity()
        conn.close()

    @patch("neo4j_db.connector.GraphDatabase")
    def test_close_sets_driver_none(self, mock_gdb):
        driver = MagicMock()
        mock_gdb.driver.return_value = driver
        conn = Neo4jConnector(_settings())
        conn.close()
        driver.close.assert_called_once()
        assert conn._driver is None

    @patch("neo4j_db.connector.GraphDatabase")
    def test_closed_driver_raises_on_query(self, mock_gdb):
        conn = Neo4jConnector(_settings())
        conn.close()
        with pytest.raises(ConnectionError, match="closed"):
            conn.execute_query("RETURN 1")


# ---------------------------------------------------------------------------
# Loader validation
# ---------------------------------------------------------------------------


class TestLoaderValidation:

    def test_validate_txns_rejects_missing_ids(self):
        df = pd.DataFrame({"txn_id": [None], "ts": [T0], "src": ["A"], "dst": ["B"], "amount": [1.0]})
        clean, rej = _validate_txns(df)
        assert len(clean) == 0
        assert rej == 1

    def test_validate_txns_rejects_nat_timestamp(self):
        df = pd.DataFrame({"txn_id": ["t1"], "ts": [pd.NaT], "src": ["A"], "dst": ["B"], "amount": [1.0]})
        clean, rej = _validate_txns(df)
        assert rej == 1

    def test_validate_txns_raises_on_missing_columns(self):
        with pytest.raises(ValueError, match="missing required columns"):
            _validate_txns(pd.DataFrame({"txn_id": ["t1"]}))

    def test_prepare_accounts_raises_without_account_id(self):
        with pytest.raises(ValueError, match="account_id"):
            _prepare_accounts(pd.DataFrame({"name": ["A"]}))

    def test_prepare_accounts_skips_nan(self):
        df = pd.DataFrame({"account_id": ["A", None, "B"]})
        records = _prepare_accounts(df)
        assert len(records) == 2

    def test_prepare_txns_maps_columns(self):
        records = _prepare_txns(_txns_df())
        assert len(records) == 2
        assert records[0]["txn_id"] == "t1"
        assert records[0]["amount"] == 100.0


# ---------------------------------------------------------------------------
# Loader with mocked connector
# ---------------------------------------------------------------------------


class TestLoaderMocked:

    def test_load_sample_calls_parameterized_queries(self):
        mock_conn = MagicMock()
        report = load_sample(mock_conn, _txns_df(), _accounts_df(), batch_size=1)
        assert report.accounts_processed == 2
        assert report.transactions_processed == 2
        assert report.rejected == 0
        # 2 account batches + 2 txn batches
        assert mock_conn.execute_query.call_count == 4

    def test_load_sample_preserves_parallel_transfers(self):
        df = _txns_df()
        df.loc[0, "dst"] = "B"
        df.loc[1, "src"] = "A"
        df.loc[1, "dst"] = "B"
        mock_conn = MagicMock()
        report = load_sample(mock_conn, df, _accounts_df())
        assert report.transactions_processed == 2

    def test_load_sample_never_writes_labels(self):
        df = _txns_df()
        df["is_laundering"] = [1, 0]
        calls = []
        def capture_query(q, p):
            calls.append((q, p))
        mock_conn = MagicMock()
        mock_conn.execute_query = capture_query
        load_sample(mock_conn, df, _accounts_df())
        for q, p in calls:
            for rec in p.get("txns", []):
                assert "is_laundering" not in rec

    def test_load_sample_separates_currencies(self):
        df = _txns_df()
        df.loc[0, "currency"] = "USD"
        df.loc[1, "currency"] = "EUR"
        calls = []
        def capture_query(q, p):
            calls.append((q, p))
        mock_conn = MagicMock()
        mock_conn.execute_query = capture_query
        load_sample(mock_conn, df)
        txn_calls = [c for q, c in calls if "UNWIND $txns" in q]
        assert len(txn_calls) == 1
        currencies = {r["currency"] for r in txn_calls[0]["txns"]}
        assert currencies == {"USD", "EUR"}


# ---------------------------------------------------------------------------
# Live integration tests (skipped when not configured)
# ---------------------------------------------------------------------------


def _live_connector():
    """Return a connector if Neo4j is configured, else skip."""
    s = Neo4jSettings.from_env()
    if not s.is_configured:
        pytest.skip("Neo4j not configured (set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)")
    return Neo4jConnector(s)


@pytest.mark.neo4j_live
class TestLiveNeo4jIntegration:

    def test_connectivity_and_version(self):
        conn = _live_connector()
        try:
            info = conn.verify_connectivity()
            assert "server_version" in info
        finally:
            conn.close()

    def test_schema_creation(self):
        conn = _live_connector()
        try:
            messages = conn.ensure_schema()
            assert len(messages) >= 2
        finally:
            conn.close()

    def test_sample_load_and_readback(self):
        conn = _live_connector()
        try:
            conn.ensure_schema()
            report = load_sample(conn, _txns_df(), _accounts_df())
            assert report.transactions_processed == 2
            assert report.accounts_processed == 2
            counts = readback_counts(conn)
            assert counts["nodes"] >= 2
            assert counts["relationships"] >= 2
        finally:
            conn.close()

    def test_idempotent_rerun(self):
        conn = _live_connector()
        try:
            conn.ensure_schema()
            load_sample(conn, _txns_df(), _accounts_df())
            c1 = readback_counts(conn)
            load_sample(conn, _txns_df(), _accounts_df())
            c2 = readback_counts(conn)
            assert c1 == c2
        finally:
            conn.close()
