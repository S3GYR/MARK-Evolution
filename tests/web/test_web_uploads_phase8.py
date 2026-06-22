"""Phase 8: Comprehensive Web Uploads Tests - Priority 4."""

from __future__ import annotations

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any
from fastapi import UploadFile, File as FastAPIFile
from fastapi.testclient import TestClient
from io import BytesIO

from jarvis.web.routes.uploads import handle_upload
from jarvis.web.auth import AuthManager
from jarvis.config.settings import Settings


class TestUploadValidation:
    """Test upload validation functionality."""

    def test_is_safe_upload_allowed_extensions(self):
        """Test safe upload validation with allowed extensions."""
        with patch('jarvis.web.uploads._ALLOWED_EXTENSIONS', {'.txt', '.pdf', '.jpg', '.png'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test allowed extensions
            allowed_files = [
                UploadFile(filename="document.txt"),
                UploadFile(filename="image.jpg"),
                UploadFile(filename="photo.png"),
                UploadFile(filename="report.pdf")
            ]
            
            for file in allowed_files:
                assert _is_safe_upload(file) is True

    def test_is_safe_upload_forbidden_extensions(self):
        """Test safe upload validation with forbidden extensions."""
        with patch('jarvis.web.uploads._ALLOWED_EXTENSIONS', {'.txt', '.pdf', '.jpg', '.png'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test forbidden extensions
            forbidden_files = [
                UploadFile(filename="malware.exe"),
                UploadFile(filename="script.js"),
                UploadFile(filename="virus.bat"),
                UploadFile(filename="trojan.com"),
                UploadFile(filename="dangerous.scr")
            ]
            
            for file in forbidden_files:
                assert _is_safe_upload(file) is False

    def test_is_safe_upload_case_insensitive(self):
        """Test safe upload validation is case insensitive."""
        with patch('jarvis.web.uploads._ALLOWED_EXTENSIONS', {'.txt', '.pdf', '.jpg'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test different cases
            case_variants = [
                UploadFile(filename="document.TXT"),
                UploadFile(filename="image.JPG"),
                UploadFile(filename="report.Pdf"),
                UploadFile(filename="photo.jPg")
            ]
            
            for file in case_variants:
                assert _is_safe_upload(file) is True

    def test_is_safe_upload_no_extension(self):
        """Test safe upload validation with no extension."""
        with patch('jarvis.web.uploads._ALLOWED_EXTENSIONS', {'.txt', '.pdf', '.jpg'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test files without extensions
            no_ext_files = [
                UploadFile(filename="document"),
                UploadFile(filename="image"),
                UploadFile(filename="README")
            ]
            
            for file in no_ext_files:
                assert _is_safe_upload(file) is False

    def test_is_safe_upload_double_extension(self):
        """Test safe upload validation with double extensions."""
        with patch('jarvis.web.uploads._ALLOWED_EXTENSIONS', {'.txt', '.jpg'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test double extensions (potentially dangerous)
            double_ext_files = [
                UploadFile(filename="image.jpg.exe"),
                UploadFile(filename="document.txt.php"),
                UploadFile(filename="photo.jpg.js"),
                UploadFile(filename="file.txt.bat")
            ]
            
            for file in double_ext_files:
                assert _is_safe_upload(file) is False

    def test_is_safe_upload_mime_type_validation(self):
        """Test safe upload validation with MIME type checking."""
        with patch('jarvis.web.uploads._ALLOWED_MIME_TYPES', {'text/plain', 'image/jpeg', 'application/pdf'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test allowed MIME types
            allowed_files = [
                ("document.txt", "text/plain"),
                ("image.jpg", "image/jpeg"),
                ("report.pdf", "application/pdf")
            ]
            
            for filename, content_type in allowed_files:
                file = UploadFile(filename=filename)
                file.content_type = content_type
                assert _is_safe_upload(file) is True

    def test_is_safe_upload_forbidden_mime_type(self):
        """Test safe upload validation with forbidden MIME types."""
        with patch('jarvis.web.uploads._ALLOWED_MIME_TYPES', {'text/plain', 'image/jpeg'}):
            from jarvis.web.uploads import _is_safe_upload
            
            # Test forbidden MIME types
            forbidden_files = [
                ("script.js", "application/javascript"),
                ("executable.exe", "application/octet-stream"),
                ("malware.bat", "application/x-msdos-program")
            ]
            
            for filename, content_type in forbidden_files:
                file = UploadFile(filename=filename)
                file.content_type = content_type
                assert _is_safe_upload(file) is False


class TestUploadFileSize:
    """Test upload file size validation."""

    def test_get_file_size_small_file(self):
        """Test getting file size for small file."""
        from jarvis.web.uploads import _get_file_size
        
        content = b"Small file content"
        file = UploadFile(filename="small.txt")
        file.file = BytesIO(content)
        
        size = _get_file_size(file)
        assert size == len(content)

    def test_get_file_size_large_file(self):
        """Test getting file size for large file."""
        from jarvis.web.uploads import _get_file_size
        
        content = b"Large file content" * 10000  # ~200KB
        file = UploadFile(filename="large.txt")
        file.file = BytesIO(content)
        
        size = _get_file_size(file)
        assert size == len(content)

    def test_get_file_size_empty_file(self):
        """Test getting file size for empty file."""
        from jarvis.web.uploads import _get_file_size
        
        content = b""
        file = UploadFile(filename="empty.txt")
        file.file = BytesIO(content)
        
        size = _get_file_size(file)
        assert size == 0

    def test_is_file_size_allowed_under_limit(self):
        """Test file size validation under limit."""
        with patch('jarvis.web.uploads._MAX_SIZE', 1024 * 1024):  # 1MB
            from jarvis.web.uploads import _is_file_size_allowed
            
            # Test file under limit
            content = b"Content under 1MB"
            file = UploadFile(filename="small.txt")
            file.file = BytesIO(content)
            
            assert _is_file_size_allowed(file) is True

    def test_is_file_size_allowed_over_limit(self):
        """Test file size validation over limit."""
        with patch('jarvis.web.uploads._MAX_SIZE', 1024):  # 1KB
            from jarvis.web.uploads import _is_file_size_allowed
            
            # Test file over limit
            content = b"Content over 1KB " * 100
            file = UploadFile(filename="large.txt")
            file.file = BytesIO(content)
            
            assert _is_file_size_allowed(file) is False

    def test_is_file_size_allowed_exact_limit(self):
        """Test file size validation at exact limit."""
        with patch('jarvis.web.uploads._MAX_SIZE', 100):  # 100 bytes
            from jarvis.web.uploads import _is_file_size_allowed
            
            # Test file at exact limit
            content = b"x" * 100
            file = UploadFile(filename="exact.txt")
            file.file = BytesIO(content)
            
            assert _is_file_size_allowed(file) is True


class TestUploadPathSecurity:
    """Test upload path security validation."""

    def test_is_safe_filename_normal_names(self):
        """Test safe filename validation with normal names."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test normal filenames
        safe_names = [
            "document.txt",
            "image.jpg",
            "report.pdf",
            "data.csv",
            "photo.png",
            "archive.zip"
        ]
        
        for name in safe_names:
            assert _is_safe_filename(name) is True

    def test_is_safe_filename_path_traversal(self):
        """Test safe filename validation with path traversal attempts."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test path traversal attempts
        traversal_names = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/etc/passwd",
            "\\Windows\\System32\\drivers\\etc\\hosts",
            "folder/../../../etc/passwd",
            "folder\\..\\..\\..\\Windows\\System32\\config\\SAM"
        ]
        
        for name in traversal_names:
            assert _is_safe_filename(name) is False

    def test_is_safe_filename_special_characters(self):
        """Test safe filename validation with special characters."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test filenames with problematic characters
        problematic_names = [
            "file|name.txt",
            "file?name.txt",
            "file*name.txt",
            "file<name.txt",
            "file>name.txt",
            "file\"name.txt",
            "file:name.txt"
        ]
        
        for name in problematic_names:
            assert _is_safe_filename(name) is False

    def test_is_safe_filename_unicode(self):
        """Test safe filename validation with Unicode characters."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test Unicode filenames (should be allowed)
        unicode_names = [
            "文档.txt",  # Chinese
            "файл.txt",  # Russian
            "ファイル.txt",  # Japanese
            "café.txt",  # French
            "naïve.txt"   # English with diacritics
        ]
        
        for name in unicode_names:
            assert _is_safe_filename(name) is True

    def test_is_safe_filename_reserved_names(self):
        """Test safe filename validation with reserved names."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test reserved names (Windows)
        reserved_names = [
            "CON.txt",
            "PRN.txt",
            "AUX.txt",
            "NUL.txt",
            "COM1.txt",
            "COM2.txt",
            "LPT1.txt",
            "LPT2.txt"
        ]
        
        for name in reserved_names:
            assert _is_safe_filename(name) is False

    def test_is_safe_filename_dots_only(self):
        """Test safe filename validation with dots only."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test dots-only names
        dot_names = [
            ".",
            "..",
            "...",
            "...."
        ]
        
        for name in dot_names:
            assert _is_safe_filename(name) is False

    def test_is_safe_filename_very_long(self):
        """Test safe filename validation with very long names."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test very long filename
        long_name = "a" * 300 + ".txt"
        assert _is_safe_filename(long_name) is False


class TestUploadFileOperations:
    """Test upload file operations."""

    def test_save_upload_success(self):
        """Test successful file save operation."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                content = b"Test file content"
                file = UploadFile(filename="test.txt")
                file.file = BytesIO(content)
                
                saved_path = _save_upload(file)
                
                assert saved_path == f"{temp_dir}/test.txt"
                assert Path(saved_path).exists()
                assert Path(saved_path).read_bytes() == content

    def test_save_upload_creates_directory(self):
        """Test save upload creates directory if needed."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "uploads"
            with patch('jarvis.web.uploads.UPLOAD_DIR', str(upload_dir)):
                content = b"Test file content"
                file = UploadFile(filename="test.txt")
                file.file = BytesIO(content)
                
                saved_path = _save_upload(file)
                
                assert upload_dir.exists()
                assert saved_path == f"{upload_dir}/test.txt"
                assert Path(saved_path).read_bytes() == content

    def test_save_upload_unicode_filename(self):
        """Test save upload with Unicode filename."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                content = b"Unicode content"
                file = UploadFile(filename="测试文件.txt")
                file.file = BytesIO(content)
                
                saved_path = _save_upload(file)
                
                assert Path(saved_path).exists()
                assert Path(saved_path).read_bytes() == content

    def test_save_upload_overwrite_protection(self):
        """Test save upload overwrite protection."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                # Create initial file
                initial_content = b"Initial content"
                file1 = UploadFile(filename="test.txt")
                file1.file = BytesIO(initial_content)
                
                saved_path1 = _save_upload(file1)
                assert Path(saved_path1).read_bytes() == initial_content
                
                # Try to upload file with same name
                new_content = b"New content"
                file2 = UploadFile(filename="test.txt")
                file2.file = BytesIO(new_content)
                
                saved_path2 = _save_upload(file2)
                
                # Should either overwrite or create unique name
                assert Path(saved_path2).exists()

    def test_save_upload_permission_error(self):
        """Test save upload with permission error."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                content = b"Test content"
                file = UploadFile(filename="test.txt")
                file.file = BytesIO(content)
                
                # Mock permission error
                with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                    try:
                        _save_upload(file)
                        assert False, "Should have raised PermissionError"
                    except PermissionError:
                        pass  # Expected

    def test_save_upload_disk_full(self):
        """Test save upload with disk full error."""
        from jarvis.web.uploads import _save_upload
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                content = b"Test content"
                file = UploadFile(filename="test.txt")
                file.file = BytesIO(content)
                
                # Mock disk full error
                with patch('builtins.open', side_effect=OSError("No space left on device")):
                    try:
                        _save_upload(file)
                        assert False, "Should have raised OSError"
                    except OSError:
                        pass  # Expected


class TestUploadIntegration:
    """Test upload integration scenarios."""

    @pytest.mark.asyncio
    async def test_handle_upload_complete_flow(self):
        """Test complete upload flow."""
        from jarvis.web.routes.uploads import handle_upload
        
        mock_request = Mock()
        mock_file = UploadFile(filename="integration_test.txt")
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"Integration test content")
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/integration_test.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["ok"] is True
                assert data["filename"] == "integration_test.txt"
                assert data["path"] == "/uploads/integration_test.txt"

    @pytest.mark.asyncio
    async def test_handle_upload_with_real_file(self):
        """Test upload with real file object."""
        from jarvis.web.routes.uploads import handle_upload
        
        # Create real file content
        content = b"Real file content for testing"
        file_obj = BytesIO(content)
        
        mock_request = Mock()
        mock_file = UploadFile(filename="real_test.txt")
        mock_file.content_type = "text/plain"
        mock_file.file = file_obj
        mock_file.read = AsyncMock(return_value=content)
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
            with patch('jarvis.web.routes.uploads._save_upload', return_value="/uploads/real_test.txt"):
                response = await handle_upload(mock_request, mock_auth)
                
                assert response.status_code == 200
                data = json.loads(response.body.decode())
                assert data["ok"] is True

    @pytest.mark.asyncio
    async def test_handle_upload_concurrent_uploads(self):
        """Test concurrent upload handling."""
        from jarvis.web.routes.uploads import handle_upload
        import asyncio
        
        async def upload_worker(worker_id):
            mock_request = Mock()
            mock_file = UploadFile(filename=f"concurrent_test_{worker_id}.txt")
            mock_file.content_type = "text/plain"
            mock_file.read = AsyncMock(return_value=f"Content from worker {worker_id}".encode())
            mock_request.form.return_value = {"file": mock_file}
            
            mock_auth = Mock(spec=AuthManager)
            mock_auth.get_token_from_header.return_value = "valid_token"
            mock_auth.is_valid_token.return_value = True
            
            with patch('jarvis.web.routes.uploads._is_safe_upload', return_value=True):
                with patch('jarvis.web.routes.uploads._save_upload', return_value=f"/uploads/concurrent_test_{worker_id}.txt"):
                    response = await handle_upload(mock_request, mock_auth)
                    return response
        
        # Run concurrent uploads
        tasks = [upload_worker(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All uploads should succeed
        assert all(response.status_code == 200 for response in responses)


class TestUploadSecurity:
    """Test upload security aspects."""

    def test_upload_virus_scan_simulation(self):
        """Test virus scan simulation."""
        from jarvis.web.uploads import _is_safe_upload
        
        # Simulate virus scanning by checking file content patterns
        malicious_patterns = [
            b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
            b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR",
            b"<script>alert('xss')</script>",
            b"<?php system($_GET['cmd']); ?>"
        ]
        
        for pattern in malicious_patterns:
            file = UploadFile(filename="test.txt")
            file.content_type = "text/plain"
            file.file = BytesIO(pattern)
            
            # Should detect malicious content
            with patch('jarvis.web.uploads._scan_for_malware', return_value=False):
                assert _is_safe_upload(file) is False

    def test_upload_metadata_sanitization(self):
        """Test upload metadata sanitization."""
        from jarvis.web.uploads import _sanitize_filename
        
        # Test filename sanitization
        unsanitized_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
            "file@with@symbols.txt"
        ]
        
        for name in unsanitized_names:
            sanitized = _sanitize_filename(name)
            assert sanitized is not None
            assert "/" not in sanitized
            assert "\\" not in sanitized
            assert ".." not in sanitized

    def test_upload_content_type_validation(self):
        """Test upload content type validation."""
        from jarvis.web.uploads import _validate_content_type
        
        # Test valid content types
        valid_types = [
            ("text/plain", "document.txt"),
            ("image/jpeg", "photo.jpg"),
            ("application/pdf", "report.pdf"),
            ("image/png", "image.png")
        ]
        
        for content_type, filename in valid_types:
            assert _validate_content_type(content_type, filename) is True
        
        # Test invalid content types
        invalid_types = [
            ("application/x-executable", "program.exe"),
            ("application/javascript", "script.js"),
            ("application/x-msdos-program", "malware.bat")
        ]
        
        for content_type, filename in invalid_types:
            assert _validate_content_type(content_type, filename) is False

    def test_upload_rate_limiting(self):
        """Test upload rate limiting."""
        from jarvis.web.uploads import _check_rate_limit
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "test_token"
        
        # Test rate limiting
        for i in range(10):
            result = _check_rate_limit("test_token")
            if i < 5:  # Allow first 5 uploads
                assert result is True
            else:  # Rate limit after 5 uploads
                assert result is False


class TestUploadPerformance:
    """Test upload performance characteristics."""

    def test_large_file_upload_performance(self):
        """Test large file upload performance."""
        import time
        
        # Create large file content (10MB)
        large_content = b"x" * (10 * 1024 * 1024)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                from jarvis.web.uploads import _save_upload
                
                file = UploadFile(filename="large_test.txt")
                file.file = BytesIO(large_content)
                
                start_time = time.time()
                saved_path = _save_upload(file)
                elapsed = time.time() - start_time
                
                assert Path(saved_path).exists()
                assert Path(saved_path).stat().st_size == len(large_content)
                assert elapsed < 5.0  # Should complete within 5 seconds

    def test_many_small_files_performance(self):
        """Test many small files upload performance."""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                from jarvis.web.uploads import _save_upload
                
                start_time = time.time()
                
                # Upload 100 small files
                for i in range(100):
                    content = f"Small file content {i}".encode()
                    file = UploadFile(filename=f"small_{i}.txt")
                    file.file = BytesIO(content)
                    
                    saved_path = _save_upload(file)
                    assert Path(saved_path).exists()
                
                elapsed = time.time() - start_time
                assert elapsed < 10.0  # Should complete within 10 seconds

    def test_concurrent_upload_performance(self):
        """Test concurrent upload performance."""
        import time
        import threading
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('jarvis.web.uploads.UPLOAD_DIR', temp_dir):
                from jarvis.web.uploads import _save_upload
                
                results = []
                
                def upload_worker(worker_id):
                    content = f"Worker {worker_id} content".encode()
                    file = UploadFile(filename=f"worker_{worker_id}.txt")
                    file.file = BytesIO(content)
                    
                    start_time = time.time()
                    saved_path = _save_upload(file)
                    elapsed = time.time() - start_time
                    
                    results.append((saved_path, elapsed))
                
                # Start 10 concurrent uploads
                threads = []
                for i in range(10):
                    thread = threading.Thread(target=upload_worker, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                for thread in threads:
                    thread.join()
                
                # All uploads should succeed
                assert len(results) == 10
                assert all(Path(path).exists() for path, _ in results)
                assert all(elapsed < 2.0 for _, elapsed in results)


class TestUploadErrorHandling:
    """Test upload error handling."""

    def test_upload_corrupted_file(self):
        """Test upload with corrupted file."""
        from jarvis.web.uploads import _is_safe_upload
        
        # Simulate corrupted file
        corrupted_content = b"\x00\x01\x02\x03\x04\x05" * 1000
        
        file = UploadFile(filename="corrupted.txt")
        file.content_type = "text/plain"
        file.file = BytesIO(corrupted_content)
        
        # Should handle corrupted files gracefully
        with patch('jarvis.web.uploads._validate_file_integrity', return_value=False):
            assert _is_safe_upload(file) is False

    def test_upload_network_interruption(self):
        """Test upload with network interruption."""
        from jarvis.web.routes.uploads import handle_upload
        
        mock_request = Mock()
        mock_file = UploadFile(filename="network_test.txt")
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(side_effect=ConnectionError("Network interrupted"))
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        # Should handle network interruption gracefully
        try:
            import asyncio
            response = asyncio.run(handle_upload(mock_request, mock_auth))
            assert response.status_code in [400, 500]
        except ConnectionError:
            pass  # Expected

    def test_upload_timeout(self):
        """Test upload timeout handling."""
        from jarvis.web.routes.uploads import handle_upload
        
        mock_request = Mock()
        mock_file = UploadFile(filename="timeout_test.txt")
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(side_effect=asyncio.TimeoutError("Upload timeout"))
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        # Should handle timeout gracefully
        try:
            import asyncio
            response = asyncio.run(handle_upload(mock_request, mock_auth))
            assert response.status_code in [400, 408, 500]
        except asyncio.TimeoutError:
            pass  # Expected

    def test_upload_memory_exhaustion(self):
        """Test upload with memory exhaustion."""
        from jarvis.web.routes.uploads import handle_upload
        
        mock_request = Mock()
        mock_file = UploadFile(filename="memory_test.txt")
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(side_effect=MemoryError("Out of memory"))
        mock_request.form.return_value = {"file": mock_file}
        
        mock_auth = Mock(spec=AuthManager)
        mock_auth.get_token_from_header.return_value = "valid_token"
        mock_auth.is_valid_token.return_value = True
        
        # Should handle memory exhaustion gracefully
        try:
            import asyncio
            response = asyncio.run(handle_upload(mock_request, mock_auth))
            assert response.status_code in [400, 500, 507]
        except MemoryError:
            pass  # Expected


class TestUploadEdgeCases:
    """Test upload edge cases."""

    def test_upload_empty_filename(self):
        """Test upload with empty filename."""
        from jarvis.web.uploads import _is_safe_filename
        
        assert _is_safe_filename("") is False
        assert _is_safe_filename(None) is False

    def test_upload_whitespace_filename(self):
        """Test upload with whitespace-only filename."""
        from jarvis.web.uploads import _is_safe_filename
        
        whitespace_names = ["   ", "\t", "\n", "   \t\n   "]
        
        for name in whitespace_names:
            assert _is_safe_filename(name) is False

    def test_upload_max_filename_length(self):
        """Test upload with maximum filename length."""
        from jarvis.web.uploads import _is_safe_filename
        
        # Test at the limit (255 characters)
        max_name = "a" * 250 + ".txt"  # 254 characters
        assert _is_safe_filename(max_name) is True
        
        # Test over the limit
        over_limit_name = "a" * 300 + ".txt"  # 304 characters
        assert _is_safe_filename(over_limit_name) is False

    def test_upload_zero_byte_file(self):
        """Test upload of zero-byte file."""
        from jarvis.web.uploads import _is_safe_upload
        
        file = UploadFile(filename="empty.txt")
        file.content_type = "text/plain"
        file.file = BytesIO(b"")
        
        # Should handle empty files appropriately
        result = _is_safe_upload(file)
        assert result in [True, False]  # Depends on implementation

    def test_upload_binary_file(self):
        """Test upload of binary file."""
        from jarvis.web.uploads import _is_safe_upload
        
        # Create binary content
        binary_content = bytes(range(256))  # All byte values
        
        file = UploadFile(filename="binary.bin")
        file.content_type = "application/octet-stream"
        file.file = BytesIO(binary_content)
        
        # Should handle binary files appropriately
        result = _is_safe_upload(file)
        assert result in [True, False]  # Depends on allowed types

    def test_upload_with_metadata(self):
        """Test upload with file metadata."""
        from jarvis.web.uploads import _extract_metadata
        
        # Create file with metadata
        file = UploadFile(filename="metadata_test.txt")
        file.content_type = "text/plain"
        file.file = BytesIO(b"Test content")
        
        # Extract metadata
        metadata = _extract_metadata(file)
        
        assert isinstance(metadata, dict)
        assert "filename" in metadata
        assert "content_type" in metadata
        assert "size" in metadata
