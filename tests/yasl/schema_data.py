CUSTOMER_LIST_YASL = """
definitions:
  acme:
    description: Acme Corporation schema definitions.
    enums:
      customer_status:
        description: The status of the customer.
        values:
          - active
          - inactive
    types:
      customer:
        description: Information about a customer.
        properties:
          name:
            type: str
            description: The customer's name.
            presence: required
            unique: true
          age:
            type: int
            description: The customer's age.
            presence: optional
          email:
            type: str
            description:  The customer's email address.
            presence: required
          status:
            type: customer_status
            description: The customer's status.
            presence: required
      customer_list:
        description: A list of customers.
        properties:
          customers:
            type: customer[]
            description: Information about a customer.
            list_min: 2
            list_max: 3
      account:
        description: Information about an account.
        properties:
          id:
            type: str
            description: The unique identifier for the account.
            presence: required
          account_rep:
            type: str
            description: The name of the account representative.
            presence: required
          customer_name:
            type: ref[customer.name]
            description: The name of the customer associated with the account.
            presence: required
      business:
        description: A list of accounts.
        properties:
          business_name:
            type: str
            description: The name of the business.
            presence: required
          customers:
            type: customer[]
            description: Information about a list of customers.
            presence: required
          accounts:
            type: account[]
            description: Information about an account.
            presence: required
"""

NAMESPACE_CUSTOMER_LIST_YASL = """
definitions:
    acme:
        description: Acme Corporation schema definitions.
        enums:
            customer_status:
                description: The status of the customer.
                values:
                    - active
                    - inactive
        types:
            customer:
                description: Information about a customer.
                properties:
                    name:
                        type: str
                        description: The customer's name.
                        presence: required
                        unique: true
                    age:
                        type: int
                        description: The customer's age.
                        presence: optional
                    email:
                        type: str
                        description:  The customer's email address.
                        presence: required
                    status:
                        type: customer_status
                        description: The customer's status.
                        presence: required
            customer_list:
                description: A list of customers.
                properties:
                    customers:
                        type: acme.customer[]
                        description: Information about a customer.
                        list_min: 2
                        list_max: 3
            account:
                description: Information about an account.
                properties:
                    id:
                        type: str
                        description: The unique identifier for the account.
                        presence: required
                    account_rep:
                        type: str
                        description: The name of the account representative.
                        presence: required
                    customer_name:
                        type: ref[acme.customer.name]
                        description: The name of the customer associated with the account.
                        presence: required
            business:
                description: A list of accounts.
                properties:
                    business_name:
                        type: str
                        description: The name of the business.
                        presence: required
                    customers:
                        type: acme.customer[]
                        description: Information about a list of customers.
                        presence: required
                    accounts:
                        type: acme.account[]
                        description: Information about an account.
                        presence: required
"""

PERSON_YASL = """
definitions:
    acme:
        description: Acme Corporation schema definitions.
        types:
            person:
                description: Information about a person.
                properties:
                    name:
                        type: str
                        description: The person's name.
                        presence: required
                        str_min: 5
                        str_max: 15
                        str_regex: '^[A-Za-z ]+$'
                    age:
                        type: int
                        description: The person's age.
                        presence: required
                        ge: 18
                        lt: 125
                        whole_number: true
                        multiple_of: 2
                        exclude:
                            - 64
                    birthday:
                        type: date
                        description: The person's birthday.
                        presence: optional
                        after: "1900-01-01"
                        before: "2050-12-31"
                    favorite_time:
                        type: clocktime
                        description: The person's favorite time of day.
                        presence: optional
                    office:
                        type: any
                        description: The person's office number, or true / false to indicate need.
                        presence: optional
                        any_of:
                            - int
                            - bool
                    bio:
                        type: path
                        description: Path to a bio file.
                        presence: optional
                        is_file: true
                        path_exists: false
                        file_ext:
                            - txt
                            - md
                    home_directory:
                        type: path
                        description: Path to the person's home directory.
                        presence: optional
                        is_dir: true
                        path_exists: true
                    website:
                        type: url
                        description: The person's website.
                        presence: optional
                        url_base: www.example.com
                        url_protocols:
                            - http
                            - https
"""

PERSON_ADDRESS_MULTI_YASL = """
definitions:
  acme:
    types:
      address:
        description: Information about an address.
        properties:
          street:
            type: str
            description: The street address.
            presence: required
          city:
            type: str
            description: The city.
            presence: optional
          zip_code:
            type: PositiveInt
            description: The postal code.
            presence: required
          other:
            type: str[]
            description: The name by which the address is known.
            presence: required
---
definitions:
  acme:
    types:
      person:
        description: Information about a person.
        properties:
          name:
            type: str
            description: The person's name.
            presence: required
          age:
            type: int
            description: The person's age.
            presence: required
            ge: 18
            lt: 125
            whole_number: true
            exclude:
              - 65
          birthday:
            type: date
            description: The person's birthday.
            presence: optional
            after: "1900-01-01"
            before: "2050-12-31"
          favorite_time:
            type: clocktime
            description: The person's favorite time of day.
            presence: optional
            after: "11:00:00"
            before: "15:00:00"
          office:
            type: any
            description: The person's office location.
            presence: optional
            any_of:
              - int
              - bool
          bio:
            type: path
            description: Path to a file containing the person's biography.
            presence: optional
            path_exists: false
            is_file: true
            file_ext:
              - txt
              - .md
          home_directory:
            type: path
            description: Path to the person's home directory.
            presence: optional
            path_exists: true
            is_dir: true
          website:
            type: url
            description: The person's website.
            presence: optional
            url_protocols:
              - http
              - https
          address:
            type: address
            description: The person's address.
            presence: optional
"""

PERSON_WEBSITE_REACHABLE_YAML = """
definitions:
    acme:
        description: Acme Corporation schema definitions.
        types:
            person:
                description: Information about a person.
                properties:
                    name:
                        type: str
                        description: The person's name.
                        presence: required
                        str_min: 5
                        str_max: 15
                        str_regex: '^[A-Za-z ]+$'
                    website:
                        type: url
                        description: The person's website.
                        presence: required
                        url_reachable: true
"""

SHAPE_YASL = """
definitions:
  acme:
    types:
      shape:
        description: Information about a shape.
        properties:
          name:
              type: str
              description: The name of the shape.
              presence: required
          type:
              type: ShapeType
              description: The type of shape.
              presence: required
          radius:
              type: float
              description: The radius of the circle.
              presence: optional
              gt: 0
          side_length:
              type: float
              description: The length of the side of the square or triangle.
              presence: optional
              gt: 0
          color:
              type: str
              description: The color of the shape.
              presence: optional
          colour:
              type: str
              description: The color of the shape (British spelling).
              presence: optional
          location:
              type: str
              description: The location of the shape.
              presence: optional
          orientation:
              type: str
              description: The orientation of the shape.
              presence: optional
        validators:
          only_one:
            - color
            - colour
          at_least_one:
            - location
            - orientation
          if_then:
            - eval: type
              value:
                - circle
              present:
                - radius
              absent:
                - side_length
            - eval: type
              value:
                - square
                - triangle
              present:
                - side_length
              absent:
                - radius
    enums:
      ShapeType:
        description: The type of shape.
        values:
          - circle
          - square
          - triangle
"""

TODO_YASL = """
definitions:
    dynamic:
        types:
            task:
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
            list_of_tasks:
                description: A list of tasks to complete.
                properties:
                    task_list:
                        type: map[str, task]
                        description: A list of tasks to do.
                        presence: required
"""

TODO_ENUM_MAP_YASL = """
definitions:
    dynamic:
        types:
            task:
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
            list_of_tasks:
                description: A list of tasks to complete.
                properties:
                    task_list:
                        type: map[taskkey, task]
                        description: A list of tasks to do.
                        presence: required
        enums:
            taskkey:
                description: The type of shape.
                values:
                - task_01
                - task_02
"""

TODO_MIXED_NAMESPACE_YASL = """
definitions:
    something:
        types:
            task:
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
    dynamic:
        types:
            list_of_tasks:
                description: A list of tasks to complete.
                properties:
                    task_list:
                        type: map[other.taskkey, something.task]
                        description: A list of tasks to do.
                        presence: required
    other:
        enums:
            taskkey:
                description: The type of task.
                values:
                - task_01
                - task_02
                - task_03
"""

TODO_NESTED_MAP_YASL = """
definitions:
    dynamic:
        types:
            task:
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
            feature:
                description: A list of tasks to complete.
                properties:
                    feature:
                        type: str
                        description: The feature name.
                        presence: required
                    task_list:
                        type: map[str, task]
                        description: A list of tasks to do.
                        presence: required
            project:
                description: A project with tasks.
                properties:
                    project_name:
                        type: str
                        description: The name of the project.
                        presence: required
                    features:
                        type: feature[]
                        description: The tasks for the project.
                        presence: required
"""

TODO_INT_MAP_YASL = """
definitions:
    dynamic:
        types:
            task:
                description: A thing to do.
                namespace: dynamic
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
            list_of_tasks:
                description: A list of tasks to complete.
                namespace: dynamic
                properties:
                    task_list:
                        type: map[int, task]
                        description: A list of tasks to do.
                        presence: required
"""

TODO_BOOL_MAP_YASL = """
definitions:
    dynamic:
        types:
            task:
                description: A thing to do.
                namespace: dynamic
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
            list_of_tasks:
                description: A list of tasks to complete.
                namespace: dynamic
                properties:
                    task_list:
                        type: map[bool, task]
                        description: A list of tasks to do.
                        presence: required
"""

TODO_BAD_MAP_VALUE_YASL = """
definitions:
    dynamic:
        types:
            task:
                description: A thing to do.
                namespace: dynamic
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
            list_of_tasks:
                description: A list of tasks to complete.
                namespace: dynamic
                properties:
                    task_list:
                        type: map[str, junktask]
                        description: A list of tasks to do.
                        presence: required
"""

PYDANTIC_TYPES_YASL = """
definitions:
    pydantic:
        types:
            thing:
                description: Information about a thing.
                properties:
                    id:
                        type: str
                        description: The unique identifier for the thing.
                        presence: required
                    strict_bool:
                        type: StrictBool
                        description: A strict boolean value.
                        presence: optional
                    markdown:
                        type: markdown
                        description: A markdown value
                        presence: optional
                    positive_int:
                        type: PositiveInt
                        description: A positive integer value.
                        presence: optional
                    negative_int:
                        type: NegativeInt
                        description: A negative integer value.
                        presence: optional
                    non_positive_int:
                        type: NonPositiveInt
                        description: A non-positive integer value.
                        presence: optional
                    non_negative_int:
                        type: NonNegativeInt
                        description: A non-negative integer value.
                        presence: optional
                    strict_int:
                        type: StrictInt
                        description: A strict integer value.
                        presence: optional
                    positive_float:
                        type: PositiveFloat
                        description: A positive float value.
                        presence: optional
                    negative_float:
                        type: NegativeFloat
                        description: A negative float value.
                        presence: optional
                    non_positive_float:
                        type: NonPositiveFloat
                        description: A non-positive float value.
                        presence: optional
                    non_negative_float:
                        type: NonNegativeFloat
                        description: A non-negative float value.
                        presence: optional
                    strict_float:
                        type: StrictFloat
                        description: A strict float value.
                        presence: optional
                    finite_float:
                        type: FiniteFloat
                        description: A finite float value (not NaN or infinite).
                        presence: optional
                    strict_str:
                        type: StrictStr
                        description: A strict string value.
                        presence: optional
                    uuid1:
                        type: UUID1
                        description: A UUID version 1.
                        presence: optional
                    uuid3:
                        type: UUID3
                        description: A UUID version 3.
                        presence: optional
                    uuid4:
                        type: UUID4
                        description: A UUID version 4.
                        presence: optional
                    uuid5:
                        type: UUID5
                        description: A UUID version 5.
                        presence: optional
                    uuid6:
                        type: UUID6
                        description: A UUID version 6.
                        presence: optional
                    uuid7:
                        type: UUID7
                        description: A UUID version 7.
                        presence: optional
                    uuid8:
                        type: UUID8
                        description: A UUID version 8.
                        presence: optional
                    file_path:
                        type: FilePath
                        description: A valid file path.
                        presence: optional
                    directory_path:
                        type: DirectoryPath
                        description: A valid directory path.
                        presence: optional
                    base64_bytes:
                        type: Base64Bytes
                        description: A base64 encoded byte string.
                        presence: optional
                    base64_str:
                        type: Base64Str
                        description: A base64 encoded string.
                        presence: optional
                    base64_url_bytes:
                        type: Base64UrlBytes
                        description: A base64 URL-safe encoded byte string.
                        presence: optional
                    base64_url_str:
                        type: Base64UrlStr
                        description: A base64 URL-safe encoded string.
                        presence: optional
                    any_url:
                        type: AnyUrl
                        description: Any valid URL.
                        presence: optional
                    any_http_url:
                        type: AnyHttpUrl
                        description: Any valid HTTP or HTTPS URL.
                        presence: optional
                    http_url:
                        type: HttpUrl
                        description: A valid HTTP or HTTPS URL.
                        presence: optional
                    any_websocket_url:
                        type: AnyWebsocketUrl
                        description: Any valid WebSocket or secure WebSocket URL.
                        presence: optional
                    websocket_url:
                        type: WebsocketUrl
                        description: A valid WebSocket or secure WebSocket URL.
                        presence: optional
                    file_url:
                        type: FileUrl
                        description: A valid file URL.
                        presence: optional
                    ftp_url:
                        type: FtpUrl
                        description: A valid FTP or FTPS URL.
                        presence: optional
                    postgres_dsn:
                        type: PostgresDsn
                        description: A valid PostgreSQL DSN.
                        presence: optional
                    cockroach_dsn:
                        type: CockroachDsn
                        description: A valid CockroachDB DSN.
                        presence: optional
                    amqp_dsn:
                        type: AmqpDsn
                        description: A valid AMQP DSN.
                        presence: optional
                    redis_dsn:
                        type: RedisDsn
                        description: A valid Redis DSN.
                        presence: optional
                    mongo_dsn:
                        type: MongoDsn
                        description: A valid MongoDB DSN.
                        presence: optional
                    kafka_dsn:
                        type: KafkaDsn
                        description: A valid Kafka DSN.
                        presence: optional
                    nats_dsn:
                        type: NatsDsn
                        description: A valid NATS DSN.
                        presence: optional
                    mysql_dsn:
                        type: MySQLDsn
                        description: A valid MySQL DSN.
                        presence: optional
                    mariadb_dsn:
                        type: MariaDBDsn
                        description: A valid MariaDB DSN.
                        presence: optional
                    clickhouse_dsn:
                        type: ClickHouseDsn
                        description: A valid ClickHouse DSN.
                        presence: optional
                    snowflake_dsn:
                        type: SnowflakeDsn
                        description: A valid Snowflake DSN.
                        presence: optional
                    email_str:
                        type: EmailStr
                        description: A valid email address.
                        presence: optional
                    name_email:
                        type: NameEmail
                        description: A valid name and email address.
                        presence: optional
                    ipvany_address:
                        type: IPvAnyAddress
                        description: A valid IPv4 or IPv6 address.
                        presence: optional
"""

MARKDOWN_YASL = """
definitions:
    acme:
        types:
            thing:
                description: Information about a thing.
                properties:
                    id:
                        type: str
                        description: The unique identifier for the thing.
                        presence: required
                    markdown:
                        type: markdown
                        description: A markdown value
                        presence: required
"""

TASK_BAD_NAMESPACE_REF_YASL = """
definitions:
    main:
        types:
            task:
                description: A thing to do.
                namespace: main
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
    other:
        types:
            list_of_tasks:
                description: A list of tasks to complete.
                namespace: other
                properties:
                    task_list:
                        type: map[int, notmain.task]
                        description: A list of tasks to do.
                        presence: required
"""

TODO_DOT_NAMESPACE_YASL = """
metadata:
  author: John Doe
  date: 2024-06-15
  description: A schema for managing a to-do list with tasks.
  license: MIT
  version: 1.0.0
  tags:
    - todo
    - tasks
    - example
definitions:
  acme.dynamic:
    types:
      task:
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
  acme:
    types:
      list_of_tasks:
        description: A list of tasks to complete.
        properties:
          task_list:
            type: map[acme.taskkey, acme.dynamic.task]
            description: A list of tasks to do.
            presence: required
    enums:
      taskkey:
        description: The type of shape.
        values:
          - task_01
          - task_02
          - task_03
"""

REF_LIST_YASL = """
definitions:
  acme:
    types:
      item:
        description: An item.
        properties:
          item_name:
            type: str
            description: The item name.
            presence: required
            unique: true
      collection:
        description: A collection of items and references.
        properties:
          item_list:
            type: ref[item.item_name][]
            description: The list of items.
            presence: required
"""
