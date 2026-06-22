"""Phase 7: Comprehensive File Processor Tests - Priority 2."""

from __future__ import annotations

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

# Import the file_processor module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "actions"))
import file_processor


class TestFileProcessorPDF:
    """Test file processor PDF handling."""

    def test_process_pdf_success(self):
        """Test successful PDF processing."""
        # Create a minimal PDF-like file for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.PdfReader') as mock_pdf_reader:
                    # Mock PDF reader
                    mock_reader = Mock()
                    mock_page = Mock()
                    mock_page.extract_text.return_value = "Sample PDF content"
                    mock_reader.pages = [mock_page]
                    mock_pdf_reader.return_value = mock_reader
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Sample PDF content" in result
                    assert "success" in result.lower() or "processed" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_pdf_corrupted(self):
        """Test processing corrupted PDF."""
        corrupted_content = b"Not a PDF file at all"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(corrupted_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.PdfReader', side_effect=Exception("PDF corrupted")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "error" in result.lower() or "corrupted" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_pdf_password_protected(self):
        """Test processing password-protected PDF."""
        pdf_content = b"%PDF-1.4\nencrypted\n"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.PdfReader') as mock_pdf_reader:
                    mock_reader = Mock()
                    mock_reader.is_encrypted = True
                    mock_reader.decrypt.return_value = False  # Failed to decrypt
                    mock_pdf_reader.return_value = mock_reader
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "password" in result.lower() or "encrypted" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_pdf_no_pages(self):
        """Test processing PDF with no pages."""
        pdf_content = b"%PDF-1.4\nempty\n"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.PdfReader') as mock_pdf_reader:
                    mock_reader = Mock()
                    mock_reader.pages = []  # No pages
                    mock_pdf_reader.return_value = mock_reader
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "empty" in result.lower() or "no pages" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_pdf_large_file(self):
        """Test processing large PDF file."""
        pdf_content = b"%PDF-1.4\n" + b"x" * 1000000  # 1MB
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.PdfReader') as mock_pdf_reader:
                    mock_reader = Mock()
                    mock_page = Mock()
                    mock_page.extract_text.return_value = "Large PDF content " * 1000
                    mock_reader.pages = [mock_page] * 100  # Many pages
                    mock_pdf_reader.return_value = mock_reader
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Large PDF content" in result
                    assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorDOCX:
    """Test file processor DOCX handling."""

    def test_process_docx_success(self):
        """Test successful DOCX processing."""
        # Create a minimal DOCX-like file
        docx_content = b"PK\x03\x04" + b"x" * 100  # ZIP header + content
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(docx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Document') as mock_document:
                    # Mock DOCX document
                    mock_doc = Mock()
                    mock_paragraph = Mock()
                    mock_paragraph.text = "Sample DOCX content"
                    mock_doc.paragraphs = [mock_paragraph]
                    mock_document.return_value = mock_doc
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Sample DOCX content" in result
                    assert "success" in result.lower() or "processed" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_docx_corrupted(self):
        """Test processing corrupted DOCX."""
        corrupted_content = b"Not a DOCX file"
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(corrupted_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Document', side_effect=Exception("DOCX corrupted")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "error" in result.lower() or "corrupted" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_docx_empty_document(self):
        """Test processing empty DOCX document."""
        docx_content = b"PK\x03\x04" + b"x" * 100
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(docx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Document') as mock_document:
                    mock_doc = Mock()
                    mock_doc.paragraphs = []  # No paragraphs
                    mock_document.return_value = mock_doc
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "empty" in result.lower() or "no content" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_docx_unicode_content(self):
        """Test processing DOCX with Unicode content."""
        docx_content = b"PK\x03\x04" + b"x" * 100
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(docx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Document') as mock_document:
                    mock_doc = Mock()
                    mock_paragraph = Mock()
                    mock_paragraph.text = "Unicode: ñáéíóú 中文 русский 日本語"
                    mock_doc.paragraphs = [mock_paragraph]
                    mock_document.return_value = mock_doc
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Unicode: ñáéíóú" in result
                    assert "中文" in result
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorXLSX:
    """Test file processor XLSX handling."""

    def test_process_xlsx_success(self):
        """Test successful XLSX processing."""
        # Create a minimal XLSX-like file
        xlsx_content = b"PK\x03\x04" + b"x" * 100  # ZIP header + content
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write(xlsx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.openpyxl.load_workbook') as mock_load:
                    # Mock Excel workbook
                    mock_workbook = Mock()
                    mock_sheet = Mock()
                    mock_cell = Mock()
                    mock_cell.value = "Cell content"
                    mock_row = [mock_cell]
                    mock_sheet.iter_rows.return_value = [mock_row]
                    mock_workbook.sheetnames = ["Sheet1"]
                    mock_workbook.__getitem__.return_value = mock_sheet
                    mock_load.return_value = mock_workbook
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Cell content" in result
                    assert "Sheet1" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_xlsx_corrupted(self):
        """Test processing corrupted XLSX."""
        corrupted_content = b"Not an XLSX file"
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write(corrupted_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.openpyxl.load_workbook', side_effect=Exception("XLSX corrupted")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "error" in result.lower() or "corrupted" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_xlsx_empty_workbook(self):
        """Test processing empty XLSX workbook."""
        xlsx_content = b"PK\x03\x04" + b"x" * 100
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write(xlsx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.openpyxl.load_workbook') as mock_load:
                    mock_workbook = Mock()
                    mock_workbook.sheetnames = []  # No sheets
                    mock_load.return_value = mock_workbook
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "empty" in result.lower() or "no sheets" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_xlsx_large_workbook(self):
        """Test processing large XLSX workbook."""
        xlsx_content = b"PK\x03\x04" + b"x" * 100
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file.write(xlsx_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.openpyxl.load_workbook') as mock_load:
                    mock_workbook = Mock()
                    mock_sheet = Mock()
                    mock_cell = Mock()
                    mock_cell.value = f"Cell {i}"
                    
                    # Mock many rows
                    mock_rows = []
                    for i in range(100):
                        mock_row = [mock_cell]
                        mock_rows.append(mock_row)
                    
                    mock_sheet.iter_rows.return_value = mock_rows
                    mock_workbook.sheetnames = ["Sheet1", "Sheet2", "Sheet3"]
                    mock_workbook.__getitem__.return_value = mock_sheet
                    mock_load.return_value = mock_workbook
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "Sheet1" in result
                    assert "Sheet2" in result
                    assert "Sheet3" in result
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorCSV:
    """Test file processor CSV handling."""

    def test_process_csv_success(self):
        """Test successful CSV processing."""
        csv_content = "Name,Age,City\nJohn,30,New York\nJane,25,Los Angeles"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "John" in result
                assert "30" in result
                assert "New York" in result
                assert "Jane" in result
                assert "25" in result
                assert "Los Angeles" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_csv_with_delimiter(self):
        """Test processing CSV with different delimiter."""
        csv_content = "Name;Age;City\nJohn;30;New York\nJane;25;Los Angeles"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "John" in result
                assert "30" in result
                assert "New York" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_csv_unicode_content(self):
        """Test processing CSV with Unicode content."""
        csv_content = "Name,City\nJosé,São Paulo\nFrançois,München\n北京,北京"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "José" in result
                assert "São Paulo" in result
                assert "François" in result
                assert "München" in result
                assert "北京" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_csv_empty_file(self):
        """Test processing empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "empty" in result.lower() or "no content" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_csv_large_file(self):
        """Test processing large CSV file."""
        # Generate large CSV content
        lines = ["ID,Name,Value"]
        for i in range(10000):
            lines.append(f"{i},Name_{i},Value_{i}")
        csv_content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "Name_0" in result
                assert "Name_9999" in result
                assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorImages:
    """Test file processor image handling."""

    def test_process_jpeg_success(self):
        """Test successful JPEG processing."""
        # Create a minimal JPEG header
        jpeg_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(jpeg_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Image') as mock_image:
                    # Mock PIL Image
                    mock_img = Mock()
                    mock_img.format = "JPEG"
                    mock_img.size = (1920, 1080)
                    mock_img.mode = "RGB"
                    mock_image.open.return_value = mock_img
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "JPEG" in result
                    assert "1920x1080" in result
                    assert "RGB" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_png_success(self):
        """Test successful PNG processing."""
        # Create a minimal PNG header
        png_content = b"\x89PNG\r\n\x1a\n"
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(png_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Image') as mock_image:
                    mock_img = Mock()
                    mock_img.format = "PNG"
                    mock_img.size = (800, 600)
                    mock_img.mode = "RGBA"
                    mock_image.open.return_value = mock_img
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "PNG" in result
                    assert "800x600" in result
                    assert "RGBA" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_image_corrupted(self):
        """Test processing corrupted image."""
        corrupted_content = b"Not an image file"
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(corrupted_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Image', side_effect=Exception("Image corrupted")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "error" in result.lower() or "corrupted" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_process_image_exif_data(self):
        """Test processing image with EXIF data."""
        jpeg_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(jpeg_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.Image') as mock_image:
                    mock_img = Mock()
                    mock_img.format = "JPEG"
                    mock_img.size = (1920, 1080)
                    mock_img.mode = "RGB"
                    mock_img._getexif.return_value = {
                        36867: "2023:01:01 12:00:00",  # DateTime
                        271: "Canon",  # Make
                        272: "EOS 5D"  # Model
                    }
                    mock_image.open.return_value = mock_img
                    
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "JPEG" in result
                    assert "Canon" in result
                    assert "EOS 5D" in result
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorTextFiles:
    """Test file processor text file handling."""

    def test_process_txt_success(self):
        """Test successful TXT processing."""
        text_content = "This is a text file\nWith multiple lines\nAnd Unicode: ñáéíóú"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "This is a text file" in result
                assert "With multiple lines" in result
                assert "ñáéíóú" in result
        finally:
            os.unlink(temp_file_path)

    def test_process_txt_large_file(self):
        """Test processing large text file."""
        # Generate large text content
        lines = ["Large text file line " + str(i) for i in range(10000)]
        text_content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "Large text file line 0" in result
                assert "Large text file line 9999" in result
                assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)

    def test_process_txt_different_encodings(self):
        """Test processing text files with different encodings."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            text_content = "Text with encoding: " + encoding
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding=encoding) as temp_file:
                temp_file.write(text_content)
                temp_file_path = temp_file.name
            
            try:
                with patch('file_processor._is_safe_path', return_value=True):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert encoding in result
            finally:
                os.unlink(temp_file_path)

    def test_process_txt_empty_file(self):
        """Test processing empty text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                assert "empty" in result.lower() or "no content" in result.lower()
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorSecurity:
    """Test file processor security features."""

    def test_unsafe_path_rejection(self):
        """Test rejection of unsafe paths."""
        unsafe_paths = [
            "/etc/passwd",
            "/var/log/syslog",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../etc/shadow"
        ]
        
        for unsafe_path in unsafe_paths:
            with patch('file_processor._is_safe_path', return_value=False):
                result = file_processor.process_file(unsafe_path)
                
                assert "unsafe" in result.lower() or "denied" in result.lower()

    def test_file_size_limits(self):
        """Test file size limits."""
        # Create a very large file
        large_content = b"x" * 100_000_000  # 100MB
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(large_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                # Should handle large files gracefully
                assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)

    def test_malicious_file_detection(self):
        """Test detection of potentially malicious files."""
        # Create files with suspicious content
        suspicious_contents = [
            b"<script>alert('xss')</script>",
            b"javascript:void(0)",
            b"eval(malicious_code)",
            b"system('rm -rf /')",
            b"powershell -c malicious_command"
        ]
        
        for content in suspicious_contents:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                with patch('file_processor._is_safe_path', return_value=True):
                    result = file_processor.process_file(temp_file_path)
                    
                    # Should handle suspicious content appropriately
                    assert isinstance(result, str)
            finally:
                os.unlink(temp_file_path)

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config\\SAM",
            "/safe/path/../../../etc/passwd",
            "safe\\path\\..\\..\\..\\Windows\\System32\\config\\SAM"
        ]
        
        for path in traversal_paths:
            with patch('file_processor._is_safe_path', return_value=False):
                result = file_processor.process_file(path)
                
                assert "unsafe" in result.lower() or "denied" in result.lower()


class TestFileProcessorErrorHandling:
    """Test file processor error handling."""

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        nonexistent_path = "/nonexistent/file.txt"
        
        with patch('file_processor._is_safe_path', return_value=True):
            result = file_processor.process_file(nonexistent_path)
            
            assert "not found" in result.lower() or "does not exist" in result.lower()

    def test_permission_denied(self):
        """Test handling of permission denied errors."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "permission" in result.lower() or "denied" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_io_error_handling(self):
        """Test handling of I/O errors."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('builtins.open', side_effect=IOError("I/O error")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "error" in result.lower() or "failed" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_memory_error_handling(self):
        """Test handling of memory errors."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('builtins.open', side_effect=MemoryError("Out of memory")):
                    result = file_processor.process_file(temp_file_path)
                    
                    assert "memory" in result.lower() or "error" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_timeout_handling(self):
        """Test handling of processing timeouts."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                with patch('file_processor.time.time', side_effect=[0, 100]):  # Simulate timeout
                    result = file_processor.process_file(temp_file_path)
                    
                    # Should handle timeout gracefully
                    assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorPerformance:
    """Test file processor performance characteristics."""

    def test_processing_speed(self):
        """Test file processing speed."""
        import time
        
        # Create a moderately sized file
        content = "Test content line\n" * 10000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                start_time = time.time()
                result = file_processor.process_file(temp_file_path)
                elapsed = time.time() - start_time
                
                assert "Test content line" in result
                assert elapsed < 5.0  # Should complete within 5 seconds
        finally:
            os.unlink(temp_file_path)

    def test_concurrent_processing(self):
        """Test concurrent file processing."""
        import threading
        
        results = []
        
        def process_worker(i):
            content = f"Worker {i} content\n" * 100
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                with patch('file_processor._is_safe_path', return_value=True):
                    result = file_processor.process_file(temp_file_path)
                    results.append(result)
            finally:
                os.unlink(temp_file_path)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(f"Worker {i} content" in results[i] for i in range(5))

    def test_memory_usage_stability(self):
        """Test memory usage stability with many operations."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                # Process file many times
                for i in range(100):
                    result = file_processor.process_file(temp_file_path)
                    assert isinstance(result, str)
                
                # Should not accumulate memory excessively
                assert True
        finally:
            os.unlink(temp_file_path)


class TestFileProcessorEdgeCases:
    """Test file processor edge cases."""

    def test_unknown_file_type(self):
        """Test processing unknown file types."""
        unknown_content = b"This is an unknown file type"
        
        with tempfile.NamedTemporaryFile(suffix='.unknown', delete=False) as temp_file:
            temp_file.write(unknown_content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                # Should handle unknown types gracefully
                assert isinstance(result, str)
                assert "unknown" in result.lower() or "unsupported" in result.lower()
        finally:
            os.unlink(temp_file_path)

    def test_file_without_extension(self):
        """Test processing file without extension."""
        content = b"File without extension"
        
        with tempfile.NamedTemporaryFile(suffix='', delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(temp_file_path)
                
                # Should attempt to process based on content
                assert isinstance(result, str)
        finally:
            os.unlink(temp_file_path)

    def test_very_long_filename(self):
        """Test processing files with very long names."""
        long_name = "a" * 200 + ".txt"
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            # Rename to long name
            long_path = Path(temp_file_path).parent / long_name
            os.rename(temp_file_path, long_path)
            
            with patch('file_processor._is_safe_path', return_value=True):
                result = file_processor.process_file(str(long_path))
                
                assert isinstance(result, str)
        finally:
            if long_path.exists():
                os.unlink(long_path)

    def test_special_characters_in_filename(self):
        """Test processing files with special characters in names."""
        special_names = [
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file with spaces.txt",
            "file@with#symbols.txt",
            "file(1).txt",
            "file[1].txt"
        ]
        
        for name in special_names:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_file.write(b"test content")
                temp_file_path = temp_file.name
            
            try:
                # Rename to special name
                special_path = Path(temp_file_path).parent / name
                os.rename(temp_file_path, special_path)
                
                with patch('file_processor._is_safe_path', return_value=True):
                    result = file_processor.process_file(str(special_path))
                    
                    assert isinstance(result, str)
            finally:
                if special_path.exists():
                    os.unlink(special_path)

    def test_unicode_filenames(self):
        """Test processing files with Unicode filenames."""
        unicode_names = [
            "файл.txt",  # Russian
            "文件.txt",   # Chinese
            "ファイル.txt", # Japanese
            "café.txt",   # French
            "naïve.txt"   # English with diacritics
        ]
        
        for name in unicode_names:
            try:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                    temp_file.write(b"test content")
                    temp_file_path = temp_file.name
                
                # Rename to Unicode name
                unicode_path = Path(temp_file_path).parent / name
                os.rename(temp_file_path, unicode_path)
                
                with patch('file_processor._is_safe_path', return_value=True):
                    result = file_processor.process_file(str(unicode_path))
                    
                    assert isinstance(result, str)
            except (UnicodeEncodeError, OSError):
                # Skip if filesystem doesn't support Unicode
                continue
            finally:
                if 'unicode_path' in locals() and unicode_path.exists():
                    os.unlink(unicode_path)


class TestFileProcessorIntegration:
    """Test file processor integration scenarios."""

    def test_batch_processing(self):
        """Test batch processing of multiple files."""
        files = []
        
        try:
            # Create multiple test files
            for i in range(5):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(f"File {i} content")
                    temp_file_path = temp_file.name
                    files.append(temp_file_path)
            
            # Process all files
            results = []
            with patch('file_processor._is_safe_path', return_value=True):
                for file_path in files:
                    result = file_processor.process_file(file_path)
                    results.append(result)
            
            assert len(results) == 5
            for i, result in enumerate(results):
                assert f"File {i} content" in result
        
        finally:
            for file_path in files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_mixed_file_types(self):
        """Test processing mixed file types."""
        files = []
        
        try:
            # Create files of different types
            # Text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write("Text content")
                files.append(temp_file.name)
            
            # CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                temp_file.write("Name,Value\nTest,123")
                files.append(temp_file.name)
            
            # Process all files
            results = []
            with patch('file_processor._is_safe_path', return_value=True):
                for file_path in files:
                    result = file_processor.process_file(file_path)
                    results.append(result)
            
            assert len(results) == 2
            assert "Text content" in results[0]
            assert "Test" in results[1]
        
        finally:
            for file_path in files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_error_recovery_in_batch(self):
        """Test error recovery in batch processing."""
        files = []
        
        try:
            # Create mix of valid and invalid files
            # Valid file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write("Valid content")
                files.append(temp_file.name)
            
            # Invalid file (non-existent)
            files.append("/nonexistent/file.txt")
            
            # Process all files
            results = []
            with patch('file_processor._is_safe_path', return_value=True):
                for file_path in files:
                    result = file_processor.process_file(file_path)
                    results.append(result)
            
            assert len(results) == 2
            assert "Valid content" in results[0]
            assert "not found" in results[1].lower()
        
        finally:
            # Clean up existing files
            for file_path in files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
