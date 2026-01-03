import os
import tempfile
from io import StringIO

import pytest

from yasl import yasl_eval
from yasl.primitives import PRIMITIVE_TYPE_MAP


def run_eval_command(yaml_data, yasl_schema, model_name, expect_valid):
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "test.yaml")
        yasl_path = os.path.join(tmpdir, "test.yasl")
        with open(yaml_path, "w") as f:
            f.write(yaml_data)
        with open(yasl_path, "w") as f:
            f.write(yasl_schema)

        test_log = StringIO()
        yasl_model = yasl_eval(
            yasl_path,
            yaml_path,
            model_name,
            verbose_log=True,
            output="text",
            log_stream=test_log,
        )

        if not expect_valid:
            assert yasl_model is None, (
                f"Expected validation failure, but got success. Log:\n{test_log.getvalue()}"
            )
            assert "❌" in test_log.getvalue()
        else:
            assert yasl_model is not None, (
                f"Expected validation success, but got failure. Log:\n{test_log.getvalue()}"
            )
            assert "data validation successful" in test_log.getvalue()


def test_duration_validation():
    time_type = PRIMITIVE_TYPE_MAP["time"]
    # Valid time
    assert time_type.validate("10 s") == "10 s"
    assert time_type.validate("2.5 min") == "2.5 min"

    # Invalid unit for time (using length instead)
    with pytest.raises(ValueError, match="Physical type mismatch"):
        time_type.validate("10 m")

    # Invalid format
    with pytest.raises(ValueError, match="Invalid quantity"):
        time_type.validate("not a number")


def test_length_validation():
    length_type = PRIMITIVE_TYPE_MAP["length"]
    # Valid length
    assert length_type.validate("100 m") == "100 m"
    assert length_type.validate("1.5 km") == "1.5 km"

    # Invalid unit for length
    with pytest.raises(ValueError, match="Physical type mismatch"):
        length_type.validate("10 s")


def test_velocity_validation():
    velocity_type = PRIMITIVE_TYPE_MAP["velocity"]
    # Valid velocity
    assert velocity_type.validate("10 m/s") == "10 m/s"
    assert velocity_type.validate("100 km/h") == "100 km/h"

    # Invalid unit
    with pytest.raises(ValueError, match="Physical type mismatch"):
        velocity_type.validate("10 m")


def test_mass_validation():
    mass_type = PRIMITIVE_TYPE_MAP["mass"]
    # Valid mass
    assert mass_type.validate("10 kg") == "10 kg"
    assert mass_type.validate("500 g") == "500 g"

    # Invalid unit
    with pytest.raises(ValueError, match="Physical type mismatch"):
        mass_type.validate("10 s")


def test_temperature_validation():
    temp_type = PRIMITIVE_TYPE_MAP["temperature"]
    # Valid temperature
    assert temp_type.validate("300 K") == "300 K"

    # Note: Astropy treats 'deg_C' as a unit of temperature difference unless specified otherwise,
    # but for simple Quantity validation it usually works if the physical type matches.
    # Let's check Kelvin which is the base unit.

    # Invalid unit
    with pytest.raises(ValueError, match="Physical type mismatch"):
        temp_type.validate("10 m")


def test_volume_validation():
    volume_type = PRIMITIVE_TYPE_MAP["volume"]
    # Valid volume
    assert volume_type.validate("10 m3") == "10 m3"
    # Liters
    assert volume_type.validate("5 L") == "5 L"
    assert volume_type.validate("500 ml") == "500 ml"

    # Invalid unit
    with pytest.raises(ValueError, match="Physical type mismatch"):
        volume_type.validate("10 m")


def test_complex_units_validation():
    # Test multi-word physical type names

    # "amount of substance"
    amount_type = PRIMITIVE_TYPE_MAP["amount of substance"]
    assert amount_type.validate("5 mol") == "5 mol"
    with pytest.raises(ValueError, match="Physical type mismatch"):
        amount_type.validate("5 kg")

    # "thermal conductivity"
    thermal_cond_type = PRIMITIVE_TYPE_MAP["thermal conductivity"]
    # W / (m K)
    assert thermal_cond_type.validate("10 W / (m K)") == "10 W / (m K)"
    with pytest.raises(ValueError, match="Physical type mismatch"):
        thermal_cond_type.validate("10 W")

    # "specific heat capacity"
    spec_heat_type = PRIMITIVE_TYPE_MAP["specific heat capacity"]
    # J / (kg K)
    assert spec_heat_type.validate("4184 J / (kg K)") == "4184 J / (kg K)"
    with pytest.raises(ValueError, match="Physical type mismatch"):
        spec_heat_type.validate("100 J")

    # "electric field strength" - note mismatch in PRIMITIVE_TYPE_MAP vs astropy name sometimes, let's check
    # In primitives.py: (si.V / si.m, "electrical field strength"),
    elec_field_type = PRIMITIVE_TYPE_MAP["electrical field strength"]
    assert elec_field_type.validate("100 V/m") == "100 V/m"
    with pytest.raises(ValueError, match="Physical type mismatch"):
        elec_field_type.validate("10 V")


def test_imaginary_numbers_supported():
    """
    Verify that imaginary numbers ARE now supported by checking
    that 'complex' is a key in the PRIMITIVE_TYPE_MAP and maps to the complex type.
    """
    assert "complex" in PRIMITIVE_TYPE_MAP
    assert PRIMITIVE_TYPE_MAP["complex"] is complex


def test_imaginary_value_validation():
    """
    Test basic usage of complex numbers to ensure Python's complex type works as expected.
    """
    c = 1 + 2j
    assert isinstance(c, complex)
    assert c.real == 1
    assert c.imag == 2


# --- YASL Integration Tests ---


def test_yasl_time_integration():
    yasl_schema = """
definitions:
  main:
    types:
      event:
        properties:
          duration:
            type: time
"""
    # Valid
    yaml_data_good = """
duration: 10 s
"""
    run_eval_command(yaml_data_good, yasl_schema, "event", True)

    # Invalid unit
    yaml_data_bad = """
duration: 10 m
"""
    run_eval_command(yaml_data_bad, yasl_schema, "event", False)


def test_yasl_length_integration():
    yasl_schema = """
definitions:
  main:
    types:
      trip:
        properties:
          distance:
            type: length
"""
    # Valid
    yaml_data_good = """
distance: 15 km
"""
    run_eval_command(yaml_data_good, yasl_schema, "trip", True)

    # Invalid unit
    yaml_data_bad = """
distance: 15 kg
"""
    run_eval_command(yaml_data_bad, yasl_schema, "trip", False)


def test_yasl_mixed_physical_types():
    yasl_schema = """
definitions:
  main:
    types:
      car:
        properties:
          max_speed:
            type: velocity
          curb_weight:
            type: mass
"""
    yaml_data = """
max_speed: 120 km/h
curb_weight: 1500 kg
"""
    run_eval_command(yaml_data, yasl_schema, "car", True)

    yaml_data_bad = """
max_speed: 120 km
curb_weight: 1500 kg
"""
    run_eval_command(yaml_data_bad, yasl_schema, "car", False)


def test_yasl_complex_units_integration():
    yasl_schema = """
definitions:
  main:
    types:
      material_properties:
        properties:
          conductivity:
            type: thermal conductivity
          specific_heat:
            type: specific heat capacity
"""
    # Valid
    yaml_data_good = """
conductivity: 200 W / (m K)
specific_heat: 900 J / (kg K)
"""
    run_eval_command(yaml_data_good, yasl_schema, "material_properties", True)

    # Invalid
    yaml_data_bad = """
conductivity: 200 J
specific_heat: 900 W
"""
    run_eval_command(yaml_data_bad, yasl_schema, "material_properties", False)
