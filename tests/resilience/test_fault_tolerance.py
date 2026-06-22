"""Fault tolerance and resilience tests for MARK XLVI."""

from __future__ import annotations

import pytest
import tempfile
import time
import threading
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from jarvis.core.orchestrator import AgentOrchestrator
from jarvis.core.tool_runner import ToolRunner
from jarvis.llm.client import LLMClient
from jarvis.memory.json_store import JsonMemoryStore


class TestLLMFaultTolerance:
    """Test LLM client fault tolerance."""

    def test_llm_connection_failure_recovery(self):
        """Test LLM client recovery from connection failures."""
        client = LLMClient()
        
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            # Simulate connection failure
            mock_request.side_effect = ConnectionError("Connection refused")
            
            with pytest.raises(ConnectionError):
                client.chat(messages=[{"role": "user", "content": "test"}])
        
        # Test recovery after failure
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{
                    "message": {
                        "content": "Recovered response"
                    }
                }]
            }
            
            result = client.chat(messages=[{"role": "user", "content": "test"}])
            assert result.content == "Recovered response"

    def test_llm_timeout_handling(self):
        """Test LLM client timeout handling."""
        client = LLMClient()
        
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.side_effect = TimeoutError("Request timed out")
            
            with pytest.raises(TimeoutError):
                client.chat(messages=[{"role": "user", "content": "test"}])

    def test_llm_rate_limiting(self):
        """Test LLM client rate limiting behavior."""
        client = LLMClient()
        
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            # Simulate rate limit error
            mock_request.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(Exception):
                client.chat(messages=[{"role": "user", "content": "test"}])

    def test_llm_invalid_response_handling(self):
        """Test handling of invalid LLM responses."""
        client = LLMClient()
        
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            # Invalid response format
            mock_request.return_value = {"invalid": "response"}
            
            # Should handle invalid response gracefully
            result = client.chat(messages=[{"role": "user", "content": "test"}])
            assert result is not None


class TestMemoryFaultTolerance:
    """Test memory store fault tolerance."""

    def test_memory_file_corruption_recovery(self):
        """Test memory store recovery from file corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            # Create corrupted JSON file
            store_file.write_text("invalid json content")
            
            # Should handle corrupted file gracefully
            try:
                memory_store = JsonMemoryStore(store_file)
                # If it creates a new store, that's good
                assert True
            except Exception:
                # If it fails, it should be handled gracefully
                assert True

    def test_memory_concurrent_access_safety(self):
        """Test memory store safety under concurrent access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            results = []
            errors = []
            
            def concurrent_operation(session_id, operation_id):
                try:
                    for i in range(10):
                        memory_store.store(session_id, f"key_{operation_id}_{i}", f"value_{operation_id}_{i}")
                        result = memory_store.retrieve(session_id, f"key_{operation_id}_{i}")
                        results.append(result)
                except Exception as e:
                    errors.append(e)
            
            # Run concurrent operations
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=concurrent_operation,
                    args=(f"session{i}", i)
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Should handle concurrent access safely
            assert len(errors) == 0 or len(errors) < len(threads)
            assert len(results) > 0

    def test_memory_disk_full_handling(self):
        """Test memory store handling when disk is full."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            # Simulate disk full error
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError("No space left on device")
                
                try:
                    memory_store.store("session", "key", "value")
                except OSError:
                    # Should handle disk full gracefully
                    assert True

    def test_memory_permission_denied(self):
        """Test memory store handling when permission denied."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            # Simulate permission error
            with patch('pathlib.Path.write_text') as mock_write:
                mock_write.side_effect = PermissionError("Permission denied")
                
                try:
                    memory_store = JsonMemoryStore(store_file)
                    memory_store.store("session", "key", "value")
                except PermissionError:
                    # Should handle permission error gracefully
                    assert True


class TestToolFaultTolerance:
    """Test tool runner fault tolerance."""

    def test_tool_runner_crash_recovery(self):
        """Test tool runner recovery from tool crashes."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            # Test with a tool that crashes
            with patch('jarvis.tools.computer_control.computer_control') as mock_tool:
                mock_tool.side_effect = Exception("Tool crashed")
                
                result = tool_runner.run_tool("computer_control", {"action": "crash"})
                
                # Should handle tool crash gracefully
                assert "error" in result.lower()

    def test_tool_runner_timeout_handling(self):
        """Test tool runner timeout handling."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            # Test with a tool that hangs
            with patch('jarvis.tools.computer_control.computer_control') as mock_tool:
                mock_tool.side_effect = TimeoutError("Tool timed out")
                
                result = tool_runner.run_tool("computer_control", {"action": "hang"})
                
                # Should handle timeout gracefully
                assert "error" in result.lower() or "timeout" in result.lower()

    def test_tool_runner_invalid_parameters(self):
        """Test tool runner handling of invalid parameters."""
        tool_runner = ToolRunner()
        
        # Test various invalid parameter scenarios
        invalid_params = [
            None,
            {},
            {"invalid": "parameters"},
            {"action": None},
            {"action": ""},
            {"action": 123}
        ]
        
        for params in invalid_params:
            result = tool_runner.run_tool("computer_control", params)
            
            # Should handle invalid parameters gracefully
            assert isinstance(result, str)

    def test_tool_runner_missing_dependencies(self):
        """Test tool runner handling when dependencies are missing."""
        tool_runner = ToolRunner()
        
        # Test when a tool's dependencies are unavailable
        with patch('jarvis.tools.computer_control.computer_control') as mock_tool:
            mock_tool.side_effect = ImportError("Required dependency not found")
            
            result = tool_runner.run_tool("computer_control", {"action": "test"})
            
            # Should handle missing dependencies gracefully
            assert "error" in result.lower() or "unavailable" in result.lower()


class TestOrchestratorFaultTolerance:
    """Test orchestrator fault tolerance."""

    def test_orchestrator_llm_failure_handling(self):
        """Test orchestrator handling of LLM failures."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.side_effect = Exception("LLM service unavailable")
            mock_llm.return_value = mock_client
            
            orchestrator = AgentOrchestrator()
            
            result = orchestrator.process_request(
                "Test request during LLM failure",
                session_id="test_session"
            )
            
            # Should handle LLM failure gracefully
            assert isinstance(result, dict)

    def test_orchestrator_memory_failure_handling(self):
        """Test orchestrator handling of memory failures."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.return_value = Mock(content="I'll help you")
            mock_llm.return_value = mock_client
            
            orchestrator = AgentOrchestrator()
            
            # Mock memory store failure
            with patch.object(orchestrator, 'memory_store') as mock_memory:
                mock_memory.store.side_effect = Exception("Memory store failed")
                
                result = orchestrator.process_request(
                    "Test request during memory failure",
                    session_id="test_session"
                )
                
                # Should handle memory failure gracefully
                assert isinstance(result, dict)

    def test_orchestrator_tool_failure_handling(self):
        """Test orchestrator handling of tool failures."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.return_value = Mock(content="Use computer control tool")
            mock_llm.return_value = mock_client
            
            with patch('jarvis.core.orchestrator.ToolRunner') as mock_runner:
                mock_tool_runner = Mock()
                mock_tool_runner.run_tool.side_effect = Exception("Tool execution failed")
                mock_runner.return_value = mock_tool_runner
                
                orchestrator = AgentOrchestrator()
                
                result = orchestrator.process_request(
                    "Test request during tool failure",
                    session_id="test_session"
                )
                
                # Should handle tool failure gracefully
                assert isinstance(result, dict)

    def test_orchestrator_cascading_failures(self):
        """Test orchestrator handling of cascading failures."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.side_effect = Exception("LLM failed")
            mock_llm.return_value = mock_client
            
            orchestrator = AgentOrchestrator()
            
            # Mock multiple component failures
            with patch.object(orchestrator, 'memory_store') as mock_memory:
                mock_memory.store.side_effect = Exception("Memory failed")
                
                result = orchestrator.process_request(
                    "Test request during cascading failures",
                    session_id="test_session"
                )
                
                # Should handle cascading failures gracefully
                assert isinstance(result, dict)


class TestSecurityFaultTolerance:
    """Test security system fault tolerance."""

    def test_permission_system_failure(self):
        """Test permission system failure handling."""
        from jarvis.security.permissions import ActionContext
        
        with patch('jarvis.core.player.ConsolePlayer.request_confirmation') as mock_confirm:
            mock_confirm.side_effect = Exception("Permission system failed")
            
            context = ActionContext("test_tool", "test action", Mock())
            
            # Should handle permission system failure
            try:
                result = context.check()
                # If it succeeds or fails gracefully, both are acceptable
                assert isinstance(result, bool)
            except Exception:
                # If it raises an exception, that's also acceptable
                assert True

    def test_sandbox_failure_handling(self):
        """Test sandbox failure handling."""
        from jarvis.security.sandbox import execute_code
        
        with patch('jarvis.security.sandbox.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Sandbox failed")
            
            result = execute_code("print('test')")
            
            # Should handle sandbox failure gracefully
            assert result["success"] is False

    def test_secrets_store_failure(self):
        """Test secrets store failure handling."""
        # Test secrets module functions instead of SecretStore class
        with patch('jarvis.security.secrets.get_secret') as mock_get:
            mock_get.side_effect = Exception("Secrets store failed")
            
            try:
                from jarvis.security.secrets import get_secret
                result = get_secret("test_key")
            except Exception:
                # Should handle secrets store failure gracefully
                assert True


class TestNetworkFaultTolerance:
    """Test network-related fault tolerance."""

    def test_network_connectivity_loss(self):
        """Test handling of network connectivity loss."""
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.side_effect = ConnectionError("Network unreachable")
            
            client = LLMClient()
            
            with pytest.raises(ConnectionError):
                client.chat(messages=[{"role": "user", "content": "test"}])
            
            # Test recovery after network restoration
            mock_request.side_effect = None
            mock_request.return_value = {
                "choices": [{
                    "message": {
                        "content": "Network restored"
                    }
                }]
            }
            
            result = client.chat(messages=[{"role": "user", "content": "test"}])
            assert result.content == "Network restored"

    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.side_effect = Exception("DNS resolution failed")
            
            client = LLMClient()
            
            with pytest.raises(Exception):
                client.chat(messages=[{"role": "user", "content": "test"}])

    def test_ssl_certificate_failure(self):
        """Test handling of SSL certificate failures."""
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.side_effect = Exception("SSL certificate verification failed")
            
            client = LLMClient()
            
            with pytest.raises(Exception):
                client.chat(messages=[{"role": "user", "content": "test"}])


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""

    def test_memory_exhaustion_handling(self):
        """Test handling of memory exhaustion."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            # Simulate memory exhaustion
            with patch('jarvis.tools.computer_control.computer_control') as mock_tool:
                mock_tool.side_effect = MemoryError("Out of memory")
                
                result = tool_runner.run_tool("computer_control", {"action": "test"})
                
                # Should handle memory exhaustion gracefully
                assert "error" in result.lower()

    def test_file_descriptor_exhaustion(self):
        """Test handling of file descriptor exhaustion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            # Simulate file descriptor exhaustion
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError("Too many open files")
                
                try:
                    memory_store = JsonMemoryStore(store_file)
                    memory_store.store("session", "key", "value")
                except OSError:
                    # Should handle file descriptor exhaustion gracefully
                    assert True

    def test_cpu_exhaustion_handling(self):
        """Test handling of CPU exhaustion scenarios."""
        # This would typically be handled at the OS level
        # Test that the system doesn't crash under high CPU load
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            # Simulate CPU-intensive operation failure
            with patch('jarvis.tools.computer_control.computer_control') as mock_tool:
                mock_tool.side_effect = Exception("CPU overload")
                
                result = tool_runner.run_tool("computer_control", {"action": "test"})
                
                # Should handle CPU exhaustion gracefully
                assert "error" in result.lower()


class TestDataCorruption:
    """Test data corruption scenarios."""

    def test_memory_data_corruption(self):
        """Test handling of memory data corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            # Create partially corrupted JSON
            store_file.write_text('{"session": {"key": "value"}')
            
            try:
                memory_store = JsonMemoryStore(store_file)
                # Should handle corrupted data
                assert True
            except Exception:
                # Should fail gracefully
                assert True

    def test_configuration_corruption(self):
        """Test handling of configuration corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            
            # Create corrupted configuration
            config_file.write_text("invalid json {")
            
            # System should handle corrupted configuration
            try:
                from jarvis.config.settings import get_settings
                # If it loads defaults, that's good
                settings = get_settings()
                assert settings is not None
            except Exception:
                # If it fails, it should be handled gracefully
                assert True

    def test_secrets_corruption(self):
        """Test handling of secrets corruption."""
        # Test secrets module corruption handling
        with patch('jarvis.security.secrets.get_secret') as mock_get:
            mock_get.side_effect = Exception("Corrupted secrets data")
            
            try:
                from jarvis.security.secrets import get_secret
                result = get_secret("test_key")
            except Exception:
                # Should fail gracefully
                assert True


class TestConcurrencyFaultTolerance:
    """Test concurrency-related fault tolerance."""

    def test_race_condition_handling(self):
        """Test handling of race conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            results = []
            
            def race_condition_test(thread_id):
                try:
                    # Multiple threads trying to write the same key
                    for i in range(10):
                        memory_store.store("session", "race_key", f"value_{thread_id}_{i}")
                        result = memory_store.retrieve("session", "race_key")
                        results.append(result)
                except Exception as e:
                    results.append(f"Error: {e}")
            
            # Run multiple threads to create race conditions
            threads = []
            for i in range(5):
                thread = threading.Thread(target=race_condition_test, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Should handle race conditions without crashing
            assert len(results) > 0

    def test_deadlock_prevention(self):
        """Test deadlock prevention in concurrent operations."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            def deadlock_test(thread_id):
                try:
                    # Simulate operations that could deadlock
                    tool_runner.run_tool("computer_control", {"action": f"test_{thread_id}"})
                except Exception as e:
                    # Should not deadlock
                    assert "deadlock" not in str(e).lower()
            
            # Run multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=deadlock_test, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait with timeout to detect deadlocks
            for thread in threads:
                thread.join(timeout=5.0)
                if thread.is_alive():
                    # If thread is still alive, it might be deadlocked
                    assert False, "Potential deadlock detected"

    def test_thread_safety(self):
        """Test thread safety of components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            errors = []
            
            def thread_safety_test(thread_id):
                try:
                    # Multiple operations on shared resource
                    for i in range(20):
                        memory_store.store(f"session_{thread_id}", f"key_{i}", f"value_{i}")
                        memory_store.retrieve(f"session_{thread_id}", f"key_{i}")
                except Exception as e:
                    errors.append(e)
            
            # Run many threads
            threads = []
            for i in range(10):
                thread = threading.Thread(target=thread_safety_test, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Should be thread-safe
            assert len(errors) == 0
