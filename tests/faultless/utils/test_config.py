import os
from pathlib import Path

import pytest

from base.utils.config import (  # Adjusted import to correct path
    MissingDefaultConfigError,  # Added import for the exception
    find_config_file,
    get,
    replace_env_vars,
)


class TestFindConfigFile:
    def test_existing_file(self, tmp_path: Path):
        """An existing file."""
        temp_config_path = tmp_path / "config.yml"
        temp_config_path.write_text("dummy_content")
        config_path = find_config_file(temp_config_path, use_parent=False)
        assert config_path == temp_config_path

    def test_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            find_config_file("non_existing_file.yml", use_parent=False)


class TestReplaceEnvVars:
    def test_replace_env_vars_dict(self):
        """Test that replace_env_vars replaces environment variables in a dictionary."""
        os.environ["TEST_VAR"] = "replaced_value"
        input_data = {"key1": "$TEST_VAR", "key2": "value2"}
        expected_output = {"key1": "replaced_value", "key2": "value2"}
        assert replace_env_vars(input_data) == expected_output
        del os.environ["TEST_VAR"]

    def test_replace_env_vars_list(self):
        """Test that replace_env_vars replaces environment variables in a list."""
        os.environ["TEST_VAR"] = "replaced_value"
        input_data = ["$TEST_VAR", "value2"]
        expected_output = ["replaced_value", "value2"]
        assert replace_env_vars(input_data) == expected_output
        del os.environ["TEST_VAR"]


class TestGet:
    def test_existing_value(self, tmp_path: Path):
        temp_config_path = tmp_path / "config.yml"
        temp_config_path.write_text("""
        default:
            key1: value1
            key2: value2
        """)
        os.environ["CONFIG_ACTIVE"] = temp_config_path.as_posix()
        assert get("key1", file=temp_config_path) == "value1"
        del os.environ["CONFIG_ACTIVE"]

    def test_non_existing_value(self, tmp_path: Path):
        """Non-existing key in the config file should return None."""
        temp_config_path = tmp_path / "config.yml"
        temp_config_path.write_text("""
        default:
            key1: value1
            key2: value2
        """)
        os.environ["CONFIG_ACTIVE"] = temp_config_path.as_posix()
        assert get("non_existing_key", file=temp_config_path) is None
        del os.environ["CONFIG_ACTIVE"]

    def test_missing_default_key(self, tmp_path: Path):
        """Raises an error when the default key is missing in the config file."""
        temp_config_path = tmp_path / "config.yml"
        temp_config_path.write_text("""
        environment:
            key1: value1
            key2: value2
        """)
        with pytest.raises(MissingDefaultConfigError):
            get(file=temp_config_path)
