from typing import Any

import astropy.units as u


def _ensure_comparable(value: Any, bound: Any) -> tuple[Any, Any]:
    """
    Ensures value and bound are comparable, specifically handling Astropy quantities.
    Returns (converted_value, converted_bound).
    """
    # Handle case where value is already a Quantity (e.g. from physical primitives)
    if isinstance(value, u.Quantity):
        if isinstance(bound, (str, int, float)):
            try:
                q_bound = u.Quantity(bound)
                # Check if units are equivalent (comparable)
                # Ensure .unit attribute exists and is not None to satisfy type checker
                val_unit = getattr(value, "unit", None)
                bound_unit = getattr(q_bound, "unit", None)

                if val_unit is not None and bound_unit is not None:
                    if val_unit.is_equivalent(bound_unit):
                        return value, q_bound
            except Exception:
                pass

    # Check if we are dealing with strings that might be physical quantities
    if isinstance(value, str):
        try:
            q_val = u.Quantity(value)
            # If value parses as a quantity, we check if bound also parses
            if isinstance(bound, (str, int, float)):
                try:
                    q_bound = u.Quantity(bound)
                    # If both are quantities, check units compatibility
                    # type checker seems confused about .unit access, but astropy Quantity has it.
                    unit_val = getattr(q_val, "unit", None)
                    unit_bound = getattr(q_bound, "unit", None)

                    # Use a guard to satisfy type checker that unit_val is not None
                    if unit_val is not None and unit_bound is not None:
                        if unit_val.is_equivalent(unit_bound):
                            return q_val, q_bound

                except Exception:
                    pass
        except Exception:
            pass

    # If not quantities or mixed types that we can't handle, return as is
    return value, bound
