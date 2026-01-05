from unittest.mock import patch

import pytest

from yasl.validators import type_validator


# Dummy class for the validator's 'cls' argument
class MockCls:
    pass


class TestTypeKeywordValidator:
    """
    Explicit unit tests for the 'type' keyword validation.

    YASL allows a property to be defined as `type: type`.
    This means the value of that property must itself be a valid YASL type signature.

    Valid signatures include:
    - Primitives: "int", "str", "bool", etc.
    - Lists: "int[]", "MyType[]"
    - Maps: "map[KeyType, ValueType]"
    - References: "ref[Target]"
    - User-defined types: "MyType", "Namespace.MyType"
    """

    def test_primitive_types(self):
        """Verify standard primitives are accepted."""
        primitives = [
            "int",
            "str",
            "bool",
            "float",
            "date",
            "datetime",
            "path",
            "url",
            "any",
        ]
        for p in primitives:
            assert type_validator(MockCls, p) == p

    def test_list_types(self):
        """Verify list syntax is accepted recursively."""
        assert type_validator(MockCls, "int[]") == "int[]"
        assert type_validator(MockCls, "str[]") == "str[]"
        # Nested/Complex lists
        assert type_validator(MockCls, "map[str, int][]") == "map[str, int][]"

    def test_map_types_valid(self):
        """Verify map syntax map[Key, Value] is accepted."""
        assert type_validator(MockCls, "map[str, int]") == "map[str, int]"
        assert type_validator(MockCls, "map[str, str]") == "map[str, str]"
        assert type_validator(MockCls, "map[int, bool]") == "map[int, bool]"

    def test_map_types_recursive(self):
        """Verify map values are recursively validated."""
        # Value is a list
        assert type_validator(MockCls, "map[str, int[]]") == "map[str, int[]]"
        # Value is another map (nested)
        assert (
            type_validator(MockCls, "map[str, map[int, str]]")
            == "map[str, map[int, str]]"
        )

    def test_map_types_invalid_key(self):
        """Verify map keys must be str, int, or Enum."""
        # 'bool' is a valid type, but NOT a valid map key
        with pytest.raises(ValueError, match="Invalid map key type"):
            type_validator(MockCls, "map[bool, int]")

        # 'float' is valid type, but NOT valid map key
        with pytest.raises(ValueError, match="Invalid map key type"):
            type_validator(MockCls, "map[float, int]")

    def test_map_types_invalid_value(self):
        """Verify map values must be valid types."""
        # 'Unknown' is not a valid type
        with pytest.raises(ValueError, match="Type 'Unknown' is not a valid primitive"):
            type_validator(MockCls, "map[str, Unknown]")

    def test_map_syntax_errors(self):
        """Verify malformed map strings are rejected."""
        # Missing comma
        with pytest.raises(ValueError, match="Invalid map type format"):
            type_validator(MockCls, "map[str int]")

        # Check logic:
        # "map[str,]" parses as key="str", value="".
        # Recursive validation of "" raises "Type '' is not a valid primitive..."
        # This is technically correct behavior (value type is missing/invalid) but the error message
        # comes from the recursive call, not the map format check.

        # If we want to specifically test "Invalid map type format", we need to trigger the splitting error
        # but NOT the missing comma error. The split logic is: map_content.split(",", 1)
        # It's hard to trigger a ValueError on split with user input if we already checked `if "," not in content`.
        # So essentially the "Invalid map type format" error is only raised if comma is missing.
        # Other syntax errors (like empty parts) are caught by recursive validation.

        # Let's adjust expectation for empty value part to match reality
        with pytest.raises(ValueError, match="Type '' is not a valid primitive"):
            type_validator(MockCls, "map[str,]")

    def test_references(self):
        """Verify ref syntax is accepted."""
        assert type_validator(MockCls, "ref[SomeTarget]") == "ref[SomeTarget]"
        assert (
            type_validator(MockCls, "ref[Namespace.Target]") == "ref[Namespace.Target]"
        )

    @patch("yasl.validators.YaslRegistry")
    def test_user_defined_types(self, mock_registry_cls):
        """Verify registered user types and enums are accepted."""
        mock_registry = mock_registry_cls.return_value

        # Setup: 'MyType' exists in registry
        def get_type_side_effect(name, ns, default_ns):
            if name == "MyType":
                return "MockClass"
            return None

        mock_registry.get_type.side_effect = get_type_side_effect
        mock_registry.get_enum.return_value = None

        assert type_validator(MockCls, "MyType") == "MyType"

        # Setup: 'MyEnum' exists
        mock_registry.get_type.return_value = None

        def get_enum_side_effect(name, ns, default_ns):
            if name == "MyEnum":
                return "MockEnum"
            return None

        mock_registry.get_enum.side_effect = get_enum_side_effect

        assert type_validator(MockCls, "MyEnum") == "MyEnum"

    @patch("yasl.validators.YaslRegistry")
    def test_unknown_type_with_hint(self, mock_registry_cls):
        """Verify helpful error message when type exists in another namespace."""
        mock_registry = mock_registry_cls.return_value
        mock_registry.get_type.return_value = None
        mock_registry.get_enum.return_value = None

        # Populate registry internals for the search logic
        mock_registry.yasl_type_defs = {("SecretType", "hidden_ns"): "Mock"}
        mock_registry.yasl_enumerations = {}

        # User asks for 'SecretType' without namespace
        with pytest.raises(ValueError, match="Did you mean one of: hidden_ns"):
            type_validator(MockCls, "SecretType")
