import os
import tempfile
from io import StringIO

from yasl import yasl_eval


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
            assert yasl_model is None
            assert "❌" in test_log.getvalue()
        else:
            if yasl_model is None:
                print(test_log.getvalue())
            assert yasl_model is not None
            assert "data validation successful" in test_log.getvalue()


def test_map_type_ref_value_good():
    yasl = """
metadata:
  name: map_ref_test
  description: Testing map with ref value
definitions:
  map_ref_test:
    types:
      model:
        properties:
          name:
            type: str
            presence: required
            unique: true
      input:
        properties:
          data:
            type: map[str, ref[model.name]]
            presence: required
"""
    yaml_data = """
name: item1
---
data:
  key1: item1
"""
    run_eval_command(yaml_data, yasl, None, True)
