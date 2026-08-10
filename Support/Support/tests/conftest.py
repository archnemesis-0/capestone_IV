from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "customer360.duckdb"
SOURCE_DIR = ROOT / "data" / "source"


@pytest.fixture(scope="session")
def conn():
    if not DB_PATH.exists():
        pytest.fail(
            f"{DB_PATH} not found. Run the pipeline scripts in src/ before running tests."
        )

    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


def row_count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]
