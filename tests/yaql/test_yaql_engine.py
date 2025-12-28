from pathlib import Path

import pytest

from yaql.engine import YaqlEngine
from yasl.cache import get_yasl_registry

# Mock data paths
BASE_DIR = Path(__file__).parent.parent.parent
YASL_DIR = BASE_DIR / "tests" / "yaql" / "data"


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear the YASL registry before each test to prevent singleton pollution."""
    registry = get_yasl_registry()
    registry.clear_caches()
    yield
    registry.clear_caches()


def test_engine_init():
    engine = YaqlEngine()
    assert engine.conn is not None
    assert engine.registry is not None
    engine.close()


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
    assert len(tables) > 0
    assert "acme_person" in tables
    # The actual table name depends on the namespace in person.yasl
    # If person.yasl has namespace 'my.ns', table might be 'my_ns_Person'
    engine.close()


def test_load_schema_dir():
    engine = YaqlEngine()
    # Using a known existing schema file from the repo
    schema_path = YASL_DIR

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
    assert len(tables) > 0
    assert "acme_person" in tables
    # The actual table name depends on the namespace in person.yasl
    # If person.yasl has namespace 'my.ns', table might be 'my_ns_Person'
    engine.close()


def test_load_data():
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    data_path = YASL_DIR / "person.yaml"

    if not schema_path.exists() or not data_path.exists():
        pytest.skip("Schema or data file not found")

    engine.load_schema(str(schema_path))
    count = engine.load_data(str(data_path))

    assert count > 0

    # Verify data is in DB
    # We expect 'acme_person' table to contain the data

    # Debug info
    res = engine.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
    assert res is not None
    tables = [row["name"] for row in res]
    print(f"Tables found: {tables}")

    found_rows = 0
    for table in tables:
        rows = engine.execute_sql(f'SELECT * FROM "{table}"')
        assert rows is not None
        found_rows += len(rows)

    assert found_rows == count
    engine.close()


def test_load_data_dir():
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    data_path = YASL_DIR

    if not schema_path.exists() or not data_path.exists():
        pytest.skip("Schema or data file not found")

    engine.load_schema(str(schema_path))
    count = engine.load_data(str(data_path))

    assert count > 0

    # Verify data is in DB
    # We expect 'acme_person' table to contain the data

    # Debug info
    res = engine.execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
    assert res is not None
    tables = [row["name"] for row in res]
    print(f"Tables found: {tables}")

    found_rows = 0
    for table in tables:
        rows = engine.execute_sql(f'SELECT * FROM "{table}"')
        assert rows is not None
        found_rows += len(rows)

    assert found_rows == count
    engine.close()


def test_sql_execution():
    engine = YaqlEngine()
    engine.execute_sql("CREATE TABLE test (id INTEGER, name TEXT)")
    engine.execute_sql("INSERT INTO test VALUES (1, 'Alice')")

    rows = engine.execute_sql("SELECT * FROM test")
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    engine.close()


def test_store_schema(tmp_path):
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")

    engine.load_schema(str(schema_path))

    output_file = tmp_path / "exported_schema.yasl"
    success = engine.store_schema(str(output_file))

    assert success is True
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    # Basic check if content looks like YAML/YASL
    content = output_file.read_text()
    assert "definitions:" in content
    assert "acme:" in content
    assert "types:" in content
    assert "person:" in content
    engine.close()


def test_store_data(tmp_path):
    engine = YaqlEngine()
    schema_path = YASL_DIR / "person.yasl"
    data_path = YASL_DIR / "person.yaml"

    if not schema_path.exists() or not data_path.exists():
        pytest.skip("Schema or data file not found")

    engine.load_schema(str(schema_path))
    engine.load_data(str(data_path))

    output_file = tmp_path / "exported_data.yaml"
    engine.store_data(str(output_file))

    assert output_file.exists()
    # Check if data was exported
    # We expect 2 records
    from ruamel.yaml import YAML

    yaml = YAML()
    with open(output_file) as f:
        data = yaml.load(f)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "John Doe"
    engine.close()
