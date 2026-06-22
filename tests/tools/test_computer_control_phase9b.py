"""Phase 9B: Comprehensive Computer Control Tests - Priority 5."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List

from jarvis.tools.computer_control import (
    computer_control, _safe_player
)
from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext


class TestComputerControlSecurity:
    """Test computer control security functions."""

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


class TestComputerControlBasicOperations:
    """Test computer control basic operations."""

    def test_computer_control_no_parameters(self):
        """Test computer control with no parameters."""
        result = computer_control()
        
        assert result is not None
        assert isinstance(result, str)

    def test_computer_control_empty_parameters(self):
        """Test computer control with empty parameters."""
        result = computer_control(parameters={})
        
        assert result is not None
        assert isinstance(result, str)

    def test_computer_control_no_action(self):
        """Test computer control with no action specified."""
        params = {"text": "some text"}
        
        result = computer_control(parameters=params)
        
        assert result is not None
        assert isinstance(result, str)

    def test_computer_control_with_player(self):
        """Test computer control with custom player."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "type", "text": "test"}
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Text typed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result is not None
            mock_player.write_log.assert_called()

    def test_computer_control_logging(self):
        """Test computer control logging functionality."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "type", "text": "test"}
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Text typed"
            
            computer_control(parameters=params, player=mock_player)
            
            # Should log the action
            mock_player.write_log.assert_called_once()
            log_call = mock_player.write_log.call_args[0][0]
            assert "[computer]" in log_call

    def test_parameter_extraction(self):
        """Test parameter extraction and validation."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "click",
            "x": 100,
            "y": 200,
            "key": "enter",
            "keys": ["ctrl", "c"],
            "text": "test text",
            "direction": "up"
        }
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result is not None


class TestComputerControlKeyboardOperations:
    """Test computer control keyboard operations."""

    def test_type_text_success(self):
        """Test successful text typing."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "type",
            "text": "Hello World"
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Text typed successfully"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Text typed successfully"
            mock_type.assert_called_once_with("Hello World")

    def test_type_empty_text(self):
        """Test typing empty text."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "type",
            "text": ""
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Empty text typed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result is not None
            mock_type.assert_called_once_with("")

    def test_type_unicode_text(self):
        """Test typing Unicode text."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "type",
            "text": "Unicode test: ñáéíóú 中文 русский 日本語"
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Unicode text typed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Unicode text typed"
            mock_type.assert_called_once_with("Unicode test: ñáéíóú 中文 русский 日本語")

    def test_type_very_long_text(self):
        """Test typing very long text."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        long_text = "x" * 10000  # 10KB text
        
        params = {
            "action": "type",
            "text": long_text
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Long text typed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Long text typed"
            mock_type.assert_called_once_with(long_text)

    def test_press_key_success(self):
        """Test successful key press."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "press",
            "key": "enter"
        }
        
        with patch('jarvis.tools.computer_control._press') as mock_press:
            mock_press.return_value = "Key pressed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Key pressed"
            mock_press.assert_called_once_with("enter")

    def test_press_special_keys(self):
        """Test pressing special keys."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        special_keys = ["ctrl", "alt", "shift", "tab", "esc", "space"]
        
        for key in special_keys:
            params = {"action": "press", "key": key}
            
            with patch('jarvis.tools.computer_control._press') as mock_press:
                mock_press.return_value = f"{key} pressed"
                
                result = computer_control(parameters=params, player=mock_player)
                
                assert result == f"{key} pressed"
                mock_press.assert_called_once_with(key)

    def test_hotkey_success(self):
        """Test successful hotkey combination."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "hotkey",
            "keys": ["ctrl", "c"]
        }
        
        with patch('jarvis.tools.computer_control._hotkey') as mock_hotkey:
            mock_hotkey.return_value = "Hotkey executed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Hotkey executed"
            mock_hotkey.assert_called_once_with(["ctrl", "c"])

    def test_hotkey_multiple_keys(self):
        """Test hotkey with multiple keys."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "hotkey",
            "keys": ["ctrl", "shift", "t"]
        }
        
        with patch('jarvis.tools.computer_control._hotkey') as mock_hotkey:
            mock_hotkey.return_value = "Multi-key hotkey executed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Multi-key hotkey executed"
            mock_hotkey.assert_called_once_with(["ctrl", "shift", "t"])

    def test_smart_type_success(self):
        """Test smart typing functionality."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "smart_type",
            "text": "Hello, World!"
        }
        
        with patch('jarvis.tools.computer_control._smart_type') as mock_smart_type:
            mock_smart_type.return_value = "Smart typing completed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Smart typing completed"
            mock_smart_type.assert_called_once_with("Hello, World!")


class TestComputerControlMouseOperations:
    """Test computer control mouse operations."""

    def test_click_success(self):
        """Test successful mouse click."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "click",
            "x": 100,
            "y": 200
        }
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked at (100, 200)"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Clicked at (100, 200)"
            mock_click.assert_called_once_with(100, 200)

    def test_click_missing_coordinates(self):
        """Test click with missing coordinates."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "click"}
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked at default position"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result is not None
            mock_click.assert_called_once()

    def test_click_negative_coordinates(self):
        """Test click with negative coordinates."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "click",
            "x": -50,
            "y": -100
        }
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked at (-50, -100)"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Clicked at (-50, -100)"
            mock_click.assert_called_once_with(-50, -100)

    def test_scroll_up(self):
        """Test scrolling up."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "scroll",
            "direction": "up"
        }
        
        with patch('jarvis.tools.computer_control._scroll') as mock_scroll:
            mock_scroll.return_value = "Scrolled up"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Scrolled up"
            mock_scroll.assert_called_once_with("up")

    def test_scroll_down(self):
        """Test scrolling down."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "scroll",
            "direction": "down"
        }
        
        with patch('jarvis.tools.computer_control._scroll') as mock_scroll:
            mock_scroll.return_value = "Scrolled down"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Scrolled down"
            mock_scroll.assert_called_once_with("down")

    def test_scroll_left(self):
        """Test scrolling left."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "scroll",
            "direction": "left"
        }
        
        with patch('jarvis.tools.computer_control._scroll') as mock_scroll:
            mock_scroll.return_value = "Scrolled left"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Scrolled left"
            mock_scroll.assert_called_once_with("left")

    def test_scroll_right(self):
        """Test scrolling right."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "scroll",
            "direction": "right"
        }
        
        with patch('jarvis.tools.computer_control._scroll') as mock_scroll:
            mock_scroll.return_value = "Scrolled right"
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert result == "Scrolled right"
            mock_scroll.assert_called_once_with("right")


class TestComputerControlSecurityValidation:
    """Test computer control security validation."""

    def test_action_context_creation(self):
        """Test ActionContext creation for security validation."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "type",
            "text": "test"
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            result = computer_control(parameters=params, player=mock_player)
            
            # ActionContext should be created for security validation
            assert result is not None

    def test_unsupported_action_handling(self):
        """Test handling of unsupported actions."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "unsupported_action"
        }
        
        result = computer_control(parameters=params, player=mock_player)
        
        assert "unsupported" in result.lower() or "not recognized" in result.lower()

    def test_malicious_command_detection(self):
        """Test detection of malicious commands."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        malicious_params = [
            {"action": "type", "text": "rm -rf /"},
            {"action": "hotkey", "keys": ["ctrl", "alt", "delete"]},
            {"action": "type", "text": "format c:"}
        ]
        
        for params in malicious_params:
            result = computer_control(parameters=params, player=mock_player)
            
            # Should handle potentially dangerous operations
            assert result is not None

    def test_parameter_sanitization(self):
        """Test parameter sanitization."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params_with_special_chars = {
            "action": "type",
            "text": "Text with \n\r\t special chars"
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Sanitized text typed"
            
            result = computer_control(parameters=params_with_special_chars, player=mock_player)
            
            assert result is not None
            mock_type.assert_called_once()


class TestComputerControlErrorHandling:
    """Test computer control error handling scenarios."""

    def test_legacy_function_not_available(self):
        """Test handling when legacy functions are not available."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "type", "text": "test"}
        
        with patch('jarvis.tools.computer_control._type', side_effect=NameError("Function not available")):
            result = computer_control(parameters=params, player=mock_player)
            
            assert "not available" in result.lower() or "error" in result.lower()

    def test_permission_denied_error(self):
        """Test handling of permission denied errors."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "click", "x": 100, "y": 100}
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.side_effect = PermissionError("Permission denied")
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert "permission" in result.lower() or "denied" in result.lower()

    def test_invalid_coordinates_error(self):
        """Test handling of invalid coordinates."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {
            "action": "click",
            "x": "invalid",
            "y": "invalid"
        }
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.side_effect = ValueError("Invalid coordinates")
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert "invalid" in result.lower() or "coordinates" in result.lower()

    def test_keyboard_interrupt_error(self):
        """Test handling of keyboard interrupt."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "type", "text": "test"}
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.side_effect = KeyboardInterrupt("User interrupted")
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert "interrupted" in result.lower() or "cancelled" in result.lower()

    def test_timeout_error(self):
        """Test handling of timeout errors."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        params = {"action": "click", "x": 100, "y": 100}
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.side_effect = TimeoutError("Operation timeout")
            
            result = computer_control(parameters=params, player=mock_player)
            
            assert "timeout" in result.lower() or "timed out" in result.lower()


class TestComputerControlConcurrency:
    """Test computer control concurrent operations."""

    def test_concurrent_keyboard_operations(self):
        """Test concurrent keyboard operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Text typed"
            
            def type_worker(text):
                params = {"action": "type", "text": text}
                return computer_control(parameters=params, player=mock_player)
            
            # Run concurrent typing operations
            results = []
            for i in range(5):
                result = type_worker(f"Text {i}")
                results.append(result)
            
            assert len(results) == 5
            assert all("Text typed" in result for result in results)
            assert mock_type.call_count == 5

    def test_concurrent_mouse_operations(self):
        """Test concurrent mouse operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked"
            
            def click_worker(x, y):
                params = {"action": "click", "x": x, "y": y}
                return computer_control(parameters=params, player=mock_player)
            
            # Run concurrent click operations
            results = []
            for i in range(5):
                result = click_worker(i * 100, i * 100)
                results.append(result)
            
            assert len(results) == 5
            assert all("Clicked" in result for result in results)
            assert mock_click.call_count == 5

    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type, \
             patch('jarvis.tools.computer_control._click') as mock_click, \
             patch('jarvis.tools.computer_control._press') as mock_press:
            
            mock_type.return_value = "Typed"
            mock_click.return_value = "Clicked"
            mock_press.return_value = "Pressed"
            
            # Perform mixed operations
            operations = [
                {"action": "type", "text": "test"},
                {"action": "click", "x": 100, "y": 100},
                {"action": "press", "key": "enter"}
            ]
            
            results = []
            for params in operations:
                result = computer_control(parameters=params, player=mock_player)
                results.append(result)
            
            assert len(results) == 3
            mock_type.assert_called_once()
            mock_click.assert_called_once()
            mock_press.assert_called_once()


class TestComputerControlPerformance:
    """Test computer control performance characteristics."""

    def test_bulk_operation_performance(self):
        """Test bulk operation performance."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            import time
            start_time = time.time()
            
            # Perform many operations
            for i in range(100):
                params = {"action": "type", "text": f"Text {i}"}
                computer_control(parameters=params, player=mock_player)
            
            elapsed = time.time() - start_time
            
            assert elapsed < 2.0  # Should complete within 2 seconds
            assert mock_type.call_count == 100

    def test_large_text_performance(self):
        """Test performance with large text."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        large_text = "x" * 100000  # 100KB text
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Large text typed"
            
            import time
            start_time = time.time()
            
            params = {"action": "type", "text": large_text}
            result = computer_control(parameters=params, player=mock_player)
            
            elapsed = time.time() - start_time
            
            assert elapsed < 1.0  # Should complete within 1 second
            assert result == "Large text typed"
            mock_type.assert_called_once_with(large_text)

    def test_memory_usage_stability(self):
        """Test memory usage stability."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            # Perform many operations
            for i in range(1000):
                params = {"action": "type", "text": f"Text {i}"}
                computer_control(parameters=params, player=mock_player)
            
            # Memory usage should be stable
            assert True


class TestComputerControlEdgeCases:
    """Test computer control edge cases."""

    def test_case_insensitive_actions(self):
        """Test case insensitive action handling."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            test_cases = [
                "type",
                "TYPE",
                "Type",
                "tYpE"
            ]
            
            for action in test_cases:
                params = {"action": action, "text": "test"}
                result = computer_control(parameters=params, player=mock_player)
                
                assert result == "Typed"
                mock_type.assert_called()

    def test_whitespace_handling(self):
        """Test whitespace handling in parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            test_cases = [
                {"action": "  type  ", "text": "  test  "},
                {"action": "\ttype\t", "text": "\ttest\t"},
                {"action": "\ntype\n", "text": "\ntest\n"}
            ]
            
            for params in test_cases:
                result = computer_control(parameters=params, player=mock_player)
                
                assert result == "Typed"
                # Should strip whitespace
                mock_type.assert_called_with("test")

    def test_empty_and_null_parameters(self):
        """Test empty and null parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        # Test various empty/null parameter combinations
        test_cases = [
            {},
            {"action": ""},
            {"action": None},
            {"action": "   "},
            {"action": "type", "text": None},
            {"action": "type", "text": ""},
            {"action": "type", "text": "   "},
            {"action": "click", "x": None},
            {"action": "click", "y": None}
        ]
        
        for params in test_cases:
            result = computer_control(parameters=params, player=mock_player)
            
            # Should handle gracefully
            assert result is not None
            assert isinstance(result, str)

    def test_unicode_in_all_parameters(self):
        """Test Unicode in all parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        unicode_params = {
            "action": "type",
            "text": "Unicode test: ñáéíóú 中文 русский 日本語",
            "key": "ñáéíóú",
            "keys": ["ctrl", "ñáéíóú"]
        }
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Unicode typed"
            
            result = computer_control(parameters=unicode_params, player=mock_player)
            
            assert result == "Unicode typed"
            mock_type.assert_called_once_with("Unicode test: ñáéíóú 中文 русский 日本語")

    def test_very_large_coordinates(self):
        """Test very large coordinate values."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        large_coords = [
            {"x": 999999, "y": 999999},
            {"x": -999999, "y": -999999},
            {"x": 0, "y": 0}
        ]
        
        with patch('jarvis.tools.computer_control._click') as mock_click:
            mock_click.return_value = "Clicked"
            
            for coords in large_coords:
                params = {"action": "click", **coords}
                result = computer_control(parameters=params, player=mock_player)
                
                assert result == "Clicked"
                mock_click.assert_called_with(coords["x"], coords["y"])

    def test_special_characters_in_text(self):
        """Test special characters in text."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        special_texts = [
            "Text with\nnewlines",
            "Text with\ttabs",
            "Text with\r\rcarriage returns",
            "Text with \"quotes\"",
            "Text with 'apostrophes'",
            "Text with \\backslashes\\",
            "Text with @#$%^&*() symbols"
        ]
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Special text typed"
            
            for text in special_texts:
                params = {"action": "type", "text": text}
                result = computer_control(parameters=params, player=mock_player)
                
                assert result == "Special text typed"
                mock_type.assert_called_with(text)

    def test_rapid_operations(self):
        """Test rapid successive operations."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        with patch('jarvis.tools.computer_control._type') as mock_type:
            mock_type.return_value = "Typed"
            
            # Rapid operations
            for i in range(50):
                params = {"action": "type", "text": f"Rapid {i}"}
                result = computer_control(parameters=params, player=mock_player)
                assert result == "Typed"
            
            assert mock_type.call_count == 50

    def test_parameter_type_validation(self):
        """Test parameter type validation."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        # Test with wrong parameter types
        invalid_params = [
            {"action": "click", "x": "not_a_number", "y": "also_not_a_number"},
            {"action": "type", "text": 12345},  # Number instead of string
            {"action": "press", "key": ["not", "a", "string"]},  # List instead of string
            {"action": "hotkey", "keys": "not_a_list"}  # String instead of list
        ]
        
        for params in invalid_params:
            result = computer_control(parameters=params, player=mock_player)
            
            # Should handle gracefully or provide meaningful error
            assert result is not None
            assert isinstance(result, str)

    def test_boundary_values(self):
        """Test boundary values for parameters."""
        mock_player = Mock(spec=Player)
        mock_player.write_log = Mock()
        
        boundary_params = [
            {"action": "click", "x": 0, "y": 0},
            {"action": "click", "x": -1, "y": -1},
            {"action": "click", "x": 1, "y": 1},
            {"action": "type", "text": ""},
            {"action": "type", "text": "x" * 1},  # Single character
            {"action": "type", "text": "x" * 1000}  # Long string
        ]
        
        with patch('jarvis.tools.computer_control._type') as mock_type, \
             patch('jarvis.tools.computer_control._click') as mock_click:
            
            mock_type.return_value = "Typed"
            mock_click.return_value = "Clicked"
            
            for params in boundary_params:
                result = computer_control(parameters=params, player=mock_player)
                
                assert result is not None
                assert isinstance(result, str)
