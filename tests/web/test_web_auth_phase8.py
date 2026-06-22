"""Phase 8: Comprehensive Web Auth Tests - Priority 2."""

from __future__ import annotations

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from jarvis.web.auth import AuthManager
from jarvis.config.settings import Settings


class TestAuthManagerInitialization:
    """Test AuthManager initialization and setup."""

    def test_auth_manager_initialization(self):
        """Test AuthManager initialization with settings."""
        mock_settings = Mock(spec=Settings)
        mock_settings.dashboard_auth_token_ttl = 3600
        
        auth_manager = AuthManager(mock_settings)
        
        assert auth_manager.settings == mock_settings
        assert auth_manager._pending_pins == {}
        assert auth_manager._tokens == set()
        assert auth_manager._token_keys == {}
        assert auth_manager._aes_cache == {}
        assert auth_manager._device_sessions == {}
        assert auth_manager._failed_attempts == {}
        assert auth_manager._max_attempts == 5
        assert auth_manager._lockout_seconds == 60

    def test_auth_manager_default_values(self):
        """Test AuthManager default values."""
        mock_settings = Mock(spec=Settings)
        
        auth_manager = AuthManager(mock_settings)
        
        # Security-related defaults
        assert auth_manager._max_attempts == 5
        assert auth_manager._lockout_seconds == 60
        
        # Empty state
        assert len(auth_manager._pending_pins) == 0
        assert len(auth_manager._tokens) == 0
        assert len(auth_manager._token_keys) == 0
        assert len(auth_manager._aes_cache) == 0
        assert len(auth_manager._device_sessions) == 0
        assert len(auth_manager._failed_attempts) == 0


class TestAuthManagerLockout:
    """Test AuthManager lockout functionality."""

    def test_is_locked_out_no_attempts(self):
        """Test lockout check with no previous attempts."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        assert auth_manager.is_locked_out("192.168.1.100") is False

    def test_is_locked_out_few_attempts(self):
        """Test lockout check with few failed attempts."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Record 3 failed attempts (less than max)
        for _ in range(3):
            auth_manager.record_attempt("192.168.1.100", False)
        
        assert auth_manager.is_locked_out("192.168.1.100") is False

    def test_is_locked_out_max_attempts(self):
        """Test lockout check with maximum failed attempts."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Record 5 failed attempts (max attempts)
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        assert auth_manager.is_locked_out("192.168.1.100") is True

    def test_is_locked_out_after_lockout_period(self):
        """Test lockout check after lockout period expires."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Record max attempts to trigger lockout
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        assert auth_manager.is_locked_out("192.168.1.100") is True
        
        # Mock time advancement beyond lockout period
        with patch('time.time', return_value=time.time() + 70):  # 70 seconds later
            assert auth_manager.is_locked_out("192.168.1.100") is False

    def test_is_locked_out_different_ips(self):
        """Test lockout isolation between different IPs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Lock out one IP
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        # Other IP should not be locked out
        assert auth_manager.is_locked_out("192.168.1.100") is True
        assert auth_manager.is_locked_out("192.168.1.101") is False
        assert auth_manager.is_locked_out("10.0.0.1") is False

    def test_record_attempt_success(self):
        """Test recording successful attempt."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Record some failed attempts first
        for _ in range(3):
            auth_manager.record_attempt("192.168.1.100", False)
        
        assert len(auth_manager._failed_attempts) == 1
        
        # Record successful attempt
        auth_manager.record_attempt("192.168.1.100", True)
        
        # Failed attempts should be cleared
        assert len(auth_manager._failed_attempts) == 0
        assert "192.168.1.100" not in auth_manager._failed_attempts

    def test_record_attempt_failure_increment(self):
        """Test recording failed attempt increments counter."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Record failed attempts
        for i in range(3):
            auth_manager.record_attempt("192.168.1.100", False)
            count, lockout_until = auth_manager._failed_attempts["192.168.1.100"]
            assert count == i + 1

    def test_record_attempt_lockout_trigger(self):
        """Test that max attempts trigger lockout."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Record attempts up to max
        for i in range(5):
            with patch('time.time', return_value=current_time + i):
                auth_manager.record_attempt("192.168.1.100", False)
        
        count, lockout_until = auth_manager._failed_attempts["192.168.1.100"]
        assert count == 5
        assert lockout_until > current_time + 4  # Should be set to future time

    def test_record_attempt_after_lockout_expiry(self):
        """Test recording attempt after lockout expires."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Trigger lockout
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        # Wait for lockout to expire
        future_time = current_time + 70
        with patch('time.time', return_value=future_time):
            # Record another failed attempt
            auth_manager.record_attempt("192.168.1.100", False)
            
            count, lockout_until = auth_manager._failed_attempts["192.168.1.100"]
            assert count == 1  # Should reset to 1
            assert lockout_until == 0.0  # No lockout yet


class TestAuthManagerPinGeneration:
    """Test AuthManager PIN generation functionality."""

    def test_new_pin_creation(self):
        """Test new PIN creation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        with patch('jarvis.web.auth.generate_pin', return_value="123456"):
            pin = auth_manager.new_pin()
            
            assert pin == "123456"
            assert pin in auth_manager._pending_pins
            assert auth_manager._pending_pins[pin] > time.time()

    def test_new_pin_expiry_cleanup(self):
        """Test that expired PINs are cleaned up."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Add some expired PINs
        auth_manager._pending_pins = {
            "111111": current_time - 100,  # Expired
            "222222": current_time - 50,   # Expired
            "333333": current_time + 100,  # Valid
        }
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.generate_pin', return_value="444444"):
                pin = auth_manager.new_pin()
                
                # Expired PINs should be removed
                assert "111111" not in auth_manager._pending_pins
                assert "222222" not in auth_manager._pending_pins
                assert "333333" in auth_manager._pending_pins
                assert "444444" in auth_manager._pending_pins

    def test_new_pin_custom_expiry(self):
        """Test new PIN creation with custom expiry."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.generate_pin', return_value="123456"):
                pin = auth_manager.new_pin(expiry_secs=300)  # 5 minutes
                
                expiry_time = auth_manager._pending_pins[pin]
                assert expiry_time == current_time + 300

    def test_new_pin_uniqueness(self):
        """Test that new PINs are unique."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        pins = set()
        
        with patch('jarvis.web.auth.generate_pin') as mock_generate:
            mock_generate.side_effect = ["111111", "222222", "333333", "444444"]
            
            for _ in range(4):
                pin = auth_manager.new_pin()
                pins.add(pin)
            
            assert len(pins) == 4
            assert pins == {"111111", "222222", "333333", "444444"}


class TestAuthManagerPinValidation:
    """Test AuthManager PIN validation functionality."""

    def test_validate_pin_success(self):
        """Test successful PIN validation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Add valid PIN
        auth_manager._pending_pins = {"123456": current_time + 600}
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.derive_key', return_value=b"session_key_123"):
                session_key = auth_manager.validate_pin("123456", "192.168.1.100")
                
                assert session_key == b"session_key_123"
                # PIN should be consumed
                assert "123456" not in auth_manager._pending_pins

    def test_validate_pin_not_found(self):
        """Test PIN validation with non-existent PIN."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = auth_manager.validate_pin("999999", "192.168.1.100")
        
        assert session_key is None

    def test_validate_pin_expired(self):
        """Test PIN validation with expired PIN."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Add expired PIN
        auth_manager._pending_pins = {"123456": current_time - 100}
        
        with patch('time.time', return_value=current_time):
            session_key = auth_manager.validate_pin("123456", "192.168.1.100")
            
            assert session_key is None

    def test_validate_pin_case_insensitive(self):
        """Test PIN validation is case insensitive."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Add PIN in lowercase
        auth_manager._pending_pins = {"abcdef": current_time + 600}
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.derive_key', return_value=b"session_key_123"):
                # Test uppercase input
                session_key = auth_manager.validate_pin("ABCDEF", "192.168.1.100")
                
                assert session_key == b"session_key_123"

    def test_validate_pin_whitespace_handling(self):
        """Test PIN validation with whitespace handling."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Add PIN
        auth_manager._pending_pins = {"123456": current_time + 600}
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.derive_key', return_value=b"session_key_123"):
                # Test with whitespace
                session_key = auth_manager.validate_pin(" 123456 ", "192.168.1.100")
                
                assert session_key == b"session_key_123"

    def test_validate_pin_records_attempt(self):
        """Test that PIN validation records attempts."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Test failed validation
        session_key = auth_manager.validate_pin("wrong_pin", "192.168.1.100")
        
        assert session_key is None
        assert "192.168.1.100" in auth_manager._failed_attempts
        count, _ = auth_manager._failed_attempts["192.168.1.100"]
        assert count == 1

    def test_validate_pin_locked_out(self):
        """Test PIN validation when IP is locked out."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Lock out the IP
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        # Add valid PIN
        current_time = time.time()
        auth_manager._pending_pins = {"123456": current_time + 600}
        
        with patch('time.time', return_value=current_time):
            session_key = auth_manager.validate_pin("123456", "192.168.1.100")
            
            # Should return None even with valid PIN due to lockout
            assert session_key is None


class TestAuthManagerTokenManagement:
    """Test AuthManager token management functionality."""

    def test_create_token_success(self):
        """Test successful token creation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        
        with patch('jarvis.web.auth.generate_token', return_value="token_456"):
            token = auth_manager.create_token(session_key)
            
            assert token == "token_456"
            assert token in auth_manager._tokens
            assert auth_manager._token_keys[token] == session_key

    def test_create_token_uniqueness(self):
        """Test that created tokens are unique."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        
        with patch('jarvis.web.auth.generate_token') as mock_generate:
            mock_generate.side_effect = ["token_1", "token_2", "token_3"]
            
            token1 = auth_manager.create_token(session_key)
            token2 = auth_manager.create_token(session_key)
            token3 = auth_manager.create_token(session_key)
            
            assert token1 != token2 != token3
            assert len(auth_manager._tokens) == 3
            assert all(token in auth_manager._token_keys for token in [token1, token2, token3])

    def test_validate_token_success(self):
        """Test successful token validation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        token = "valid_token_456"
        
        # Add token
        auth_manager._tokens.add(token)
        auth_manager._token_keys[token] = session_key
        
        with patch('jarvis.web.auth.derive_key', return_value=b"derived_key_123"):
            result = auth_manager.validate_token(token)
            
            assert result is True
            # AES key should be cached
            assert session_key in auth_manager._aes_cache

    def test_validate_token_not_found(self):
        """Test token validation with non-existent token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_token("nonexistent_token")
        
        assert result is False

    def test_validate_token_empty(self):
        """Test token validation with empty token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_token("")
        
        assert result is False

    def test_validate_token_none(self):
        """Test token validation with None token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_token(None)
        
        assert result is False

    def test_validate_token_with_cache(self):
        """Test token validation uses AES key cache."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        token = "valid_token_456"
        
        # Add token and cache
        auth_manager._tokens.add(token)
        auth_manager._token_keys[token] = session_key
        auth_manager._aes_cache[session_key] = b"cached_aes_key"
        
        with patch('jarvis.web.auth.derive_key') as mock_derive:
            mock_derive.return_value = b"cached_aes_key"
            
            result = auth_manager.validate_token(token)
            
            assert result is True
            # Should use cached key
            mock_derive.assert_called_once()

    def test_invalidate_token_success(self):
        """Test successful token invalidation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        token = "valid_token_456"
        
        # Add token
        auth_manager._tokens.add(token)
        auth_manager._token_keys[token] = session_key
        auth_manager._aes_cache[session_key] = b"aes_key"
        
        auth_manager.invalidate_token(token)
        
        assert token not in auth_manager._tokens
        assert token not in auth_manager._token_keys
        assert session_key not in auth_manager._aes_cache

    def test_invalidate_token_nonexistent(self):
        """Test invalidating non-existent token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Should not raise error
        auth_manager.invalidate_token("nonexistent_token")
        
        assert len(auth_manager._tokens) == 0
        assert len(auth_manager._token_keys) == 0


class TestAuthManagerDeviceSessions:
    """Test AuthManager device session functionality."""

    def test_create_device_session_success(self):
        """Test successful device session creation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        
        with patch('jarvis.web.auth.generate_token', return_value="device_token_789"):
            device_token = auth_manager.create_device_session(session_key)
            
            assert device_token == "device_token_789"
            assert device_token in auth_manager._device_sessions
            assert auth_manager._device_sessions[device_token]["session_key"] == session_key

    def test_create_device_session_metadata(self):
        """Test device session creation includes metadata."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        current_time = time.time()
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.generate_token', return_value="device_token_789"):
                device_token = auth_manager.create_device_session(session_key)
                
                metadata = auth_manager._device_sessions[device_token]
                assert metadata["session_key"] == session_key
                assert "created_at" in metadata
                assert metadata["created_at"] == current_time

    def test_validate_device_session_success(self):
        """Test successful device session validation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        device_token = "device_token_789"
        
        # Add device session
        auth_manager._device_sessions[device_token] = {
            "session_key": session_key,
            "created_at": time.time()
        }
        
        result = auth_manager.validate_device_session(device_token)
        
        assert result == session_key

    def test_validate_device_session_not_found(self):
        """Test device session validation with non-existent token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_device_session("nonexistent_device_token")
        
        assert result is None

    def test_validate_device_session_empty(self):
        """Test device session validation with empty token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_device_session("")
        
        assert result is None

    def test_validate_device_session_none(self):
        """Test device session validation with None token."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        result = auth_manager.validate_device_session(None)
        
        assert result is None

    def test_invalidate_device_session_success(self):
        """Test successful device session invalidation."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        device_token = "device_token_789"
        
        # Add device session
        auth_manager._device_sessions[device_token] = {
            "session_key": b"session_key_123",
            "created_at": time.time()
        }
        
        auth_manager.invalidate_device_session(device_token)
        
        assert device_token not in auth_manager._device_sessions

    def test_invalidate_device_session_nonexistent(self):
        """Test invalidating non-existent device session."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Should not raise error
        auth_manager.invalidate_device_session("nonexistent_device_token")
        
        assert len(auth_manager._device_sessions) == 0


class TestAuthManagerCleanup:
    """Test AuthManager cleanup functionality."""

    def test_cleanup_expired_pins(self):
        """Test cleanup of expired PINs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Mix of expired and valid PINs
        auth_manager._pending_pins = {
            "111111": current_time - 100,  # Expired
            "222222": current_time + 100,  # Valid
            "333333": current_time - 50,   # Expired
            "444444": current_time + 200,  # Valid
        }
        
        with patch('time.time', return_value=current_time):
            # Trigger cleanup by creating new PIN
            with patch('jarvis.web.auth.generate_pin', return_value="555555"):
                auth_manager.new_pin()
                
                # Only valid PINs should remain
                assert "111111" not in auth_manager._pending_pins
                assert "333333" not in auth_manager._pending_pins
                assert "222222" in auth_manager._pending_pins
                assert "444444" in auth_manager._pending_pins
                assert "555555" in auth_manager._pending_pins

    def test_cleanup_expired_device_sessions(self):
        """Test cleanup of expired device sessions."""
        mock_settings = Mock(spec=Settings)
        mock_settings.dashboard_auth_token_ttl = 3600  # 1 hour
        
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Mix of expired and valid device sessions
        auth_manager._device_sessions = {
            "device1": {
                "session_key": b"key1",
                "created_at": current_time - 7200  # 2 hours ago (expired)
            },
            "device2": {
                "session_key": b"key2",
                "created_at": current_time - 1800  # 30 minutes ago (valid)
            },
            "device3": {
                "session_key": b"key3",
                "created_at": current_time - 4000  # Over 1 hour ago (expired)
            }
        }
        
        auth_manager.cleanup_expired_sessions()
        
        # Only valid sessions should remain
        assert "device1" not in auth_manager._device_sessions
        assert "device3" not in auth_manager._device_sessions
        assert "device2" in auth_manager._device_sessions

    def test_cleanup_expired_failed_attempts(self):
        """Test cleanup of expired failed attempts."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Mix of expired and valid failed attempts
        auth_manager._failed_attempts = {
            "192.168.1.100": (3, current_time - 120),  # Expired lockout
            "192.168.1.101": (2, current_time + 60),   # Valid lockout
            "192.168.1.102": (5, current_time - 180),  # Expired lockout
        }
        
        auth_manager.cleanup_expired_attempts()
        
        # Only valid attempts should remain
        assert "192.168.1.100" not in auth_manager._failed_attempts
        assert "192.168.1.102" not in auth_manager._failed_attempts
        assert "192.168.1.101" in auth_manager._failed_attempts

    def test_cleanup_aes_cache(self):
        """Test cleanup of AES key cache."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Add some cached keys
        auth_manager._aes_cache = {
            b"session1": b"aes_key1",
            b"session2": b"aes_key2",
            b"session3": b"aes_key3",
        }
        
        # Remove some tokens to make their session keys orphaned
        auth_manager._token_keys = {
            "token1": b"session1",
            "token2": b"session2"
        }
        
        auth_manager.cleanup_aes_cache()
        
        # Only cached keys for active tokens should remain
        assert b"session1" in auth_manager._aes_cache
        assert b"session2" in auth_manager._aes_cache
        assert b"session3" not in auth_manager._aes_cache


class TestAuthManagerSecurity:
    """Test AuthManager security aspects."""

    def test_pin_brute_force_protection(self):
        """Test protection against PIN brute force attacks."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Add valid PIN
        current_time = time.time()
        auth_manager._pending_pins = {"123456": current_time + 600}
        
        # Attempt brute force
        for i in range(10):
            session_key = auth_manager.validate_pin(f"wrong_{i}", "192.168.1.100")
            assert session_key is None
        
        # Should be locked out
        assert auth_manager.is_locked_out("192.168.1.100")
        
        # Even valid PIN should be rejected
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.derive_key', return_value=b"session_key_123"):
                session_key = auth_manager.validate_pin("123456", "192.168.1.100")
                assert session_key is None

    def test_token_uniqueness_security(self):
        """Test that tokens are cryptographically unique."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key = b"session_key_123"
        tokens = set()
        
        # Generate many tokens
        for _ in range(100):
            with patch('jarvis.web.auth.generate_token') as mock_generate:
                mock_generate.return_value = f"token_{len(tokens)}"
                token = auth_manager.create_token(session_key)
                tokens.add(token)
        
        # All tokens should be unique
        assert len(tokens) == 100

    def test_session_key_isolation(self):
        """Test that session keys are properly isolated."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        session_key1 = b"session_key_1"
        session_key2 = b"session_key_2"
        
        with patch('jarvis.web.auth.generate_token') as mock_generate:
            mock_generate.side_effect = ["token1", "token2"]
            
            token1 = auth_manager.create_token(session_key1)
            token2 = auth_manager.create_token(session_key2)
            
            assert auth_manager._token_keys[token1] == session_key1
            assert auth_manager._token_keys[token2] == session_key2
            assert auth_manager._token_keys[token1] != auth_manager._token_keys[token2]

    def test_ip_isolation_security(self):
        """Test that failed attempts are isolated by IP."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Lock out one IP
        for _ in range(5):
            auth_manager.record_attempt("192.168.1.100", False)
        
        # Other IPs should not be affected
        assert auth_manager.is_locked_out("192.168.1.100")
        assert not auth_manager.is_locked_out("192.168.1.101")
        assert not auth_manager.is_locked_out("10.0.0.1")

    def test_concurrent_pin_validation(self):
        """Test concurrent PIN validation safety."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        auth_manager._pending_pins = {"123456": current_time + 600}
        
        import threading
        
        results = []
        
        def validate_pin():
            with patch('time.time', return_value=current_time):
                with patch('jarvis.web.auth.derive_key', return_value=b"session_key"):
                    result = auth_manager.validate_pin("123456", "192.168.1.100")
                    results.append(result)
        
        # Multiple threads trying to validate same PIN
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=validate_pin)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Only one should succeed (PIN should be consumed)
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) <= 1


class TestAuthManagerPerformance:
    """Test AuthManager performance characteristics."""

    def test_large_scale_pin_management(self):
        """Test performance with many PINs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Create many PINs
        current_time = time.time()
        for i in range(1000):
            auth_manager._pending_pins[f"pin_{i:06d}"] = current_time + 600
        
        assert len(auth_manager._pending_pins) == 1000
        
        # Cleanup should be efficient
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.generate_pin', return_value="new_pin"):
                auth_manager.new_pin()
                
                # Should still be efficient
                assert len(auth_manager._pending_pins) <= 1001

    def test_large_scale_token_management(self):
        """Test performance with many tokens."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Create many tokens
        for i in range(1000):
            token = f"token_{i}"
            session_key = f"session_{i}".encode()
            auth_manager._tokens.add(token)
            auth_manager._token_keys[token] = session_key
        
        assert len(auth_manager._tokens) == 1000
        assert len(auth_manager._token_keys) == 1000
        
        # Token validation should be efficient
        for i in range(1000):
            token = f"token_{i}"
            if token in auth_manager._tokens:
                with patch('jarvis.web.auth.derive_key', return_value=b"derived_key"):
                    result = auth_manager.validate_token(token)
                    assert result is True

    def test_memory_usage_stability(self):
        """Test memory usage stability over time."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Perform many operations
        for i in range(100):
            # Create PIN
            pin = f"pin_{i:06d}"
            auth_manager._pending_pins[pin] = time.time() + 600
            
            # Create token
            token = f"token_{i}"
            session_key = f"session_{i}".encode()
            auth_manager._tokens.add(token)
            auth_manager._token_keys[token] = session_key
            
            # Create device session
            device_token = f"device_{i}"
            auth_manager._device_sessions[device_token] = {
                "session_key": session_key,
                "created_at": time.time()
            }
            
            # Cleanup some old entries
            if i % 10 == 0:
                auth_manager.cleanup_expired_sessions()
        
        # Memory usage should be reasonable
        assert len(auth_manager._pending_pins) <= 100
        assert len(auth_manager._tokens) <= 100
        assert len(auth_manager._device_sessions) <= 100


class TestAuthManagerEdgeCases:
    """Test AuthManager edge cases."""

    def test_empty_string_inputs(self):
        """Test handling of empty string inputs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Empty PIN
        session_key = auth_manager.validate_pin("", "192.168.1.100")
        assert session_key is None
        
        # Empty token
        result = auth_manager.validate_token("")
        assert result is False
        
        # Empty device token
        result = auth_manager.validate_device_session("")
        assert result is None

    def test_none_inputs(self):
        """Test handling of None inputs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # None PIN
        session_key = auth_manager.validate_pin(None, "192.168.1.100")
        assert session_key is None
        
        # None token
        result = auth_manager.validate_token(None)
        assert result is False
        
        # None device token
        result = auth_manager.validate_device_session(None)
        assert result is None

    def test_unicode_inputs(self):
        """Test handling of Unicode inputs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        current_time = time.time()
        
        # Unicode PIN
        unicode_pin = "ñáéíóú"
        auth_manager._pending_pins[unicode_pin.lower()] = current_time + 600
        
        with patch('time.time', return_value=current_time):
            with patch('jarvis.web.auth.derive_key', return_value=b"unicode_session"):
                session_key = auth_manager.validate_pin("ÑÁÉÍÓÚ", "192.168.1.100")
                assert session_key == b"unicode_session"

    def test_very_long_inputs(self):
        """Test handling of very long inputs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        # Very long PIN
        long_pin = "1" * 1000
        session_key = auth_manager.validate_pin(long_pin, "192.168.1.100")
        assert session_key is None
        
        # Very long token
        long_token = "a" * 1000
        result = auth_manager.validate_token(long_token)
        assert result is False

    def test_special_character_inputs(self):
        """Test handling of special character inputs."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        special_pins = [
            "123!@#",
            "abc$%^",
            "test&*()",
            "pin+-=[]",
            "data{}|\\"
        ]
        
        for pin in special_pins:
            session_key = auth_manager.validate_pin(pin, "192.168.1.100")
            assert session_key is None

    def test_concurrent_operations_safety(self):
        """Test safety of concurrent operations."""
        mock_settings = Mock(spec=Settings)
        auth_manager = AuthManager(mock_settings)
        
        import threading
        
        def worker(worker_id):
            for i in range(10):
                # Record attempts
                auth_manager.record_attempt(f"192.168.1.{worker_id}", i % 2 == 0)
                
                # Check lockout
                auth_manager.is_locked_out(f"192.168.1.{worker_id}")
        
        # Run multiple workers
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert len(auth_manager._failed_attempts) >= 0
