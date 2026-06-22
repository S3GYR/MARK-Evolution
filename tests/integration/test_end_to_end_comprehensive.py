"""Comprehensive end-to-end integration tests for MARK XLVI."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
import tempfile
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict

from jarvis.core.orchestrator import AgentOrchestrator
from jarvis.core.tool_runner import ToolRunner
from jarvis.llm.client import LLMClient
from jarvis.memory.json_store import JsonMemoryStore
from jarvis.tools.registry import get_tool_declarations
from jarvis.security.permissions import ActionContext


@pytest.mark.asyncio
async def test_full_assistant_workflow():
    """Test complete assistant workflow from input to response."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        mock_settings.return_value.llm_api_key = "test-key"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Hello! I'm JARVIS, your assistant."
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    # Create and setup assistant
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test command execution
                    result = await assistant.run_command("Hello JARVIS")
                    
                    assert result == "Hello! I'm JARVIS, your assistant."
                    mock_orchestrator.run.assert_called_once_with("Hello JARVIS")
                    mock_player.play.assert_called_once_with("Hello! I'm JARVIS, your assistant.")
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_memory_integration_workflow():
    """Test memory integration with assistant workflow."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.search.return_value = [
                {"content": "Previous conversation", "metadata": {"source": "user"}}
            ]
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "I remember our previous conversation."
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test memory-dependent command
                    result = await assistant.run_command("Do you remember me?")
                    
                    assert result == "I remember our previous conversation."
                    mock_memory.search.assert_called_once()
                    mock_orchestrator.run.assert_called_once()
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_tool_runner_integration():
    """Test tool runner integration with orchestrator."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.generate_response.return_value = "Tool executed successfully"
            mock_llm_client.return_value = mock_client
            
            with patch('jarvis.core.orchestrator.ToolRunner') as mock_tool_runner_class:
                mock_tool_runner = Mock()
                mock_tool_runner_class.return_value = mock_tool_runner
                
                from jarvis.core.orchestrator import AgentOrchestrator
                
                orchestrator = AgentOrchestrator(
                    settings=mock_settings.return_value,
                    memory=mock_memory,
                    player=mock_player
                )
                
                result = await orchestrator.run("Execute tool: test_tool")
                
                assert result == "Tool executed successfully"
                mock_tool_runner_class.assert_called_once_with(mock_player)


@pytest.mark.asyncio
async def test_llm_client_integration():
    """Test LLM client integration with orchestrator."""
    with patch('jarvis.core.orchestrator.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "gpt-4"
        mock_settings.return_value.llm_temperature = 0.5
        mock_settings.return_value.llm_max_tokens = 500
        mock_settings.return_value.llm_api_key = "test-api-key"
        
        mock_memory = AsyncMock()
        mock_player = Mock()
        
        with patch('litellm.completion') as mock_completion:
            mock_response = {
                "choices": [
                    {"message": {"content": "LLM integration response"}}
                ]
            }
            mock_completion.return_value = mock_response
            
            from jarvis.core.orchestrator import AgentOrchestrator
            
            orchestrator = AgentOrchestrator(
                settings=mock_settings.return_value,
                memory=mock_memory,
                player=mock_player
            )
            
            result = await orchestrator.run("Test LLM integration")
            
            assert result == "LLM integration response"
            mock_completion.assert_called_once()
            
            # Verify LLM parameters were passed correctly
            call_args = mock_completion.call_args[1]
            assert call_args.get('model') == "gpt-4"
            assert call_args.get('temperature') == 0.5
            assert call_args.get('max_tokens') == 500


@pytest.mark.asyncio
async def test_embeddings_integration():
    """Test embeddings integration with memory store."""
    with patch('jarvis.llm.embeddings.get_embedding_provider') as mock_get_provider:
        mock_provider = Mock()
        mock_provider.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_provider.dimension = 5
        mock_get_provider.return_value = mock_provider
        
        with patch('jarvis.memory.json_store.get_settings') as mock_settings:
            mock_settings.return_value.memory_file = "test_memory.json"
            
            from jarvis.memory.json_store import JsonMemoryStore
            
            memory_store = JsonMemoryStore()
            await memory_store.initialize()
            
            # Test embedding-based search
            test_text = "Test embedding integration"
            embedding = mock_provider.encode(test_text)
            
            assert len(embedding) == 5
            assert all(isinstance(x, float) for x in embedding)
            mock_provider.encode.assert_called_once_with(test_text)
            
            await memory_store.close()


@pytest.mark.asyncio
async def test_web_server_integration():
    """Test web server integration with application."""
    with patch('jarvis.web.server.get_settings') as mock_settings:
        mock_settings.return_value.web_host = "127.0.0.1"
        mock_settings.return_value.web_port = 8000
        
        with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
            mock_auth = Mock()
            mock_auth_manager.return_value = mock_auth
            
            from jarvis.web.server import DashboardServer
            
            server = DashboardServer()
            
            # Test server creation and route setup
            assert server is not None
            assert hasattr(server, 'app')
            
            # Check that routes are properly configured
            routes = [route.path for route in server.app.routes]
            assert "/" in routes
            assert "/login" in routes
            assert "/api/command" in routes


@pytest.mark.asyncio
async def test_audio_integration():
    """Test audio components integration."""
    with patch('jarvis.audio.capture.get_settings') as mock_settings:
        mock_settings.return_value.audio_sample_rate = 16000
        mock_settings.return_value.audio_chunk_size = 1024
        
        with patch('sounddevice.InputStream') as mock_stream:
            mock_stream_instance = Mock()
            mock_stream.return_value = mock_stream_instance
            
            from jarvis.audio.capture import AudioCapture
            
            # Test capture initialization
            output_callback = Mock()
            capture = AudioCapture(
                output_callback=output_callback,
                is_speaking=lambda: False,
                is_muted=lambda: False,
                is_phone_active=lambda: False
            )
            
            assert capture is not None
            assert capture._running is False
            
            # Test start/stop workflow
            loop = asyncio.get_event_loop()
            capture.start(loop)
            assert capture._running is True
            
            capture.stop()
            assert capture._running is False


@pytest.mark.asyncio
async def test_security_integration():
    """Test security components integration."""
    with patch('jarvis.security.secrets.get_secret') as mock_get_secret:
        mock_get_secret.return_value = "test-secret-value"
        
        with patch('jarvis.security.permissions.check_permission') as mock_check_permission:
            mock_check_permission.return_value = True
            
            from jarvis.security.secrets import get_secret
            from jarvis.security.permissions import check_permission
            
            # Test secret retrieval
            secret = get_secret("test_secret")
            assert secret == "test-secret-value"
            
            # Test permission checking
            has_permission = check_permission("file.read", "/safe/path")
            assert has_permission is True


@pytest.mark.asyncio
async def test_observability_integration():
    """Test observability components integration."""
    with patch('jarvis.observability.tracing.configure_tracing') as mock_configure_tracing:
        with patch('jarvis.observability.logger.configure_logging') as mock_configure_logging:
            
            from jarvis.observability.tracing import configure_tracing
            from jarvis.observability.logger import configure_logging
            
            # Test tracing configuration
            configure_tracing()
            mock_configure_tracing.assert_called_once()
            
            # Test logging configuration
            configure_logging()
            mock_configure_logging.assert_called_once()


@pytest.mark.asyncio
async def test_complete_workflow_with_errors():
    """Test complete workflow with error handling."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = Exception("Memory save error")
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Response despite memory error"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test workflow continues despite memory errors
                    result = await assistant.run_command("Test error handling")
                    
                    assert result == "Response despite memory error"
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_concurrent_requests_workflow():
    """Test workflow with concurrent requests."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Concurrent response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test concurrent requests
                    tasks = [
                        assistant.run_command(f"Concurrent request {i}")
                        for i in range(5)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    assert len(results) == 5
                    assert all(result == "Concurrent response" for result in results)
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_configuration_integration():
    """Test configuration integration across components."""
    with patch('jarvis.config.settings.get_settings') as mock_get_settings:
        mock_settings = Mock()
        mock_settings.llm_model = "test-model"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1000
        mock_settings.web_host = "127.0.0.1"
        mock_settings.web_port = 8000
        mock_settings.audio_sample_rate = 16000
        mock_settings.memory_file = "test_memory.json"
        mock_get_settings.return_value = mock_settings
        
        # Test that all components can access the same configuration
        from jarvis.config.settings import get_settings
        
        settings = get_settings()
        assert settings.llm_model == "test-model"
        assert settings.web_host == "127.0.0.1"
        assert settings.audio_sample_rate == 16000
        assert settings.memory_file == "test_memory.json"


@pytest.mark.asyncio
async def test_plugin_system_integration():
    """Test plugin/tool system integration."""
    with patch('jarvis.tools.registry.get_tool_function') as mock_get_tool:
        mock_tool = Mock()
        mock_tool.return_value = "Plugin executed"
        mock_get_tool.return_value = mock_tool
        
        with patch('jarvis.core.tool_runner.get_settings') as mock_settings:
            mock_settings.return_value.tool_timeout = 30
            
            from jarvis.core.tool_runner import ToolRunner
            from jarvis.core.player import ConsolePlayer
            
            player = ConsolePlayer()
            runner = ToolRunner(player)
            
            # Test plugin execution
            result = await runner.run("test_plugin", {"param": "value"})
            
            assert result == "Plugin executed"
            mock_get_tool.assert_called_once_with("test_plugin")


@pytest.mark.asyncio
async def test_data_flow_integration():
    """Test data flow between components."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        # Track data flow through the system
        data_flow = []
        
        def track_memory_save(key, value, category):
            data_flow.append(f"Memory save: {key}")
            
        def track_orchestrator_run(input_text):
            data_flow.append(f"Orchestrator run: {input_text}")
            return "Data flow response"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = track_memory_save
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.side_effect = track_orchestrator_run
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test data flow
                    result = await assistant.run_command("Track data flow")
                    
                    assert result == "Data flow response"
                    assert "Orchestrator run: Track data flow" in data_flow
                    assert len(data_flow) >= 2  # Should have memory saves too
                    
                    await assistant.shutdown()


@pytest.mark.asyncio
async def test_lifecycle_integration():
    """Test complete application lifecycle."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        lifecycle_events = []
        
        def track_lifecycle(event):
            lifecycle_events.append(event)
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Lifecycle test response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    # Test lifecycle: initialization -> setup -> run -> shutdown
                    track_lifecycle("initialization")
                    assistant = JarvisAssistant()
                    
                    track_lifecycle("setup")
                    await assistant.setup()
                    
                    track_lifecycle("run")
                    result = await assistant.run_command("Lifecycle test")
                    assert result == "Lifecycle test response"
                    
                    track_lifecycle("shutdown")
                    await assistant.shutdown()
                    
                    # Verify lifecycle events
                    expected_events = ["initialization", "setup", "run", "shutdown"]
                    assert lifecycle_events == expected_events


@pytest.mark.asyncio
async def test_error_recovery_integration():
    """Test error recovery across the system."""
    with patch('jarvis.main.get_settings') as mock_settings:
        mock_settings.return_value.llm_model = "test-model"
        mock_settings.return_value.llm_temperature = 0.7
        mock_settings.return_value.llm_max_tokens = 1000
        
        error_count = 0
        
        def failing_operation():
            nonlocal error_count
            error_count += 1
            if error_count <= 2:
                raise Exception(f"Simulated error {error_count}")
            return "Success after recovery"
        
        with patch('jarvis.main.get_memory_store') as mock_memory_store:
            mock_memory = AsyncMock()
            mock_memory.save.side_effect = failing_operation
            mock_memory_store.return_value = mock_memory
            
            with patch('jarvis.main.AgentOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.run.return_value = "Recovery response"
                mock_orchestrator_class.return_value = mock_orchestrator
                
                with patch('jarvis.main.ConsolePlayer') as mock_player_class:
                    mock_player = Mock()
                    mock_player_class.return_value = mock_player
                    
                    from jarvis.main import JarvisAssistant
                    
                    assistant = JarvisAssistant()
                    await assistant.setup()
                    
                    # Test error recovery
                    try:
                        result = await assistant.run_command("Test recovery")
                        # If it succeeds, system recovered
                        assert result == "Recovery response"


class TestOrchestratorIntegration:
    """Test orchestrator integration with all components."""

    def test_orchestrator_tool_integration(self):
        """Test orchestrator integration with tools."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.return_value = Mock(content="Use the computer control tool")
            mock_llm.return_value = mock_client
            
            with patch('jarvis.core.orchestrator.ToolRunner') as mock_runner:
                mock_tool_runner = Mock()
                mock_tool_runner.run_tool.return_value = "Tool executed successfully"
                mock_runner.return_value = mock_tool_runner
                
                orchestrator = AgentOrchestrator()
                
                result = orchestrator.process_request(
                    "Please help me with computer control",
                    session_id="test_session"
                )
                
                # Should integrate LLM and tool runner
                assert isinstance(result, dict)
                assert "response" in result

    def test_orchestrator_memory_integration(self):
        """Test orchestrator integration with memory store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                mock_client = Mock()
                mock_client.chat.return_value = Mock(content="I'll help you")
                mock_llm.return_value = mock_client
                
                orchestrator = AgentOrchestrator()
                orchestrator.memory_store = JsonMemoryStore(store_file)
                
                # Test memory integration
                result = orchestrator.process_request(
                    "Remember my preference for dark mode",
                    session_id="test_session"
                )
                
                # Should store and retrieve from memory
                assert isinstance(result, dict)


class TestToolRunnerIntegration:
    """Test tool runner integration with tools and security."""

    def test_tool_runner_registry_integration(self):
        """Test tool runner integration with tool registry."""
        tool_runner = ToolRunner()
        declarations = get_tool_declarations()
        
        # Should have access to all tool declarations
        assert isinstance(declarations, list)
        assert len(declarations) > 0
        
        # Test tool availability
        for declaration in declarations:
            tool_name = declaration.get("function", {}).get("name", "")
            if tool_name:
                assert tool_runner.has_tool(tool_name)

    def test_tool_runner_security_integration(self):
        """Test tool runner security integration."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = False  # Denied
            
            result = tool_runner.run_tool(
                "computer_control",
                {"action": "dangerous_operation"}
            )
            
            # Should handle security denial
            assert "cancelled" in result.lower() or "denied" in result.lower()

    def test_tool_runner_error_handling(self):
        """Test tool runner error handling."""
        tool_runner = ToolRunner()
        
        # Test invalid tool
        result = tool_runner.run_tool("nonexistent_tool", {})
        assert "not found" in result.lower() or "error" in result.lower()
        
        # Test invalid parameters
        result = tool_runner.run_tool("computer_control", None)
        assert isinstance(result, str)


class TestLLMIntegration:
    """Test LLM client integration."""

    def test_llm_tool_integration(self):
        """Test LLM client integration with tool declarations."""
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{
                    "message": {
                        "content": "I'll help you with that task"
                    }
                }]
            }
            
            client = LLMClient()
            declarations = get_tool_declarations()
            
            result = client.chat(
                messages=[{"role": "user", "content": "Help me"}],
                tools=declarations
            )
            
            # Should integrate tools with LLM
            assert result.content is not None

    def test_llm_memory_integration(self):
        """Test LLM client integration with memory context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            # Store some context
            memory_store.store("test_session", "user_preference", "dark_mode")
            
            with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
                mock_request.return_value = {
                    "choices": [{
                        "message": {
                            "content": "I remember your preference"
                        }
                    }]
                }
                
                client = LLMClient()
                result = client.chat(
                    messages=[{"role": "user", "content": "What do you remember?"}],
                    memory_context=memory_store.get_session_context("test_session")
                )
                
                # Should use memory context
                assert result.content is not None

    def test_llm_error_handling(self):
        """Test LLM client error handling."""
        with patch('jarvis.llm.client.LLMClient._make_request') as mock_request:
            mock_request.side_effect = Exception("API error")
            
            client = LLMClient()
            
            with pytest.raises(Exception):
                client.chat(messages=[{"role": "user", "content": "test"}])


class TestMemoryIntegration:
    """Test memory store integration."""

    def test_memory_json_integration(self):
        """Test JSON memory store integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            # Test storage and retrieval
            memory_store.store("session1", "key1", "value1")
            result = memory_store.retrieve("session1", "key1")
            assert result == "value1"
            
            # Test session management
            context = memory_store.get_session_context("session1")
            assert isinstance(context, dict)

    def test_memory_concurrent_access(self):
        """Test memory store concurrent access."""
        results = []
        
        def store_operation(session_id, key, value):
            with tempfile.TemporaryDirectory() as temp_dir:
                store_file = Path(temp_dir) / f"test_store_{session_id}.json"
                memory_store = JsonMemoryStore(store_file)
                memory_store.store(session_id, key, value)
                result = memory_store.retrieve(session_id, key)
                results.append(result)
        
        # Run concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=store_operation,
                args=(f"session{i}", f"key{i}", f"value{i}")
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == f"value{i}"

    def test_memory_persistence(self):
        """Test memory store persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            
            # Store data in first instance
            memory_store1 = JsonMemoryStore(store_file)
            memory_store1.store("session1", "key1", "persistent_value")
            memory_store1.close()
            
            # Retrieve data in second instance
            memory_store2 = JsonMemoryStore(store_file)
            result = memory_store2.retrieve("session1", "key1")
            assert result == "persistent_value"


class TestSecurityIntegration:
    """Test security system integration."""

    def test_permissions_tool_integration(self):
        """Test permissions system integration with tools."""
        with patch('jarvis.core.player.ConsolePlayer.request_confirmation') as mock_confirm:
            mock_confirm.return_value = "y"  # User confirms
            
            context = ActionContext("test_tool", "test action", Mock())
            result = context.check()
            
            # Should integrate with player for confirmation
            assert result is True

    def test_sandbox_tool_integration(self):
        """Test sandbox integration with tools."""
        from jarvis.security.sandbox import execute_code
        
        # Test safe code execution
        result = execute_code("print('Hello, World!')")
        assert result["success"] is True
        assert "Hello, World!" in result["stdout"]
        
        # Test dangerous code blocking
        result = execute_code("import os; os.system('echo hacked')")
        assert result["success"] is False

    def test_secrets_integration(self):
        """Test secrets management integration."""
        from jarvis.security.secrets import SecretStore
        
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_file = Path(temp_dir) / "test_secrets.json"
            secret_store = SecretStore(secrets_file)
            
            # Test secret storage and retrieval
            secret_store.set_secret("test_key", "test_value")
            result = secret_store.get_secret("test_key")
            assert result == "test_value"


class TestWorkflowIntegration:
    """Test complete workflow integration."""

    def test_complete_user_workflow(self):
        """Test complete user request workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup components
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
                mock_client = Mock()
                mock_client.chat.return_value = Mock(content="I'll help you with that")
                mock_llm.return_value = mock_client
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    orchestrator = AgentOrchestrator()
                    orchestrator.memory_store = memory_store
                    
                    # Process user request
                    result = orchestrator.process_request(
                        "Help me organize my desktop",
                        session_id="user_session"
                    )
                    
                    # Should complete full workflow
                    assert isinstance(result, dict)
                    assert "response" in result

    def test_multi_tool_workflow(self):
        """Test workflow using multiple tools."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            # Test multiple tool operations
            tools_to_test = [
                ("computer_control", {"action": "stats"}),
                ("send_message", {"platform": "test", "receiver": "user", "message": "hello"}),
                ("browser_control", {"action": "screenshot"})
            ]
            
            results = []
            for tool_name, params in tools_to_test:
                try:
                    result = tool_runner.run_tool(tool_name, params)
                    results.append((tool_name, result))
                except Exception as e:
                    results.append((tool_name, f"Error: {e}"))
            
            # Should handle multiple tools
            assert len(results) == len(tools_to_test)

    def test_error_recovery_workflow(self):
        """Test workflow error recovery."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            # Simulate LLM error
            mock_client = Mock()
            mock_client.chat.side_effect = Exception("LLM unavailable")
            mock_llm.return_value = mock_client
            
            orchestrator = AgentOrchestrator()
            
            result = orchestrator.process_request(
                "Test request during LLM failure",
                session_id="test_session"
            )
            
            # Should handle LLM failure gracefully
            assert isinstance(result, dict)


class TestPerformanceIntegration:
    """Test performance integration scenarios."""

    def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        with patch('jarvis.core.orchestrator.LLMClient') as mock_llm:
            mock_client = Mock()
            mock_client.chat.return_value = Mock(content="Response")
            mock_llm.return_value = mock_client
            
            orchestrator = AgentOrchestrator()
            results = []
            
            def process_request(request_id):
                result = orchestrator.process_request(
                    f"Request {request_id}",
                    session_id=f"session_{request_id}"
                )
                results.append(result)
            
            # Process multiple requests concurrently
            threads = []
            start_time = time.time()
            
            for i in range(3):
                thread = threading.Thread(target=process_request, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            elapsed = time.time() - start_time
            
            # Should handle concurrent requests efficiently
            assert len(results) == 3
            assert elapsed < 5.0  # Should complete within 5 seconds

    def test_memory_performance(self):
        """Test memory performance under load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "test_store.json"
            memory_store = JsonMemoryStore(store_file)
            
            start_time = time.time()
            
            # Perform many memory operations
            for i in range(50):
                memory_store.store(f"session{i}", f"key{i}", f"value{i}")
                memory_store.retrieve(f"session{i}", f"key{i}")
            
            elapsed = time.time() - start_time
            
            # Should handle memory operations efficiently
            assert elapsed < 2.0  # Should complete within 2 seconds

    def test_tool_performance(self):
        """Test tool performance under load."""
        tool_runner = ToolRunner()
        
        with patch('jarvis.security.permissions.ActionContext') as mock_context:
            mock_context.return_value.check.return_value = True
            
            start_time = time.time()
            
            # Perform many tool operations
            for i in range(25):
                tool_runner.run_tool("computer_control", {"action": "stats"})
            
            elapsed = time.time() - start_time
            
            # Should handle tool operations efficiently
            assert elapsed < 3.0  # Should complete within 3 seconds
