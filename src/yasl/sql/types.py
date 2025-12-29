from typing import Any

import astropy.units as u
from pydantic import BaseModel
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import JSON, String, TypeDecorator


class PydanticType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for Pydantic Models.
    Stores Pydantic models as JSON in the database.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_type: type[BaseModel]):
        super().__init__()
        self.pydantic_type = pydantic_type

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.pydantic_type.model_validate(value)


class AstropyQuantityType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for astropy Quantities.
    Stores quantities as strings (e.g., "10 m").
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect: Dialect) -> Any | None:
        if value is None:
            return None
        return u.Quantity(value)
