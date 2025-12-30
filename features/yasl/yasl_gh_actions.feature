Feature: YASL GitHub Actions Schema Validation
  As a developer
  I want to validate my GitHub Actions yaml
  So that I can ensure correctness of my workflows

  Scenario: Validating the yasl-ci.yml file against the GitHub Actions schema
    Given a YASL schema "schemas/gh_actions/github_actions.yasl" is provided
    And a YAML document ".github/workflows/yasl-ci.yml" is provided
    And the model name "github_actions" is provided
    When I run the YASL CLI with provided arguments
    Then the validation should pass

  Scenario: Validating the publish.yml file against the GitHub Actions schema
    Given a YASL schema "schemas/gh_actions/github_actions.yasl" is provided
    And a YAML document ".github/workflows/publish.yml" is provided
    And the model name "github_actions" is provided
    When I run the YASL CLI with provided arguments
    Then the validation should pass
    