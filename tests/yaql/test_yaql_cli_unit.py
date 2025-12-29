import logging
from unittest.mock import MagicMock, patch

import pytest

from yaql.cli import YaqlShell


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def shell(mock_engine):
    return YaqlShell(mock_engine)


def test_load_schema_success(shell, mock_engine, caplog):
    mock_engine.load_schema.return_value = True
    with caplog.at_level(logging.INFO):
        shell.do_load_schema("some/path")

    mock_engine.load_schema.assert_called_with("some/path")
    assert "Loading schema from: some/path" in caplog.text
    assert "✅ Schema loaded successfully." in caplog.text


def test_load_schema_failure(shell, mock_engine, caplog):
    mock_engine.load_schema.return_value = False
    with caplog.at_level(logging.INFO):
        shell.do_load_schema("some/path")

    mock_engine.load_schema.assert_called_with("some/path")
    assert "Loading schema from: some/path" in caplog.text
    assert "❌ Failed to load schema." in caplog.text


def test_load_schema_no_arg(shell, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_load_schema("")
    assert "❌ Please provide a file path or directory." in caplog.text


def test_load_data_success(shell, mock_engine, caplog):
    mock_engine.load_data.return_value = 5
    with caplog.at_level(logging.INFO):
        shell.do_load_data("data/path")

    mock_engine.load_data.assert_called_with("data/path")
    assert "Loading data from: data/path" in caplog.text
    assert "✅ Loaded 5 data records." in caplog.text


def test_load_data_no_arg(shell, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_load_data("")
    assert "❌ Please provide a file path or directory." in caplog.text


def test_store_schema_not_implemented(shell, mock_engine, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_store_schema("out.yasl")
    assert "❌ store_schema is not yet implemented for SQLModel engine." in caplog.text


def test_store_schema_no_arg(shell, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_store_schema("")
    assert "❌ Please provide an output file path." in caplog.text


def test_store_data_not_implemented(shell, mock_engine, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_store_data("out.yaml")
    assert "❌ store_data is not yet implemented for SQLModel engine." in caplog.text


def test_store_data_no_arg(shell, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_store_data("")
    assert "❌ Please provide an output path." in caplog.text


def test_sql_success_with_results(shell, mock_engine, capsys):
    mock_engine.execute_sql.return_value = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    shell.do_sql("SELECT * FROM users")

    mock_engine.execute_sql.assert_called_with("SELECT * FROM users")
    captured = capsys.readouterr()
    assert "id | name" in captured.out
    assert "1 | Alice" in captured.out
    assert "2 | Bob" in captured.out


def test_sql_success_empty_results(shell, mock_engine, caplog):
    mock_engine.execute_sql.return_value = []
    with caplog.at_level(logging.INFO):
        shell.do_sql("SELECT * FROM users")

    assert "Query executed successfully (no results)." in caplog.text


def test_sql_success_none_results(shell, mock_engine, caplog):
    # e.g. for INSERT/UPDATE where execute_sql might return None or empty list depending on impl
    # The current implementation returns [] for non-selects usually, but let's check None branch
    mock_engine.execute_sql.return_value = None
    with caplog.at_level(logging.INFO):
        shell.do_sql("INSERT INTO users ...")

    assert "Query executed successfully." in caplog.text


def test_sql_exception(shell, mock_engine, caplog):
    mock_engine.execute_sql.side_effect = Exception("SQL Syntax Error")
    with caplog.at_level(logging.ERROR):
        shell.do_sql("SELECT * FROM")

    assert "❌ SQL Error: SQL Syntax Error" in caplog.text


def test_sql_no_arg(shell, caplog):
    with caplog.at_level(logging.ERROR):
        shell.do_sql("")
    assert "❌ Please provide a SQL query." in caplog.text


def test_exit_no_changes(shell, mock_engine, caplog):
    mock_engine.unsaved_changes = False
    with caplog.at_level(logging.INFO):
        result = shell.do_exit("")

    # mock_engine.close.assert_called_once()
    assert "Goodbye!" in caplog.text
    assert result is True


def test_exit_unsaved_changes_confirm(shell, mock_engine, caplog):
    mock_engine.unsaved_changes = True

    with patch("builtins.input", return_value="y"):
        with caplog.at_level(logging.INFO):
            result = shell.do_exit("")

    # mock_engine.close.assert_called_once()
    assert "Goodbye!" in caplog.text
    assert result is True


def test_quit_alias(shell, mock_engine):
    mock_engine.unsaved_changes = False
    result = shell.do_quit("")
    # mock_engine.close.assert_called_once()
    assert result is True


def test_eof_alias(shell, mock_engine):
    mock_engine.unsaved_changes = False
    result = shell.do_EOF("")
    # mock_engine.close.assert_called_once()
    assert result is True
