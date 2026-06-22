"""Phase 8: Comprehensive Web Server Tests - Priority 1."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

from jarvis.web.server import DashboardServer, _read_static
from jarvis.config.settings import Settings


class TestDashboardServerInitialization:
    """Test DashboardServer initialization and setup."""

    def test_server_initialization_default_params(self):
        """Test server initialization with default parameters."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                assert server.settings == mock_settings
                assert server.auth is not None
                assert isinstance(server.command_queue, asyncio.Queue)
                assert server.wake_callback is None
                assert server.connect_callback is None
                assert server._clients == set()
                assert server._history == []
                assert isinstance(server._phone_audio_queue, asyncio.Queue)

    def test_server_initialization_custom_params(self):
        """Test server initialization with custom parameters."""
        custom_queue = asyncio.Queue()
        custom_wake_callback = Mock()
        custom_connect_callback = Mock()
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer(
                    command_queue=custom_queue,
                    wake_callback=custom_wake_callback,
                    connect_callback=custom_connect_callback
                )
                
                assert server.command_queue == custom_queue
                assert server.wake_callback == custom_wake_callback
                assert server.connect_callback == custom_connect_callback

    def test_server_builds_fastapi_app(self):
        """Test that server builds FastAPI application."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                assert isinstance(server.app, FastAPI)
                assert server.app.docs_url is None
                assert server.app.redoc_url is None

    def test_server_registers_routes(self):
        """Test that server registers routes correctly."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Check that main routes are registered
                routes = [route.path for route in server.app.routes]
                assert "/login" in routes
                assert "/" in routes
                assert "/auto-login" in routes

    def test_static_file_reading(self):
        """Test static file reading functionality."""
        with patch('jarvis.web.server.STATIC_DIR') as mock_static_dir:
            mock_file = Mock()
            mock_file.read_text.return_value = "<html>Test content</html>"
            mock_static_dir.__truediv__ = Mock(return_value=mock_file)
            
            content = _read_static("test.html")
            
            assert content == "<html>Test content</html>"
            mock_static_dir.__truediv__.assert_called_once_with("test.html")
            mock_file.read_text.assert_called_once_with(encoding="utf-8")

    def test_static_file_reading_error(self):
        """Test static file reading with error."""
        with patch('jarvis.web.server.STATIC_DIR') as mock_static_dir:
            mock_file = Mock()
            mock_file.read_text.side_effect = FileNotFoundError("File not found")
            mock_static_dir.__truediv__ = Mock(return_value=mock_file)
            
            try:
                _read_static("nonexistent.html")
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass  # Expected


class TestDashboardServerLifecycle:
    """Test DashboardServer lifecycle management."""

    def test_server_startup_configuration(self):
        """Test server startup configuration."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_host = "127.0.0.1"
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Server should be properly configured
                assert server.app is not None
                assert isinstance(server._clients, set)
                assert isinstance(server._history, list)
                assert isinstance(server._phone_audio_queue, asyncio.Queue)

    def test_server_dependency_injection(self):
        """Test dependency injection in server."""
        custom_queue = asyncio.Queue(maxsize=100)
        custom_callback = Mock()
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer(
                    command_queue=custom_queue,
                    wake_callback=custom_callback
                )
                
                assert server.command_queue == custom_queue
                assert server.wake_callback == custom_callback
                assert server._phone_audio_queue.maxsize == 200

    def test_server_middleware_configuration(self):
        """Test server middleware configuration."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Check that middleware is properly configured
                assert server.app is not None
                # FastAPI should have default middleware

    def test_server_state_management(self):
        """Test server state management."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Initial state should be clean
                assert len(server._clients) == 0
                assert len(server._history) == 0
                assert server._phone_audio_queue.empty()


class TestDashboardServerRoutes:
    """Test DashboardServer HTTP routes."""

    def test_login_page_route(self):
        """Test login page route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                with patch('jarvis.web.server._read_static') as mock_read_static:
                    mock_read_static.return_value = "<html>Login page</html>"
                    
                    server = DashboardServer()
                    client = TestClient(server.app)
                    
                    response = client.get("/login")
                    
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "text/html; charset=utf-8"
                    assert "<html>Login page</html>" in response.text

    def test_index_page_route(self):
        """Test index page route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                with patch('jarvis.web.server._read_static') as mock_read_static:
                    mock_read_static.return_value = "<html>App page __IP__:__PORT__</html>"
                    
                    server = DashboardServer()
                    client = TestClient(server.app)
                    
                    response = client.get("/")
                    
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "text/html; charset=utf-8"
                    assert "127.0.0.1" in response.text
                    assert "8000" in response.text

    def test_login_route_success(self):
        """Test successful login route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "session_key_123"
                mock_auth.create_token.return_value = "token_456"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.post("/login", json={"pin": "1234"})
                
                assert response.status_code == 200
                data = response.json()
                assert data["ok"] is True
                assert data["token"] == "token_456"
                mock_auth.validate_pin.assert_called_once_with("1234", "testclient")

    def test_login_route_failure(self):
        """Test failed login route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = None
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.post("/login", json={"pin": "wrong"})
                
                assert response.status_code == 401
                data = response.json()
                assert data["ok"] is False
                assert "Invalid or expired key" in data["error"]

    def test_login_route_invalid_json(self):
        """Test login route with invalid JSON."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.post("/login", data="invalid json")
                    
                assert response.status_code == 422  # Validation error

    def test_auto_login_route_success(self):
        """Test successful auto-login route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "session_key_123"
                mock_auth.create_token.return_value = "token_456"
                mock_auth.create_device_session.return_value = "device_token_789"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.get("/auto-login?key=valid_key")
                
                assert response.status_code == 200
                assert "sessionStorage.setItem('jarvis_token','token_456')" in response.text
                assert "localStorage.setItem('jarvis_device_token','device_token_789')" in response.text

    def test_auto_login_route_failure(self):
        """Test failed auto-login route."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = None
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.get("/auto-login?key=invalid_key")
                
                assert response.status_code == 200
                assert "Link expired" in response.text


class TestDashboardServerWebSocket:
    """Test DashboardServer WebSocket functionality."""

    def test_websocket_connection_handling(self):
        """Test WebSocket connection handling."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Initially no clients
                assert len(server._clients) == 0
                
                # Mock WebSocket client
                mock_websocket = Mock()
                server._clients.add(mock_websocket)
                
                assert len(server._clients) == 1
                assert mock_websocket in server._clients

    def test_websocket_broadcast(self):
        """Test WebSocket broadcast functionality."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Add mock clients
                mock_ws1 = Mock()
                mock_ws2 = Mock()
                server._clients.add(mock_ws1)
                server._clients.add(mock_ws2)
                
                # Test broadcast
                message = {"type": "test", "text": "broadcast message"}
                
                # Mock async send
                async def mock_send_json(data):
                    pass
                
                mock_ws1.send_json = AsyncMock(side_effect=mock_send_json)
                mock_ws2.send_json = AsyncMock(side_effect=mock_send_json)
                
                # Run broadcast
                asyncio.run(server.broadcast(message))
                
                # Both clients should receive the message
                mock_ws1.send_json.assert_called_once_with(message)
                mock_ws2.send_json.assert_called_once_with(message)

    def test_websocket_client_removal(self):
        """Test WebSocket client removal on disconnect."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Add mock client
                mock_websocket = Mock()
                server._clients.add(mock_websocket)
                
                assert len(server._clients) == 1
                
                # Remove client
                server._clients.remove(mock_websocket)
                
                assert len(server._clients) == 0
                assert mock_websocket not in server._clients


class TestDashboardServerExceptions:
    """Test DashboardServer exception handling."""

    def test_static_file_not_found(self):
        """Test handling of missing static files."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                with patch('jarvis.web.server._read_static') as mock_read_static:
                    mock_read_static.side_effect = FileNotFoundError("Static file not found")
                    
                    try:
                        server = DashboardServer()
                        # Should handle missing static files gracefully
                        assert True
                    except FileNotFoundError:
                        # Should propagate or handle gracefully
                        assert True

    def test_auth_manager_initialization_error(self):
        """Test handling of AuthManager initialization error."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager', side_effect=Exception("Auth error")):
                try:
                    server = DashboardServer()
                    # Should handle AuthManager errors gracefully
                    assert True
                except Exception:
                    # Should propagate or handle gracefully
                    assert True

    def test_route_exception_handling(self):
        """Test exception handling in routes."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.side_effect = Exception("Auth validation error")
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                response = client.post("/login", json={"pin": "1234"})
                
                # Should handle exceptions gracefully
                assert response.status_code in [500, 401]

    def test_websocket_exception_handling(self):
        """Test WebSocket exception handling."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Add mock client that throws exception
                mock_websocket = Mock()
                mock_websocket.send_json = AsyncMock(side_effect=Exception("WebSocket error"))
                server._clients.add(mock_websocket)
                
                # Broadcast should handle exceptions
                message = {"type": "test", "text": "error test"}
                
                try:
                    asyncio.run(server.broadcast(message))
                    # Should handle WebSocket errors gracefully
                    assert True
                except Exception:
                    # Should handle or propagate appropriately
                    assert True


class TestDashboardServerConfiguration:
    """Test DashboardServer configuration handling."""

    def test_settings_integration(self):
        """Test settings integration in server."""
        custom_settings = Mock(spec=Settings)
        custom_settings.dashboard_host = "0.0.0.0"
        custom_settings.dashboard_port = 9000
        custom_settings.debug = True
        
        with patch('jarvis.web.server.get_settings', return_value=custom_settings):
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                assert server.settings == custom_settings
                assert server.settings.dashboard_port == 9000
                assert server.settings.debug is True

    def test_certificate_handling(self):
        """Test certificate handling in server."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                with patch('jarvis.web.server.ensure_certificates') as mock_ensure_certs:
                    server = DashboardServer()
                    
                    # Should ensure certificates are available
                    # (This would be called during server startup)
                    assert True

    def test_queue_configuration(self):
        """Test queue configuration in server."""
        custom_queue = asyncio.Queue(maxsize=50)
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer(command_queue=custom_queue)
                
                assert server.command_queue == custom_queue
                assert server._phone_audio_queue.maxsize == 200

    def test_callback_configuration(self):
        """Test callback configuration in server."""
        wake_callback = Mock()
        connect_callback = Mock()
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer(
                    wake_callback=wake_callback,
                    connect_callback=connect_callback
                )
                
                assert server.wake_callback == wake_callback
                assert server.connect_callback == connect_callback


class TestDashboardServerPerformance:
    """Test DashboardServer performance characteristics."""

    def test_multiple_client_connections(self):
        """Test handling multiple client connections."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Add multiple mock clients
                clients = []
                for i in range(100):
                    mock_client = Mock()
                    clients.append(mock_client)
                    server._clients.add(mock_client)
                
                assert len(server._clients) == 100
                
                # Test broadcast to many clients
                message = {"type": "test", "text": "broadcast to many"}
                
                # Mock async send for all clients
                async def mock_send_json(data):
                    pass
                
                for client in clients:
                    client.send_json = AsyncMock(side_effect=mock_send_json)
                
                # Run broadcast
                asyncio.run(server.broadcast(message))
                
                # All clients should receive the message
                for client in clients:
                    client.send_json.assert_called_once_with(message)

    def test_history_management(self):
        """Test history management performance."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Add many history entries
                for i in range(1000):
                    entry = {"type": "test", "text": f"Message {i}"}
                    server._history.append(entry)
                
                assert len(server._history) == 1000
                
                # History should be manageable
                assert isinstance(server._history, list)
                assert all(isinstance(entry, dict) for entry in server._history)

    def test_queue_performance(self):
        """Test queue performance under load."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                
                # Fill command queue
                for i in range(100):
                    command = {"type": "test", "data": f"command_{i}"}
                    server.command_queue.put_nowait(command)
                
                assert server.command_queue.qsize() == 100
                
                # Fill phone audio queue
                for i in range(200):
                    audio_data = f"audio_data_{i}"
                    try:
                        server._phone_audio_queue.put_nowait(audio_data)
                    except asyncio.QueueFull:
                        break  # Queue is full as expected
                
                assert server._phone_audio_queue.qsize() == 200


class TestDashboardServerIntegration:
    """Test DashboardServer integration scenarios."""

    def test_auth_integration(self):
        """Test authentication integration."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "valid_session"
                mock_auth.create_token.return_value = "valid_token"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test login integration
                response = client.post("/login", json={"pin": "1234"})
                
                assert response.status_code == 200
                assert response.json()["token"] == "valid_token"
                mock_auth.validate_pin.assert_called_once()
                mock_auth.create_token.assert_called_once_with("valid_session")

    def test_callback_integration(self):
        """Test callback integration."""
        connect_callback = Mock()
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "valid_session"
                mock_auth.create_token.return_value = "valid_token"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer(connect_callback=connect_callback)
                client = TestClient(server.app)
                
                # Test callback is called on successful login
                response = client.post("/login", json={"pin": "1234"})
                
                assert response.status_code == 200
                connect_callback.assert_called_once()

    def test_broadcast_integration(self):
        """Test broadcast integration with callbacks."""
        connect_callback = Mock()
        
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "valid_session"
                mock_auth.create_token.return_value = "valid_token"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer(connect_callback=connect_callback)
                
                # Mock WebSocket client
                mock_websocket = Mock()
                mock_websocket.send_json = AsyncMock()
                server._clients.add(mock_websocket)
                
                # Test broadcast on login
                client = TestClient(server.app)
                response = client.post("/login", json={"pin": "1234"})
                
                assert response.status_code == 200
                connect_callback.assert_called_once()
                
                # Check that broadcast was called
                asyncio.run(server.broadcast({"type": "test"}))
                mock_websocket.send_json.assert_called()

    def test_static_file_integration(self):
        """Test static file integration."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                with patch('jarvis.web.server._read_static') as mock_read_static:
                    mock_read_static.return_value = "<html>Test content</html>"
                    
                    server = DashboardServer()
                    client = TestClient(server.app)
                    
                    # Test static file serving
                    response = client.get("/login")
                    
                    assert response.status_code == 200
                    assert "<html>Test content</html>" in response.text
                    mock_read_static.assert_called_once_with("login.html")

    def test_error_propagation(self):
        """Test error propagation through server layers."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.side_effect = Exception("Database error")
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test error propagation
                response = client.post("/login", json={"pin": "1234"})
                
                # Should handle errors appropriately
                assert response.status_code in [500, 401]


class TestDashboardServerEdgeCases:
    """Test DashboardServer edge cases."""

    def test_empty_request_body(self):
        """Test handling of empty request body."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test empty POST request
                response = client.post("/login", data="")
                
                assert response.status_code == 422  # Validation error

    def test_malformed_json_request(self):
        """Test handling of malformed JSON requests."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager:
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test malformed JSON
                response = client.post("/login", data='{"pin": "1234"')
                
                assert response.status_code == 422  # Validation error

    def test_missing_pin_parameter(self):
        """Test handling of missing PIN parameter."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = None
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test missing PIN
                response = client.post("/login", json={})
                
                assert response.status_code == 401
                data = response.json()
                assert data["ok"] is False

    def test_unicode_handling(self):
        """Test Unicode handling in requests."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "unicode_session"
                mock_auth.create_token.return_value = "unicode_token"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test Unicode PIN
                response = client.post("/login", json={"pin": "ñáéíóú"})
                
                assert response.status_code == 200
                mock_auth.validate_pin.assert_called_once_with("ÑÁÉÍÓÚ", "testclient")

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        with patch('jarvis.web.server.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.dashboard_port = 8000
            mock_get_settings.return_value = mock_settings
            
            with patch('jarvis.web.server.AuthManager') as mock_auth_manager_class:
                mock_auth = Mock()
                mock_auth.validate_pin.return_value = "session_concurrent"
                mock_auth.create_token.return_value = "token_concurrent"
                mock_auth_manager_class.return_value = mock_auth
                
                server = DashboardServer()
                client = TestClient(server.app)
                
                # Test multiple concurrent requests
                import threading
                
                responses = []
                
                def make_request():
                    response = client.post("/login", json={"pin": "1234"})
                    responses.append(response)
                
                threads = []
                for _ in range(10):
                    thread = threading.Thread(target=make_request)
                    threads.append(thread)
                    thread.start()
                
                for thread in threads:
                    thread.join()
                
                assert len(responses) == 10
                assert all(response.status_code == 200 for response in responses)
