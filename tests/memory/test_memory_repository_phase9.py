"""Phase 9A: Comprehensive Memory Repository Tests - Priority 2."""

from __future__ import annotations

import pytest
import asyncio
import json
import uuid
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List
from datetime import datetime, timezone

from jarvis.memory.store import MemoryEntry, MemoryStore
from jarvis.memory.store import MemoryStore
from jarvis.config.settings import Settings

# Alias for compatibility
RepositoryError = Exception
MemoryRepository = MemoryStore


class TestMemoryRepositoryInitialization:
    """Test MemoryRepository initialization and setup."""

    def test_repository_init_with_store(self):
        """Test repository initialization with custom store."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        assert repo.store == mock_store

    def test_repository_init_with_default_store(self):
        """Test repository initialization with default store."""
        with patch('jarvis.memory.repository.get_memory_store') as mock_get_store:
            mock_store = Mock(spec=MemoryStore)
            mock_get_store.return_value = mock_store
            
            repo = MemoryRepository()
            
            assert repo.store == mock_store
            mock_get_store.assert_called_once()

    def test_repository_init_with_settings(self):
        """Test repository initialization with settings."""
        mock_store = Mock(spec=MemoryStore)
        mock_settings = Mock(spec=Settings)
        
        repo = MemoryRepository(store=mock_store, settings=mock_settings)
        
        assert repo.store == mock_store
        assert repo.settings == mock_settings


class TestMemoryRepositoryCreate:
    """Test MemoryRepository create operations."""

    @pytest.mark.asyncio
    async def test_create_memory_success(self):
        """Test successful memory creation."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.create(
            category="test_category",
            key="test_key",
            value="test_value",
            metadata={"meta": "data"}
        )
        
        assert entry.category == "test_category"
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.metadata == {"meta": "data"}
        assert entry.id is not None
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
        
        mock_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_memory_without_metadata(self):
        """Test memory creation without metadata."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.create(
            category="test_category",
            key="test_key",
            value="test_value"
        )
        
        assert entry.metadata == {}

    @pytest.mark.asyncio
    async def test_create_memory_with_unicode(self):
        """Test memory creation with Unicode content."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        unicode_value = "Unicode test: ñáéíóú 中文 русский 日本語"
        unicode_meta = {"unicode": "ñáéíóú", "chinese": "中文"}
        
        entry = await repo.create(
            category="unicode_category",
            key="unicode_key",
            value=unicode_value,
            metadata=unicode_meta
        )
        
        assert entry.value == unicode_value
        assert entry.metadata == unicode_meta

    @pytest.mark.asyncio
    async def test_create_memory_empty_values(self):
        """Test memory creation with empty values."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.create(
            category="",
            key="",
            value=""
        )
        
        assert entry.category == ""
        assert entry.key == ""
        assert entry.value == ""

    @pytest.mark.asyncio
    async def test_create_memory_store_error(self):
        """Test memory creation with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_create_memory_duplicate_key(self):
        """Test memory creation with duplicate key."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=Exception("Duplicate key"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_create_memory_very_long_content(self):
        """Test memory creation with very long content."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        long_content = "x" * 100000  # 100KB
        long_meta = {"large": "x" * 10000}
        
        entry = await repo.create(
            category="large_category",
            key="large_key",
            value=long_content,
            metadata=long_meta
        )
        
        assert entry.value == long_content
        assert entry.metadata == long_meta

    @pytest.mark.asyncio
    async def test_create_memory_special_characters(self):
        """Test memory creation with special characters."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        special_content = "Special chars: !@#$%^&*()[]{}|\\:;\"'<>?,./\n\t\r"
        special_meta = {"special": "!@#$%^&*()[]{}|\\:;\"'<>?,./"}
        
        entry = await repo.create(
            category="special_category",
            key="special_key",
            value=special_content,
            metadata=special_meta
        )
        
        assert entry.value == special_content
        assert entry.metadata == special_meta


class TestMemoryRepositoryRead:
    """Test MemoryRepository read operations."""

    @pytest.mark.asyncio
    async def test_read_memory_success(self):
        """Test successful memory reading."""
        mock_store = Mock(spec=MemoryStore)
        mock_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="test_category",
            key="test_key",
            value="test_value",
            metadata={"meta": "data"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_store.get = AsyncMock(return_value=mock_entry)
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.read("test_category", "test_key")
        
        assert entry is not None
        assert entry.category == "test_category"
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.metadata == {"meta": "data"}

    @pytest.mark.asyncio
    async def test_read_memory_not_found(self):
        """Test reading non-existent memory."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.get = AsyncMock(return_value=None)
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.read("test_category", "nonexistent_key")
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_read_memory_store_error(self):
        """Test memory reading with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.get = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.read("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_read_memory_invalid_category(self):
        """Test reading with invalid category."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.get = AsyncMock(return_value=None)
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.read("", "test_key")
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_read_memory_invalid_key(self):
        """Test reading with invalid key."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.get = AsyncMock(return_value=None)
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.read("test_category", "")
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_read_memory_unicode_params(self):
        """Test reading with Unicode parameters."""
        mock_store = Mock(spec=MemoryStore)
        mock_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="unicode_category",
            key="unicode_key",
            value="Unicode value: ñáéíóú",
            metadata={"unicode": "中文"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_store.get = AsyncMock(return_value=mock_entry)
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.read("unicode_category", "unicode_key")
        
        assert entry is not None
        assert "ñáéíóú" in entry.value
        assert entry.metadata["unicode"] == "中文"


class TestMemoryRepositoryUpdate:
    """Test MemoryRepository update operations."""

    @pytest.mark.asyncio
    async def test_update_memory_success(self):
        """Test successful memory update."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        entry = await repo.update(
            category="test_category",
            key="test_key",
            value="updated_value",
            metadata={"updated": "meta"}
        )
        
        assert entry.category == "test_category"
        assert entry.key == "test_key"
        assert entry.value == "updated_value"
        assert entry.metadata == {"updated": "meta"}
        assert entry.id is not None
        assert isinstance(entry.updated_at, datetime)
        
        mock_store.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memory_partial(self):
        """Test partial memory update."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Update only value
        entry = await repo.update(
            category="test_category",
            key="test_key",
            value="updated_value"
        )
        
        assert entry.value == "updated_value"
        assert entry.metadata == {}

    @pytest.mark.asyncio
    async def test_update_memory_unicode(self):
        """Test memory update with Unicode content."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        unicode_value = "Updated Unicode: ñáéíóú 中文 русский"
        unicode_meta = {"updated_unicode": "ñáéíóú"}
        
        entry = await repo.update(
            category="unicode_category",
            key="unicode_key",
            value=unicode_value,
            metadata=unicode_meta
        )
        
        assert entry.value == unicode_value
        assert entry.metadata == unicode_meta

    @pytest.mark.asyncio
    async def test_update_memory_store_error(self):
        """Test memory update with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.update("test_category", "test_key", "updated_value")

    @pytest.mark.asyncio
    async def test_update_memory_nonexistent(self):
        """Test updating non-existent memory."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Should create new entry if it doesn't exist
        entry = await repo.update(
            category="nonexistent_category",
            key="nonexistent_key",
            value="new_value"
        )
        
        assert entry is not None
        assert entry.value == "new_value"

    @pytest.mark.asyncio
    async def test_update_memory_large_content(self):
        """Test memory update with large content."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        large_content = "x" * 50000  # 50KB
        
        entry = await repo.update(
            category="large_category",
            key="large_key",
            value=large_content
        )
        
        assert entry.value == large_content


class TestMemoryRepositoryDelete:
    """Test MemoryRepository delete operations."""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self):
        """Test successful memory deletion."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=True)
        
        repo = MemoryRepository(store=mock_store)
        
        result = await repo.delete("test_category", "test_key")
        
        assert result is True
        mock_store.delete.assert_called_once_with("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self):
        """Test deleting non-existent memory."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=False)
        
        repo = MemoryRepository(store=mock_store)
        
        result = await repo.delete("test_category", "nonexistent_key")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_memory_store_error(self):
        """Test memory deletion with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.delete("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_delete_memory_invalid_params(self):
        """Test deletion with invalid parameters."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=False)
        
        repo = MemoryRepository(store=mock_store)
        
        # Empty category
        result = await repo.delete("", "test_key")
        assert result is False
        
        # Empty key
        result = await repo.delete("test_category", "")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_memory_unicode_params(self):
        """Test deletion with Unicode parameters."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=True)
        
        repo = MemoryRepository(store=mock_store)
        
        result = await repo.delete("unicode_category", "unicode_key")
        
        assert result is True
        mock_store.delete.assert_called_once_with("unicode_category", "unicode_key")


class TestMemoryRepositoryList:
    """Test MemoryRepository list operations."""

    @pytest.mark.asyncio
    async def test_list_by_category_success(self):
        """Test successful listing by category."""
        mock_store = Mock(spec=MemoryStore)
        mock_entries = []
        for i in range(3):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key=f"key_{i}",
                value=f"value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_entries.append(entry)
        mock_store.list = AsyncMock(return_value=mock_entries)
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.list_by_category("test_category")
        
        assert len(entries) == 3
        assert all(entry.category == "test_category" for entry in entries)
        assert entries[0].key == "key_0"
        assert entries[1].key == "key_1"
        assert entries[2].key == "key_2"

    @pytest.mark.asyncio
    async def test_list_by_category_empty(self):
        """Test listing empty category."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.list = AsyncMock(return_value=[])
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.list_by_category("empty_category")
        
        assert entries == []

    @pytest.mark.asyncio
    async def test_list_by_category_with_limit(self):
        """Test listing with limit."""
        mock_store = Mock(spec=MemoryStore)
        mock_entries = []
        for i in range(2):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key=f"key_{i}",
                value=f"value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_entries.append(entry)
        mock_store.list = AsyncMock(return_value=mock_entries)
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.list_by_category("test_category", limit=2)
        
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_list_by_category_store_error(self):
        """Test listing with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.list = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.list_by_category("test_category")

    @pytest.mark.asyncio
    async def test_list_by_category_unicode(self):
        """Test listing with Unicode category."""
        mock_store = Mock(spec=MemoryStore)
        mock_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="unicode_category",
            key="unicode_key",
            value="Unicode value: ñáéíóú",
            metadata={"unicode": "中文"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_store.list = AsyncMock(return_value=[mock_entry])
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.list_by_category("unicode_category")
        
        assert len(entries) == 1
        assert "ñáéíóú" in entries[0].value


class TestMemoryRepositorySearch:
    """Test MemoryRepository search operations."""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        mock_store = Mock(spec=MemoryStore)
        mock_entries = []
        for i in range(3):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key=f"key_{i}",
                value=f"searchable_value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_entries.append(entry)
        mock_store.search = AsyncMock(return_value=mock_entries)
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.search("search_query", "test_category")
        
        assert len(entries) == 3
        assert all("searchable_value" in entry.value for entry in entries)

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.search = AsyncMock(return_value=[])
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.search("no_results_query", "test_category")
        
        assert entries == []

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """Test search with limit."""
        mock_store = Mock(spec=MemoryStore)
        mock_entries = []
        for i in range(2):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key=f"key_{i}",
                value=f"value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_entries.append(entry)
        mock_store.search = AsyncMock(return_value=mock_entries)
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.search("search_query", "test_category", limit=2)
        
        assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_search_store_error(self):
        """Test search with store error."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.search = AsyncMock(side_effect=Exception("Store error"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.search("search_query", "test_category")

    @pytest.mark.asyncio
    async def test_search_unicode_query(self):
        """Test search with Unicode query."""
        mock_store = Mock(spec=MemoryStore)
        mock_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="unicode_category",
            key="unicode_key",
            value="Unicode content: ñáéíóú 中文 русский",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_store.search = AsyncMock(return_value=[mock_entry])
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.search("Unicode search: ñáéíóú", "unicode_category")
        
        assert len(entries) == 1
        assert "ñáéíóú" in entries[0].value

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.search = AsyncMock(return_value=[])
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.search("", "test_category")
        
        assert entries == []


class TestMemoryRepositoryBatchOperations:
    """Test MemoryRepository batch operations."""

    @pytest.mark.asyncio
    async def test_batch_create_success(self):
        """Test successful batch creation."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        memories = [
            {
                "category": "test_category",
                "key": f"key_{i}",
                "value": f"value_{i}",
                "metadata": {"batch": i}
            }
            for i in range(3)
        ]
        
        entries = await repo.batch_create(memories)
        
        assert len(entries) == 3
        assert all(entry.category == "test_category" for entry in entries)
        assert entries[0].key == "key_0"
        assert entries[1].key == "key_1"
        assert entries[2].key == "key_2"
        
        assert mock_store.save.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_create_partial_failure(self):
        """Test batch creation with partial failure."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=[None, Exception("Save failed"), None])
        
        repo = MemoryRepository(store=mock_store)
        
        memories = [
            {"category": "test_category", "key": "key_0", "value": "value_0"},
            {"category": "test_category", "key": "key_1", "value": "value_1"},
            {"category": "test_category", "key": "key_2", "value": "value_2"}
        ]
        
        with pytest.raises(RepositoryError):
            await repo.batch_create(memories)

    @pytest.mark.asyncio
    async def test_batch_create_empty_list(self):
        """Test batch creation with empty list."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        entries = await repo.batch_create([])
        
        assert entries == []
        mock_store.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_create_invalid_data(self):
        """Test batch creation with invalid data."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Missing required fields
        invalid_memories = [
            {"category": "test_category"},  # Missing key and value
            {"key": "key_1"},  # Missing category and value
            {"value": "value_2"}  # Missing category and key
        ]
        
        with pytest.raises(RepositoryError):
            await repo.batch_create(invalid_memories)

    @pytest.mark.asyncio
    async def test_batch_delete_success(self):
        """Test successful batch deletion."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=True)
        
        repo = MemoryRepository(store=mock_store)
        
        keys = [
            {"category": "test_category", "key": "key_0"},
            {"category": "test_category", "key": "key_1"},
            {"category": "test_category", "key": "key_2"}
        ]
        
        results = await repo.batch_delete(keys)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_store.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_partial_failure(self):
        """Test batch deletion with partial failure."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(side_effect=[True, Exception("Delete failed"), True])
        
        repo = MemoryRepository(store=mock_store)
        
        keys = [
            {"category": "test_category", "key": "key_0"},
            {"category": "test_category", "key": "key_1"},
            {"category": "test_category", "key": "key_2"}
        ]
        
        with pytest.raises(RepositoryError):
            await repo.batch_delete(keys)

    @pytest.mark.asyncio
    async def test_batch_update_success(self):
        """Test successful batch update."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        updates = [
            {"category": "test_category", "key": "key_0", "value": "updated_value_0"},
            {"category": "test_category", "key": "key_1", "value": "updated_value_1"},
            {"category": "test_category", "key": "key_2", "value": "updated_value_2"}
        ]
        
        entries = await repo.batch_update(updates)
        
        assert len(entries) == 3
        assert all(entry.category == "test_category" for entry in entries)
        assert entries[0].value == "updated_value_0"
        assert entries[1].value == "updated_value_1"
        assert entries[2].value == "updated_value_2"
        
        assert mock_store.save.call_count == 3


class TestMemoryRepositoryValidation:
    """Test MemoryRepository validation operations."""

    @pytest.mark.asyncio
    async def test_validate_memory_data_success(self):
        """Test successful memory data validation."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        valid_data = {
            "category": "test_category",
            "key": "test_key",
            "value": "test_value",
            "metadata": {"valid": "data"}
        }
        
        # Should not raise any exceptions
        result = await repo._validate_memory_data(valid_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_memory_data_missing_category(self):
        """Test validation with missing category."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        invalid_data = {
            "key": "test_key",
            "value": "test_value"
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)

    @pytest.mark.asyncio
    async def test_validate_memory_data_missing_key(self):
        """Test validation with missing key."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        invalid_data = {
            "category": "test_category",
            "value": "test_value"
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)

    @pytest.mark.asyncio
    async def test_validate_memory_data_missing_value(self):
        """Test validation with missing value."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        invalid_data = {
            "category": "test_category",
            "key": "test_key"
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)

    @pytest.mark.asyncio
    async def test_validate_memory_data_invalid_types(self):
        """Test validation with invalid types."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        # Invalid category type
        invalid_data = {
            "category": 123,  # Should be string
            "key": "test_key",
            "value": "test_value"
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)

    @pytest.mark.asyncio
    async def test_validate_memory_data_invalid_metadata(self):
        """Test validation with invalid metadata."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        invalid_data = {
            "category": "test_category",
            "key": "test_key",
            "value": "test_value",
            "metadata": "not_a_dict"  # Should be dict
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)

    @pytest.mark.asyncio
    async def test_validate_memory_data_too_long(self):
        """Test validation with data that's too long."""
        mock_store = Mock(spec=MemoryStore)
        
        repo = MemoryRepository(store=mock_store)
        
        invalid_data = {
            "category": "x" * 1000,  # Too long
            "key": "test_key",
            "value": "test_value"
        }
        
        with pytest.raises(RepositoryError):
            await repo._validate_memory_data(invalid_data)


class TestMemoryRepositoryConcurrency:
    """Test MemoryRepository concurrency handling."""

    @pytest.mark.asyncio
    async def test_concurrent_create_operations(self):
        """Test concurrent create operations."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        async def create_worker(worker_id):
            return await repo.create(
                category=f"category_{worker_id}",
                key=f"key_{worker_id}",
                value=f"value_{worker_id}"
            )
        
        # Run concurrent operations
        tasks = [create_worker(i) for i in range(5)]
        entries = await asyncio.gather(*tasks)
        
        assert len(entries) == 5
        assert all(entry is not None for entry in entries)
        assert mock_store.save.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_read_operations(self):
        """Test concurrent read operations."""
        mock_store = Mock(spec=MemoryStore)
        mock_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="test_category",
            key="test_key",
            value="test_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_store.get = AsyncMock(return_value=mock_entry)
        
        repo = MemoryRepository(store=mock_store)
        
        async def read_worker(worker_id):
            return await repo.read("test_category", f"key_{worker_id}")
        
        # Run concurrent operations
        tasks = [read_worker(i) for i in range(5)]
        entries = await asyncio.gather(*tasks)
        
        assert len(entries) == 5
        assert mock_store.get.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_update_operations(self):
        """Test concurrent update operations."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        async def update_worker(worker_id):
            return await repo.update(
                category="test_category",
                key="test_key",
                value=f"updated_value_{worker_id}"
            )
        
        # Run concurrent operations
        tasks = [update_worker(i) for i in range(5)]
        entries = await asyncio.gather(*tasks)
        
        assert len(entries) == 5
        assert all(entry is not None for entry in entries)
        assert mock_store.save.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_delete_operations(self):
        """Test concurrent delete operations."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.delete = AsyncMock(return_value=True)
        
        repo = MemoryRepository(store=mock_store)
        
        async def delete_worker(worker_id):
            return await repo.delete("test_category", f"key_{worker_id}")
        
        # Run concurrent operations
        tasks = [delete_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result is True for result in results)
        assert mock_store.delete.call_count == 5


class TestMemoryRepositoryErrorHandling:
    """Test MemoryRepository error handling."""

    @pytest.mark.asyncio
    async def test_store_connection_error(self):
        """Test handling of store connection errors."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=ConnectionError("Connection failed"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_store_timeout_error(self):
        """Test handling of store timeout errors."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=asyncio.TimeoutError("Operation timeout"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_store_permission_error(self):
        """Test handling of store permission errors."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=PermissionError("Permission denied"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_store_data_corruption_error(self):
        """Test handling of data corruption errors."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.get = AsyncMock(side_effect=json.JSONDecodeError("Corrupted data", "", 0))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.read("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_store_memory_error(self):
        """Test handling of memory errors."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock(side_effect=MemoryError("Out of memory"))
        
        repo = MemoryRepository(store=mock_store)
        
        with pytest.raises(RepositoryError):
            await repo.create("test_category", "test_key", "test_value")


class TestMemoryRepositoryPerformance:
    """Test MemoryRepository performance characteristics."""

    @pytest.mark.asyncio
    async def test_batch_operation_performance(self):
        """Test batch operation performance."""
        import time
        
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Create large batch
        memories = [
            {
                "category": "test_category",
                "key": f"key_{i}",
                "value": f"value_{i}"
            }
            for i in range(100)
        ]
        
        start_time = time.time()
        entries = await repo.batch_create(memories)
        elapsed = time.time() - start_time
        
        assert len(entries) == 100
        assert elapsed < 5.0  # Should complete within 5 seconds
        assert mock_store.save.call_count == 100

    @pytest.mark.asyncio
    async def test_search_performance(self):
        """Test search performance."""
        import time
        
        mock_store = Mock(spec=MemoryStore)
        mock_entries = []
        for i in range(1000):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key=f"key_{i}",
                value=f"searchable_value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_entries.append(entry)
        mock_store.search = AsyncMock(return_value=mock_entries)
        
        repo = MemoryRepository(store=mock_store)
        
        start_time = time.time()
        entries = await repo.search("search_query", "test_category")
        elapsed = time.time() - start_time
        
        assert len(entries) == 1000
        assert elapsed < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        mock_store.get = AsyncMock()
        mock_store.list = AsyncMock(return_value=[])
        
        repo = MemoryRepository(store=mock_store)
        
        # Perform many operations
        for i in range(1000):
            await repo.create(f"category_{i}", f"key_{i}", f"value_{i}")
            await repo.read(f"category_{i}", f"key_{i}")
        
        # Memory usage should be stable
        assert True


class TestMemoryRepositoryEdgeCases:
    """Test MemoryRepository edge cases."""

    @pytest.mark.asyncio
    async def test_extremely_long_content(self):
        """Test handling of extremely long content."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        extremely_long_content = "x" * 1000000  # 1MB
        
        entry = await repo.create(
            category="large_category",
            key="large_key",
            value=extremely_long_content
        )
        
        assert entry.value == extremely_long_content

    @pytest.mark.asyncio
    async def test_deeply_nested_metadata(self):
        """Test handling of deeply nested metadata."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Create deeply nested metadata
        deep_metadata = {"level1": {"level2": {"level3": {"level4": {"deep": "value"}}}}}
        
        entry = await repo.create(
            category="nested_category",
            key="nested_key",
            value="nested_value",
            metadata=deep_metadata
        )
        
        assert entry.metadata == deep_metadata

    @pytest.mark.asyncio
    async def test_special_unicode_characters(self):
        """Test handling of special Unicode characters."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        special_unicode = {
            "emoji": "🚀🎉🔥",
            "math": "∑∏∫∆∇∂",
            "currency": "€£¥₹₽",
            "symbols": "♠♣♥♦★☆♪♫",
            "arabic": "العربية",
            "hebrew": "עברית",
            "thai": "ไทย"
        }
        
        entry = await repo.create(
            category="unicode_category",
            key="unicode_key",
            value="Unicode with special chars",
            metadata=special_unicode
        )
        
        assert entry.metadata == special_unicode

    @pytest.mark.asyncio
    async def test_concurrent_same_key_updates(self):
        """Test concurrent updates to the same key."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        async def update_worker(worker_id):
            return await repo.update(
                category="test_category",
                key="same_key",
                value=f"value_from_worker_{worker_id}"
            )
        
        # Run concurrent updates to same key
        tasks = [update_worker(i) for i in range(5)]
        entries = await asyncio.gather(*tasks)
        
        assert len(entries) == 5
        assert all(entry is not None for entry in entries)
        assert mock_store.save.call_count == 5

    @pytest.mark.asyncio
    async def test_null_and_none_handling(self):
        """Test handling of null and None values."""
        mock_store = Mock(spec=MemoryStore)
        mock_store.save = AsyncMock()
        
        repo = MemoryRepository(store=mock_store)
        
        # Test with None values in metadata
        metadata_with_none = {
            "null_value": None,
            "string_value": "test",
            "int_value": 42
        }
        
        entry = await repo.create(
            category="test_category",
            key="test_key",
            value="test_value",
            metadata=metadata_with_none
        )
        
        # Should handle None values appropriately
        assert entry.metadata["null_value"] is None
        assert entry.metadata["string_value"] == "test"
        assert entry.metadata["int_value"] == 42
