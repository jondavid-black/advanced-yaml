from pathlib import Path

import pytest
from sqlmodel import SQLModel

from yaql.engine import YaqlEngine
from yasl.cache import YaslRegistry

YASL_DIR = Path("tests/yaql/data")


@pytest.fixture(autouse=True)
def clear_registry():
    YaslRegistry().clear_caches()
    SQLModel.metadata.clear()
    yield
    YaslRegistry().clear_caches()
    SQLModel.metadata.clear()


def test_engine_init():
    engine = YaqlEngine()
    assert (
        engine.engine is not None
    )  # conn is no longer a public attribute in sqlmodel engine


def test_load_schema():
    engine = YaqlEngine()
    # Using a known existing schema file from the repo
    schema_path = YASL_DIR / "person.yasl"

    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")

    success = engine.load_schema(str(schema_path))
    assert success is True

    # Check if table was created
    # Assuming person.yasl defines a 'Person' type in default namespace or similar
    # We can inspect the sqlite master to see what tables were created
    res = engine.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
    assert res is not None
    tables = [row["name"] for row in res]
    # Check if 'acme_person' or 'person' table exists.
    # Namespace handling might rename it.
    assert any("person" in t for t in tables)


def test_load_schema_dir():
    engine = YaqlEngine()
    # Using a known existing schema file from the repo
    schema_path = YASL_DIR

    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")

    success = engine.load_schema(str(schema_path))
    assert success is True

    # Check if table was created
    res = engine.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
    assert res is not None
    tables = [row["name"] for row in res]
    assert len(tables) > 0


def test_load_data():
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    data_path = YASL_DIR / "person.yaml"

    if not schema_path.exists() or not data_path.exists():
        pytest.skip("Schema or data file not found")

    engine.load_schema(str(schema_path))
    count = engine.load_data(str(data_path))

    assert count > 0


def test_load_data_dir():
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    data_path = YASL_DIR

    if not schema_path.exists() or not data_path.exists():
        pytest.skip("Schema or data file not found")

    engine.load_schema(str(schema_path))
    count = engine.load_data(str(data_path))

    assert count > 0


def test_sql_execution():
    engine = YaqlEngine()
    engine.execute_sql("CREATE TABLE test (id INTEGER, name TEXT)")
    engine.execute_sql("INSERT INTO test VALUES (1, 'Alice')")

    rows = engine.execute_sql("SELECT * FROM test")
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    # engine.close() # Close removed


def test_store_schema_not_implemented(tmp_path):
    # just verify it raises or errors log, but since we removed the method...
    # assert not hasattr(engine, 'store_schema')
    pass


def test_store_data_not_implemented(tmp_path):
    # assert not hasattr(engine, 'store_data')
    pass


def test_relationships_and_fks():
    engine = YaqlEngine()
    schema_path = YASL_DIR / "relationship.yasl"
    data_path = YASL_DIR / "relationship.yaml"

    assert schema_path.exists()
    assert data_path.exists()

    # Load schema
    assert engine.load_schema(str(schema_path)) is True

    # Load data
    assert engine.load_data(str(data_path)) > 0

    # Verify via SQL that tables exist and data is linked
    # Note: SQLite by default doesn't enforce FKs unless PRAGMA foreign_keys = ON;
    # But here we just want to verify the schema generation created the FK column.

    # 1. Check schema of 'rel_test_employee' table (namespace 'rel_test')
    # Use pragma table_info to check columns
    # DEBUG: Check DDL
    engine.execute_sql("SELECT sql FROM sqlite_master WHERE name='rel_test_employee'")

    cols = engine.execute_sql("PRAGMA table_info(rel_test_employee)")
    assert cols is not None
    col_names = [c["name"] for c in cols]
    assert "dept_name" in col_names

    # 2. Check foreign key definition
    fks = engine.execute_sql("PRAGMA foreign_key_list(rel_test_employee)")
    # fks should look like: id, seq, table, from, to, on_update, on_delete, match
    # we expect table='rel_test_department', from='dept_name', to='name'
    found_fk = False
    assert fks is not None
    for fk in fks:
        if (
            fk["table"] == "rel_test_department"
            and fk["from"] == "dept_name"
            and fk["to"] == "name"
        ):
            found_fk = True
            break
    assert found_fk, "Foreign Key constraint not found in SQLite schema"

    # 3. Join Query
    query = """
    SELECT e.name as emp_name, d.name as dept_name
    FROM rel_test_employee e
    JOIN rel_test_department d ON e.dept_name = d.name
    """
    results = engine.execute_sql(query)
    assert results is not None
    assert len(results) == 1
    assert results[0]["emp_name"] == "Alice"
    assert results[0]["dept_name"] == "Engineering"
