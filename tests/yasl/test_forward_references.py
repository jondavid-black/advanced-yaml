import os
import unittest

from yasl.cache import YaslRegistry
from yasl.core import check_schema, yasl_eval


class TestYaslForwardReferences(unittest.TestCase):
    def setUp(self):
        self.registry = YaslRegistry()
        self.registry.clear_caches()
        self.schema_file = os.path.join(
            os.path.dirname(__file__), "data/forward_ref.yasl"
        )
        self.data_file = os.path.join(
            os.path.dirname(__file__), "data/forward_ref.yaml"
        )

    def tearDown(self):
        self.registry.clear_caches()

    def test_forward_references_schema_validation(self):
        """Test that a schema with forward references is valid."""
        is_valid = check_schema(self.schema_file)
        self.assertTrue(is_valid, "Schema with forward references should be valid")

    def test_forward_references_data_validation(self):
        """Test that data can be validated against a schema with forward references."""
        # Ensure schema is loaded first implicitly by check_schema or explicitly if needed,
        # but yasl_eval handles loading schema.
        results = yasl_eval(self.schema_file, self.data_file)
        self.assertIsNotNone(results, "Data validation should succeed")
        if results is None:  # Guard for type checking
            return

        self.assertEqual(len(results), 2, "Should validate 2 documents")

        # Verify content
        node_doc = results[0]
        other_doc = results[1]

        # Depending on order, might need to swap
        # We access attributes dynamically because the Pydantic models are generated dynamically
        # Using getattr to avoid static analysis errors on dynamic models, but silence B009 for Ruff
        if hasattr(node_doc, "name"):
            node_doc, other_doc = other_doc, node_doc

        self.assertEqual(node_doc.id, 1)  # type: ignore
        self.assertEqual(node_doc.child, 1)  # type: ignore
        self.assertEqual(node_doc.other, "something")  # type: ignore

        self.assertEqual(other_doc.name, "something")  # type: ignore


if __name__ == "__main__":
    unittest.main()
