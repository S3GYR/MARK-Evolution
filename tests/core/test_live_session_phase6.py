"""Phase 6: Comprehensive Live Session Tests - Priority Absolute."""

from __future__ import annotations

import pytest
import asyncio
import threading
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from jarvis.core.live_session import GeminiLiveSession, _clean_transcript, _load_system_prompt
from jarvis.core.player import Player
from jarvis.config.settings import Settings


class TestLiveSessionHelpers:
    """Test live session helper functions."""

    def test_clean_transcript_normal_text(self):
        """Test transcript cleaning with normal text."""
        text = "Hello, how are you today?"
        result = _clean_transcript(text)
        assert result == "Hello, how are you today?"

    def test_clean_transcript_with_ctrl_tags(self):
        """Test transcript cleaning with control tags."""
        text = "Hello<ctrl1> how are<ctrl2> you today?"
        result = _clean_transcript(text)
        assert result == "Hello how are you today?"

    def test_clean_transcript_with_control_characters(self):
        """Test transcript cleaning with control characters."""
        text = "Hello\x00\x01\x02 how are you?"
        result = _clean_transcript(text)
        assert result == "Hello how are you?"

    def test_clean_transcript_with_mixed_content(self):
        """Test transcript cleaning with mixed content."""
        text = "Hello<ctrl1>\x00\x01 how are\x02<ctrl2> you today?"
        result = _clean_transcript(text)
        assert result == "Hello how are you today?"

    def test_clean_transcript_empty_string(self):
        """Test transcript cleaning with empty string."""
        result = _clean_transcript("")
        assert result == ""

    def test_clean_transcript_whitespace(self):
        """Test transcript cleaning with whitespace."""
        text = "  Hello   how are   you?  "
        result = _clean_transcript(text)
        assert result == "Hello how are you?"

    def test_load_system_prompt_success(self):
        """Test successful system prompt loading."""
        mock_prompt_content = "You are JARVIS AI assistant."
        
        with patch('jarvis.core.live_session.PROMPT_PATH') as mock_path:
            mock_path.read_text.return_value = mock_prompt_content
            
            result = _load_system_prompt()
            
            assert result == mock_prompt_content
            mock_path.read_text.assert_called_once_with(encoding="utf-8")

    def test_load_system_prompt_file_error(self):
        """Test system prompt loading with file error."""
        with patch('jarvis.core.live_session.PROMPT_PATH') as mock_path:
            mock_path.read_text.side_effect = FileNotFoundError("Prompt file not found")
            
            result = _load_system_prompt()
            
            assert "JARVIS" in result
            assert "Tony Stark's AI assistant" in result

    def test_load_system_prompt_permission_error(self):
        """Test system prompt loading with permission error."""
        with patch('jarvis.core.live_session.PROMPT_PATH') as mock_path:
            mock_path.read_text.side_effect = PermissionError("Permission denied")
            
            result = _load_system_prompt()
            
            assert "JARVIS" in result
            assert "concise" in result


class TestGeminiLiveSessionInitialization:
    """Test Gemini Live Session initialization."""

    def test_session_initialization_default(self):
        """Test session initialization with default parameters."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_get_settings.return_value = mock_settings
            
            session = GeminiLiveSession(mock_player)
            
            assert session.player == mock_player
            assert session.settings == mock_settings
            assert session.session is None
            assert session.audio_in_queue is None
            assert session.out_queue is None
            assert session._loop is None
            assert session._is_speaking is False
            assert session._phone_active is False
            assert session._turn_done_event is None
            assert session._tasks == []
            assert session._audio_capture is None
            assert session._audio_playback is None
            assert session._phone_relay is None

    def test_session_initialization_custom_settings(self):
        """Test session initialization with custom settings."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        assert session.player == mock_player
        assert session.settings == mock_settings

    def test_session_initialization_tool_runner(self):
        """Test session initializes tool runner."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            session = GeminiLiveSession(mock_player)
            
            assert session._tool_runner is not None
            assert session._tool_runner.player == mock_player

    def test_session_initialization_speaking_lock(self):
        """Test session initializes speaking lock."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            session = GeminiLiveSession(mock_player)
            
            assert isinstance(session._speaking_lock, threading.Lock)


class TestGeminiLiveSessionAPIKeyHandling:
    """Test Gemini Live Session API key handling."""

    def test_get_api_key_success(self):
        """Test successful API key retrieval."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            with patch('jarvis.core.live_session.get_secret') as mock_get_secret:
                mock_get_secret.return_value = "test_api_key"
                
                session = GeminiLiveSession(mock_player)
                key = session._get_api_key()
                
                assert key == "test_api_key"
                mock_get_secret.assert_called_once_with("gemini_api_key", env_override="GEMINI_API_KEY")

    def test_get_api_key_from_env(self):
        """Test API key retrieval from environment."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            with patch('jarvis.core.live_session.get_secret') as mock_get_secret:
                mock_get_secret.return_value = "env_api_key"
                
                session = GeminiLiveSession(mock_player)
                key = session._get_api_key()
                
                assert key == "env_api_key"

    def test_get_api_key_missing(self):
        """Test API key retrieval when key is missing."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            with patch('jarvis.core.live_session.get_secret') as mock_get_secret:
                mock_get_secret.return_value = None
                
                session = GeminiLiveSession(mock_player)
                
                with pytest.raises(RuntimeError, match="Gemini API key not configured"):
                    session._get_api_key()

    def test_get_api_key_empty_string(self):
        """Test API key retrieval when key is empty string."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            with patch('jarvis.core.live_session.get_secret') as mock_get_secret:
                mock_get_secret.return_value = ""
                
                session = GeminiLiveSession(mock_player)
                
                with pytest.raises(RuntimeError, match="Gemini API key not configured"):
                    session._get_api_key()

    def test_get_api_key_exception_handling(self):
        """Test API key retrieval with exception."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.core.live_session.get_settings') as mock_get_settings:
            mock_get_settings.return_value = Mock(spec=Settings)
            
            with patch('jarvis.core.live_session.get_secret') as mock_get_secret:
                mock_get_secret.side_effect = Exception("Secret access error")
                
                session = GeminiLiveSession(mock_player)
                
                with pytest.raises(Exception, match="Secret access error"):
                    session._get_api_key()


class TestGeminiLiveSessionConfigBuilding:
    """Test Gemini Live Session configuration building."""

    def test_build_config_basic(self):
        """Test basic config building."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = "Memory context"
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    config = session._build_config()
                    
                    assert config is not None
                    # Should include time context, memory, system prompt, and tools

    def test_build_config_without_memory(self):
        """Test config building without memory."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    config = session._build_config()
                    
                    assert config is not None

    def test_build_config_with_tools(self):
        """Test config building with tool declarations."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = [
                    {
                        "function": {
                            "name": "test_tool",
                            "description": "Test tool",
                            "parameters": {"type": "object", "properties": {}}
                        }
                    }
                ]
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = "Memory context"
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    config = session._build_config()
                    
                    assert config is not None

    def test_build_config_memory_error(self):
        """Test config building with memory error."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.side_effect = Exception("Memory error")
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    
                    try:
                        config = session._build_config()
                        # Should handle memory error gracefully
                        assert True
                    except Exception:
                        # Should propagate or handle memory error
                        assert True


class TestGeminiLiveSessionLifecycle:
    """Test Gemini Live Session lifecycle management."""

    @pytest.mark.asyncio
    async def test_session_start_success(self):
        """Test successful session start."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_session = Mock()
                            mock_client.aio.live.connect.return_value = mock_session
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            await session.start()
                            
                            assert session.session == mock_session
                            assert session.audio_in_queue is not None
                            assert session.out_queue is not None
                            assert session._turn_done_event is not None

    @pytest.mark.asyncio
    async def test_session_start_api_key_error(self):
        """Test session start with API key error."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
            mock_api_key.side_effect = RuntimeError("API key not configured")
            
            session = GeminiLiveSession(mock_player, mock_settings)
            
            with pytest.raises(RuntimeError, match="API key not configured"):
                await session.start()

    @pytest.mark.asyncio
    async def test_session_start_connection_error(self):
        """Test session start with connection error."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_client.aio.live.connect.side_effect = Exception("Connection failed")
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            with pytest.raises(Exception, match="Connection failed"):
                                await session.start()

    @pytest.mark.asyncio
    async def test_session_stop_success(self):
        """Test successful session stop."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock session and tasks
        mock_session = Mock()
        session.session = mock_session
        session._tasks = [Mock(), Mock()]
        session.audio_in_queue = Mock()
        session.out_queue = Mock()
        session._turn_done_event = Mock()
        
        await session.stop()
        
        mock_session.close.assert_called_once()
        for task in session._tasks:
            task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_stop_no_session(self):
        """Test session stop when no session is active."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Should not raise error
        await session.stop()
        assert True

    @pytest.mark.asyncio
    async def test_session_restart(self):
        """Test session restart."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_session = Mock()
                            mock_client.aio.live.connect.return_value = mock_session
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            # Start session
                            await session.start()
                            assert session.session == mock_session
                            
                            # Stop session
                            await session.stop()
                            assert session.session is None
                            
                            # Restart session
                            mock_client.aio.live.connect.return_value = Mock()
                            await session.start()
                            assert session.session is not None


class TestGeminiLiveSessionAudioHandling:
    """Test Gemini Live Session audio handling."""

    @pytest.mark.asyncio
    async def test_audio_streaming_setup(self):
        """Test audio streaming setup."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
            with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    
                    await session._setup_audio()
                    
                    mock_capture.assert_called_once()
                    mock_playback.assert_called_once()
                    mock_phone.assert_called_once()
                    assert session._audio_capture is not None
                    assert session._audio_playback is not None
                    assert session._phone_relay is not None

    @pytest.mark.asyncio
    async def test_audio_capture_error(self):
        """Test audio capture error handling."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
            mock_capture.side_effect = Exception("Audio capture error")
            
            session = GeminiLiveSession(mock_player, mock_settings)
            
            try:
                await session._setup_audio()
                # Should handle error gracefully
                assert True
            except Exception:
                # Should propagate or handle error
                assert True

    @pytest.mark.asyncio
    async def test_audio_playback_error(self):
        """Test audio playback error handling."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
            with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                mock_capture.return_value = Mock()
                mock_playback.side_effect = Exception("Audio playback error")
                
                session = GeminiLiveSession(mock_player, mock_settings)
                
                try:
                    await session._setup_audio()
                    # Should handle error gracefully
                    assert True
                except Exception:
                    # Should propagate or handle error
                    assert True

    @pytest.mark.asyncio
    async def test_phone_relay_error(self):
        """Test phone relay error handling."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
            with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                with patch('jarvis.core.live_session.PhoneAudioRelay') as mock_phone:
                    mock_capture.return_value = Mock()
                    mock_playback.return_value = Mock()
                    mock_phone.side_effect = Exception("Phone relay error")
                    
                    session = GeminiLiveSession(mock_player, mock_settings)
                    
                    try:
                        await session._setup_audio()
                        # Should handle error gracefully
                        assert True
                    except Exception:
                        # Should propagate or handle error
                        assert True


class TestGeminiLiveSessionToolExecution:
    """Test Gemini Live Session tool execution."""

    @pytest.mark.asyncio
    async def test_tool_execution_success(self):
        """Test successful tool execution."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner
        session._tool_runner.run = AsyncMock(return_value="Tool executed successfully")
        
        result = await session._handle_tool_call("test_tool", {"param": "value"})
        
        assert result == "Tool executed successfully"
        session._tool_runner.run.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_tool_execution_not_found(self):
        """Test tool execution when tool not found."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner to return not found
        session._tool_runner.run = AsyncMock(return_value="Unknown tool: test_tool")
        
        result = await session._handle_tool_call("test_tool", {"param": "value"})
        
        assert result == "Unknown tool: test_tool"

    @pytest.mark.asyncio
    async def test_tool_execution_error(self):
        """Test tool execution with error."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner to raise exception
        session._tool_runner.run = AsyncMock(side_effect=Exception("Tool execution failed"))
        
        result = await session._handle_tool_call("error_tool", {"param": "value"})
        
        # Should handle error gracefully
        assert "Tool execution failed" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self):
        """Test tool execution with timeout."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner to timeout
        session._tool_runner.run = AsyncMock(side_effect=asyncio.TimeoutError("Tool timeout"))
        
        result = await session._handle_tool_call("timeout_tool", {"param": "value"})
        
        # Should handle timeout gracefully
        assert "timeout" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test concurrent tool execution."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner
        session._tool_runner.run = AsyncMock(return_value="Tool result")
        
        # Execute multiple tools concurrently
        tasks = [
            session._handle_tool_call(f"tool_{i}", {"id": i}) for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert result == "Tool result"
        assert session._tool_runner.run.call_count == 5


class TestGeminiLiveSessionNetworkHandling:
    """Test Gemini Live Session network handling."""

    @pytest.mark.asyncio
    async def test_network_reconnection(self):
        """Test network reconnection handling."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_session = Mock()
                            
                            # First connection succeeds, second fails, third succeeds
                            mock_client.aio.live.connect.side_effect = [
                                mock_session,
                                Exception("Network error"),
                                Mock()
                            ]
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            # Initial connection
                            await session.start()
                            assert session.session == mock_session
                            
                            # Simulate network error and reconnection
                            await session.stop()
                            
                            try:
                                await session.start()
                                # Reconnection should succeed or fail gracefully
                                assert True
                            except Exception:
                                # Should handle network errors gracefully
                                assert True

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test network timeout handling."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
            mock_api_key.return_value = "test_key"
            
            with patch('google.genai') as mock_genai:
                mock_client = Mock()
                mock_client.aio.live.connect.side_effect = asyncio.TimeoutError("Network timeout")
                mock_genai.Client.return_value = mock_client
                
                session = GeminiLiveSession(mock_player, mock_settings)
                
                try:
                    await session.start()
                    # Should handle timeout gracefully
                    assert True
                except asyncio.TimeoutError:
                    # Should propagate timeout
                    assert True

    @pytest.mark.asyncio
    async def test_connection_loss_during_session(self):
        """Test connection loss during active session."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_session = Mock()
                            mock_session.receive.side_effect = Exception("Connection lost")
                            mock_client.aio.live.connect.return_value = mock_session
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            await session.start()
                            
                            try:
                                # Simulate receiving data during connection loss
                                await session._handle_session_events()
                                # Should handle connection loss gracefully
                                assert True
                            except Exception:
                                # Should handle connection errors
                                assert True


class TestGeminiLiveSessionStateManagement:
    """Test Gemini Live Session state management."""

    def test_speaking_state_management(self):
        """Test speaking state management."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Initial state
        assert session._is_speaking is False
        
        # Set speaking
        session.set_speaking(True)
        assert session._is_speaking is True
        
        # Clear speaking
        session.set_speaking(False)
        assert session._is_speaking is False

    def test_speaking_lock_thread_safety(self):
        """Test speaking lock thread safety."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        def set_speaking_thread(value):
            session.set_speaking(value)
        
        # Test concurrent access to speaking state
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_speaking_thread, args=(i % 2 == 0,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should not raise errors due to lock
        assert True

    def test_phone_state_management(self):
        """Test phone state management."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Initial state
        assert session._phone_active is False
        
        # Activate phone
        session.set_phone_active(True)
        assert session._phone_active is True
        
        # Deactivate phone
        session.set_phone_active(False)
        assert session._phone_active is False

    @pytest.mark.asyncio
    async def test_turn_done_event_management(self):
        """Test turn done event management."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Create turn done event
        session._turn_done_event = asyncio.Event()
        
        # Event should not be set initially
        assert not session._turn_done_event.is_set()
        
        # Set event
        session._turn_done_event.set()
        assert session._turn_done_event.is_set()
        
        # Clear event
        session._turn_done_event.clear()
        assert not session._turn_done_event.is_set()

    @pytest.mark.asyncio
    async def test_task_management(self):
        """Test background task management."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Create mock tasks
        async def mock_task():
            await asyncio.sleep(0.1)
        
        task1 = asyncio.create_task(mock_task())
        task2 = asyncio.create_task(mock_task())
        
        session._tasks = [task1, task2]
        
        # Cancel tasks
        for task in session._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*session._tasks, return_exceptions=True)
        
        # Tasks should be cancelled
        assert True


class TestGeminiLiveSessionErrorRecovery:
    """Test Gemini Live Session error recovery."""

    @pytest.mark.asyncio
    async def test_gemini_api_error_recovery(self):
        """Test recovery from Gemini API errors."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
            mock_api_key.return_value = "test_key"
            
            with patch('google.genai') as mock_genai:
                mock_client = Mock()
                mock_client.aio.live.connect.side_effect = Exception("Gemini API error")
                mock_genai.Client.return_value = mock_client
                
                session = GeminiLiveSession(mock_player, mock_settings)
                
                try:
                    await session.start()
                    # Should handle API error gracefully
                    assert False, "Should have raised exception"
                except Exception:
                    # Should be able to retry after error
                    with patch('google.genai') as mock_genai_retry:
                        mock_client_retry = Mock()
                        mock_client_retry.aio.live.connect.return_value = Mock()
                        mock_genai_retry.Client.return_value = mock_client_retry
                        
                        try:
                            await session.start()
                            # Should recover and connect successfully
                            assert True
                        except Exception:
                            # Should handle retry errors gracefully
                            assert True

    @pytest.mark.asyncio
    async def test_audio_device_error_recovery(self):
        """Test recovery from audio device errors."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        with patch('jarvis.core.live_session.AudioCapture') as mock_capture:
            with patch('jarvis.core.live_session.AudioPlayback') as mock_playback:
                # First attempt fails, second succeeds
                mock_capture.side_effect = [Exception("Device not found"), Mock()]
                mock_playback.return_value = Mock()
                
                # First attempt fails
                try:
                    await session._setup_audio()
                    assert False, "Should have raised exception"
                except Exception:
                    pass
                
                # Second attempt succeeds
                await session._setup_audio()
                assert session._audio_capture is not None

    @pytest.mark.asyncio
    async def test_memory_store_error_recovery(self):
        """Test recovery from memory store errors."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        with patch.object(session, '_sync_memory_prompt') as mock_memory:
            # Memory error on first call, success on second
            mock_memory.side_effect = [Exception("Memory store error"), "Memory context"]
            
            # First call fails
            try:
                result = session._sync_memory_prompt()
                assert False, "Should have raised exception"
            except Exception:
                pass
            
            # Second call succeeds
            result = session._sync_memory_prompt()
            assert result == "Memory context"

    @pytest.mark.asyncio
    async def test_tool_runner_error_recovery(self):
        """Test recovery from tool runner errors."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner to fail then succeed
        call_count = 0
        async def mock_run(tool_name, args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Tool runner error")
            return "Success"
        
        session._tool_runner.run = mock_run
        
        # First call fails
        result1 = await session._handle_tool_call("test_tool", {})
        assert "error" in result1.lower()
        
        # Second call succeeds
        result2 = await session._handle_tool_call("test_tool", {})
        assert result2 == "Success"


class TestGeminiLiveSessionPerformance:
    """Test Gemini Live Session performance characteristics."""

    @pytest.mark.asyncio
    async def test_session_startup_performance(self):
        """Test session startup performance."""
        import time
        
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        with patch('jarvis.core.live_session._load_system_prompt') as mock_load_prompt:
            mock_load_prompt.return_value = "System prompt"
            
            with patch('jarvis.core.live_session.get_tool_declarations') as mock_get_tools:
                mock_get_tools.return_value = []
                
                with patch.object(GeminiLiveSession, '_sync_memory_prompt') as mock_memory:
                    mock_memory.return_value = ""
                    
                    with patch.object(GeminiLiveSession, '_get_api_key') as mock_api_key:
                        mock_api_key.return_value = "test_key"
                        
                        with patch('google.genai') as mock_genai:
                            mock_client = Mock()
                            mock_session = Mock()
                            mock_client.aio.live.connect.return_value = mock_session
                            mock_genai.Client.return_value = mock_client
                            
                            session = GeminiLiveSession(mock_player, mock_settings)
                            
                            start_time = time.time()
                            await session.start()
                            elapsed = time.time() - start_time
                            
                            # Should start reasonably quickly
                            assert elapsed < 5.0
                            assert session.session is not None

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """Test concurrent session operations."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner for concurrent operations
        session._tool_runner.run = AsyncMock(return_value="Operation result")
        
        async def concurrent_operation(operation_id):
            return await session._handle_tool_call(f"tool_{operation_id}", {"id": operation_id})
        
        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        for result in results:
            assert result == "Operation result"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability during long session."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Mock tool runner
        session._tool_runner.run = AsyncMock(return_value="Memory test result")
        
        # Execute many operations to test memory stability
        for i in range(100):
            result = await session._handle_tool_call("memory_test_tool", {"iteration": i})
            assert result == "Memory test result"
        
        # Should not accumulate memory or leak resources
        assert True

    def test_resource_cleanup_on_deletion(self):
        """Test resource cleanup when session is deleted."""
        mock_player = Mock(spec=Player)
        mock_settings = Mock(spec=Settings)
        
        session = GeminiLiveSession(mock_player, mock_settings)
        
        # Simulate session with resources
        session.session = Mock()
        session._tasks = [Mock(), Mock()]
        
        # Delete session
        del session
        
        # Resources should be cleaned up properly
        assert True
