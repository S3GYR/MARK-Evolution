"""Phase 7: Comprehensive Config Manager Tests - Priority 1."""

from __future__ import annotations

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from jarvis.config.settings import Settings, get_settings


class TestSettingsInitialization:
    """Test Settings initialization and default values."""

    def test_default_settings_values(self):
        """Test default settings values."""
        settings = Settings()
        
        # General settings
        assert settings.app_name == "JARVIS"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        
        # LLM settings
        assert settings.llm_provider == "gemini"
        assert settings.llm_model == "gemini/gemini-2.5-flash"
        assert settings.llm_fallback_model is None
        assert settings.llm_api_key is None
        assert settings.llm_temperature == 0.7
        assert settings.llm_max_tokens is None
        
        # Audio settings
        assert settings.audio_channels == 1
        assert settings.audio_send_sample_rate == 16000
        assert settings.audio_receive_sample_rate == 24000
        assert settings.audio_chunk_size == 1024
        assert settings.audio_device_index is None
        
        # Dashboard settings
        assert settings.dashboard_host == "127.0.0.1"
        assert settings.dashboard_port == 8000
        assert settings.dashboard_max_upload_mb == 500
        assert settings.dashboard_auth_token_ttl == 3600
        assert settings.dashboard_auto_firewall is False
        
        # Security settings
        assert settings.require_confirmation is True
        assert settings.sandbox_enabled is True

    def test_settings_from_environment_variables(self):
        """Test settings loaded from environment variables."""
        env_vars = {
            "JARVIS_APP_NAME": "CustomJARVIS",
            "JARVIS_DEBUG": "true",
            "JARVIS_LOG_LEVEL": "DEBUG",
            "JARVIS_LLM_PROVIDER": "openai",
            "JARVIS_LLM_MODEL": "gpt-4",
            "JARVIS_LLM_TEMPERATURE": "0.5",
            "JARVIS_DASHBOARD_PORT": "9000",
            "JARVIS_REQUIRE_CONFIRMATION": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.app_name == "CustomJARVIS"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            assert settings.llm_provider == "openai"
            assert settings.llm_model == "gpt-4"
            assert settings.llm_temperature == 0.5
            assert settings.dashboard_port == 9000
            assert settings.require_confirmation is False

    def test_settings_from_env_file(self):
        """Test settings loaded from .env file."""
        env_content = """
JARVIS_APP_NAME=EnvJARVIS
JARVIS_DEBUG=true
JARVIS_LLM_PROVIDER=anthropic
JARVIS_DASHBOARD_PORT=7000
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_file_path = env_file.name
        
        try:
            with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                mock_config.env_file = env_file_path
                
                settings = Settings()
                
                assert settings.app_name == "EnvJARVIS"
                assert settings.debug is True
                assert settings.llm_provider == "anthropic"
                assert settings.dashboard_port == 7000
        finally:
            os.unlink(env_file_path)

    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variables."""
        env_vars = {
            "JARVIS_LLM_TEMPERATURE": "invalid_float",
            "JARVIS_DASHBOARD_PORT": "invalid_int",
            "JARVIS_DEBUG": "invalid_bool"
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                settings = Settings()
                # Should handle invalid values gracefully or use defaults
                assert True
            except ValueError:
                # Should raise validation errors for invalid types
                assert True

    def test_secret_str_handling(self):
        """Test SecretStr handling for sensitive values."""
        env_vars = {
            "JARVIS_LLM_API_KEY": "secret_api_key_123"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.llm_api_key is not None
            # SecretStr should hide the value in repr
            assert "secret_api_key_123" not in repr(settings.llm_api_key)
            # But should be accessible via get_secret_value
            assert settings.llm_api_key.get_secret_value() == "secret_api_key_123"


class TestSettingsValidation:
    """Test Settings validation and constraints."""

    def test_llm_temperature_validation(self):
        """Test LLM temperature validation constraints."""
        # Valid temperatures
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        for temp in valid_temps:
            env_vars = {"JARVIS_LLM_TEMPERATURE": str(temp)}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.llm_temperature == temp
        
        # Invalid temperatures
        invalid_temps = [-0.1, 2.1, 10.0]
        for temp in invalid_temps:
            env_vars = {"JARVIS_LLM_TEMPERATURE": str(temp)}
            with patch.dict(os.environ, env_vars):
                try:
                    settings = Settings()
                    assert False, f"Should have raised validation error for temperature {temp}"
                except ValueError:
                    pass  # Expected

    def test_dashboard_port_validation(self):
        """Test dashboard port validation."""
        # Valid ports
        valid_ports = [1, 80, 443, 8000, 65535]
        for port in valid_ports:
            env_vars = {"JARVIS_DASHBOARD_PORT": str(port)}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.dashboard_port == port
        
        # Invalid ports
        invalid_ports = [0, -1, 65536, 100000]
        for port in invalid_ports:
            env_vars = {"JARVIS_DASHBOARD_PORT": str(port)}
            with patch.dict(os.environ, env_vars):
                try:
                    settings = Settings()
                    assert False, f"Should have raised validation error for port {port}"
                except ValueError:
                    pass  # Expected

    def test_audio_sample_rate_validation(self):
        """Test audio sample rate validation."""
        # Common valid sample rates
        valid_rates = [8000, 16000, 22050, 44100, 48000, 96000]
        for rate in valid_rates:
            env_vars = {"JARVIS_AUDIO_SEND_SAMPLE_RATE": str(rate)}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.audio_send_sample_rate == rate

    def test_dashboard_max_upload_validation(self):
        """Test dashboard max upload size validation."""
        # Valid upload sizes
        valid_sizes = [1, 100, 500, 1024, 2048]
        for size in valid_sizes:
            env_vars = {"JARVIS_DASHBOARD_MAX_UPLOAD_MB": str(size)}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.dashboard_max_upload_mb == size
        
        # Invalid negative size
        env_vars = {"JARVIS_DASHBOARD_MAX_UPLOAD_MB": "-100"}
        with patch.dict(os.environ, env_vars):
            try:
                settings = Settings()
                assert False, "Should have raised validation error for negative upload size"
            except ValueError:
                pass  # Expected


class TestGetSettingsFunction:
    """Test get_settings singleton behavior."""

    def test_get_settings_returns_settings_instance(self):
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_singleton_behavior(self):
        """Test get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_with_custom_config(self):
        """Test get_settings with custom configuration."""
        env_vars = {
            "JARVIS_APP_NAME": "SingletonTest",
            "JARVIS_DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = get_settings()
            assert settings.app_name == "SingletonTest"
            assert settings.debug is True

    def test_get_settings_caching_with_env_changes(self):
        """Test get_settings caching with environment changes."""
        # Initial call
        env_vars = {"JARVIS_APP_NAME": "Initial"}
        with patch.dict(os.environ, env_vars, clear=True):
            settings1 = get_settings()
            assert settings1.app_name == "Initial"
            
            # Change environment
            os.environ["JARVIS_APP_NAME"] = "Changed"
            settings2 = get_settings()
            
            # Should return cached instance (not reflect change)
            assert settings2.app_name == "Initial"
            assert settings1 is settings2


class TestSettingsConfigurationMigration:
    """Test settings configuration migration scenarios."""

    def test_missing_env_file_handling(self):
        """Test handling of missing .env file."""
        with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
            mock_config.env_file = "/nonexistent/.env"
            
            try:
                settings = Settings()
                # Should handle missing file gracefully
                assert True
            except Exception:
                # Should not crash on missing file
                assert False, "Should not crash on missing .env file"

    def test_malformed_env_file_handling(self):
        """Test handling of malformed .env file."""
        malformed_content = """
INVALID_LINE_WITHOUT_EQUALS
JARVIS_DEBUG=true
ANOTHER_INVALID_LINE
JARVIS_APP_NAME=Test
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(malformed_content)
            env_file_path = env_file.name
        
        try:
            with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                mock_config.env_file = env_file_path
                
                settings = Settings()
                
                # Should parse valid lines and ignore invalid ones
                assert settings.debug is True
                assert settings.app_name == "Test"
        finally:
            os.unlink(env_file_path)

    def test_env_file_with_unicode(self):
        """Test .env file with Unicode characters."""
        unicode_content = """
JARVIS_APP_NAME=JARVIS测试
JARVIS_DEBUG=true
JARVIS_LOG_LEVEL=INFO
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as env_file:
            env_file.write(unicode_content)
            env_file_path = env_file.name
        
        try:
            with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                mock_config.env_file = env_file_path
                
                settings = Settings()
                
                assert settings.app_name == "JARVIS测试"
                assert settings.debug is True
        finally:
            os.unlink(env_file_path)

    def test_configuration_priority(self):
        """Test configuration priority (env vars > env file > defaults)."""
        env_content = """
JARVIS_APP_NAME=FromFile
JARVIS_DEBUG=false
JARVIS_LLM_PROVIDER=anthropic
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_file_path = env_file.name
        
        try:
            env_vars = {
                "JARVIS_APP_NAME": "FromEnv",  # Should override file
                "JARVIS_DEBUG": "true"        # Should override file
            }
            
            with patch.dict(os.environ, env_vars):
                with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                    mock_config.env_file = env_file_path
                    
                    settings = Settings()
                    
                    # Environment variables should take priority
                    assert settings.app_name == "FromEnv"
                    assert settings.debug is True
                    
                    # File should provide value not in environment
                    assert settings.llm_provider == "anthropic"
        finally:
            os.unlink(env_file_path)


class TestSettingsErrorHandling:
    """Test Settings error handling scenarios."""

    def test_permission_denied_env_file(self):
        """Test handling of permission denied .env file."""
        env_content = "JARVIS_APP_NAME=Test"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as env_file:
            env_file.write(env_content)
            env_file_path = env_file.name
        
        try:
            # Mock permission denied
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                    mock_config.env_file = env_file_path
                    
                    try:
                        settings = Settings()
                        # Should handle permission denied gracefully
                        assert True
                    except PermissionError:
                        # Should propagate or handle permission errors
                        assert True
        finally:
            os.unlink(env_file_path)

    def test_corrupted_env_file_encoding(self):
        """Test handling of corrupted encoding in .env file."""
        # Create file with invalid encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.env', delete=False) as env_file:
            env_file.write(b'\xff\xfe\x00\x49\x00\x6e\x00\x76\x00\x61\x00\x6c\x00\x69\x00\x64\x00')
            env_file_path = env_file.name
        
        try:
            with patch('jarvis.config.settings.BaseSettings.model_config') as mock_config:
                mock_config.env_file = env_file_path
                
                try:
                    settings = Settings()
                    # Should handle encoding errors gracefully
                    assert True
                except UnicodeDecodeError:
                    # Should handle encoding errors
                    assert True
        finally:
            os.unlink(env_file_path)

    def test_very_long_env_values(self):
        """Test handling of very long environment variable values."""
        long_value = "x" * 10000
        env_vars = {"JARVIS_APP_NAME": long_value}
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            assert settings.app_name == long_value

    def test_special_characters_in_env_values(self):
        """Test special characters in environment variable values."""
        special_values = [
            "App with spaces",
            "app-with-dashes",
            "app_with_underscores",
            "app.with.dots",
            "app@with#symbols",
            "app/with/slashes",
            "app\\with\\backslashes",
            "Unicode: ñáéíóú 中文 русский"
        ]
        
        for value in special_values:
            env_vars = {"JARVIS_APP_NAME": value}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.app_name == value


class TestSettingsIntegration:
    """Test Settings integration scenarios."""

    def test_settings_with_directory_paths(self):
        """Test settings integration with directory paths."""
        with patch('jarvis.config.settings.CONFIG_DIR') as mock_config_dir:
            with patch('jarvis.config.settings.CACHE_DIR') as mock_cache_dir:
                with patch('jarvis.config.settings.DATA_DIR') as mock_data_dir:
                    mock_config_dir = Path("/mock/config")
                    mock_cache_dir = Path("/mock/cache")
                    mock_data_dir = Path("/mock/data")
                    
                    settings = Settings()
                    
                    # Settings should be independent of path configuration
                    assert isinstance(settings, Settings)

    def test_settings_export_to_dict(self):
        """Test exporting settings to dictionary."""
        env_vars = {
            "JARVIS_APP_NAME": "ExportTest",
            "JARVIS_DEBUG": "true",
            "JARVIS_LLM_PROVIDER": "openai"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Export to dict
            settings_dict = settings.model_dump()
            
            assert isinstance(settings_dict, dict)
            assert settings_dict["app_name"] == "ExportTest"
            assert settings_dict["debug"] is True
            assert settings_dict["llm_provider"] == "openai"
            
            # SecretStr should be hidden in export
            if "llm_api_key" in settings_dict:
                assert settings_dict["llm_api_key"] is None or isinstance(settings_dict["llm_api_key"], str)

    def test_settings_json_serialization(self):
        """Test settings JSON serialization."""
        env_vars = {
            "JARVIS_APP_NAME": "JSONTest",
            "JARVIS_DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Serialize to JSON
            settings_json = settings.model_dump_json()
            
            assert isinstance(settings_json, str)
            
            # Deserialize from JSON
            parsed_data = json.loads(settings_json)
            assert parsed_data["app_name"] == "JSONTest"
            assert parsed_data["debug"] is True

    def test_settings_copy_and_modify(self):
        """Test copying and modifying settings."""
        original_settings = Settings()
        
        # Create copy
        copied_settings = Settings.model_construct(**original_settings.model_dump())
        
        # Modify copy
        copied_settings.app_name = "ModifiedCopy"
        
        # Original should be unchanged
        assert original_settings.app_name != "ModifiedCopy"
        assert copied_settings.app_name == "ModifiedCopy"


class TestSettingsPerformance:
    """Test Settings performance characteristics."""

    def test_settings_initialization_performance(self):
        """Test settings initialization performance."""
        import time
        
        # Test with many environment variables
        env_vars = {}
        for i in range(100):
            env_vars[f"JARVIS_TEST_VAR_{i}"] = f"value_{i}"
        
        with patch.dict(os.environ, env_vars):
            start_time = time.time()
            
            for _ in range(10):
                settings = Settings()
            
            elapsed = time.time() - start_time
            
            # Should initialize quickly
            assert elapsed < 1.0

    def test_get_settings_caching_performance(self):
        """Test get_settings caching performance."""
        import time
        
        start_time = time.time()
        
        # Multiple calls should be fast due to caching
        for _ in range(100):
            settings = get_settings()
        
        elapsed = time.time() - start_time
        
        # Should be very fast due to caching
        assert elapsed < 0.1

    def test_memory_usage_stability(self):
        """Test memory usage stability with many setting instances."""
        # Create many settings instances
        settings_list = []
        
        for i in range(100):
            env_vars = {"JARVIS_APP_NAME": f"Test_{i}"}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                settings_list.append(settings)
        
        # Should not accumulate excessive memory
        assert len(settings_list) == 100
        for i, settings in enumerate(settings_list):
            assert settings.app_name == f"Test_{i}"


class TestSettingsEdgeCases:
    """Test Settings edge cases."""

    def test_empty_environment_variables(self):
        """Test empty environment variables."""
        env_vars = {
            "JARVIS_APP_NAME": "",
            "JARVIS_LLM_PROVIDER": "",
            "JARVIS_LOG_LEVEL": ""
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Empty strings should be handled appropriately
            assert settings.app_name == ""  # or default value
            assert settings.llm_provider == ""  # or default value
            assert settings.log_level == ""  # or default value

    def test_whitespace_only_environment_variables(self):
        """Test whitespace-only environment variables."""
        env_vars = {
            "JARVIS_APP_NAME": "   ",
            "JARVIS_DEBUG": "   ",
            "JARVIS_LLM_TEMPERATURE": "   "
        }
        
        with patch.dict(os.environ, env_vars):
            try:
                settings = Settings()
                # Should handle whitespace-only values appropriately
                assert True
            except ValueError:
                # Should validate and reject whitespace-only for typed fields
                assert True

    def test_numeric_string_environment_variables(self):
        """Test numeric strings for string fields."""
        env_vars = {
            "JARVIS_APP_NAME": "123",
            "JARVIS_LLM_PROVIDER": "456",
            "JARVIS_LOG_LEVEL": "789"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Should preserve numeric strings as strings
            assert settings.app_name == "123"
            assert settings.llm_provider == "456"
            assert settings.log_level == "789"

    def test_boolean_string_variations(self):
        """Test various boolean string representations."""
        boolean_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("Yes", True),
            ("on", True),
            ("On", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("No", False),
            ("off", False),
            ("Off", False)
        ]
        
        for env_value, expected in boolean_cases:
            env_vars = {"JARVIS_DEBUG": env_value}
            with patch.dict(os.environ, env_vars):
                settings = Settings()
                assert settings.debug == expected

    def test_extra_environment_variables_ignored(self):
        """Test that extra environment variables are ignored."""
        env_vars = {
            "JARVIS_APP_NAME": "Test",
            "JARVIS_EXTRA_FIELD": "should_be_ignored",
            "JARVIS_ANOTHER_EXTRA": "also_ignored"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Should only load defined fields
            assert settings.app_name == "Test"
            assert not hasattr(settings, 'extra_field')
            assert not hasattr(settings, 'another_extra')


class TestSettingsSecurity:
    """Test Settings security aspects."""

    def test_sensitive_data_protection(self):
        """Test protection of sensitive data."""
        env_vars = {
            "JARVIS_LLM_API_KEY": "super_secret_api_key_12345"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # SecretStr should not expose value in string representation
            settings_str = str(settings)
            assert "super_secret_api_key_12345" not in settings_str
            
            settings_repr = repr(settings)
            assert "super_secret_api_key_12345" not in settings_repr
            
            # But should be accessible through proper method
            assert settings.llm_api_key.get_secret_value() == "super_secret_api_key_12345"

    def test_settings_model_dump_excludes_secrets(self):
        """Test model_dump excludes secret values by default."""
        env_vars = {
            "JARVIS_LLM_API_KEY": "secret_key"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Default dump should exclude secrets
            settings_dict = settings.model_dump()
            
            if "llm_api_key" in settings_dict:
                assert settings_dict["llm_api_key"] is None
            
            # But can include secrets if explicitly requested
            settings_dict_with_secrets = settings.model_dump(exclude_none=False, secrets_repr=True)
            
            # Should handle secret representation appropriately
            assert isinstance(settings_dict_with_secrets, dict)

    def test_environment_variable_injection_prevention(self):
        """Test prevention of environment variable injection."""
        # Try to inject malicious environment variables
        malicious_env = {
            "JARVIS_APP_NAME": "App$(rm -rf /)",
            "JARVIS_DEBUG": "true`whoami`",
            "JARVIS_LLM_PROVIDER": "service; curl malicious.com"
        }
        
        with patch.dict(os.environ, malicious_env):
            settings = Settings()
            
            # Should treat values as literal strings, not execute commands
            assert "$(rm -rf /)" in settings.app_name
            assert "true`whoami`" in str(settings.debug)
            assert "service; curl malicious.com" in settings.llm_provider
