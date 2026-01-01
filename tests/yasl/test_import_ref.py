from yasl import check_schema


def test_import_ref_valid():
    schema_path = "tests/yasl/data/import_ref.yasl"

    # Should pass
    result = check_schema(schema_path)
    assert result is True
