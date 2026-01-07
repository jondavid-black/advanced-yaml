import os
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest
from schema_data import (
    CUSTOMER_LIST_YASL,
    MARKDOWN_YASL,
    NAMESPACE_CUSTOMER_LIST_YASL,
    PERSON_ADDRESS_MULTI_YASL,
    PERSON_WEBSITE_REACHABLE_YAML,
    PERSON_YASL,
    PYDANTIC_TYPES_YASL,
    REF_LIST_YASL,
    SHAPE_YASL,
    TASK_BAD_NAMESPACE_REF_YASL,
    TODO_BAD_MAP_VALUE_YASL,
    TODO_BOOL_MAP_YASL,
    TODO_DOT_NAMESPACE_YASL,
    TODO_ENUM_MAP_YASL,
    TODO_INT_MAP_YASL,
    TODO_MIXED_NAMESPACE_YASL,
    TODO_NESTED_MAP_YASL,
    TODO_YASL,
)

from yasl import yasl_eval
from yasl.cli import main as yasl_cli_main


def run_cli(args):
    filtered_args = [item for item in args if item is not None]
    result = subprocess.run(["yasl"] + filtered_args, capture_output=True, text=True)
    return result


def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["yasl", "--version"])
    with pytest.raises(SystemExit) as e:
        yasl_cli_main()
    assert e.value.code == 0
    captured = capsys.readouterr()
    assert "YASL version" in captured.out


def test_cli_quiet_and_verbose(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["yasl", "--quiet", "--verbose", "check", "file.yasl", "data.yaml"]
    )
    with pytest.raises(SystemExit) as e:
        yasl_cli_main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "❌ Cannot use both --quiet and --verbose." in captured.out


def test_cli_missing_args(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["yasl", "check"])
    with pytest.raises(SystemExit) as e:
        yasl_cli_main()
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "the following arguments are required" in captured.err


def test_cli_good(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "yasl",
            "check",
            "./features/yasl/data/todo.yasl",
            "./features/yasl/data/todo.yaml",
            "--model",
            "list_of_tasks",
        ],
    )
    with pytest.raises(SystemExit) as e:
        yasl_cli_main()
    assert e.value.code == 0


def test_quiet_and_verbose():
    result = run_cli(["--quiet", "--verbose", "check", "file.yasl", "file.yaml"])
    assert result.returncode != 0
    assert "Cannot use both" in result.stdout


def run_eval_command(yaml_data, yasl_schema, model_name, expect_valid):
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "test.yaml")
        yasl_path = os.path.join(tmpdir, "test.yasl")
        with open(yaml_path, "w") as f:
            f.write(yaml_data)
        with open(yasl_path, "w") as f:
            f.write(yasl_schema)

        run_eval_command_with_paths(yaml_path, yasl_path, model_name, expect_valid)


def run_eval_command_with_paths(yaml_path, yasl_path, model_name, expect_valid):
    # Test via the API
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
        assert yasl_model is not None
        assert "data validation successful" in test_log.getvalue()

    # Test via the CLI
    cli_args = ["check", yasl_path, yaml_path]
    if model_name:
        cli_args.extend(["--model", model_name])

    result = run_cli(cli_args)
    if not expect_valid:
        assert result.returncode != 0
        assert "❌" in result.stdout
    else:
        assert result.returncode == 0
        assert "data validation successful" in result.stdout


def test_eval_nested_types_and_enum():
    yaml_data = """
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: active
  - name: Joe Smith
    age: 40
    email: joe@example.com
    status: inactive
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "customer_list", True)


def test_eval_nested_types_with_bad_enum():
    yaml_data = """
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: unknown
  - name: Joe Smith
    age: 40
    email: joe@example.com
    status: inactive
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "customer_list", False)


def test_eval_non_unique():
    yaml_data = """
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: unknown
  - name: Bob Smith
    age: 40
    email: joe@example.com
    status: inactive
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "customer_list", False)


def test_eval_business_good():
    yaml_data = """
business_name: Acme Corporation
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: inactive
  - name: Alice Johnson
    age: 25
    email: alice@example.com
    status: active
accounts:
  - id: ACC123
    account_rep: John Doe
    customer_name: Bob Smith
  - id: ACC456
    account_rep: Jane Doe
    customer_name: Alice Johnson
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "business", True)


def test_eval_business_namespace_good():
    yaml_data = """
business_name: Acme Corporation
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: inactive
  - name: Alice Johnson
    age: 25
    email: alice@example.com
    status: active
accounts:
  - id: ACC123
    account_rep: John Doe
    customer_name: Bob Smith
  - id: ACC456
    account_rep: Jane Doe
    customer_name: Alice Johnson
"""
    yasl_schema = NAMESPACE_CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "business", True)


def test_eval_business_bad_ref():
    yaml_data = """
business_name: Acme Corporation
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: inactive
  - name: Alice Johnson
    age: 25
    email: alice@example.com
    status: active
accounts:
  - id: ACC123
    account_rep: John Doe
    customer_name: Dan Smith
  - id: ACC456
    account_rep: Jane Doe
    customer_name: Alice Johnson
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "business", False)


def test_eval_min_list():
    yaml_data = """
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: active
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "customer_list", False)


def test_eval_max_list():
    yaml_data = """
customers:
  - name: Bob Smith
    age: 30
    email: bob@example.com
    status: active
  - name: Joe Smith
    age: 30
    email: joe@example.com
    status: active
  - name: Tom Smith
    age: 30
    email: tom@example.com
    status: active
  - name: Rob Smith
    age: 30
    email: rob@example.com
    status: active
"""
    yasl_schema = CUSTOMER_LIST_YASL
    run_eval_command(yaml_data, yasl_schema, "customer_list", False)


def test_eval_person_good():
    yaml_data = """
name: John Doe
age: 20
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_age_too_small():
    yaml_data = """
name: John Doe
age: 10
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_age_too_big():
    yaml_data = """
name: John Doe
age: 130
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_age_excluded():
    yaml_data = """
name: John Doe
age: 64
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_age_float():
    yaml_data = """
name: John Doe
age: 34.2
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_age_odd():
    yaml_data = """
name: John Doe
age: 35
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_name_short():
    yaml_data = """
name: Joe
age: 24
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_name_long():
    yaml_data = """
name: Joseph Reginold Smithington the Third
age: 24
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_name_invalid():
    yaml_data = """
name: Joe-Smith123
age: 24
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_birthday_good():
    yaml_data = """
name: Joe Smith
age: 24
birthday: 1970-01-01
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_birthday_before():
    yaml_data = """
name: Joe Smith
age: 24
birthday: 1800-01-01
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_birthday_after():
    yaml_data = """
name: Joe Smith
age: 24
birthday: 2800-01-01
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_favorite_time_good():
    yaml_data = """
name: Joe Smith
age: 24
favorite_time: 12:30:00
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_favorite_time_early():
    yaml_data = """
name: Joe Smith
age: 24
favorite_time: 06:30:00
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_favorite_time_late():
    yaml_data = """
name: Joe Smith
age: 24
favorite_time: 16:30:00
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_office_int_good():
    yaml_data = """
name: Joe Smith
age: 24
office: 42
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_office_bool_good():
    yaml_data = """
name: Joe Smith
age: 24
office: true
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_office_str():
    yaml_data = """
name: Joe Smith
age: 24
office: please
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_office_float():
    yaml_data = """
name: Joe Smith
age: 24
office: 33.3
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_bio_good():
    yaml_data = """
name: Joe Smith
age: 24
bio: ./myfile.txt
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_bio_bad_ext():
    yaml_data = """
name: Joe Smith
age: 24
bio: ./myfile.docx
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_home_dir_good():
    yaml_data = f"""
name: Joe Smith
age: 24
home_directory: {os.getcwd()}
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_home_dir_not_exist():
    yaml_data = """
name: Joe Smith
age: 24
home_directory: /not/a/real/dir
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_website_good():
    yaml_data = """
name: Joe Smith
age: 24
website: https://www.example.com/joe_smith
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_website_bad_protocol():
    yaml_data = """
name: Joe Smith
age: 24
website: ftp://www.example.com/joe_smith
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_website_reachable():
    yasl_schema = PERSON_WEBSITE_REACHABLE_YAML
    yaml_data = """
name: Joe Smith
website: https://www.google.com
"""
    run_eval_command(yaml_data, yasl_schema, "person", True)


def test_eval_website_bad_base():
    yaml_data = """
name: Joe Smith
age: 24
website: ftp://www.notexample.com/joe_smith
"""
    yasl_schema = PERSON_YASL
    run_eval_command(yaml_data, yasl_schema, "person", False)


def test_eval_shape_good():
    yaml_data = """
name: bob
type: square
side_length: 10.0
color: red
location: top-left
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", True)


def test_eval_shape_only_one_fail():
    yaml_data = """
name: bob
type: square
side_length: 10.0
color: red
colour: blue
location: top-left
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", False)


def test_eval_shape_at_least_one_fail():
    yaml_data = """
name: bob
type: square
side_length: 10.0
color: red
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", False)


def test_eval_shape_if_then_1_fail():
    yaml_data = """
name: bob
type: circle
side_length: 10.0
color: red
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", False)


def test_eval_shape_if_then_2_fail():
    yaml_data = """
name: bob
type: square
radius: 10.0
color: red
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", False)


def test_eval_shape_if_then_3_fail():
    yaml_data = """
name: bob
type: triangle
radius: 10.0
color: red
"""
    yasl_schema = SHAPE_YASL
    run_eval_command(yaml_data, yasl_schema, "shape", False)


def test_version_command():
    result = run_cli(["--version"])
    assert result.returncode == 0
    assert "YASL version" in result.stdout


def test_pydantic_types():
    yasl = PYDANTIC_TYPES_YASL
    yaml_data = """
id: test
strict_bool: true
markdown: |
  # Hello World
  This is some random markdown.
  [Link to Google](https://www.google.com)
positive_int: 42
negative_int: -42
non_positive_int: -1
non_negative_int: 0
strict_int: 100
positive_float: 3.14
negative_float: -3.14
non_positive_float: -0.1
non_negative_float: 0.0
strict_float: 2.718
finite_float: 1.618
strict_str: "Hello, World!"
uuid1: "550e8400-e29b-11d4-a716-446655440000"
uuid3: "550e8400-e29b-31d4-a716-446655440000"
uuid4: "550e8400-e29b-41d4-a716-446655440000"
uuid5: "550e8400-e29b-51d4-a716-446655440000"
uuid6: "550e8400-e29b-61d4-a716-446655440000"
uuid7: "550e8400-e29b-71d4-a716-446655440000"
uuid8: "550e8400-e29b-81d4-a716-446655440000"
file_path: "./features/yasl/data/thing.yaml"
directory_path: "./features/yasl/data/"
base64_bytes: "SGVsbG8sIFdvcmxkIQ=="
base64_str: "SGVsbG8sIFdvcmxkIQ=="
base64_url_bytes: "SHc_dHc-TXc=="
base64_url_str: "SHc_dHc-TXc=="
any_url: "https://example.com"
any_http_url: "http://example.com"
http_url: "http://example.com"
any_websocket_url: "ws://example.com/socket"
websocket_url: "ws://example.com/socket"
file_url: "file:///path/to/file.txt"
ftp_url: "ftp://example.com/resource"
postgres_dsn: "postgresql://user:password@localhost:5432/dbname"
cockroach_dsn: "cockroachdb://user:password@localhost:26257/dbname"
amqp_dsn: "amqp://user:password@localhost:5672/vhost"
redis_dsn: "redis://localhost:6379/0"
mongo_dsn: "mongodb://mongodb0.example.com:27017"
kafka_dsn: "kafka://localhost:9092"
nats_dsn: "nats://localhost:4222"
mysql_dsn: "mysql://user:password@localhost:3306/dbname"
mariadb_dsn: "mariadb://user:password@localhost:3306/dbname"
clickhouse_dsn: "clickhouse://user:password@localhost:8123/dbname"
snowflake_dsn: "snowflake://user:password@account/dbname/schema?warehouse=wh"
email_str: "user@example.com"
name_email: "User <user@example.com>"
ipvany_address: "192.0.2.1"
"""
    run_eval_command(yaml_data, yasl, "thing", True)


def test_dir_inputs_good():
    yasl_path = "./features/yasl/data/dir_test"
    yaml_path = "./features/yasl/data/dir_test"
    # cwd = os.getcwd()
    # os.chdir(str((Path(__file__).parent.parent.parent / "features").resolve()))
    run_eval_command_with_paths(
        str(Path(yasl_path).absolute()), str(Path(yaml_path).absolute()), None, True
    )
    # os.chdir(cwd)


def test_dir_inputs_bad():
    yasl_path = "./features/yasl/data/bad_dir_test"
    yaml_path = "./features/yasl/data/bad_dir_test"
    # cwd = os.getcwd()
    # os.chdir(str((Path(__file__).parent.parent.parent / "features").resolve()))
    run_eval_command_with_paths(
        str(Path(yasl_path).absolute()), str(Path(yaml_path).absolute()), None, False
    )
    # os.chdir(cwd)


def test_map_type__str_good():
    yasl = TODO_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_02:
    description: Lead morning standup.
    owner: Jim
    complete: false
  task_03:
    description: Refine Backlog.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", True)


def test_map_type_int_good():
    yasl = TODO_INT_MAP_YASL
    yaml_data = """
task_list:
  1:
    description:  Buy coffee.
    owner: Jim
    complete: false
  2:
    description: Lead morning standup.
    owner: Jim
    complete: false
  3:
    description: Refine Backlog.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", True)


def test_map_type_bool_bad():
    yasl = TODO_BOOL_MAP_YASL
    yaml_data = """
task_list:
  true:
    description:  Buy coffee.
    owner: Jim
    complete: false
  false:
    description: Lead morning standup.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", False)


def test_map_type_bad():
    yasl = TODO_BAD_MAP_VALUE_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_02:
    description: Lead morning standup.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", False)


def test_map_type_enum_key_good():
    yasl = TODO_ENUM_MAP_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_02:
    description: Lead morning standup.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", True)


def test_map_type_enum_value_bad():
    yasl = TODO_ENUM_MAP_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_03:
    description: Lead morning standup.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", False)


def test_map_nested_value_namespace_good():
    yasl = TODO_MIXED_NAMESPACE_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_02:
    description: Lead morning standup.
    owner: Jim
    complete: false
  task_03:
    description: Refine Backlog.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", True)


def test_map_nested_value_good():
    yasl = TODO_NESTED_MAP_YASL
    yaml_data = """
project_name: Important Project
features:
  - feature: Initial Setup
    task_list:
      task_01:
        description:  Buy coffee.
        owner: Jim
        complete: false
      task_02:
        description: Lead morning standup.
        owner: Jim
        complete: false
"""
    run_eval_command(yaml_data, yasl, "project", True)


def test_empty_markdown():
    yasl = MARKDOWN_YASL
    yaml_data = """
id: test
markdown: ""
"""
    run_eval_command(yaml_data, yasl, "thing", False)


def test_namespace_refs_bad():
    yasl = TASK_BAD_NAMESPACE_REF_YASL
    yaml_data = """
task_list:
  1:
    description:  Buy coffee.
    owner: Jim
    complete: false
  2:
    description: Lead morning standup.
    owner: Jim
    complete: false
  3:
    description: Refine Backlog.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", False)


def test_default_namespace():
    yasl_path = "./features/yasl/data/ambiguous_ns/todo01.yasl"
    yaml_path = "./features/yasl/data/ambiguous_ns/todo.yaml"
    run_eval_command_with_paths(
        str(Path(yaml_path).absolute()),
        str(Path(yasl_path).absolute()),
        "task_list",
        True,
    )


def test_dot_in_namespace():
    yasl = TODO_DOT_NAMESPACE_YASL
    yaml_data = """
task_list:
  task_01:
    description:  Buy coffee.
    owner: Jim
    complete: false
  task_02:
    description: Lead morning standup.
    owner: Jim
    complete: false
  task_03:
    description: Refine Backlog.
    owner: Jim
    complete: false
"""
    run_eval_command(yaml_data, yasl, "list_of_tasks", True)


def test_multi_doc_yaml():
    yasl = PERSON_YASL
    yaml_data = """
name: John Doe
age: 30
birthday: 1975-11-01
office: 55
---
name: Jane Doe
age: 28
birthday: 1975-11-02
office: 54
"""
    run_eval_command(yaml_data, yasl, "person", True)


def test_multi_doc_yasl():
    yasl = PERSON_ADDRESS_MULTI_YASL
    yaml_data = """
name: John Doe
age: 30
birthday: 1975-11-01
office: 55
"""
    run_eval_command(yaml_data, yasl, "person", True)


def test_multi_yasl_and_multi_doc_yaml():
    yasl = PERSON_ADDRESS_MULTI_YASL
    yaml_data = """
name: John Doe
age: 30
birthday: 1975-11-01
office: 55
---
name: Jane Doe
age: 28
birthday: 1975-11-02
office: 54
"""
    run_eval_command(yaml_data, yasl, "person", True)


def test_ref_list():
    yasl = REF_LIST_YASL
    yaml_data = """
item_name: apple
---
item_name: banana
---
item_name: cherry
---
item_list:
  - apple
  - cherry
"""
    run_eval_command(yaml_data, yasl, None, True)


def test_ref_list_bad_ref():
    yasl = REF_LIST_YASL
    yaml_data = """
item_name: apple
---
item_name: banana
---
item_name: cherry
---
item_list:
  - apple
  - dragonfruit
"""
    run_eval_command(yaml_data, yasl, None, False)
