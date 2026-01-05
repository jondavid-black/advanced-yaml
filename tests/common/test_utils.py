from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from common.utils import advanced_yaml_version


def test_version_installed():
    """Test version retrieval when package is installed."""
    with patch("common.utils.version") as mock_version:
        mock_version.return_value = "1.2.3"
        assert advanced_yaml_version() == "1.2.3"
        mock_version.assert_called_once_with("advanced-yaml")


def test_version_not_installed():
    """Test version retrieval when package is not installed."""
    with patch("common.utils.version") as mock_version:
        mock_version.side_effect = PackageNotFoundError
        assert advanced_yaml_version() == "Unknown (package not installed)"
        mock_version.assert_called_once_with("advanced-yaml")
