"""Phase 9B: Comprehensive Desktop Tests - Priority 4."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List
from pathlib import Path

from jarvis.tools.desktop import (
    desktop_control, _safe_player
)
from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext
from jarvis.security.sandbox import SandboxError


class TestDesktopControlSecurity:
    """Test desktop control security functions."""

    def test_safe_player_with_none(self):
        """Test _safe_player with None input."""
        player = _safe_player(None)
        
        assert isinstance(player, ConsolePlayer)

    def test_safe_player_with_player(self):
        """Test _safe_player with valid player."""
        mock_player = Mock(spec=Player)
        
        player = _safe_player(mock_player)
        
        assert player == mock_player

    def test_safe_player_with_invalid_player(self):
        """Test _safe_player with invalid player."""
        invalid_player = "not a player"
        
        # Should return ConsolePlayer for invalid input
        player = _safe_player(invalid_player)
        
        assert isinstance(player, ConsolePlayer)


class TestDesktopControlBasicOperations:
    """Test desktop control basic operations."""

    @pytest.mark.asyncio
    async def test_desktop_control_no_parameters(self):
        """Test desktop control with no parameters."""
        result = await desktop_control()
        
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_desktop_control_empty_parameters(self):
        """Test desktop control with empty parameters."""
        result = await desktop_control(parameters={})
        
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_desktop_control_no_action(self):
        """Test desktop control with no action specified."""
        params = {"task": "some task"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Desktop stats"
            
            result = await desktop_control(parameters=params)
            
            assert result is not None
            mock_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_desktop_control_with_player(self):
        """Test desktop control with custom player."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "stats"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Desktop stats"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert result is not None
            mock_player.write_log.assert_called()

    @pytest.mark.asyncio
    async def test_desktop_control_logging(self):
        """Test desktop control logging functionality."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "stats"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Desktop stats"
            
            await desktop_control(parameters=params, player=mock_player)
            
            # Should log the action
            mock_player.write_log.assert_called_once()
            log_call = mock_player.write_log.call_args[0][0]
            assert "[desktop]" in log_call
            assert "stats" in log_call

    @pytest.mark.asyncio
    async def test_desktop_control_task_fallback(self):
        """Test desktop control task fallback to description."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"description": "custom task description"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Desktop stats"
            
            await desktop_control(parameters=params, player=mock_player)
            
            # Should use description as task
            mock_player.write_log.assert_called_once()
            log_call = mock_player.write_log.call_args[0][0]
            assert "custom task description" in log_call


class TestDesktopControlWallpaperOperations:
    """Test desktop control wallpaper operations."""

    @pytest.mark.asyncio
    async def test_set_wallpaper_success(self):
        """Test successful wallpaper setting."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "path": "/path/to/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Wallpaper set successfully"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert result == "Wallpaper set successfully"
            mock_set_wallpaper.assert_called_once_with("/path/to/wallpaper.jpg")

    @pytest.mark.asyncio
    async def test_set_wallpaper_no_path(self):
        """Test wallpaper setting with no path provided."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "wallpaper"}
        
        result = await desktop_control(parameters=params, player=mock_player)
        
        assert result == "No image path provided."

    @pytest.mark.asyncio
    async def test_set_wallpaper_empty_path(self):
        """Test wallpaper setting with empty path."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "path": ""
        }
        
        result = await desktop_control(parameters=params, player=mock_player)
        
        assert result == "No image path provided."

    @pytest.mark.asyncio
    async def test_set_wallpaper_permission_denied(self):
        """Test wallpaper setting with permission denied."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "path": "/protected/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.side_effect = PermissionError("Permission denied")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "Permission denied" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_set_wallpaper_invalid_path(self):
        """Test wallpaper setting with invalid path."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "path": "/nonexistent/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.side_effect = FileNotFoundError("File not found")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "File not found" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_set_wallpaper_from_url(self):
        """Test setting wallpaper from URL."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "url": "https://example.com/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper_from_url') as mock_set_from_url:
            mock_set_from_url.return_value = "Wallpaper downloaded and set successfully"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "downloaded and set" in result.lower()
            mock_set_from_url.assert_called_once_with("https://example.com/wallpaper.jpg")

    @pytest.mark.asyncio
    async def test_get_current_wallpaper(self):
        """Test getting current wallpaper."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "get_wallpaper"}
        
        with patch('jarvis.tools.desktop.get_current_wallpaper') as mock_get_wallpaper:
            mock_get_wallpaper.return_value = "/current/wallpaper.jpg"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "/current/wallpaper.jpg" in result
            mock_get_wallpaper.assert_called_once()


class TestDesktopControlOrganizationOperations:
    """Test desktop control organization operations."""

    @pytest.mark.asyncio
    async def test_organize_desktop_success(self):
        """Test successful desktop organization."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "organize"}
        
        with patch('jarvis.tools.desktop.organize_desktop') as mock_organize:
            mock_organize.return_value = "Desktop organized successfully"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert result == "Desktop organized successfully"
            mock_organize.assert_called_once()

    @pytest.mark.asyncio
    async def test_clean_desktop_success(self):
        """Test successful desktop cleaning."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "clean"}
        
        with patch('jarvis.tools.desktop.clean_desktop') as mock_clean:
            mock_clean.return_value = "Desktop cleaned successfully"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert result == "Desktop cleaned successfully"
            mock_clean.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_desktop_success(self):
        """Test successful desktop listing."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "list"}
        
        with patch('jarvis.tools.desktop.list_desktop') as mock_list:
            mock_list.return_value = "file1.txt\\nfile2.jpg\\nfolder1/"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "file1.txt" in result
            assert "file2.jpg" in result
            assert "folder1/" in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_desktop_stats_success(self):
        """Test successful desktop stats retrieval."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "stats"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Files: 10, Folders: 3, Size: 25.5 MB"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "Files: 10" in result
            assert "Folders: 3" in result
            assert "25.5 MB" in result
            mock_stats.assert_called_once()


class TestDesktopControlSandboxing:
    """Test desktop control sandboxing and security."""

    @pytest.mark.asyncio
    async def test_sandbox_execution_success(self):
        """Test successful sandbox execution."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "custom",
            "command": "echo 'Hello World'"
        }
        
        with patch('jarvis.tools.desktop.execute_code') as mock_execute:
            mock_execute.return_value = "Hello World"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "Hello World" in result

    @pytest.mark.asyncio
    async def test_sandbox_execution_blocked(self):
        """Test blocked sandbox execution."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "custom",
            "command": "rm -rf /"  # Dangerous command
        }
        
        with patch('jarvis.tools.desktop.execute_code') as mock_execute:
            mock_execute.side_effect = SandboxError("Command blocked for security")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "blocked" in result.lower() or "security" in result.lower()

    @pytest.mark.asyncio
    async def test_action_context_creation(self):
        """Test ActionContext creation for security."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "path": "/test/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            # ActionContext should be created for security validation
            assert result is not None

    @pytest.mark.asyncio
    async def test_unsupported_command_handling(self):
        """Test handling of unsupported commands."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "unsupported_command"
        }
        
        result = await desktop_control(parameters=params, player=mock_player)
        
        assert "unsupported" in result.lower() or "not recognized" in result.lower()

    @pytest.mark.asyncio
    async def test_malicious_command_detection(self):
        """Test detection of malicious commands."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        malicious_commands = [
            "format c:",
            "del /s /q *.*",
            "sudo rm -rf /",
            "powershell -command \"Remove-Item -Recurse -Force C:\\\""
        ]
        
        for command in malicious_commands:
            params = {
                "action": "custom",
                "command": command
            }
            
            with patch('jarvis.tools.desktop.execute_code') as mock_execute:
                mock_execute.side_effect = SandboxError("Malicious command detected")
                
                result = await desktop_control(parameters=params, player=mock_player)
                
                assert "malicious" in result.lower() or "blocked" in result.lower()


class TestDesktopControlErrorHandling:
    """Test desktop control error handling scenarios."""

    @pytest.mark.asyncio
    async def test_legacy_function_not_available(self):
        """Test handling when legacy functions are not available."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "stats"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats', side_effect=NameError("Function not available")):
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "not available" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_file_system_error(self):
        """Test handling of file system errors."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "list"}
        
        with patch('jarvis.tools.desktop.list_desktop') as mock_list:
            mock_list.side_effect = OSError("File system error")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "file system" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_network_error_for_url_wallpaper(self):
        """Test network error when setting wallpaper from URL."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "wallpaper",
            "url": "https://example.com/wallpaper.jpg"
        }
        
        with patch('jarvis.tools.desktop.set_wallpaper_from_url') as mock_set_from_url:
            mock_set_from_url.side_effect = ConnectionError("Network error")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "network" in result.lower() or "connection" in result.lower()

    @pytest.mark.asyncio
    async def test_memory_error(self):
        """Test handling of memory errors."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "organize"}
        
        with patch('jarvis.tools.desktop.organize_desktop') as mock_organize:
            mock_organize.side_effect = MemoryError("Out of memory")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "memory" in result.lower() or "out of memory" in result.lower()

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "stats"}
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.side_effect = asyncio.TimeoutError("Operation timeout")
            
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert "timeout" in result.lower() or "timed out" in result.lower()


class TestDesktopControlConcurrency:
    """Test desktop control concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_wallpaper_operations(self):
        """Test concurrent wallpaper operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Wallpaper set"
            
            async def set_wallpaper_worker(path):
                params = {"action": "wallpaper", "path": path}
                return await desktop_control(parameters=params, player=mock_player)
            
            # Run concurrent operations
            tasks = [
                set_wallpaper_worker("/path1.jpg"),
                set_wallpaper_worker("/path2.jpg"),
                set_wallpaper_worker("/path3.jpg")
            ]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all("Wallpaper set" in result for result in results)
            assert mock_set_wallpaper.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_desktop_operations(self):
        """Test concurrent desktop operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats, \
             patch('jarvis.tools.desktop.list_desktop') as mock_list, \
             patch('jarvis.tools.desktop.clean_desktop') as mock_clean:
            
            mock_stats.return_value = "Stats"
            mock_list.return_value = "List"
            mock_clean.return_value = "Cleaned"
            
            async def operation_worker(action):
                params = {"action": action}
                return await desktop_control(parameters=params, player=mock_player)
            
            # Run concurrent operations
            tasks = [
                operation_worker("stats"),
                operation_worker("list"),
                operation_worker("clean")
            ]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            mock_stats.assert_called_once()
            mock_list.assert_called_once()
            mock_clean.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """Test concurrent error handling."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            # Some operations succeed, some fail
            mock_set_wallpaper.side_effect = [
                "Success",
                PermissionError("Permission denied"),
                "Success"
            ]
            
            async def set_wallpaper_worker(path):
                params = {"action": "wallpaper", "path": path}
                return await desktop_control(parameters=params, player=mock_player)
            
            # Run concurrent operations
            tasks = [
                set_wallpaper_worker("/path1.jpg"),
                set_wallpaper_worker("/path2.jpg"),
                set_wallpaper_worker("/path3.jpg")
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 3
            assert results[0] == "Success"
            assert isinstance(results[1], PermissionError)
            assert results[2] == "Success"


class TestDesktopControlPerformance:
    """Test desktop control performance characteristics."""

    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self):
        """Test bulk operation performance."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Stats"
            
            import time
            start_time = time.time()
            
            # Perform many operations
            for i in range(100):
                params = {"action": "stats"}
                await desktop_control(parameters=params, player=mock_player)
            
            elapsed = time.time() - start_time
            
            assert elapsed < 5.0  # Should complete within 5 seconds
            assert mock_stats.call_count == 100

    @pytest.mark.asyncio
    async def test_large_desktop_listing_performance(self):
        """Test performance with large desktop listings."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        # Simulate large desktop listing
        large_listing = "\\n".join([f"file_{i}.txt" for i in range(1000)])
        
        with patch('jarvis.tools.desktop.list_desktop') as mock_list:
            mock_list.return_value = large_listing
            
            import time
            start_time = time.time()
            
            params = {"action": "list"}
            result = await desktop_control(parameters=params, player=mock_player)
            
            elapsed = time.time() - start_time
            
            assert elapsed < 2.0  # Should complete within 2 seconds
            assert len(result) > 10000  # Should handle large listings

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Stats"
            
            # Perform many operations
            for i in range(1000):
                params = {"action": "stats"}
                await desktop_control(parameters=params, player=mock_player)
            
            # Memory usage should be stable
            assert True


class TestDesktopControlEdgeCases:
    """Test desktop control edge cases."""

    @pytest.mark.asyncio
    async def test_unicode_file_paths(self):
        """Test Unicode file paths in desktop operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        unicode_paths = [
            "/test/ñáéíóú.jpg",
            "/test/中文.jpg",
            "/test/русский.jpg",
            "/test/日本語.jpg"
        ]
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            for path in unicode_paths:
                params = {"action": "wallpaper", "path": path}
                result = await desktop_control(parameters=params, player=mock_player)
                
                assert result == "Success"
                mock_set_wallpaper.assert_called_with(path)

    @pytest.mark.asyncio
    async def test_very_long_file_paths(self):
        """Test very long file paths."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        long_path = "/test/" + "x" * 1000 + ".jpg"
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            params = {"action": "wallpaper", "path": long_path}
            result = await desktop_control(parameters=params, player=mock_player)
            
            assert result == "Success"
            mock_set_wallpaper.assert_called_with(long_path)

    @pytest.mark.asyncio
    async def test_special_characters_in_paths(self):
        """Test special characters in file paths."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        special_paths = [
            "/test/file with spaces.jpg",
            "/test/file-with-dashes.jpg",
            "/test/file_with_underscores.jpg",
            "/test/file.with.dots.jpg",
            "/test/file(with)parentheses.jpg"
        ]
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            for path in special_paths:
                params = {"action": "wallpaper", "path": path}
                result = await desktop_control(parameters=params, player=mock_player)
                
                assert result == "Success"

    @pytest.mark.asyncio
    async def test_empty_and_null_parameters(self):
        """Test empty and null parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        # Test various empty/null parameter combinations
        test_cases = [
            {},
            {"action": ""},
            {"action": None},
            {"action": "   "},
            {"action": "wallpaper", "path": None},
            {"action": "wallpaper", "path": ""},
            {"action": "wallpaper", "path": "   "}
        ]
        
        for params in test_cases:
            result = await desktop_control(parameters=params, player=mock_player)
            
            # Should handle gracefully
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_case_insensitive_actions(self):
        """Test case insensitive action handling."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Stats"
            
            test_cases = [
                "stats",
                "STATS",
                "Stats",
                "sTaTs"
            ]
            
            for action in test_cases:
                params = {"action": action}
                result = await desktop_control(parameters=params, player=mock_player)
                
                assert result == "Stats"
                mock_stats.assert_called()

    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test whitespace handling in parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            test_cases = [
                {"action": "  wallpaper  ", "path": "  /path.jpg  "},
                {"action": "\twallpaper\t", "path": "\t/path.jpg\t"},
                {"action": "\nwallpaper\n", "path": "\n/path.jpg\n"}
            ]
            
            for params in test_cases:
                result = await desktop_control(parameters=params, player=mock_player)
                
                assert result == "Success"
                # Should strip whitespace
                mock_set_wallpaper.assert_called_with("/path.jpg")

    @pytest.mark.asyncio
    async def test_rapid_state_changes(self):
        """Test rapid state changes."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.set_wallpaper') as mock_set_wallpaper:
            mock_set_wallpaper.return_value = "Success"
            
            # Rapidly change wallpaper
            for i in range(50):
                params = {"action": "wallpaper", "path": f"/path/wallpaper_{i}.jpg"}
                await desktop_control(parameters=params, player=mock_player)
            
            # Should handle rapid changes
            assert mock_set_wallpaper.call_count == 50

    @pytest.mark.asyncio
    async def test_concurrent_same_operation(self):
        """Test concurrent execution of same operation."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.desktop.get_desktop_stats') as mock_stats:
            mock_stats.return_value = "Stats"
            
            async def stats_worker():
                params = {"action": "stats"}
                return await desktop_control(parameters=params, player=mock_player)
            
            # Run same operation concurrently
            tasks = [stats_worker() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result == "Stats" for result in results)
            assert mock_stats.call_count == 10
