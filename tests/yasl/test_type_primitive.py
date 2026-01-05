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
            assert yasl_model is None, (
                f"Expected validation failure, but got success. Log:\n{test_log.getvalue()}"
            )
            assert "❌" in test_log.getvalue()
        else:
            assert yasl_model is not None, (
                f"Expected validation success, but got failure. Log:\n{test_log.getvalue()}"
            )
            assert "data validation successful" in test_log.getvalue()


def test_type_primitive_basic():
    yasl_schema = """
definitions:
  main:
    types:
      Config:
        properties:
          target_type:
            type: type
"""
    # Valid: pointing to a primitive
    yaml_data_int = """
target_type: int
"""
    run_eval_command(yaml_data_int, yasl_schema, "Config", True)

    # Valid: pointing to another primitive
    yaml_data_str = """
target_type: str
"""
    run_eval_command(yaml_data_str, yasl_schema, "Config", True)

    # Invalid: pointing to unknown type
    yaml_data_bad = """
target_type: UnknownType
"""
    run_eval_command(yaml_data_bad, yasl_schema, "Config", False)


def test_type_primitive_complex_syntax():
    yasl_schema = """
definitions:
  main:
    types:
      Config:
        properties:
          schema_def:
            type: type
"""
    # Valid: list syntax
    yaml_data_list = """
schema_def: int[]
"""
    run_eval_command(yaml_data_list, yasl_schema, "Config", True)

    # Valid: map syntax
    yaml_data_map = """
schema_def: map[str, int]
"""
    run_eval_command(yaml_data_map, yasl_schema, "Config", True)

    # Valid: ref syntax
    yaml_data_ref = """
schema_def: ref[SomeType.some_prop]
"""
    run_eval_command(yaml_data_ref, yasl_schema, "Config", True)


def test_type_primitive_user_types():
    yasl_schema = """
definitions:
  main:
    types:
      User:
        properties:
          name:
            type: str
      Group:
        properties:
          members:
            type: User[]

      MetaConfig:
        properties:
          entity_type:
            type: type
"""
    # Valid: referring to User type
    yaml_data_user = """
entity_type: User
"""
    run_eval_command(yaml_data_user, yasl_schema, "MetaConfig", True)

    # Valid: referring to Group type
    yaml_data_group = """
entity_type: Group
"""
    run_eval_command(yaml_data_group, yasl_schema, "MetaConfig", True)

    # Valid: referring to list of User
    yaml_data_user_list = """
entity_type: User[]
"""
    run_eval_command(yaml_data_user_list, yasl_schema, "MetaConfig", True)


def test_type_primitive_namespaces():
    yasl_schema = """
definitions:
  auth:
    types:
      Credentials:
        properties:
          token:
            type: str

  main:
    types:
      AppConfig:
        properties:
          auth_model:
            type: type
"""
    # Valid: referring to type in another namespace
    yaml_data_ns = """
auth_model: auth.Credentials
"""
    run_eval_command(yaml_data_ns, yasl_schema, "AppConfig", True)

    # Invalid: missing namespace (should suggest it)
    yaml_data_missing_ns = """
auth_model: Credentials
"""
    # This will fail validation, and ideally the log contains the suggestion "Did you mean one of: auth"
    # usage of run_eval_command here just asserts failure/success
    run_eval_command(yaml_data_missing_ns, yasl_schema, "AppConfig", False)
