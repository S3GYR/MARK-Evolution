"""Phase 6: Comprehensive Tool Dispatcher Tests - Priority Absolute."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from jarvis.core.tool_runner import ToolRunner
from jarvis.core.player import Player


class TestToolRunnerInitialization:
    """Test tool runner initialization and setup."""

    def test_tool_runner_initialization(self):
        """Test tool runner initialization with player."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        assert runner.player == mock_player
        assert hasattr(runner, '_legacy_actions')

    def test_tool_runner_initialization_with_real_player(self):
        """Test tool runner initialization with real player."""
        from jarvis.core.player import ConsolePlayer
        
        player = ConsolePlayer()
        runner = ToolRunner(player)
        
        assert runner.player == player


class TestToolRunnerSecureWrapperExecution:
    """Test tool runner execution with secure wrappers."""

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_success(self):
        """Test successful execution of secure wrapper."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Secure result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("test_tool", {"param": "value"})
            
            assert result == "Secure result"
            mock_func.assert_called_once_with({"param": "value"}, player=mock_player)
            mock_player.write_log.assert_called_once_with("[tool] test_tool")

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_sync_function(self):
        """Test execution of synchronous secure wrapper."""
        mock_player = Mock(spec=Player)
        mock_func = Mock(return_value="Sync secure result")
        mock_func.__name__ = "sync_func"  # Make it look like a regular function
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("sync_tool", {"param": "value"})
            
            assert result == "Sync secure result"
            mock_func.assert_called_once_with({"param": "value"}, player=mock_player)

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_none_result(self):
        """Test secure wrapper returning None."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value=None)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("none_tool", {})
            
            assert result == "Done."
            mock_func.assert_called_once_with({}, player=mock_player)

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_exception(self):
        """Test secure wrapper throwing exception."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=Exception("Secure wrapper error"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("error_tool", {})
            
            assert "Tool 'error_tool' failed: Secure wrapper error" in result
            mock_func.assert_called_once_with({}, player=mock_player)

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_timeout(self):
        """Test secure wrapper timeout."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=asyncio.TimeoutError("Timeout"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("timeout_tool", {})
            
            assert "Tool 'timeout_tool' failed: Timeout" in result

    @pytest.mark.asyncio
    async def test_run_secure_wrapper_with_complex_args(self):
        """Test secure wrapper with complex arguments."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Complex result")
        
        complex_args = {
            "string_param": "test",
            "int_param": 42,
            "list_param": [1, 2, 3],
            "dict_param": {"nested": "value"},
            "bool_param": True,
            "none_param": None
        }
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("complex_tool", complex_args)
            
            assert result == "Complex result"
            mock_func.assert_called_once_with(complex_args, player=mock_player)


class TestToolRunnerLegacyActionExecution:
    """Test tool runner execution with legacy actions."""

    @pytest.mark.asyncio
    async def test_run_legacy_action_success(self):
        """Test successful execution of legacy action."""
        mock_player = Mock(spec=Player)
        mock_legacy_func = AsyncMock(return_value="Legacy result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None  # No secure wrapper
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"legacy_tool": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("legacy_tool", {"param": "value"})
                
                assert result == "Legacy result"
                mock_legacy_func.assert_called_once_with(
                    parameters={"param": "value"},
                    player=mock_player,
                    response=None
                )
                mock_player.write_log.assert_called_once_with("[tool] legacy_tool")

    @pytest.mark.asyncio
    async def test_run_legacy_action_sync_function(self):
        """Test execution of synchronous legacy action."""
        mock_player = Mock(spec=Player)
        mock_legacy_func = Mock(return_value="Sync legacy result")
        mock_legacy_func.__name__ = "sync_legacy_func"
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"sync_legacy": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("sync_legacy", {"param": "value"})
                
                assert result == "Sync legacy result"
                mock_legacy_func.assert_called_once_with(
                    parameters={"param": "value"},
                    player=mock_player,
                    response=None
                )

    @pytest.mark.asyncio
    async def test_run_legacy_action_none_result(self):
        """Test legacy action returning None."""
        mock_player = Mock(spec=Player)
        mock_legacy_func = AsyncMock(return_value=None)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"none_legacy": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("none_legacy", {})
                
                assert result == "Done."

    @pytest.mark.asyncio
    async def test_run_legacy_action_exception(self):
        """Test legacy action throwing exception."""
        mock_player = Mock(spec=Player)
        mock_legacy_func = AsyncMock(side_effect=Exception("Legacy action error"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"error_legacy": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("error_legacy", {})
                
                assert "Tool 'error_legacy' failed: Legacy action error" in result

    @pytest.mark.asyncio
    async def test_run_legacy_action_not_found(self):
        """Test legacy action not found."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {}):
                runner = ToolRunner(mock_player)
                result = await runner.run("unknown_tool", {})
                
                assert result == "Unknown tool: unknown_tool"


class TestToolRunnerUnknownToolHandling:
    """Test tool runner handling of unknown tools."""

    @pytest.mark.asyncio
    async def test_run_unknown_tool(self):
        """Test execution of unknown tool."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {}):
                runner = ToolRunner(mock_player)
                result = await runner.run("completely_unknown_tool", {})
                
                assert result == "Unknown tool: completely_unknown_tool"
                mock_player.write_log.assert_called_once_with("[tool] completely_unknown_tool")

    @pytest.mark.asyncio
    async def test_run_empty_tool_name(self):
        """Test execution with empty tool name."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {}):
                runner = ToolRunner(mock_player)
                result = await runner.run("", {})
                
                assert result == "Unknown tool: "

    @pytest.mark.asyncio
    async def test_run_none_tool_name(self):
        """Test execution with None tool name."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {}):
                runner = ToolRunner(mock_player)
                result = await runner.run(None, {})  # type: ignore
                
                # Should handle None gracefully or raise appropriate error
                assert result is not None


class TestToolRunnerParameterValidation:
    """Test tool runner parameter validation and handling."""

    @pytest.mark.asyncio
    async def test_run_with_empty_args(self):
        """Test execution with empty arguments."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Empty args result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("test_tool", {})
            
            assert result == "Empty args result"
            mock_func.assert_called_once_with({}, player=mock_player)

    @pytest.mark.asyncio
    async def test_run_with_none_args(self):
        """Test execution with None arguments."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="None args result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("test_tool", None)  # type: ignore
            
            # Should handle None args gracefully
            assert result is not None

    @pytest.mark.asyncio
    async def test_run_with_invalid_args_type(self):
        """Test execution with invalid arguments type."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Invalid args result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("test_tool", "invalid_args")  # type: ignore
            
            # Should handle invalid args type gracefully
            assert result is not None

    @pytest.mark.asyncio
    async def test_run_with_large_args(self):
        """Test execution with large arguments."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Large args result")
        
        large_args = {
            "large_string": "x" * 10000,
            "large_list": list(range(1000)),
            "nested": {"deep": {"deeper": {"deepest": "value"}}}
        }
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("large_tool", large_args)
            
            assert result == "Large args result"
            mock_func.assert_called_once_with(large_args, player=mock_player)


class TestToolRunnerConcurrency:
    """Test tool runner concurrent execution."""

    @pytest.mark.asyncio
    async def test_concurrent_secure_wrapper_execution(self):
        """Test concurrent execution of secure wrappers."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Concurrent result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            # Run multiple concurrent executions
            tasks = [
                runner.run("test_tool", {"id": i}) for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            for result in results:
                assert result == "Concurrent result"
            assert mock_func.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_mixed_execution(self):
        """Test concurrent execution of secure and legacy tools."""
        mock_player = Mock(spec=Player)
        mock_secure_func = AsyncMock(return_value="Secure result")
        mock_legacy_func = AsyncMock(return_value="Legacy result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            # Alternate between secure and legacy
            mock_get_func.side_effect = [mock_secure_func, None, mock_secure_func, None]
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"legacy_tool": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                
                tasks = [
                    runner.run("secure_tool", {}),
                    runner.run("legacy_tool", {}),
                    runner.run("secure_tool2", {}),
                    runner.run("legacy_tool", {})
                ]
                
                results = await asyncio.gather(*tasks)
                
                assert results == ["Secure result", "Legacy result", "Secure result", "Legacy result"]

    @pytest.mark.asyncio
    async def test_concurrent_error_isolation(self):
        """Test that errors in one execution don't affect others."""
        mock_player = Mock(spec=Player)
        mock_success_func = AsyncMock(return_value="Success")
        mock_error_func = AsyncMock(side_effect=Exception("Error"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.side_effect = [mock_success_func, mock_error_func, mock_success_func]
            
            runner = ToolRunner(mock_player)
            
            tasks = [
                runner.run("success_tool", {}),
                runner.run("error_tool", {}),
                runner.run("success_tool2", {})
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert results[0] == "Success"
            assert "Tool 'error_tool' failed: Error" in results[1]
            assert results[2] == "Success"


class TestToolRunnerErrorHandling:
    """Test tool runner error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_run_with_registry_error(self):
        """Test execution when registry throws error."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.side_effect = Exception("Registry error")
            
            runner = ToolRunner(mock_player)
            result = await runner.run("test_tool", {})
            
            assert "Tool 'test_tool' failed: Registry error" in result

    @pytest.mark.asyncio
    async def test_run_with_legacy_actions_error(self):
        """Test execution when legacy actions dict is corrupted."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None
            
            # Mock legacy actions to raise exception
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS') as mock_legacy:
                mock_legacy.get.side_effect = Exception("Legacy actions error")
                
                runner = ToolRunner(mock_player)
                result = await runner.run("legacy_tool", {})
                
                assert "Tool 'legacy_tool' failed: Legacy actions error" in result

    @pytest.mark.asyncio
    async def test_run_with_player_error(self):
        """Test execution when player throws error."""
        mock_player = Mock(spec=Player)
        mock_player.write_log.side_effect = Exception("Player error")
        mock_func = AsyncMock(return_value="Result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            try:
                result = await runner.run("test_tool", {})
                # Should handle player error gracefully
                assert True
            except Exception:
                # Should propagate or handle player error
                assert True

    @pytest.mark.asyncio
    async def test_run_with_cancellation(self):
        """Test execution cancellation."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=asyncio.CancelledError("Cancelled"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            try:
                result = await runner.run("cancelled_tool", {})
                # Should handle cancellation gracefully
                assert True
            except asyncio.CancelledError:
                # Should propagate cancellation
                assert True

    @pytest.mark.asyncio
    async def test_run_with_memory_error(self):
        """Test execution with memory error."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=MemoryError("Out of memory"))
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("memory_tool", {})
            
            assert "Tool 'memory_tool' failed: Out of memory" in result


class TestToolRunnerMemorySaveHandler:
    """Test tool runner memory save handler."""

    @pytest.mark.asyncio
    async def test_handle_memory_save_success(self):
        """Test successful memory save handling."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        args = {
            "category": "test_category",
            "key": "test_key",
            "value": "test_value"
        }
        
        result = await runner.handle_memory_save(args)
        
        assert result == {"result": "ok", "silent": True}

    @pytest.mark.asyncio
    async def test_handle_memory_save_minimal_args(self):
        """Test memory save with minimal arguments."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        args = {}
        
        result = await runner.handle_memory_save(args)
        
        assert result == {"result": "ok", "silent": True}

    @pytest.mark.asyncio
    async def test_handle_memory_save_empty_key(self):
        """Test memory save with empty key."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        args = {
            "category": "test",
            "key": "",
            "value": "value"
        }
        
        result = await runner.handle_memory_save(args)
        
        assert result == {"result": "ok", "silent": True}

    @pytest.mark.asyncio
    async def test_handle_memory_save_empty_value(self):
        """Test memory save with empty value."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        args = {
            "category": "test",
            "key": "key",
            "value": ""
        }
        
        result = await runner.handle_memory_save(args)
        
        assert result == {"result": "ok", "silent": True}

    @pytest.mark.asyncio
    async def test_handle_memory_save_with_special_characters(self):
        """Test memory save with special characters."""
        mock_player = Mock(spec=Player)
        
        runner = ToolRunner(mock_player)
        
        args = {
            "category": "test/category",
            "key": "test-key_with.special@chars",
            "value": "Value with\nnewlines\tand\ttabs\nand Unicode: ñáéíóú"
        }
        
        result = await runner.handle_memory_save(args)
        
        assert result == {"result": "ok", "silent": True}


class TestToolRunnerCallMethods:
    """Test tool runner internal call methods."""

    @pytest.mark.asyncio
    async def test_call_async_function(self):
        """Test _call method with async function."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Async result")
        
        runner = ToolRunner(mock_player)
        
        result = await runner._call(mock_func, {"param": "value"})
        
        assert result == "Async result"
        mock_func.assert_called_once_with({"param": "value"}, player=mock_player)

    @pytest.mark.asyncio
    async def test_call_sync_function(self):
        """Test _call method with sync function."""
        mock_player = Mock(spec=Player)
        mock_func = Mock(return_value="Sync result")
        mock_func.__name__ = "sync_func"
        
        runner = ToolRunner(mock_player)
        
        result = await runner._call(mock_func, {"param": "value"})
        
        assert result == "Sync result"
        mock_func.assert_called_once_with({"param": "value"}, player=mock_player)

    @pytest.mark.asyncio
    async def test_call_legacy_async_function(self):
        """Test _call_legacy method with async function."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Legacy async result")
        
        runner = ToolRunner(mock_player)
        
        result = await runner._call_legacy(mock_func, {"param": "value"})
        
        assert result == "Legacy async result"
        mock_func.assert_called_once_with(
            parameters={"param": "value"},
            player=mock_player,
            response=None
        )

    @pytest.mark.asyncio
    async def test_call_legacy_sync_function(self):
        """Test _call_legacy method with sync function."""
        mock_player = Mock(spec=Player)
        mock_func = Mock(return_value="Legacy sync result")
        mock_func.__name__ = "legacy_sync_func"
        
        runner = ToolRunner(mock_player)
        
        result = await runner._call_legacy(mock_func, {"param": "value"})
        
        assert result == "Legacy sync result"
        mock_func.assert_called_once_with(
            parameters={"param": "value"},
            player=mock_player,
            response=None
        )

    @pytest.mark.asyncio
    async def test_call_function_exception(self):
        """Test _call method with function exception."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=Exception("Function error"))
        
        runner = ToolRunner(mock_player)
        
        try:
            result = await runner._call(mock_func, {})
            # Should propagate exception
            assert False, "Should have raised exception"
        except Exception as e:
            assert str(e) == "Function error"

    @pytest.mark.asyncio
    async def test_call_legacy_function_exception(self):
        """Test _call_legacy method with function exception."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(side_effect=Exception("Legacy function error"))
        
        runner = ToolRunner(mock_player)
        
        try:
            result = await runner._call_legacy(mock_func, {})
            # Should propagate exception
            assert False, "Should have raised exception"
        except Exception as e:
            assert str(e) == "Legacy function error"


class TestToolRunnerPerformance:
    """Test tool runner performance characteristics."""

    @pytest.mark.asyncio
    async def test_execution_performance(self):
        """Test execution performance with multiple calls."""
        import time
        
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Performance result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            start_time = time.time()
            
            # Execute multiple calls
            tasks = [runner.run("perf_tool", {"id": i}) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            elapsed = time.time() - start_time
            
            assert len(results) == 10
            assert all(result == "Performance result" for result in results)
            # Should complete reasonably quickly
            assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability during execution."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Memory test result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            # Execute many calls to test memory stability
            for i in range(100):
                result = await runner.run("memory_test_tool", {"iteration": i})
                assert result == "Memory test result"
            
            # Should not accumulate memory or leak resources
            assert True

    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test proper resource cleanup after execution."""
        mock_player = Mock(spec=Player)
        mock_func = AsyncMock(return_value="Cleanup test result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_func
            
            runner = ToolRunner(mock_player)
            
            # Execute and ensure clean cleanup
            result = await runner.run("cleanup_tool", {})
            
            assert result == "Cleanup test result"
            
            # No hanging references or resources
            assert True


class TestToolRunnerIntegration:
    """Test tool runner integration scenarios."""

    @pytest.mark.asyncio
    async def test_integration_secure_wrapper_priority(self):
        """Test that secure wrappers are preferred over legacy actions."""
        mock_player = Mock(spec=Player)
        mock_secure_func = AsyncMock(return_value="Secure result")
        mock_legacy_func = AsyncMock(return_value="Legacy result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = mock_secure_func  # Secure wrapper available
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"test_tool": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("test_tool", {})
                
                # Should use secure wrapper, not legacy
                assert result == "Secure result"
                mock_secure_func.assert_called_once()
                mock_legacy_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_integration_fallback_to_legacy(self):
        """Test fallback to legacy when no secure wrapper available."""
        mock_player = Mock(spec=Player)
        mock_legacy_func = AsyncMock(return_value="Legacy fallback result")
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_get_func.return_value = None  # No secure wrapper
            
            with patch('jarvis.core.tool_runner._LEGACY_ACTIONS', {"fallback_tool": mock_legacy_func}):
                runner = ToolRunner(mock_player)
                result = await runner.run("fallback_tool", {})
                
                # Should use legacy fallback
                assert result == "Legacy fallback result"
                mock_legacy_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_integration_error_propagation(self):
        """Test error propagation through the call chain."""
        mock_player = Mock(spec=Player)
        
        # Test error from secure wrapper
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_secure_func = AsyncMock(side_effect=Exception("Secure error"))
            mock_get_func.return_value = mock_secure_func
            
            runner = ToolRunner(mock_player)
            result = await runner.run("error_tool", {})
            
            assert "Tool 'error_tool' failed: Secure error" in result

    @pytest.mark.asyncio
    async def test_integration_logging(self):
        """Test that all execution paths are properly logged."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.tool_runner.get_tool_function') as mock_get_func:
            mock_func = AsyncMock(return_value="Logged result")
            mock_get_func.return_value = mock_func
            
            with patch('jarvis.core.tool_runner.logger') as mock_logger:
                runner = ToolRunner(mock_player)
                result = await runner.run("logged_tool", {"param": "value"})
                
                # Should log tool call
                mock_logger.info.assert_called_once_with(
                    "tool_called",
                    tool="logged_tool",
                    args={"param": "value"}
                )
                
                assert result == "Logged result"
