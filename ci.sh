#!/usr/bin/env bash

set -euo pipefail

# Print usage and exit
usage() {
    echo "Usage: $0 {test|lint|lint-fix|bdd|build|all}"
    exit 1
}

# Run unit tests
run_test() {
    echo "Running unit tests..."
    uv run pytest
    if [[ $? -ne 0 ]]; then
        echo "Error: Unit tests failed."
        exit 1
    fi
}

# Run formatter
run_format() {
    echo "Running formatter..."
    uv run ruff format src tests
    if [[ $? -ne 0 ]]; then
        echo "Error: Formatter failed."
        exit 1
    fi
}

# Run type check
run_type_check() {
    echo "Running type check..."
    uv run pyright
    if [[ $? -ne 0 ]]; then
        echo "Error: Type check failed."
        exit 1
    fi
}

# Run linter
run_lint() {
    echo "Running linter..."
    uv run ruff check src tests
    if [[ $? -ne 0 ]]; then
        echo "Error: Linter failed."
        exit 1
    fi
}

# Run linter and fix
run_lint_fix() {
    echo "Running linter..."
    uv run ruff check src tests --fix
    if [[ $? -ne 0 ]]; then
        echo "Error: Linter (fix) failed."
        exit 1
    fi
}

# Run BDD tests
run_bdd() {
    echo "Running BDD tests..."
    uv run behave
    if [[ $? -ne 0 ]]; then
        echo "Error: BDD tests failed."
        exit 1
    fi
}

# Run dependency verification
run_verify_deps() {
    echo "Verifying production dependencies..."
    ./scripts/bash/verify_prod_deps.sh
    if [[ $? -ne 0 ]]; then
        echo "Error: Dependency verification failed."
        exit 1
    fi
}

# Build docs website
run_docs() {
    echo "Building docs website..."
    uv run mkdocs build
    if [[ $? -ne 0 ]]; then
        echo "Error: Docs build failed."
        exit 1
    fi
}

# Build project
run_build() {
    echo "Building project..."
    uv run python -m build
    if [[ $? -ne 0 ]]; then
        echo "Error: Build failed."
        exit 1
    fi
}

# Run all CI steps
run_all() {
    run_test
    run_format
    run_lint
    run_type_check
    run_bdd
    run_verify_deps
    run_docs
    run_build
}

# Main
if [[ $# -ne 1 ]]; then
    usage
fi

case "$1" in
    test)  run_test ;;
    format)  run_format ;;
    lint)  run_lint ;;
    lint-fix)  run_lint_fix ;;
    type-check)  run_type_check ;;
    bdd)   run_bdd ;;
    verify-deps) run_verify_deps ;;
    docs)  run_docs ;;
    build) run_build ;;
    all) run_all ;;
    *)     usage ;;
esac