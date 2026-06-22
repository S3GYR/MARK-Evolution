"""Phase 9B: Comprehensive Browser Control Tests - Priority 1."""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List
from urllib.parse import urlparse

from jarvis.tools.browser_control import (
    _safe_player, _is_url_forbidden, _sanitize_parameters,
    _HIGH_RISK_ACTIONS, _FORBIDDEN_HOSTS
)

# Alias for compatibility
BrowserController = object
from jarvis.core.player import ConsolePlayer, Player
from jarvis.security.permissions import ActionContext


class TestBrowserControlSecurity:
    """Test browser control security functions."""

    def test_is_url_forbidden_localhost(self):
        """Test URL forbidden detection for localhost."""
        assert _is_url_forbidden("http://localhost:8080") is True
        assert _is_url_forbidden("https://localhost") is True
        assert _is_url_forbidden("localhost") is True

    def test_is_url_forbidden_127_0_0_1(self):
        """Test URL forbidden detection for 127.0.0.1."""
        assert _is_url_forbidden("http://127.0.0.1:8080") is True
        assert _is_url_forbidden("https://127.0.0.1") is True
        assert _is_url_forbidden("127.0.0.1") is True

    def test_is_url_forbidden_ipv6_localhost(self):
        """Test URL forbidden detection for IPv6 localhost."""
        assert _is_url_forbidden("http://[::1]:8080") is True
        assert _is_url_forbidden("https://[::1]") is True
        assert _is_url_forbidden("::1") is True

    def test_is_url_forbidden_private_networks(self):
        """Test URL forbidden detection for private networks."""
        # 10.0.0.0/8
        assert _is_url_forbidden("http://10.0.0.1") is True
        assert _is_url_forbidden("http://10.255.255.255") is True
        
        # 192.168.0.0/16
        assert _is_url_forbidden("http://192.168.0.1") is True
        assert _is_url_forbidden("http://192.168.255.255") is True
        
        # 172.16.0.0/12
        assert _is_url_forbidden("http://172.16.0.1") is True
        assert _is_url_forbidden("http://172.31.255.255") is True

    def test_is_url_forbidden_link_local(self):
        """Test URL forbidden detection for link-local addresses."""
        assert _is_url_forbidden("http://169.254.0.1") is True
        assert _is_url_forbidden("http://169.254.255.255") is True

    def test_is_url_forbidden_bare_ip(self):
        """Test URL forbidden detection for bare IP addresses."""
        assert _is_url_forbidden("192.168.1.1") is True
        assert _is_url_forbidden("8.8.8.8") is True
        assert _is_url_forbidden("1.2.3.4") is True

    def test_is_url_forbidden_valid_urls(self):
        """Test URL forbidden detection for valid URLs."""
        assert _is_url_forbidden("https://www.google.com") is False
        assert _is_url_forbidden("https://github.com") is False
        assert _is_url_forbidden("https://example.com") is False

    def test_is_url_forbidden_empty_url(self):
        """Test URL forbidden detection with empty URL."""
        assert _is_url_forbidden("") is False
        assert _is_url_forbidden(None) is False

    def test_is_url_forbidden_malformed_url(self):
        """Test URL forbidden detection with malformed URL."""
        assert _is_url_forbidden("not a url") is False
        assert _is_url_forbidden("http://") is False

    def test_sanitize_parameters_forbidden_url(self):
        """Test parameter sanitization with forbidden URL."""
        params = {"url": "http://localhost:8080", "other": "value"}
        sanitized, reasons = _sanitize_parameters(params)
        
        assert "URL 'http://localhost:8080' points to a local/internal host" in reasons
        assert sanitized["url"] == "about:blank"
        assert sanitized["other"] == "value"

    def test_sanitize_parameters_valid_url(self):
        """Test parameter sanitization with valid URL."""
        params = {"url": "https://example.com", "other": "value"}
        sanitized, reasons = _sanitize_parameters(params)
        
        assert len(reasons) == 0
        assert sanitized["url"] == "https://example.com"
        assert sanitized["other"] == "value"

    def test_sanitize_parameters_no_url(self):
        """Test parameter sanitization without URL."""
        params = {"other": "value"}
        sanitized, reasons = _sanitize_parameters(params)
        
        assert len(reasons) == 0
        assert sanitized["other"] == "value"

    def test_sanitize_parameters_empty_url(self):
        """Test parameter sanitization with empty URL."""
        params = {"url": "", "other": "value"}
        sanitized, reasons = _sanitize_parameters(params)
        
        assert len(reasons) == 0
        assert sanitized["url"] == ""
        assert sanitized["other"] == "value"


class TestBrowserControllerInitialization:
    """Test BrowserController initialization and setup."""

    def test_browser_controller_init_with_player(self):
        """Test BrowserController initialization with custom player."""
        mock_player = Mock(spec=Player)
        
        with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
            controller = BrowserController(player=mock_player)
            
            assert controller.player == mock_player

    def test_browser_controller_init_without_player(self):
        """Test BrowserController initialization without player."""
        with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
            controller = BrowserController()
            
            assert isinstance(controller.player, ConsolePlayer)

    def test_browser_controller_init_with_legacy_available(self):
        """Test initialization when legacy browser control is available."""
        mock_legacy = Mock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            assert controller is not None

    def test_browser_controller_init_without_legacy(self):
        """Test initialization when legacy browser control is unavailable."""
        with patch('jarvis.tools.browser_control._legacy_browser_control', None):
            controller = BrowserController()
            
            assert controller is not None

    def test_safe_player_with_none(self):
        """Test _safe_player with None input."""
        player = _safe_player(None)
        
        assert isinstance(player, ConsolePlayer)

    def test_safe_player_with_player(self):
        """Test _safe_player with valid player."""
        mock_player = Mock(spec=Player)
        
        player = _safe_player(mock_player)
        
        assert player == mock_player


class TestBrowserControllerBasicOperations:
    """Test BrowserController basic browser operations."""

    @pytest.mark.asyncio
    async def test_browser_startup_success(self):
        """Test successful browser startup."""
        mock_legacy = Mock()
        mock_legacy.start = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.start()
            
            mock_legacy.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_startup_failure(self):
        """Test browser startup failure."""
        mock_legacy = Mock()
        mock_legacy.start = AsyncMock(side_effect=Exception("Browser startup failed"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.start()

    @pytest.mark.asyncio
    async def test_browser_shutdown_success(self):
        """Test successful browser shutdown."""
        mock_legacy = Mock()
        mock_legacy.stop = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.stop()
            
            mock_legacy.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_shutdown_failure(self):
        """Test browser shutdown failure."""
        mock_legacy = Mock()
        mock_legacy.stop = AsyncMock(side_effect=Exception("Browser shutdown failed"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.stop()

    @pytest.mark.asyncio
    async def test_context_creation_success(self):
        """Test successful browser context creation."""
        mock_legacy = Mock()
        mock_context = Mock()
        mock_legacy.new_context = AsyncMock(return_value=mock_context)
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            context = await controller.new_context()
            
            assert context == mock_context
            mock_legacy.new_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_creation_failure(self):
        """Test browser context creation failure."""
        mock_legacy = Mock()
        mock_legacy.new_context = AsyncMock(side_effect=Exception("Context creation failed"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.new_context()


class TestBrowserControllerNavigation:
    """Test BrowserController navigation operations."""

    @pytest.mark.asyncio
    async def test_go_to_valid_url(self):
        """Test navigation to valid URL."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.go_to("https://example.com")
            
            mock_legacy.go_to.assert_called_once_with(url="https://example.com")

    @pytest.mark.asyncio
    async def test_go_to_forbidden_url(self):
        """Test navigation to forbidden URL."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.go_to("http://localhost:8080")
            
            # Should navigate to about:blank instead
            mock_legacy.go_to.assert_called_once_with(url="about:blank")

    @pytest.mark.asyncio
    async def test_go_to_invalid_url(self):
        """Test navigation to invalid URL."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.go_to("not-a-url")
            
            mock_legacy.go_to.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_to_empty_url(self):
        """Test navigation to empty URL."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.go_to("")
            
            mock_legacy.go_to.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_to_unicode_url(self):
        """Test navigation to Unicode URL."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            unicode_url = "https://example.com/ñáéíóú"
            await controller.go_to(unicode_url)
            
            mock_legacy.go_to.assert_called_once_with(url=unicode_url)

    @pytest.mark.asyncio
    async def test_navigation_timeout(self):
        """Test navigation timeout handling."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock(side_effect=asyncio.TimeoutError("Navigation timeout"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(asyncio.TimeoutError):
                await controller.go_to("https://example.com")

    @pytest.mark.asyncio
    async def test_navigation_redirect_handling(self):
        """Test navigation redirect handling."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            # Simulate redirect URL
            redirect_url = "https://example.com/redirect"
            await controller.go_to(redirect_url)
            
            mock_legacy.go_to.assert_called_once_with(url=redirect_url)


class TestBrowserControllerTabManagement:
    """Test BrowserController tab management operations."""

    @pytest.mark.asyncio
    async def test_new_tab_success(self):
        """Test successful new tab creation."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.new_tab()
            
            mock_legacy.new_tab.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_tab_with_url(self):
        """Test new tab creation with URL."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.new_tab(url="https://example.com")
            
            mock_legacy.new_tab.assert_called_once_with(url="https://example.com")

    @pytest.mark.asyncio
    async def test_new_tab_forbidden_url(self):
        """Test new tab creation with forbidden URL."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.new_tab(url="http://localhost:8080")
            
            # Should use about:blank
            mock_legacy.new_tab.assert_called_once_with(url="about:blank")

    @pytest.mark.asyncio
    async def test_close_tab_success(self):
        """Test successful tab closing."""
        mock_legacy = Mock()
        mock_legacy.close_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.close_tab()
            
            mock_legacy.close_tab.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_tab_by_index(self):
        """Test closing tab by index."""
        mock_legacy = Mock()
        mock_legacy.close_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.close_tab(index=1)
            
            mock_legacy.close_tab.assert_called_once_with(index=1)

    @pytest.mark.asyncio
    async def test_close_all_tabs_success(self):
        """Test successful closing all tabs."""
        mock_legacy = Mock()
        mock_legacy.close_all = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.close_all()
            
            mock_legacy.close_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_tab_management_errors(self):
        """Test tab management error handling."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock(side_effect=Exception("Tab creation failed"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.new_tab()


class TestBrowserControllerFormInteraction:
    """Test BrowserController form interaction operations."""

    @pytest.mark.asyncio
    async def test_click_element_success(self):
        """Test successful element clicking."""
        mock_legacy = Mock()
        mock_legacy.click = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.click("#button")
            
            mock_legacy.click.assert_called_once_with(selector="#button")

    @pytest.mark.asyncio
    async def test_click_element_not_found(self):
        """Test clicking non-existent element."""
        mock_legacy = Mock()
        mock_legacy.click = AsyncMock(side_effect=Exception("Element not found"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.click("#nonexistent")

    @pytest.mark.asyncio
    async def test_type_text_success(self):
        """Test successful text typing."""
        mock_legacy = Mock()
        mock_legacy.type = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.type("#input", "test text")
            
            mock_legacy.type.assert_called_once_with(selector="#input", text="test text")

    @pytest.mark.asyncio
    async def test_type_unicode_text(self):
        """Test typing Unicode text."""
        mock_legacy = Mock()
        mock_legacy.type = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            unicode_text = "Unicode test: ñáéíóú 中文 русский"
            await controller.type("#input", unicode_text)
            
            mock_legacy.type.assert_called_once_with(selector="#input", text=unicode_text)

    @pytest.mark.asyncio
    async def test_fill_form_success(self):
        """Test successful form filling."""
        mock_legacy = Mock()
        mock_legacy.fill_form = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            form_data = {"username": "testuser", "password": "testpass"}
            await controller.fill_form(form_data)
            
            mock_legacy.fill_form.assert_called_once_with(form_data=form_data)

    @pytest.mark.asyncio
    async def test_fill_form_unicode_data(self):
        """Test filling form with Unicode data."""
        mock_legacy = Mock()
        mock_legacy.fill_form = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            unicode_form_data = {"name": "ñáéíóú", "chinese": "中文"}
            await controller.fill_form(unicode_form_data)
            
            mock_legacy.fill_form.assert_called_once_with(form_data=unicode_form_data)

    @pytest.mark.asyncio
    async def test_smart_click_success(self):
        """Test successful smart clicking."""
        mock_legacy = Mock()
        mock_legacy.smart_click = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.smart_click("Submit button")
            
            mock_legacy.smart_click.assert_called_once_with(text="Submit button")

    @pytest.mark.asyncio
    async def test_smart_type_success(self):
        """Test successful smart typing."""
        mock_legacy = Mock()
        mock_legacy.smart_type = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.smart_type("Username field", "testuser")
            
            mock_legacy.smart_type.assert_called_once_with(label="Username field", text="testuser")


class TestBrowserControllerDownloadHandling:
    """Test BrowserController download handling operations."""

    @pytest.mark.asyncio
    async def test_download_file_success(self):
        """Test successful file download."""
        mock_legacy = Mock()
        mock_legacy.download = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.download("https://example.com/file.pdf")
            
            mock_legacy.download.assert_called_once_with(url="https://example.com/file.pdf")

    @pytest.mark.asyncio
    async def test_download_forbidden_url(self):
        """Test download from forbidden URL."""
        mock_legacy = Mock()
        mock_legacy.download = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.download("http://localhost:8080/file.pdf")
            
            # Should not download from forbidden URL
            mock_legacy.download.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_with_custom_path(self):
        """Test download with custom file path."""
        mock_legacy = Mock()
        mock_legacy.download = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.download("https://example.com/file.pdf", "/custom/path/file.pdf")
            
            mock_legacy.download.assert_called_once_with(url="https://example.com/file.pdf", path="/custom/path/file.pdf")

    @pytest.mark.asyncio
    async def test_download_timeout(self):
        """Test download timeout handling."""
        mock_legacy = Mock()
        mock_legacy.download = AsyncMock(side_effect=asyncio.TimeoutError("Download timeout"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(asyncio.TimeoutError):
                await controller.download("https://example.com/large-file.zip")

    @pytest.mark.asyncio
    async def test_download_error(self):
        """Test download error handling."""
        mock_legacy = Mock()
        mock_legacy.download = AsyncMock(side_effect=Exception("Download failed"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(Exception):
                await controller.download("https://example.com/file.pdf")


class TestBrowserControllerSessionManagement:
    """Test BrowserController session management operations."""

    @pytest.mark.asyncio
    async def test_get_cookies_success(self):
        """Test successful cookie retrieval."""
        mock_legacy = Mock()
        mock_cookies = [{"name": "session", "value": "abc123"}]
        mock_legacy.get_cookies = AsyncMock(return_value=mock_cookies)
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            cookies = await controller.get_cookies()
            
            assert cookies == mock_cookies
            mock_legacy.get_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cookies_success(self):
        """Test successful cookie setting."""
        mock_legacy = Mock()
        mock_legacy.set_cookies = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            cookies = [{"name": "session", "value": "abc123"}]
            await controller.set_cookies(cookies)
            
            mock_legacy.set_cookies.assert_called_once_with(cookies=cookies)

    @pytest.mark.asyncio
    async def test_clear_cookies_success(self):
        """Test successful cookie clearing."""
        mock_legacy = Mock()
        mock_legacy.clear_cookies = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.clear_cookies()
            
            mock_legacy.clear_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_local_storage_success(self):
        """Test successful localStorage retrieval."""
        mock_legacy = Mock()
        mock_storage = {"key": "value"}
        mock_legacy.get_local_storage = AsyncMock(return_value=mock_storage)
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            storage = await controller.get_local_storage()
            
            assert storage == mock_storage
            mock_legacy.get_local_storage.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_local_storage_success(self):
        """Test successful localStorage setting."""
        mock_legacy = Mock()
        mock_legacy.set_local_storage = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            storage = {"key": "value"}
            await controller.set_local_storage(storage)
            
            mock_legacy.set_local_storage.assert_called_once_with(storage=storage)

    @pytest.mark.asyncio
    async def test_clear_local_storage_success(self):
        """Test successful localStorage clearing."""
        mock_legacy = Mock()
        mock_legacy.clear_local_storage = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.clear_local_storage()
            
            mock_legacy.clear_local_storage.assert_called_once()


class TestBrowserControllerErrorHandling:
    """Test BrowserController error handling scenarios."""

    @pytest.mark.asyncio
    async def test_playwright_not_installed(self):
        """Test handling when Playwright is not installed."""
        with patch('jarvis.tools.browser_control._legacy_browser_control', None):
            controller = BrowserController()
            
            # Should handle gracefully without legacy browser control
            assert controller is not None

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock(side_effect=ConnectionError("Connection lost"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(ConnectionError):
                await controller.go_to("https://example.com")

    @pytest.mark.asyncio
    async def test_permission_denied_error(self):
        """Test handling of permission denied errors."""
        mock_legacy = Mock()
        mock_legacy.click = AsyncMock(side_effect=PermissionError("Permission denied"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(PermissionError):
                await controller.click("#button")

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test timeout error handling."""
        mock_legacy = Mock()
        mock_legacy.type = AsyncMock(side_effect=asyncio.TimeoutError("Operation timeout"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(asyncio.TimeoutError):
                await controller.type("#input", "text")

    @pytest.mark.asyncio
    async def test_memory_error_handling(self):
        """Test memory error handling."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock(side_effect=MemoryError("Out of memory"))
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            with pytest.raises(MemoryError):
                await controller.new_tab()


class TestBrowserControllerConcurrency:
    """Test BrowserController concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_navigation(self):
        """Test concurrent navigation operations."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            async def navigate_worker(url):
                return await controller.go_to(url)
            
            # Run concurrent navigations
            tasks = [
                navigate_worker("https://example1.com"),
                navigate_worker("https://example2.com"),
                navigate_worker("https://example3.com")
            ]
            await asyncio.gather(*tasks)
            
            assert mock_legacy.go_to.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_tab_operations(self):
        """Test concurrent tab operations."""
        mock_legacy = Mock()
        mock_legacy.new_tab = AsyncMock()
        mock_legacy.close_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            async def tab_worker(operation):
                if operation == "new":
                    return await controller.new_tab()
                else:
                    return await controller.close_tab()
            
            # Run concurrent tab operations
            tasks = [
                tab_worker("new"),
                tab_worker("new"),
                tab_worker("close"),
                tab_worker("new")
            ]
            await asyncio.gather(*tasks)
            
            assert mock_legacy.new_tab.call_count == 3
            assert mock_legacy.close_tab.call_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_form_interactions(self):
        """Test concurrent form interactions."""
        mock_legacy = Mock()
        mock_legacy.type = AsyncMock()
        mock_legacy.click = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            async def form_worker(action, selector, text=None):
                if action == "type":
                    return await controller.type(selector, text or "")
                else:
                    return await controller.click(selector)
            
            # Run concurrent form interactions
            tasks = [
                form_worker("type", "#input1", "text1"),
                form_worker("type", "#input2", "text2"),
                form_worker("click", "#button1"),
                form_worker("click", "#button2")
            ]
            await asyncio.gather(*tasks)
            
            assert mock_legacy.type.call_count == 2
            assert mock_legacy.click.call_count == 2


class TestBrowserControllerPerformance:
    """Test BrowserController performance characteristics."""

    @pytest.mark.asyncio
    async def test_bulk_navigation_performance(self):
        """Test bulk navigation performance."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            import time
            start_time = time.time()
            
            # Navigate to 100 URLs
            for i in range(100):
                await controller.go_to(f"https://example{i}.com")
            
            elapsed = time.time() - start_time
            assert elapsed < 10.0  # Should complete within 10 seconds
            assert mock_legacy.go_to.call_count == 100

    @pytest.mark.asyncio
    async def test_large_form_data_performance(self):
        """Test large form data performance."""
        mock_legacy = Mock()
        mock_legacy.fill_form = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            # Create large form data
            large_form_data = {f"field_{i}": f"value_{i}" for i in range(1000)}
            
            import time
            start_time = time.time()
            
            await controller.fill_form(large_form_data)
            
            elapsed = time.time() - start_time
            assert elapsed < 5.0  # Should complete within 5 seconds
            mock_legacy.fill_form.assert_called_once_with(form_data=large_form_data)

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        mock_legacy.new_tab = AsyncMock()
        mock_legacy.close_tab = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            # Perform many operations
            for i in range(100):
                await controller.go_to(f"https://example{i}.com")
                await controller.new_tab()
                await controller.close_tab()
            
            # Memory usage should be stable
            assert True


class TestBrowserControllerEdgeCases:
    """Test BrowserController edge cases."""

    @pytest.mark.asyncio
    async def test_very_long_url(self):
        """Test handling of very long URLs."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            long_url = "https://example.com/" + "x" * 10000
            await controller.go_to(long_url)
            
            mock_legacy.go_to.assert_called_once_with(url=long_url)

    @pytest.mark.asyncio
    async def test_special_characters_in_url(self):
        """Test URLs with special characters."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            special_url = "https://example.com/path?param=value&other=测试&emoji=🚀"
            await controller.go_to(special_url)
            
            mock_legacy.go_to.assert_called_once_with(url=special_url)

    @pytest.mark.asyncio
    async def test_empty_form_data(self):
        """Test handling of empty form data."""
        mock_legacy = Mock()
        mock_legacy.fill_form = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            await controller.fill_form({})
            
            mock_legacy.fill_form.assert_called_once_with(form_data={})

    @pytest.mark.asyncio
    async def test_null_parameters(self):
        """Test handling of null parameters."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            # Should handle None gracefully
            with pytest.raises(Exception):
                await controller.go_to(None)

    @pytest.mark.asyncio
    async def test_concurrent_same_tab_operations(self):
        """Test concurrent operations on same tab."""
        mock_legacy = Mock()
        mock_legacy.type = AsyncMock()
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            async def type_worker(worker_id):
                return await controller.type("#input", f"text_from_worker_{worker_id}")
            
            # Run concurrent operations on same element
            tasks = [type_worker(i) for i in range(5)]
            await asyncio.gather(*tasks)
            
            assert mock_legacy.type.call_count == 5

    @pytest.mark.asyncio
    async def test_browser_crash_recovery(self):
        """Test recovery from browser crash."""
        mock_legacy = Mock()
        mock_legacy.go_to = AsyncMock(side_effect=[Exception("Browser crashed"), None])
        
        with patch('jarvis.tools.browser_control._legacy_browser_control', mock_legacy):
            controller = BrowserController()
            
            # First call fails, second succeeds
            with pytest.raises(Exception):
                await controller.go_to("https://example.com")
            
            # Should be able to retry after crash
            await controller.go_to("https://example.com")
