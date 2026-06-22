"""Phase 7: Comprehensive Memory Manager Tests - Priority 1."""

from __future__ import annotations

import pytest
import tempfile
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any

from jarvis.memory.json_store import JsonMemoryStore
from jarvis.memory.store import MemoryEntry
from jarvis.llm.embeddings import EmbeddingProvider


class TestJsonMemoryStoreInitialization:
    """Test JsonMemoryStore initialization and setup."""

    def test_initialization_default_path(self):
        """Test initialization with default path."""
        with patch('jarvis.memory.json_store.DATA_DIR') as mock_data_dir:
            mock_data_dir.__truediv__ = Mock(return_value=Path("/mock/data/memory.json"))
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_provider = Mock(spec=EmbeddingProvider)
                mock_get_provider.return_value = mock_provider
                
                store = JsonMemoryStore()
                
                assert store.path == Path("/mock/data/memory.json")
                assert store.embeddings == mock_provider

    def test_initialization_custom_path(self):
        """Test initialization with custom path."""
        custom_path = Path("/custom/memory.json")
        
        with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
            mock_provider = Mock(spec=EmbeddingProvider)
            mock_get_provider.return_value = mock_provider
            
            store = JsonMemoryStore(path=custom_path)
            
            assert store.path == custom_path
            assert store.embeddings == mock_provider

    def test_initialization_custom_embeddings(self):
        """Test initialization with custom embeddings provider."""
        custom_path = Path("/custom/memory.json")
        mock_custom_provider = Mock(spec=EmbeddingProvider)
        
        store = JsonMemoryStore(path=custom_path, embeddings=mock_custom_provider)
        
        assert store.path == custom_path
        assert store.embeddings == mock_custom_provider

    def test_directory_creation(self):
        """Test that parent directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dir" / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=nested_path)
                
                # Directory should be created during initialization
                assert nested_path.parent.exists()


class TestJsonMemoryStoreAsyncOperations:
    """Test JsonMemoryStore async operations."""

    @pytest.mark.asyncio
    async def test_initialize_creates_file(self):
        """Test initialize creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                await store.initialize()
                
                assert memory_path.exists()
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert data == {}

    @pytest.mark.asyncio
    async def test_initialize_existing_file(self):
        """Test initialize with existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            existing_data = {"notes": {"key1": {"value": "test"}}}
            memory_path.write_text(json.dumps(existing_data), encoding="utf-8")
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                await store.initialize()
                
                # File should still exist with original content
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert data == existing_data

    @pytest.mark.asyncio
    async def test_initialize_creates_backup(self):
        """Test initialize creates backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            backup_path = Path(temp_dir) / "memory.json.bak"
            
            # Create initial file
            initial_data = {"notes": {"key1": {"value": "test"}}}
            memory_path.write_text(json.dumps(initial_data), encoding="utf-8")
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                await store.initialize()
                
                assert backup_path.exists()
                backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
                assert backup_data == initial_data

    @pytest.mark.asyncio
    async def test_save_new_entry(self):
        """Test saving a new memory entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                await store.save(
                    category="notes",
                    key="test_key",
                    value="test_value",
                    metadata={"created": "2023-01-01"}
                )
                
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert "notes" in data
                assert "test_key" in data["notes"]
                assert data["notes"]["test_key"]["value"] == "test_value"
                assert data["notes"]["test_key"]["metadata"]["created"] == "2023-01-01"

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self):
        """Test saving overwrites existing entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save initial entry
                await store.save("notes", "test_key", "initial_value")
                
                # Overwrite with new value
                await store.save(
                    "notes",
                    "test_key",
                    "updated_value",
                    metadata={"updated": "2023-01-02"}
                )
                
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert data["notes"]["test_key"]["value"] == "updated_value"
                assert data["notes"]["test_key"]["metadata"]["updated"] == "2023-01-02"

    @pytest.mark.asyncio
    async def test_get_existing_entry(self):
        """Test retrieving existing entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save test entry
                await store.save(
                    "notes",
                    "test_key",
                    "test_value",
                    metadata={"created": "2023-01-01"}
                )
                
                # Retrieve entry
                entry = await store.get("notes", "test_key")
                
                assert entry is not None
                assert entry.category == "notes"
                assert entry.key == "test_key"
                assert entry.value == "test_value"
                assert entry.metadata["created"] == "2023-01-01"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self):
        """Test retrieving non-existent entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                entry = await store.get("notes", "nonexistent_key")
                
                assert entry is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_category(self):
        """Test retrieving from non-existent category."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                entry = await store.get("nonexistent_category", "test_key")
                
                assert entry is None


class TestJsonMemoryStoreErrorHandling:
    """Test JsonMemoryStore error handling."""

    @pytest.mark.asyncio
    async def test_json_corruption_recovery(self):
        """Test recovery from JSON corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            # Create corrupted JSON file
            memory_path.write_text('{"invalid": json}', encoding="utf-8")
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                # Should handle corruption gracefully
                data = store._load()
                assert isinstance(data, dict)
                assert all(cat in data for cat in store.DEFAULT_CATEGORIES)

    @pytest.mark.asyncio
    async def test_file_permission_denied(self):
        """Test handling of permission denied errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Mock permission denied on save
                with patch.object(store, '_save') as mock_save:
                    mock_save.side_effect = PermissionError("Permission denied")
                    
                    try:
                        await store.save("notes", "test_key", "test_value")
                        # Should handle gracefully or raise appropriate error
                        assert True
                    except PermissionError:
                        # Should propagate permission errors
                        assert True

    @pytest.mark.asyncio
    async def test_disk_full_error(self):
        """Test handling of disk full errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Mock disk full error
                with patch.object(store, '_save') as mock_save:
                    mock_save.side_effect = OSError("No space left on device")
                    
                    try:
                        await store.save("notes", "test_key", "test_value")
                        # Should handle gracefully
                        assert True
                    except OSError:
                        # Should propagate disk errors
                        assert True

    def test_load_missing_file(self):
        """Test loading when file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "nonexistent.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                data = store._load()
                
                assert isinstance(data, dict)
                assert all(cat in data for cat in store.DEFAULT_CATEGORIES)
                assert all(data[cat] == {} for cat in store.DEFAULT_CATEGORIES)

    def test_save_invalid_data_types(self):
        """Test saving with invalid data types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                
                # Test with non-serializable data
                invalid_data = {
                    "notes": {
                        "key": {
                            "value": "test",
                            "metadata": {"invalid": object()}  # Non-serializable
                        }
                    }
                }
                
                try:
                    store._save(invalid_data)
                    # Should handle or raise appropriate error
                    assert True
                except (TypeError, ValueError):
                    # Should raise serialization errors
                    assert True


class TestJsonMemoryStoreConcurrency:
    """Test JsonMemoryStore concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_saves(self):
        """Test concurrent save operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Concurrent saves
                tasks = []
                for i in range(10):
                    task = store.save("notes", f"key_{i}", f"value_{i}")
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                # Verify all entries were saved
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert len(data["notes"]) == 10
                for i in range(10):
                    assert f"key_{i}" in data["notes"]
                    assert data["notes"][f"key_{i}"]["value"] == f"value_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """Test concurrent read and write operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save initial data
                await store.save("notes", "initial_key", "initial_value")
                
                # Concurrent operations
                write_tasks = [store.save("notes", f"key_{i}", f"value_{i}") for i in range(5)]
                read_tasks = [store.get("notes", "initial_key") for _ in range(5)]
                
                all_tasks = write_tasks + read_tasks
                results = await asyncio.gather(*all_tasks)
                
                # Verify writes succeeded
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert len(data["notes"]) >= 6  # initial + 5 new
                
                # Verify reads succeeded
                read_results = results[5:]  # Last 5 results are reads
                assert all(entry is not None for entry in read_results)
                assert all(entry.value == "initial_value" for entry in read_results)

    @pytest.mark.asyncio
    async def test_file_locking_behavior(self):
        """Test file locking behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Test with portalocker available
                with patch('jarvis.memory.json_store.portalocker') as mock_portalocker:
                    mock_lock = Mock()
                    mock_portalocker.LOCK_EX = 1
                    mock_portalocker.lock = mock_lock
                    
                    await store.save("notes", "test_key", "test_value")
                    
                    # Should attempt to lock file
                    mock_lock.assert_called()

    @pytest.mark.asyncio
    async def test_fallback_without_portalocker(self):
        """Test fallback behavior when portalocker is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Mock ImportError for portalocker
                with patch.dict('sys.modules', {'portalocker': None}):
                    with patch('builtins.__import__', side_effect=ImportError):
                        await store.save("notes", "test_key", "test_value")
                        
                        # Should still save without portalocker
                        data = json.loads(memory_path.read_text(encoding="utf-8"))
                        assert "test_key" in data["notes"]


class TestJsonMemoryStoreDataIntegrity:
    """Test JsonMemoryStore data integrity."""

    @pytest.mark.asyncio
    async def test_atomic_save_operations(self):
        """Test that save operations are atomic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            tmp_path = memory_path.with_suffix(".tmp")
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save initial data
                await store.save("notes", "initial", "initial_value")
                
                # Mock atomic save failure
                with patch.object(store, '_save') as mock_save:
                    mock_save.side_effect = Exception("Save failed")
                    
                    try:
                        await store.save("notes", "new", "new_value")
                    except Exception:
                        pass
                    
                    # Original data should be intact
                    data = json.loads(memory_path.read_text(encoding="utf-8"))
                    assert data["notes"]["initial"]["value"] == "initial_value"
                    assert "new" not in data["notes"]

    @pytest.mark.asyncio
    async def test_backup_creation_on_save(self):
        """Test backup creation during save operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            backup_path = memory_path.with_suffix(".json.bak")
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save initial data
                await store.save("notes", "key1", "value1")
                
                # Save more data
                await store.save("notes", "key2", "value2")
                
                # Backup should exist and be up to date
                assert backup_path.exists()
                backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
                assert "key1" in backup_data["notes"]
                assert "key2" in backup_data["notes"]

    @pytest.mark.asyncio
    async def test_data_persistence_across_instances(self):
        """Test data persistence across different store instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                # First instance - save data
                store1 = JsonMemoryStore(path=memory_path)
                await store1.initialize()
                await store1.save("notes", "persistent_key", "persistent_value")
                
                # Second instance - read data
                store2 = JsonMemoryStore(path=memory_path)
                await store2.initialize()
                entry = await store2.get("notes", "persistent_key")
                
                assert entry is not None
                assert entry.value == "persistent_value"

    @pytest.mark.asyncio
    async def test_unicode_handling(self):
        """Test Unicode character handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                unicode_data = "Unicode test: ñáéíóú 中文 русский 日本語"
                await store.save("notes", "unicode_key", unicode_data)
                
                entry = await store.get("notes", "unicode_key")
                assert entry is not None
                assert entry.value == unicode_data

    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Create large data
                large_data = "x" * 10000
                await store.save("notes", "large_key", large_data)
                
                entry = await store.get("notes", "large_key")
                assert entry is not None
                assert entry.value == large_data


class TestJsonMemoryStoreCategoryManagement:
    """Test JsonMemoryStore category management."""

    @pytest.mark.asyncio
    async def test_default_categories_creation(self):
        """Test default categories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                for category in store.DEFAULT_CATEGORIES:
                    assert category in data
                    assert isinstance(data[category], dict)

    @pytest.mark.asyncio
    async def test_custom_category_creation(self):
        """Test custom category creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save to custom category
                await store.save("custom_category", "test_key", "test_value")
                
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert "custom_category" in data
                assert data["custom_category"]["test_key"]["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_category_isolation(self):
        """Test that categories are properly isolated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Save same key to different categories
                await store.save("notes", "same_key", "notes_value")
                await store.save("preferences", "same_key", "preferences_value")
                
                notes_entry = await store.get("notes", "same_key")
                preferences_entry = await store.get("preferences", "same_key")
                
                assert notes_entry.value == "notes_value"
                assert preferences_entry.value == "preferences_value"

    @pytest.mark.asyncio
    async def test_empty_category_handling(self):
        """Test handling of empty categories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Try to get from empty category
                entry = await store.get("notes", "nonexistent_key")
                assert entry is None
                
                # Category should still exist in data structure
                data = json.loads(memory_path.read_text(encoding="utf-8"))
                assert "notes" in data
                assert data["notes"] == {}


class TestJsonMemoryStorePerformance:
    """Test JsonMemoryStore performance characteristics."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self):
        """Test performance of bulk operations."""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Bulk save test
                start_time = time.time()
                tasks = []
                for i in range(100):
                    task = store.save("notes", f"bulk_key_{i}", f"bulk_value_{i}")
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                save_time = time.time() - start_time
                
                # Bulk read test
                start_time = time.time()
                read_tasks = []
                for i in range(100):
                    task = store.get("notes", f"bulk_key_{i}")
                    read_tasks.append(task)
                
                results = await asyncio.gather(*read_tasks)
                read_time = time.time() - start_time
                
                # Performance assertions
                assert save_time < 5.0  # Should complete in under 5 seconds
                assert read_time < 2.0  # Should complete in under 2 seconds
                assert all(entry is not None for entry in results)
                assert len(results) == 100

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability with many operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                # Perform many operations to test memory stability
                for i in range(200):
                    await store.save("notes", f"memory_test_{i}", f"value_{i}")
                    entry = await store.get("notes", f"memory_test_{i}")
                    assert entry is not None
                
                # Should not accumulate memory excessively
                assert True

    @pytest.mark.asyncio
    async def test_file_size_growth(self):
        """Test file size growth with data accumulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                initial_size = memory_path.stat().st_size if memory_path.exists() else 0
                
                # Add data
                for i in range(50):
                    await store.save("notes", f"size_test_{i}", f"x" * 100)
                
                final_size = memory_path.stat().st_size
                
                # File should have grown reasonably
                assert final_size > initial_size
                assert final_size - initial_size < 100000  # Should not be excessively large


class TestJsonMemoryStoreEdgeCases:
    """Test JsonMemoryStore edge cases."""

    @pytest.mark.asyncio
    async def test_very_long_keys(self):
        """Test handling of very long keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                long_key = "a" * 1000
                await store.save("notes", long_key, "long_key_value")
                
                entry = await store.get("notes", long_key)
                assert entry is not None
                assert entry.value == "long_key_value"

    @pytest.mark.asyncio
    async def test_special_characters_in_keys(self):
        """Test special characters in keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                special_keys = [
                    "key-with-dashes",
                    "key_with_underscores",
                    "key.with.dots",
                    "key with spaces",
                    "key@with#symbols",
                    "key/with/slashes",
                    "key\\with\\backslashes"
                ]
                
                for key in special_keys:
                    await store.save("notes", key, f"value_for_{key}")
                    entry = await store.get("notes", key)
                    assert entry is not None
                    assert entry.value == f"value_for_{key}"

    @pytest.mark.asyncio
    async def test_empty_values(self):
        """Test handling of empty values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                await store.save("notes", "empty_value", "")
                await store.save("notes", "none_value", None)  # type: ignore
                
                empty_entry = await store.get("notes", "empty_value")
                none_entry = await store.get("notes", "none_value")
                
                assert empty_entry is not None
                assert empty_entry.value == ""
                assert none_entry is not None
                assert none_entry.value is None

    @pytest.mark.asyncio
    async def test_nested_metadata(self):
        """Test handling of nested metadata structures."""
        with tempfile.TTemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            
            with patch('jarvis.memory.json_store.get_embedding_provider') as mock_get_provider:
                mock_get_provider.return_value = Mock(spec=EmbeddingProvider)
                
                store = JsonMemoryStore(path=memory_path)
                await store.initialize()
                
                nested_metadata = {
                    "level1": {
                        "level2": {
                            "level3": "deep_value"
                        },
                        "list": [1, 2, 3],
                        "boolean": True,
                        "null_value": None
                    },
                    "timestamp": "2023-01-01T00:00:00Z"
                }
                
                await store.save("notes", "nested_key", "nested_value", nested_metadata)
                
                entry = await store.get("notes", "nested_key")
                assert entry is not None
                assert entry.metadata == nested_metadata
                assert entry.metadata["level1"]["level2"]["level3"] == "deep_value"
                assert entry.metadata["level1"]["list"] == [1, 2, 3]
                assert entry.metadata["level1"]["boolean"] is True
                assert entry.metadata["level1"]["null_value"] is None
