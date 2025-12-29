from unittest.mock import MagicMock

import astropy.units as u
import pytest
from pydantic import BaseModel

from yasl.sql.types import AstropyQuantityType, PydanticType

# --- Fixtures / Setup ---


class SimpleModel(BaseModel):
    id: int
    name: str


@pytest.fixture
def mock_dialect():
    return MagicMock()


# --- Tests for PydanticType ---


class TestPydanticType:
    def test_process_bind_param_valid(self, mock_dialect):
        """Test converting a Pydantic model to a dict (JSON)."""
        model_instance = SimpleModel(id=1, name="test")
        type_decorator = PydanticType(pydantic_type=SimpleModel)

        result = type_decorator.process_bind_param(model_instance, mock_dialect)

        assert result == {"id": 1, "name": "test"}

    def test_process_bind_param_none(self, mock_dialect):
        """Test that None returns None."""
        type_decorator = PydanticType(pydantic_type=SimpleModel)
        result = type_decorator.process_bind_param(None, mock_dialect)
        assert result is None

    def test_process_bind_param_already_dict(self, mock_dialect):
        """Test that passing a dict directly works (fallback behavior)."""
        # Note: The implementation returns 'value' if it's not a BaseModel.
        # This is strictly based on the code: "if isinstance(value, BaseModel): ... return value"
        data = {"id": 1, "name": "test"}
        type_decorator = PydanticType(pydantic_type=SimpleModel)

        result = type_decorator.process_bind_param(data, mock_dialect)

        assert result == data

    def test_process_result_value_valid(self, mock_dialect):
        """Test converting a dict (JSON) back to a Pydantic model."""
        data = {"id": 1, "name": "test"}
        type_decorator = PydanticType(pydantic_type=SimpleModel)

        result = type_decorator.process_result_value(data, mock_dialect)

        assert isinstance(result, SimpleModel)
        assert result.id == 1
        assert result.name == "test"

    def test_process_result_value_none(self, mock_dialect):
        """Test that None returns None."""
        type_decorator = PydanticType(pydantic_type=SimpleModel)
        result = type_decorator.process_result_value(None, mock_dialect)
        assert result is None


# --- Tests for AstropyQuantityType ---


class TestAstropyQuantityType:
    def test_process_bind_param_valid(self, mock_dialect):
        """Test converting an astropy Quantity to a string."""
        quantity = 10 * u.meter
        type_decorator = AstropyQuantityType()

        result = type_decorator.process_bind_param(quantity, mock_dialect)

        assert result == "10.0 m"

    def test_process_bind_param_none(self, mock_dialect):
        """Test that None returns None."""
        type_decorator = AstropyQuantityType()
        result = type_decorator.process_bind_param(None, mock_dialect)
        assert result is None

    def test_process_result_value_valid(self, mock_dialect):
        """Test converting a string back to an astropy Quantity."""
        value_str = "10.0 m"
        type_decorator = AstropyQuantityType()

        result = type_decorator.process_result_value(value_str, mock_dialect)

        assert isinstance(result, u.Quantity)
        assert result.value == 10.0
        assert result.unit == u.meter

    def test_process_result_value_none(self, mock_dialect):
        """Test that None returns None."""
        type_decorator = AstropyQuantityType()
        result = type_decorator.process_result_value(None, mock_dialect)
        assert result is None
