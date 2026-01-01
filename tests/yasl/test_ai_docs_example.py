from yasl import check_schema


def test_ai_docs_valid():
    schema_path = "tests/yasl/data/ai_docs_example.yasl"

    # Should pass
    result = check_schema(schema_path)
    assert result is not None
