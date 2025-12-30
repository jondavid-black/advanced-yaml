#!/usr/bin/env bash

set -euo pipefail

# Print usage and exit
usage() {
    echo "Usage: $0 {test|lint|lint-fix|bdd|build|all|security}"
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

# Run security checks
run_security() {
    echo "=================================================="
    echo "          Running Security Scans"
    echo "=================================================="

    # Add local tools to PATH if they exist
    if [[ -d "$HOME/local-tools/bin" ]]; then
        export PATH="$HOME/local-tools/bin:$PATH"
    fi

    local tools_missing=0
    for tool in codeql dependabot; do
        if ! command -v "$tool" &> /dev/null; then
            echo "Error: $tool not found."
            tools_missing=1
        fi
    done
    if [[ $tools_missing -eq 1 ]]; then exit 1; fi

    local issues_found=0

    # --- CodeQL ---
    echo -n "[CodeQL]     Analyzing..."
    
    # Ensure queries are present
    if ! codeql resolve packs | grep -q "codeql/python-queries"; then
         codeql pack download codeql/python-queries > /dev/null 2>&1
    fi

    # Run analysis, redirect logs
    if codeql database create codeql-db --language=python --overwrite > codeql_build.log 2>&1 && \
       codeql database analyze codeql-db codeql/python-queries --format=csv --output=codeql-results.csv > codeql_analyze.log 2>&1; then
        
        local cql_count
        cql_count=$(wc -l < codeql-results.csv)
        
        if [[ "$cql_count" -gt 0 ]]; then
            echo " ⚠️  Issues found: $cql_count"
            issues_found=1
        else
            echo " ✅  Clean"
        fi
    else
        echo " ❌  Failed (see codeql_build.log)"
        issues_found=1
    fi

    # --- Dependabot ---
    echo -n "[Dependabot] Checking..."
    
    export DEPENDABOT_OPEN_TIMEOUT_IN_SECONDS=15
    if [[ -z "${DOCKER_HOST:-}" ]] && [[ -S "/run/user/$(id -u)/podman/podman.sock" ]]; then
        export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
    fi
    
    # Run dependabot, capture output
    dependabot update pip . --local . > dependabot.log 2>&1
    local dep_exit=$?
    
    # Check for specific "Updating" lines which indicate findings
    local updates
    updates=$(grep "Updating .* from .* to .*" dependabot.log || true)

    if [[ -n "$updates" ]]; then
        echo " ⚠️  Updates available"
        # We don't necessarily fail the build for available updates, but we flag them.
    elif [[ $dep_exit -ne 0 ]]; then
        echo " ❌  Failed (see dependabot.log)"
        issues_found=1
    else
        echo " ✅  Clean"
    fi

    echo "=================================================="
    echo "              Scan Results"
    echo "=================================================="
    
    if [[ -s codeql-results.csv ]]; then
        echo "🔴 CodeQL Security Issues:"
        cat codeql-results.csv
        echo ""
    else
        echo "🟢 CodeQL: No security issues detected."
    fi

    if [[ -n "$updates" ]]; then
        echo "🟠 Dependabot Updates:"
        echo "$updates" | sed 's/.*INFO //g'
    else
        echo "🟢 Dependabot: No updates required."
    fi
    echo "=================================================="
    
    if [[ $issues_found -eq 1 ]]; then
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
    security) run_security ;;
    verify-deps) run_verify_deps ;;
    docs)  run_docs ;;
    build) run_build ;;
    all) run_all ;;
    *)     usage ;;
esac