# YASL - YAML Advanced Schema Language

YASL is an advanced schema language & validation tools for YAML. 
It supports definition and validation of data structures with primitives, enumerations, and composition of defined types.

## Motivation

YAML is widely used for configuration, data exchange, and automation, but lacks native support for robust schema validation and type safety.
YASL addresses this gap by providing:

- **Reliable Data Validation:** Ensures YAML files conform to expected structures, reducing runtime errors and misconfigurations.
- **Strong Typing:** Enables precise definition of data types, enumerations, and constraints, improving clarity and maintainability.
- **Composability:** Supports modular schema design with namespaces and imports, making it easier to manage complex data models.
- **Developer Productivity:** Integrates with Pydantic and Python tooling, streamlining validation, error reporting, and code generation.
- **Documentation:** Schema definitions double as documentation, making data contracts explicit and discoverable.
- **Extensibility:** Designed to evolve with your needs, supporting advanced validation, referential integrity, and integration with CI/CD pipelines.

YASL empowers teams to confidently use YAML for critical workflows, ensuring data integrity and accelerating development.

## Usage

To use YASL you must first define your data schema in a YASL file as described in the Defining YASL Schemas section below.

> [!NOTE]
> YASL schemas are pure YAML, so you can use standard YAML comments and tools for editing and validation.
> YASL supports multi-doc formatting using the `---` document separator within a single file for both YASL schemas and YAML data.

### YASL CLI
Once you have a schema and a corresponding data file, you run the YASL command line tool.

```bash
yasl check <path> [path ...] [--model <model_name>]
```

YASL provides various options.
Here's the full usage info provided by the command line tool.

```bash
user@system:~/repos/myproject$ yasl -h
usage: yasl [-h] [--version] [--quiet] [--verbose] [--output {text,json,yaml}] {check,schema} ...

YASL - YAML Advanced Schema Language CLI Tool

options:
  -h, --help            show this help message and exit
  --version             Show version information and exit
  --quiet               Suppress output except for errors
  --verbose             Enable verbose output
  --output {text,json,yaml}
                        Set output format (text, json, yaml). Default is text.

commands:
  {check,schema}        Available commands
    check               Check mixed YASL schemas and YAML data
    schema              Check the validity of a YASL schema file
```

### YASL API

YASL provides an API for evaluating YAML files using your defined schemas.
API usage is effectively the same as the CLI.

```python
def yasl_eval(yasl_schema: str, yaml_data: str, model_name: str = None, disable_log: bool = False, quiet_log: bool = False, verbose_log: bool = False, output: str = "text", log_stream: StringIO = sys.stdout) -> Optional[List[BaseModel]]:
    """
    Evaluate YAML data against a YASL schema.

    Args:
        yasl_schema (str): Path to the YASL schema file or directory.
        yaml_data (str): Path to the YAML data file or directory.
        model_name (str, optional): Specific model name to use for validation. If not provided, the model will be auto-detected.
        disable_log (bool): If True, disables all logging output.
        quiet_log (bool): If True, suppresses all output except for errors.
        verbose_log (bool): If True, enables verbose logging output.
        output (str): Output format for logs. Options are 'text', 'json', or 'yaml'. Default is 'text'.
        log_stream (StringIO): Stream to which logs will be written. Default is sys.stdout.

    Returns:
        Optional[List[BaseModel]]: List of validated Pydantic models if validation is successful, None otherwise.
    """
```

The API interface is intentionally aligned directly to the CLI usage.
The simplest way to use the API is to pass in your yasl and yaml, then check the return type is not None and use the resulting data as a python object.
If the result is `None`, then an error has occurred.
If you wish to process the details of the error, you must capture the log data.
The simplest way to do this is to provide a `StringIO` object for the `log_stream` parameter and set the `output` to either `json` or `yaml` depending on your preference for parsing.

Example:
```python
from yasl import yasl_eval

yasl_log = StringIO()
# example using JSON logging
result =  yasl_eval(yasl_path, yaml_path, model_name, verbose_log=True, output="json", log_stream=yasl_log)

if not result:
  for line in yasl_log:
      line = line.strip()
      if not line:
          continue
      item = json.loads(line)
      if item.get("level") == "ERROR":
          ## handle error
          print(f"YAML validation error: {item.get('message')}")
else:
  # use parsed and validated data as a python object
  # just remember it is a list of objects
  ...
```

Data provided within the json or yaml log stream will have the following attributes:

- **level**: The log level (i.e. DEBUG, INFO, WARN, ERROR) from the python `logging` module.
- **time**: The timestamp of the entry includeing date and time.
- **name**: The name of the logger (i.e. 'yasl' in this case).
- **message**:  The log message.


## Defining YASL Schemas

At the heart of YASL is the schema definition.
The intent is to make schema definition as simple and familiar as possible by using the same YAML format that you are using for your data.
There are a few key concepts to consider when defining your YASL schema: primitives, enumerations, and data types.
Once you've mastered these, you'll want to consider things like data validation, referential integrity, and version control.

The root of a YASL schema allows you to define:

```yaml
imports:
  ...  # List of other yasl schemas to integrate.
metadata:
  ...  # Key-value pairs for your relevant information.
definitions:
  ...  # Namespaces with type and enumeration definitions.
```

All of these are optional to give you maximum flexibility.
Perhaps you have a top level YASL schema that only provides metadata and imports all definitions from other files.
Or perhaps you put all your data definitions into a single file and don't care about metadata.
The YASL schema does not constrain your content organization decision process.

### Comments

YASL is just YAML, so comments work the same way.
Start your comment with a `#` and everything after that is comment text.
You can do full or partial line comments.

### Imports

YASL schemas allow you to organize your data definitions across a collection of files.
It is recommended that you be as explicit as possible by maintaining a single 'entry point' for your data definitions.

Let's assume you have an engineering team working various products and features and a sales team delivering the resulting products and features to customers.

Your schema definitions may may look like:
  - my_team/yasl
    - main.yasl
    - product.yasl
    - features.yasl
    - customers.yasl
    - sales.yasl

The `main.yasl` might only contain imports from other schema files.
```yaml
imports:
  - product.yasl
  - features.yasl
  - customers.yasl
  - sales.yasl
```

To validate data, you can simply point to the `main.yasl` as your schema and all other content will be integrated.  
```bash
yasl ./my_team/yasl/main.yasl ./data/my_data.yaml
```

But you do have the flexibility to just put things into a directory and use all yasl files in that directory if you choose.
This would simply eliminate the `main.yasl` file from the structure above.
To validate data you would point the yasl tool to the directory containing your schemas rather than a single 'entry point'.
```bash
yasl ./my_team/yasl ./data/my_data.yaml
```

### Metadata

Metadata gives you the flexibility to capture relevant key-value pairs of data related to your schema.
This information is not used by the yasl validation processes but is available for your use in parsing or using schema data.

```yaml
metadata:
  author: John Doe
  license:  Apache 2.0
  version: 1.0.0
definitions:
  ...
```

### Namespaces

YASL data type and eunumeration definitions are always defined within a namespace.
A namespace is just a string value to support unique type naming.
Namespaces permit the same type name to be used in different contexts without creating naming conflicts.

```yaml
definitions:
  namespace_one:  # A namespace declaration.
    types:
      thing:  # A type name declearation.
        ...
  namespace_two:  # Another namespace declaration.
    types:
      thing:  # The same type name declaration, but differentiated by namespace.
        ...
```

YASL will attempt to discover and use the correct type declaration based on context, but you can explicitly reference a type using it's namespace in a dot notation (i.e. `namespace_two.thing`) to avoid naming conflicts.
Should a naming conflict arise, YASL will default to using the namespace of the referencing definition to resolve the conflict if possible.
Other naming conflicts will result in an error that you must correct by resolving the conflict in your schema.

### YASL Enumeration Definitions

YASL enumerations are a simple way to establish prefined values as a usable type for use in schemas.

An enumeration definition may look like...
```yaml
definitions:
  balloon_city:
    enums:
      color:
        values:
          - RED
          - BLUE
          - GREEN
      size:
        values:
          - SMALL
          - MEDIUM
          - LARGE
```

Once defined, enumerations can be used as types within type definitions.
Here's an example of using the above enumerations as fields within a type definition.

```yaml
definitions:
  balloon_city:
    types:
      baloon:
        description: A baloon product.
        properties:
          brand:
            type: str
            description: The brand name of the baloon.
          size:
            type: size
            description: The size of the baloon.
          color:
            type: color
            description: The color of the baloon.
```

### YASL Type Definitions

YASL intends to provide a simple but powerful means of defining complex data types for YAML data set validation.

Types are defined under the `types` key in the schema file.
Invididual types are captured as a map (or dict in python terms) with the type name being the key and the type attributes defined under that.

These type definitions have the following attributes:

- `description` (optional): str - A description of the type definition.
- `properties`: property[] - List of data fields for the type.
- `validators` (optional): validator - Special validators to establish field definition constraints.

#### Type Properties

Type definition properties allow you to establish the composition structure of YAML data within your YASL schema.
Not only do these serve to support data validation, they also provide a method of data documentation.

Properties are defined under the `properties` key in the type definition.
Individual properties are captured as a map (or dict in python terms) with the property name being the key and the property attributes defined under that.

Properties have the following attributes:

- `type`: type - The name of the primitive, enumeration, or type definition of the field (may include namespace in dot-notation for clarity).
- `description` (optional): str - A brief summary of the field.
- `presence` (optional): 'required', 'preferred', or 'optional' - If required and not present results in an error.  If preferred and not present results in a warning.  Default: 'optional'.
- `unique` (optional): bool - True if the field must be unique across all type_def uses in the data set.  Default: false.
- `default` (optional): any - The default value of the field if not provided.  The value type must match the type field.

> [!NOTE]
> The legacy `required` boolean attribute is deprecated and has been replaced by `presence`.
> Use `presence: required` instead of `required: true`.

In addition to these fields, the primitive validators from above may be included as desired based on the type.

Here's an example type definition:

```yaml
definitions:  # This is where we define our schema content.
  acme:  # This is the namespace for the defined types and enums.
    types:  # This is where we define our custom data types.
      task:  # This is a data type named 'task'.
        description: A thing to do.
        properties:
          description:
            type: str
            description: A description of the task.
            presence: required
          owner:
            type: str
            description: The person responsible for the task.
            presence: optional
          complete:
            type: bool
            description: Is the task finished? True if yes, false if no.
            presence: required
            default: false
      list_of_tasks: # This is a data type named 'list_of_tasks'.
        description: A list of tasks to complete.
        properties:
          task_list:
            type: map[taskkey, task]
            description: A list of tasks to do.
            presence: required

    enums:  # This is where we define our enumerated types.
      taskkey:  # This is the name of an enumerated type.
        description: Allowed task names within the task_list.
        values:
          - task_01
          - task_02
          - task_03
```

#### Type Validators

YASL recognizes there can be complexities and conditionals to consider when defining data types.
Type validators allow you to establish constraints on your type definitions.
The available validators provide for the basic definition of common data constraints in your schema.

YASL provides the following type validators:

- `only_one`: str[] - List of mutually exclusive property names where only one may be present.
- `at_least_one`: str[] - List of property names where one or more must be present.
- `if_then`: IfThen[] - List of conditional checks.
  - `eval`: str - Name of a property in the `type_def`.
  - `value`: str[] - List of values to compare to `eval` for equivalence (i.e. `true` for a bool, `42` for int, etc.).
  - `present`: str[] (optional) - list of property names in the `type_def` that must be present if the check is `true`.
  - `absent`: str[] (optional) - list of property names in the `type_def` that must be absent of the check is `true`.  Default: none.

### YASL Primitives

YASL supports the "normal" primitive types as well as a few "extended" types commonly used in modern data sets.
These should be immediately familiar.
YASL takes one further step by defining optional validators for each primitive type which can be provided as part of the field definition.
The following sections define each of the YASL primitives and the associated validators.

#### String

A string is text, generally alphanumeric and special characters.
YASL uses the same string handling as YAML.
The string primitive is represented by the type name `str` when defining fields in schemas.

String validators include:

- `str_min`: int - The minimum length of the string. Default: none.
- `str_max`: int - The maximum length of the string. Default: none.
- `str_regex`: str[] - List of regular expression validation rules. Default: none.

#### Integer

An integer is a whole number value.
YASL uses the same integer handling as YAML.
The integer primitive is represented by the type name `int` when defining fields in schemas.

Integer validators include:

- `gt`: int - Value must be greater than the parameter.
- `ge`: int - Value must be greater than or equal to the parameter.
- `lt`: int - Value must be less than the parameter.
- `le`: int - Value must be less than or equal to the parameter.
- `exclude`: int[] - List of unallowed values.  Default: none.
- `multiple_of`: int - Value must be a multiple of the parameter.

#### Float

A number is a floating point number value.
YASL uses the same number handling as YAML.
The number primitive is represented by the type name `float` when defining fields in schemas.

Float validators include:

- `gt`: int - Value must be greater than the parameter.
- `ge`: int - Value must be greater than or equal to the parameter.
- `lt`: int - Value must be less than the parameter.
- `le`: int - Value must be less than or equal to the parameter.
- `exclude`: int[] - List of unallowed values.  Default: none.
- `multiple_of`: int - Value must be a multiple of the parameter.
- `whole_number`: bool - Force the float to be a whole number (i.e. no decimal places).

#### Boolean

A boolean is a true / false value.
YASL uses the same boolean handling as YAML.
The boolean primitive is represented by the type name `bool` when defining fields in schemas.

There are no YASL validators for boolean values.

#### Date

A date is a date formatted value.
YASL uses ISO 8601 formatting for date types.
The date primitive is represented by the type name `date` when defining fields in schemas.

Date validators include:

- `before`: date - Require value to be before a specific date.  Default: none.
- `after`: date - Require value to be after a specific date.  Default: none.

#### Time

A time is a time formatted value.
YASL uses ISO 8601 formatting for date types.
The time primitive is represented by the type name `time` when defining fields in schemas.

Time validators include:

- `before`: time - Require value to be before a specific time.  Default: none.
- `after`: time - Require value to be after a specific time.  Default: none.

#### Datetime

A datetime is a datetime formatted value.
YASL uses ISO 8601 formatting for date types.
The datetime primitive is represented by the type name `datetime` when defining fields in schemas.

Datetime validators include:

- `before`: datetime - Require value to be before a specific datetime.  Default: none.
- `after`: datetime - Require value to be after a specific datetime.  Default: none.

#### Path

A path is a file system location value.
YASL uses Linux path formatting (i.e. directory/directory/file.ext) for path types.
The path primitive is represented by the type name `path` when defining fields in schemas.

Path validators include:

- `path_exists`: bool - Require value to be present on the file system.  Default: false.
- `is_dir`: bool - Requires value to be a directory and exist on the file system.  Default: false.
- `is_file`: bool - Requires value to be a file and exist on the file system. Default: false.
- `file_ext`: str[] - A list of permitted file extensions.

#### URL

A URL is a universal record locator value as commonly used for internet addresses.
YASL accepts a URL as any string that can be resolved as a network location, including protocol, port, address, etc.
The url primitive is represented by the type name `url` when defining fields in schemas.

URL validators include:

- `url_base`: str - The required base value for the URL (i.e. www.mycompany.com).  Default: none.
- `url_protocols`: str[] - List of allowable network protocols (i.e. http, https). Default: none.
- `url_reachable`: bool - Require the value to be reachable on the current network (i.e. Status=200 for HTTP). Default: false.

#### Reference

A reference is used to refer to a data element within the YAML being evaluated by YASL.
The ref primitive is represented by the type name `ref[target]` where target specified the custom type and field being referenced.
These target fields must be unique as designated by the `unique` attribute in the target field to avoid value collisions.
YASL expects the value to exist in the YAML being evaluated, but this can be overridden by setting `no_ref_check = true` in the property definition for the reference.

#### Map

A map allows for dynamic keys within the YAML structure.
A map primitive is represented by the type name `map[key_type, value_type]` where key_type is a string, int, or enum type and value_type is any valid YASL type.

#### Any

An any is a catch all that allow the value to be of any type.
The any primitive is represented by the type name `any` when defining fields in schemas.

Any validators include:

- `any_of`: str[] - List of allowed type names for the any field.

#### Pydantic Types

YASL supports all [Pydantic types](https://docs.pydantic.dev/latest/api/types/) [and Pydantic Network types](https://docs.pydantic.dev/latest/api/networks/).


