# features/yasl/steps/yasl_steps.py

import os
import subprocess
from typing import Any

from behave import given as _given
from behave import then as _then
from behave import when as _when
from behave.runner import Context

# Type cast behave decorators to Any to avoid "Object of type '_StepDecorator' is not callable" errors
given: Any = _given
when: Any = _when
then: Any = _then


def run_cli(args):
    filtered_args = [item for item in args if item is not None]
    result = subprocess.run(["yasl"] + filtered_args, capture_output=True, text=True)
    return result


@given('a YASL schema "{schema_file}" is provided')
def step_impl_schema(context: Context, schema_file: str):
    context.schema_argument = schema_file
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    print(f"Schema file: {schema_file}")


@given('a YAML document "{document_file}" is provided')
def step_impl_document(context: Context, document_file: str):
    context.document_argument = document_file
    if not os.path.exists(document_file):
        raise FileNotFoundError(f"Document file not found: {document_file}")
    print(f"Document file: {document_file}")


@given('the model name "{model_name}" is provided')
def step_impl_model_name(context: Context, model_name: str):
    context.model_name = model_name


@when("I run the YASL CLI with provided arguments")
def step_impl_run_cli(context: Context):
    # This is where your Go application's validation logic would be called
    # For now, we'll simulate success
    model_name = getattr(context, "model_name", None)

    args = ["check", context.schema_argument, context.document_argument]
    if model_name:
        args.extend(["--model", model_name])

    result = run_cli(args)
    print(f"CLI Output:\n{result.stdout}")
    context.validation_successful = result.returncode == 0


@then("the validation should pass")
def step_impl_validation_passes(context: Context):
    assert context.validation_successful is True, "Validation failed unexpectedly!"
    print("Validation passed!")


@then("the validation should fail")
def step_impl_validation_fails(context: Context):
    assert context.validation_successful is False, "Validation succeeded unexpectedly!"
    print("Validation failed as expected!")
