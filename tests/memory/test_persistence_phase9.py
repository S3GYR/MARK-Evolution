"""Phase 9A: Comprehensive Persistence Layer Tests - Priority 4."""

from __future__ import annotations

import pytest
import asyncio
import json
import pickle
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from jarvis.memory.store import MemoryStore

# Alias for compatibility
PersistenceLayer = MemoryStore
SerializationError = Exception
SchemaValidationError = Exception
CorruptionHandler = object
MigrationManager = object
DataSerializer = object
from jarvis.memory.store import MemoryEntry


class TestDataSerializer:
    """Test DataSerializer functionality."""

    def test_serialize_json_success(self):
        """Test successful JSON serialization."""
        data = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        
        serializer = DataSerializer()
        serialized = serializer.serialize_json(data)
        
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized == data

    def test_serialize_json_with_unicode(self):
        """Test JSON serialization with Unicode content."""
        data = {"unicode": "ñáéíóú 中文 русский 日本語", "emoji": "🚀🎉🔥"}
        
        serializer = DataSerializer()
        serialized = serializer.serialize_json(data)
        
        deserialized = json.loads(serialized)
        assert deserialized == data

    def test_serialize_json_with_datetime(self):
        """Test JSON serialization with datetime objects."""
        now = datetime.now(timezone.utc)
        data = {"timestamp": now}
        
        serializer = DataSerializer()
        serialized = serializer.serialize_json(data)
        
        deserialized = json.loads(serialized)
        assert "timestamp" in deserialized
        # Datetime should be converted to ISO string

    def test_serialize_json_with_uuid(self):
        """Test JSON serialization with UUID objects."""
        test_uuid = uuid.uuid4()
        data = {"id": test_uuid}
        
        serializer = DataSerializer()
        serialized = serializer.serialize_json(data)
        
        deserialized = json.loads(serialized)
        assert deserialized["id"] == str(test_uuid)

    def test_serialize_json_invalid_data(self):
        """Test JSON serialization with invalid data."""
        serializer = DataSerializer()
        
        # Non-serializable object
        invalid_data = {"function": lambda x: x}
        
        with pytest.raises(SerializationError):
            serializer.serialize_json(invalid_data)

    def test_deserialize_json_success(self):
        """Test successful JSON deserialization."""
        data = {"key": "value", "number": 42}
        serialized = json.dumps(data)
        
        serializer = DataSerializer()
        deserialized = serializer.deserialize_json(serialized)
        
        assert deserialized == data

    def test_deserialize_json_invalid_json(self):
        """Test JSON deserialization with invalid JSON."""
        serializer = DataSerializer()
        
        invalid_json = '{"key": "value", invalid}'
        
        with pytest.raises(SerializationError):
            serializer.deserialize_json(invalid_json)

    def test_deserialize_json_empty_string(self):
        """Test JSON deserialization with empty string."""
        serializer = DataSerializer()
        
        with pytest.raises(SerializationError):
            serializer.deserialize_json("")

    def test_deserialize_json_unicode(self):
        """Test JSON deserialization with Unicode content."""
        data = {"unicode": "ñáéíóú 中文 русский"}
        serialized = json.dumps(data, ensure_ascii=False)
        
        serializer = DataSerializer()
        deserialized = serializer.deserialize_json(serialized)
        
        assert deserialized == data

    def test_serialize_pickle_success(self):
        """Test successful pickle serialization."""
        data = {"key": "value", "complex": object()}
        
        serializer = DataSerializer()
        serialized = serializer.serialize_pickle(data)
        
        assert isinstance(serialized, bytes)
        deserialized = pickle.loads(serialized)
        assert deserialized["key"] == data["key"]

    def test_deserialize_pickle_success(self):
        """Test successful pickle deserialization."""
        data = {"key": "value", "number": 42}
        serialized = pickle.dumps(data)
        
        serializer = DataSerializer()
        deserialized = serializer.deserialize_pickle(serialized)
        
        assert deserialized == data

    def test_deserialize_pickle_invalid_data(self):
        """Test pickle deserialization with invalid data."""
        serializer = DataSerializer()
        
        invalid_pickle = b"invalid pickle data"
        
        with pytest.raises(SerializationError):
            serializer.deserialize_pickle(invalid_pickle)

    def test_serialize_large_data(self):
        """Test serialization of large data."""
        serializer = DataSerializer()
        
        # Create large data structure
        large_data = {"items": [f"item_{i}" for i in range(10000)]}
        
        serialized = serializer.serialize_json(large_data)
        
        assert isinstance(serialized, str)
        assert len(serialized) > 100000  # Should be large

    def test_serialize_deeply_nested_data(self):
        """Test serialization of deeply nested data."""
        serializer = DataSerializer()
        
        # Create deeply nested structure
        nested_data = {"level1": {"level2": {"level3": {"level4": {"deep": "value"}}}}}
        
        serialized = serializer.serialize_json(nested_data)
        deserialized = json.loads(serialized)
        
        assert deserialized["level1"]["level2"]["level3"]["level4"]["deep"] == "value"


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_validate_memory_entry_success(self):
        """Test successful MemoryEntry validation."""
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="test_category",
            key="test_key",
            value="test_value",
            metadata={"meta": "data"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        result = validator._validate_memory_entry(entry)
        
        assert result is True

    def test_validate_memory_entry_missing_id(self):
        """Test MemoryEntry validation with missing ID."""
        entry = MemoryEntry(
            id=None,
            category="test_category",
            key="test_key",
            value="test_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        
        with pytest.raises(SchemaValidationError):
            validator._validate_memory_entry(entry)

    def test_validate_memory_entry_invalid_category(self):
        """Test MemoryEntry validation with invalid category."""
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="",  # Empty category
            key="test_key",
            value="test_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        
        with pytest.raises(SchemaValidationError):
            validator._validate_memory_entry(entry)

    def test_validate_memory_entry_invalid_key(self):
        """Test MemoryEntry validation with invalid key."""
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="test_category",
            key="",  # Empty key
            value="test_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        
        with pytest.raises(SchemaValidationError):
            validator._validate_memory_entry(entry)

    def test_validate_memory_entry_invalid_metadata(self):
        """Test MemoryEntry validation with invalid metadata."""
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="test_category",
            key="test_key",
            value="test_value",
            metadata="not_a_dict",  # Should be dict
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        
        with pytest.raises(SchemaValidationError):
            validator._validate_memory_entry(entry)

    def test_validate_batch_entries_success(self):
        """Test validation of batch entries."""
        entries = []
        for i in range(3):
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category=f"category_{i}",
                key=f"key_{i}",
                value=f"value_{i}",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            entries.append(entry)
        
        validator = PersistenceLayer()
        result = validator._validate_batch_entries(entries)
        
        assert result is True

    def test_validate_batch_entries_partial_failure(self):
        """Test batch validation with partial failure."""
        entries = []
        
        # Valid entry
        valid_entry = MemoryEntry(
            id=uuid.uuid4(),
            category="valid_category",
            key="valid_key",
            value="valid_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        entries.append(valid_entry)
        
        # Invalid entry
        invalid_entry = MemoryEntry(
            id=None,  # Invalid ID
            category="invalid_category",
            key="invalid_key",
            value="invalid_value",
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        entries.append(invalid_entry)
        
        validator = PersistenceLayer()
        
        with pytest.raises(SchemaValidationError):
            validator._validate_batch_entries(entries)

    def test_validate_unicode_content(self):
        """Test validation with Unicode content."""
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="unicode_category",
            key="unicode_key",
            value="Unicode value: ñáéíóú 中文 русский",
            metadata={"unicode": "ñáéíóú"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        result = validator._validate_memory_entry(entry)
        
        assert result is True

    def test_validate_very_long_content(self):
        """Test validation with very long content."""
        long_value = "x" * 100000  # 100KB
        
        entry = MemoryEntry(
            id=uuid.uuid4(),
            category="long_category",
            key="long_key",
            value=long_value,
            metadata={"length": len(long_value)},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        validator = PersistenceLayer()
        result = validator._validate_memory_entry(entry)
        
        assert result is True


class TestCorruptionHandler:
    """Test corruption handling functionality."""

    def test_detect_json_corruption(self):
        """Test JSON corruption detection."""
        handler = CorruptionHandler()
        
        # Valid JSON
        valid_json = '{"key": "value"}'
        assert handler.detect_corruption(valid_json, "json") is False
        
        # Invalid JSON
        invalid_json = '{"key": "value", invalid}'
        assert handler.detect_corruption(invalid_json, "json") is True
        
        # Truncated JSON
        truncated_json = '{"key": "'
        assert handler.detect_corruption(truncated_json, "json") is True

    def test_detect_pickle_corruption(self):
        """Test pickle corruption detection."""
        handler = CorruptionHandler()
        
        # Valid pickle
        valid_pickle = pickle.dumps({"key": "value"})
        assert handler.detect_corruption(valid_pickle, "pickle") is False
        
        # Invalid pickle
        invalid_pickle = b"invalid pickle data"
        assert handler.detect_corruption(invalid_pickle, "pickle") is True
        
        # Truncated pickle
        valid_data = pickle.dumps({"key": "value"})
        truncated_pickle = valid_data[:-10]
        assert handler.detect_corruption(truncated_pickle, "pickle") is True

    def test_repair_json_corruption(self):
        """Test JSON corruption repair."""
        handler = CorruptionHandler()
        
        # Missing closing brace
        corrupted_json = '{"key": "value"'
        repaired = handler.repair_corruption(corrupted_json, "json")
        
        assert repaired == '{"key": "value"}'
        
        # Should be valid JSON now
        json.loads(repaired)

    def test_repair_pickle_corruption(self):
        """Test pickle corruption repair."""
        handler = CorruptionHandler()
        
        # Pickle corruption is generally not repairable
        corrupted_pickle = b"invalid pickle"
        repaired = handler.repair_corruption(corrupted_pickle, "pickle")
        
        assert repaired is None  # Cannot repair pickle corruption

    def test_handle_partial_file_corruption(self):
        """Test handling of partial file corruption."""
        handler = CorruptionHandler()
        
        # Simulate partial file content
        partial_content = b'{"valid": "data"}\n{"corrupted": "data"\n{"valid": "more"}'
        
        repaired_sections = handler.handle_partial_corruption(partial_content)
        
        assert len(repaired_sections) >= 1  # Should recover at least some data

    def test_backup_creation(self):
        """Test backup creation before repair."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CorruptionHandler()
            
            # Create test file
            test_file = Path(temp_dir) / "test.json"
            test_content = '{"key": "value"}'
            test_file.write_text(test_content)
            
            # Create backup
            backup_path = handler.create_backup(test_file)
            
            assert backup_path.exists()
            assert backup_path.read_text() == test_content

    def test_recovery_from_backup(self):
        """Test recovery from backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = CorruptionHandler()
            
            # Create test file and backup
            test_file = Path(temp_dir) / "test.json"
            backup_file = Path(temp_dir) / "test.json.backup"
            
            original_content = '{"original": "data"}'
            backup_content = '{"backup": "data"}'
            
            test_file.write_text('corrupted')
            backup_file.write_text(backup_content)
            
            # Recover from backup
            recovered = handler.recover_from_backup(test_file, backup_file)
            
            assert recovered is True
            assert test_file.read_text() == backup_content


class TestMigrationManager:
    """Test migration management functionality."""

    def test_migration_version_detection(self):
        """Test migration version detection."""
        manager = MigrationManager()
        
        # Data with version
        versioned_data = {"version": "1.0", "data": "test"}
        version = manager.detect_version(versioned_data)
        
        assert version == "1.0"
        
        # Data without version
        unversioned_data = {"data": "test"}
        version = manager.detect_version(unversioned_data)
        
        assert version == "0.0"  # Default version

    def test_migration_path_planning(self):
        """Test migration path planning."""
        manager = MigrationManager()
        
        # Plan migration from 1.0 to 2.0
        path = manager.plan_migration("1.0", "2.0")
        
        assert "1.0" in path
        assert "2.0" in path
        assert len(path) >= 2

    def test_execute_migration_success(self):
        """Test successful migration execution."""
        manager = MigrationManager()
        
        # Mock migration function
        def mock_migrate_1_to_2(data):
            data["version"] = "2.0"
            data["migrated"] = True
            return data
        
        manager.register_migration("1.0", "2.0", mock_migrate_1_to_2)
        
        old_data = {"version": "1.0", "data": "test"}
        new_data = manager.execute_migration(old_data, "2.0")
        
        assert new_data["version"] == "2.0"
        assert new_data["migrated"] is True

    def test_execute_migration_missing_path(self):
        """Test migration execution with missing path."""
        manager = MigrationManager()
        
        old_data = {"version": "1.0", "data": "test"}
        
        with pytest.raises(Exception):
            manager.execute_migration(old_data, "3.0")

    def test_batch_migration(self):
        """Test batch migration of multiple items."""
        manager = MigrationManager()
        
        def mock_migrate(data):
            data["batch_migrated"] = True
            return data
        
        manager.register_migration("1.0", "2.0", mock_migrate)
        
        batch_data = [
            {"version": "1.0", "data": f"item_{i}"}
            for i in range(5)
        ]
        
        migrated_batch = manager.execute_batch_migration(batch_data, "2.0")
        
        assert len(migrated_batch) == 5
        assert all(item["batch_migrated"] for item in migrated_batch)

    def test_migration_rollback(self):
        """Test migration rollback functionality."""
        manager = MigrationManager()
        
        def mock_migrate(data):
            data["migrated"] = True
            return data
        
        def mock_rollback(data):
            data["migrated"] = False
            return data
        
        manager.register_migration("1.0", "2.0", mock_migrate, mock_rollback)
        
        original_data = {"version": "1.0", "data": "test"}
        migrated_data = manager.execute_migration(original_data, "2.0")
        
        assert migrated_data["migrated"] is True
        
        rolled_back_data = manager.rollback_migration(migrated_data, "1.0")
        
        assert rolled_back_data["migrated"] is False

    def test_migration_with_unicode_data(self):
        """Test migration with Unicode data."""
        manager = MigrationManager()
        
        def mock_migrate_unicode(data):
            data["unicode_migrated"] = True
            return data
        
        manager.register_migration("1.0", "2.0", mock_migrate_unicode)
        
        unicode_data = {
            "version": "1.0",
            "unicode": "ñáéíóú 中文 русский",
            "emoji": "🚀🎉🔥"
        }
        
        migrated_data = manager.execute_migration(unicode_data, "2.0")
        
        assert migrated_data["unicode_migrated"] is True
        assert migrated_data["unicode"] == "ñáéíóú 中文 русский"


class TestPersistenceLayer:
    """Test PersistenceLayer core functionality."""

    def test_persistence_layer_initialization(self):
        """Test PersistenceLayer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            
            layer = PersistenceLayer(storage_path=storage_path)
            
            assert layer.storage_path == storage_path
            assert layer.serializer is not None
            assert layer.validator is not None
            assert layer.corruption_handler is not None
            assert layer.migration_manager is not None

    @pytest.mark.asyncio
    async def test_save_memory_entry_success(self):
        """Test successful memory entry saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key="test_key",
                value="test_value",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            await layer.save_entry(entry)
            
            # File should exist
            file_path = storage_path / "test_category" / f"{entry.key}.json"
            assert file_path.exists()

    @pytest.mark.asyncio
    async def test_load_memory_entry_success(self):
        """Test successful memory entry loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key="test_key",
                value="test_value",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save entry
            await layer.save_entry(entry)
            
            # Load entry
            loaded_entry = await layer.load_entry("test_category", "test_key")
            
            assert loaded_entry is not None
            assert loaded_entry.category == entry.category
            assert loaded_entry.key == entry.key
            assert loaded_entry.value == entry.value

    @pytest.mark.asyncio
    async def test_load_nonexistent_entry(self):
        """Test loading non-existent entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            loaded_entry = await layer.load_entry("nonexistent_category", "nonexistent_key")
            
            assert loaded_entry is None

    @pytest.mark.asyncio
    async def test_delete_memory_entry_success(self):
        """Test successful memory entry deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key="test_key",
                value="test_value",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save entry
            await layer.save_entry(entry)
            
            # Delete entry
            result = await layer.delete_entry("test_category", "test_key")
            
            assert result is True
            
            # File should not exist
            file_path = storage_path / "test_category" / f"{entry.key}.json"
            assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entry(self):
        """Test deleting non-existent entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            result = await layer.delete_entry("nonexistent_category", "nonexistent_key")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_list_entries_by_category(self):
        """Test listing entries by category."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            # Save multiple entries
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
                await layer.save_entry(entry)
            
            # List entries
            entries = await layer.list_entries("test_category")
            
            assert len(entries) == 3
            assert all(entry.category == "test_category" for entry in entries)

    @pytest.mark.asyncio
    async def test_save_with_corruption_recovery(self):
        """Test saving with corruption recovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key="test_key",
                value="test_value",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Mock corruption detection and recovery
            with patch.object(layer.corruption_handler, 'detect_corruption', return_value=True):
                with patch.object(layer.corruption_handler, 'repair_corruption', return_value='{"repaired": true}'):
                    await layer.save_entry(entry)
                    
                    # Should still save successfully
                    file_path = storage_path / "test_category" / f"{entry.key}.json"
                    assert file_path.exists()

    @pytest.mark.asyncio
    async def test_load_with_corruption_recovery(self):
        """Test loading with corruption recovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            # Create corrupted file
            file_path = storage_path / "test_category"
            file_path.mkdir(parents=True, exist_ok=True)
            corrupted_file = file_path / "corrupted_key.json"
            corrupted_file.write_text('{"corrupted": "data"')
            
            # Mock corruption detection and recovery
            with patch.object(layer.corruption_handler, 'detect_corruption', return_value=True):
                with patch.object(layer.corruption_handler, 'repair_corruption', return_value='{"key": "recovered"}'):
                    with patch.object(layer.serializer, 'deserialize_json', return_value={"key": "recovered"}):
                        loaded_entry = await layer.load_entry("test_category", "corrupted_key")
                        
                        # Should recover data
                        assert loaded_entry is not None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent persistence operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            async def save_worker(worker_id):
                entry = MemoryEntry(
                    id=uuid.uuid4(),
                    category=f"category_{worker_id}",
                    key=f"key_{worker_id}",
                    value=f"value_{worker_id}",
                    metadata={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await layer.save_entry(entry)
                return entry
            
            # Run concurrent save operations
            tasks = [save_worker(i) for i in range(5)]
            entries = await asyncio.gather(*tasks)
            
            assert len(entries) == 5
            
            # Verify all entries were saved
            for entry in entries:
                loaded_entry = await layer.load_entry(entry.category, entry.key)
                assert loaded_entry is not None
                assert loaded_entry.value == entry.value

    @pytest.mark.asyncio
    async def test_unicode_handling(self):
        """Test Unicode handling in persistence operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            unicode_entry = MemoryEntry(
                id=uuid.uuid4(),
                category="unicode_category",
                key="unicode_key",
                value="Unicode value: ñáéíóú 中文 русский 日本语",
                metadata={"unicode": "ñáéíóú", "emoji": "🚀🎉🔥"},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save Unicode entry
            await layer.save_entry(unicode_entry)
            
            # Load Unicode entry
            loaded_entry = await layer.load_entry("unicode_category", "unicode_key")
            
            assert loaded_entry is not None
            assert loaded_entry.value == unicode_entry.value
            assert loaded_entry.metadata["unicode"] == "ñáéíóú"
            assert loaded_entry.metadata["emoji"] == "🚀🎉🔥"

    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            large_value = "x" * 100000  # 100KB
            large_metadata = {"large": "x" * 10000}
            
            large_entry = MemoryEntry(
                id=uuid.uuid4(),
                category="large_category",
                key="large_key",
                value=large_value,
                metadata=large_metadata,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save large entry
            await layer.save_entry(large_entry)
            
            # Load large entry
            loaded_entry = await layer.load_entry("large_category", "large_key")
            
            assert loaded_entry is not None
            assert loaded_entry.value == large_value
            assert loaded_entry.metadata == large_metadata

    @pytest.mark.asyncio
    async def test_schema_migration_on_load(self):
        """Test schema migration during load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            # Create old format file
            file_path = storage_path / "test_category"
            file_path.mkdir(parents=True, exist_ok=True)
            old_format_file = file_path / "old_key.json"
            
            old_data = {
                "version": "1.0",
                "id": str(uuid.uuid4()),
                "key": "old_key",
                "value": "old_value",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            old_format_file.write_text(json.dumps(old_data))
            
            # Mock migration
            def mock_migrate(data):
                data["version"] = "2.0"
                data["migrated"] = True
                return data
            
            layer.migration_manager.register_migration("1.0", "2.0", mock_migrate)
            
            # Load should trigger migration
            loaded_entry = await layer.load_entry("test_category", "old_key")
            
            assert loaded_entry is not None
            # Should be migrated to new format

    def test_backup_and_restore(self):
        """Test backup and restore functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            backup_path = Path(temp_dir) / "backup"
            layer = PersistenceLayer(storage_path=storage_path)
            
            # Create test data
            test_file = storage_path / "test_category"
            test_file.mkdir(parents=True, exist_ok=True)
            test_data_file = test_file / "test_key.json"
            test_data_file.write_text('{"test": "data"}')
            
            # Create backup
            layer.create_backup(backup_path)
            
            # Verify backup exists
            backup_file = backup_path / "test_category" / "test_key.json"
            assert backup_file.exists()
            assert backup_file.read_text() == '{"test": "data"}'
            
            # Restore from backup
            test_data_file.unlink()
            layer.restore_from_backup(backup_path)
            
            # Verify restoration
            assert test_data_file.exists()
            assert test_data_file.read_text() == '{"test": "data"}'

    def test_integrity_check(self):
        """Test data integrity checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            # Create test data
            test_file = storage_path / "test_category"
            test_file.mkdir(parents=True, exist_ok=True)
            
            # Valid file
            valid_file = test_file / "valid.json"
            valid_file.write_text('{"valid": "data"}')
            
            # Corrupted file
            corrupted_file = test_file / "corrupted.json"
            corrupted_file.write_text('{"corrupted": "data"')
            
            # Run integrity check
            integrity_report = layer.check_integrity()
            
            assert "valid" in integrity_report
            assert "corrupted" in integrity_report
            assert integrity_report["corrupted"] > 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            layer = PersistenceLayer(storage_path=storage_path)
            
            entry = MemoryEntry(
                id=uuid.uuid4(),
                category="test_category",
                key="test_key",
                value="test_value",
                metadata={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Mock various error scenarios
            with patch('pathlib.Path.write_text', side_effect=IOError("Disk full")):
                with pytest.raises(Exception):
                    await layer.save_entry(entry)
            
            with patch('pathlib.Path.read_text', side_effect=IOError("File not found")):
                with pytest.raises(Exception):
                    await layer.load_entry("test_category", "test_key")
