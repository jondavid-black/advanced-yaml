import pytest

from yasl.cache import YaslRegistry
from yasl.core import load_schema


def setup_function():
    YaslRegistry().clear_caches()


def teardown_function():
    YaslRegistry().clear_caches()


def test_circular_dependency_error():
    """
    Test that a circular dependency between two types (embedding each other)
    raises a ValueError with a clear message.
    """
    schema_data = {
        "definitions": {
            "circular_ns": {
                "types": {
                    "TypeA": {"properties": {"b": {"type": "TypeB"}}},
                    "TypeB": {"properties": {"a": {"type": "TypeA"}}},
                }
            }
        }
    }

    with pytest.raises(ValueError) as exc_info:
        load_schema(schema_data)

    error_msg = str(exc_info.value)
    assert "Unable to resolve dependencies" in error_msg
    assert "TypeA" in error_msg
    assert "TypeB" in error_msg


def test_deep_chain_dependency():
    """
    Test a deep chain of dependencies: A -> B -> C -> D.
    They should resolve correctly over multiple passes.
    """
    schema_data = {
        "definitions": {
            "chain_ns": {
                "types": {
                    "TypeA": {"properties": {"b": {"type": "TypeB"}}},
                    "TypeB": {"properties": {"c": {"type": "TypeC"}}},
                    "TypeC": {"properties": {"d": {"type": "TypeD"}}},
                    "TypeD": {"properties": {"val": {"type": "int"}}},
                }
            }
        }
    }

    # Should not raise
    _ = load_schema(schema_data)

    registry = YaslRegistry()
    assert registry.get_type("TypeA", "chain_ns") is not None
    assert registry.get_type("TypeB", "chain_ns") is not None
    assert registry.get_type("TypeC", "chain_ns") is not None
    assert registry.get_type("TypeD", "chain_ns") is not None
