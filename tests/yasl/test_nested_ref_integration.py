import os

import pytest

from yasl.cache import YaslRegistry
from yasl.core import load_data_files, load_schema_files

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def registry():
    reg = YaslRegistry()
    reg.clear_caches()
    return reg


def test_nested_references_schema_loading(registry):
    """Test loading the schema with nested types."""
    schema_path = os.path.join(DATA_DIR, "nested_ref_test.yasl")
    result = load_schema_files(schema_path)
    assert result is not None
    assert len(result) == 1

    # Verify types are registered
    assert registry.get_type("Item", "container_test") is not None
    assert registry.get_type("Container", "container_test") is not None
    assert registry.get_type("ContainerList", "container_test") is not None
    assert registry.get_type("ReferenceHolder", "container_test") is not None
    assert registry.get_type("Root", "container_test") is not None


def test_valid_nested_data(registry):
    """Test validating data with valid nested unique values and references."""
    schema_path = os.path.join(DATA_DIR, "nested_ref_test.yasl")
    load_schema_files(schema_path)

    data_path = os.path.join(DATA_DIR, "nested_ref_valid.yaml")

    # Validate against the Root object which contains both the definitions (containers) and usage (target_item)
    result = load_data_files(data_path, model_name="Root")
    assert result is not None
    assert len(result) == 1

    # Verify the reference check passed (implicitly by result not being None)
    # Also verify unique values were registered
    assert registry.unique_value_exists("Item", "id", "item1", "container_test")
    assert registry.unique_value_exists("Item", "id", "item2", "container_test")
    assert registry.unique_value_exists("Item", "id", "item3", "container_test")


def test_duplicate_nested_data(registry):
    """Test that duplicate unique values in nested lists are caught."""
    schema_path = os.path.join(DATA_DIR, "nested_ref_test.yasl")
    load_schema_files(schema_path)

    data_path = os.path.join(DATA_DIR, "nested_ref_duplicate.yaml")

    # This should fail validation due to duplicate unique value
    # Note: We use ContainerList here because the dup yaml only has containers
    result = load_data_files(data_path, model_name="ContainerList")
    assert result is None
