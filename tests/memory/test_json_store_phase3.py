"""Phase 3 JSON Memory Store tests for robustness and concurrency (>80% coverage)."""

from __future__ import annotations

import pytest
import json
import tempfile
import shutil
import asyncio
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

from jarvis.memory.json_store import JsonMemoryStore
from jarvis.memory.store import MemoryEntry
from jarvis.llm.embeddings import MockEmbeddingProvider


@pytest.fixture
def temp_memory_store():
    """Create a temporary JSON memory store for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    temp_file = temp_dir / "test_memory.json"
    embeddings = MockEmbeddingProvider(dim=384)
    store = JsonMemoryStore(path=temp_file, embeddings=embeddings)
    yield store
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()
    if temp_file.with_suffix(".json.bak").exists():
        temp_file.with_suffix(".json.bak").unlink()
    if temp_file.with_suffix(".tmp").exists():
        temp_file.with_suffix(".tmp").unlink()
    temp_dir.rmdir()


@pytest.fixture
def corrupted_store():
    """Create a store with corrupted JSON file."""
    temp_dir = Path(tempfile.mkdtemp())
    temp_file = temp_dir / "corrupted_memory.json"
    
    # Write invalid JSON
    temp_file.write_text('{"invalid": json content}', encoding="utf-8")
    
    embeddings = MockEmbeddingProvider(dim=384)
    store = JsonMemoryStore(path=temp_file, embeddings=embeddings)
    yield store
    
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()
    temp_dir.rmdir()


class TestJsonMemoryStoreInitialization:
    """Test initialization scenarios."""

    @pytest.mark.asyncio
    async def test_initialize_new_file(self, temp_memory_store):
        """Test initialization with new file."""
        await temp_memory_store.initialize()
        
        assert temp_memory_store.path.exists()
        assert temp_memory_store.path.with_suffix(".json.bak").exists()
        
        # Should have default categories
        data = temp_memory_store._load()
        for category in temp_memory_store.DEFAULT_CATEGORIES:
            assert category in data

    @pytest.mark.asyncio
    async def test_initialize_existing_file(self, temp_memory_store):
        """Test initialization with existing file."""
        # Create initial data
        temp_memory_store.path.write_text(
            json.dumps({"test": {"key": "value"}}), 
            encoding="utf-8"
        )
        
        await temp_memory_store.initialize()
        
        # Should preserve existing data and add defaults
        data = temp_memory_store._load()
        assert "test" in data
        assert data["test"]["key"] == "value"
        for category in temp_memory_store.DEFAULT_CATEGORIES:
            assert category in data

    @pytest.mark.asyncio
    async def test_initialize_creates_backup(self, temp_memory_store):
        """Test that initialization creates backup."""
        # Create initial file
        initial_data = {"existing": {"data": "test"}}
        temp_memory_store.path.write_text(
            json.dumps(initial_data), 
            encoding="utf-8"
        )
        
        await temp_memory_store.initialize()
        
        # Backup should exist
        backup_path = temp_memory_store.path.with_suffix(".json.bak")
        assert backup_path.exists()
        
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        assert backup_data == initial_data

    @pytest.mark.asyncio
    async def test_backup_creation(self, temp_memory_store):
        """Test backup creation method."""
        # Create initial data
        temp_memory_store.path.write_text(
            json.dumps({"test": {"key": "value"}}), 
            encoding="utf-8"
        )
        
        temp_memory_store._backup()
        
        backup_path = temp_memory_store.path.with_suffix(".json.bak")
        assert backup_path.exists()
        
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        assert backup_data == {"test": {"key": "value"}}


class TestJsonMemoryStorePersistence:
    """Test persistence scenarios including corruption and recovery."""

    @pytest.mark.asyncio
    async def test_save_valid_entry(self, temp_memory_store):
        """Test saving a valid memory entry."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save(
            category="preferences",
            key="theme",
            value="dark",
            metadata={"source": "user_setting"}
        )
        
        # Verify data was saved
        entry = await temp_memory_store.get("preferences", "theme")
        assert entry is not None
        assert entry.category == "preferences"
        assert entry.key == "theme"
        assert entry.value == "dark"
        assert entry.metadata["source"] == "user_setting"

    @pytest.mark.asyncio
    async def test_save_empty_value(self, temp_memory_store):
        """Test saving entry with empty value."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("notes", "empty", "", {"test": True})
        
        entry = await temp_memory_store.get("notes", "empty")
        assert entry is not None
        assert entry.value == ""

    @pytest.mark.asyncio
    async def test_save_without_metadata(self, temp_memory_store):
        """Test saving entry without metadata."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("preferences", "setting", "value")
        
        entry = await temp_memory_store.get("preferences", "setting")
        assert entry is not None
        assert entry.metadata == {}

    @pytest.mark.asyncio
    async def test_save_overwrite_existing(self, temp_memory_store):
        """Test overwriting an existing entry."""
        await temp_memory_store.initialize()
        
        # Save initial entry
        await temp_memory_store.save("test", "key", "original", {"v": 1})
        
        # Overwrite
        await temp_memory_store.save("test", "key", "updated", {"v": 2})
        
        entry = await temp_memory_store.get("test", "key")
        assert entry.value == "updated"
        assert entry.metadata["v"] == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self, temp_memory_store):
        """Test getting a non-existent entry."""
        await temp_memory_store.initialize()
        
        entry = await temp_memory_store.get("nonexistent", "key")
        assert entry is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_category(self, temp_memory_store):
        """Test getting from non-existent category."""
        await temp_memory_store.initialize()
        
        entry = await temp_memory_store.get("nonexistent_category", "any_key")
        assert entry is None

    @pytest.mark.asyncio
    async def test_load_corrupted_json_recovery(self, corrupted_store):
        """Test recovery from corrupted JSON file."""
        await corrupted_store.initialize()
        
        # Should recover with default categories
        data = corrupted_store._load()
        for category in corrupted_store.DEFAULT_CATEGORIES:
            assert category in data
            assert isinstance(data[category], dict)

    @pytest.mark.asyncio
    async def test_load_partially_corrupted_json(self, temp_memory_store):
        """Test loading partially corrupted JSON with valid sections."""
        # Create partially corrupted JSON
        corrupted_content = '''{
            "valid_category": {"key1": "value1"},
            "invalid_category": {"invalid": json content},
            "another_valid": {"key2": "value2"}
        }'''
        
        temp_memory_store.path.write_text(corrupted_content, encoding="utf-8")
        
        # Should handle gracefully and add defaults
        data = temp_memory_store._load()
        assert "valid_category" in data
        assert "another_valid" in data
        assert data["valid_category"]["key1"] == "value1"
        
        # Should have default categories
        for category in temp_memory_store.DEFAULT_CATEGORIES:
            assert category in data

    @pytest.mark.asyncio
    async def test_save_after_crash_with_tmp_file(self, temp_memory_store):
        """Test recovery when .tmp file exists from crash."""
        await temp_memory_store.initialize()
        
        # Simulate crash scenario: .tmp file exists but main doesn't
        tmp_file = temp_memory_store.path.with_suffix(".tmp")
        tmp_file.write_text('{"crashed": {"data": "recovery"}}', encoding="utf-8")
        
        # Should be able to save new data
        await temp_memory_store.save("recovery", "test", "new_data")
        
        entry = await temp_memory_store.get("recovery", "test")
        assert entry is not None
        assert entry.value == "new_data"

    @pytest.mark.asyncio
    async def test_atomic_save_prevents_corruption(self, temp_memory_store):
        """Test that atomic save prevents corruption."""
        await temp_memory_store.initialize()
        
        # Save initial data
        await temp_memory_store.save("test", "initial", "data")
        
        # Simulate interruption during save by mocking
        original_save = temp_memory_store._save
        
        def interrupted_save(data):
            # Write partial data then "crash"
            tmp_file = temp_memory_store.path.with_suffix(".tmp")
            tmp_file.write_text('{"partial": "data"', encoding="utf-8")
            raise IOError("Simulated write error")
        
        temp_memory_store._save = interrupted_save
        
        # Should handle save error gracefully
        with pytest.raises(IOError):
            await temp_memory_store.save("test", "interrupted", "data")
        
        # Original data should be intact
        entry = await temp_memory_store.get("test", "initial")
        assert entry is not None
        assert entry.value == "data"
        
        # Restore original save method
        temp_memory_store._save = original_save


class TestJsonMemoryStoreConcurrency:
    """Test concurrent access scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_saves_different_categories(self, temp_memory_store):
        """Test concurrent saves to different categories."""
        await temp_memory_store.initialize()
        
        async def save_worker(category: str, start_id: int, count: int):
            for i in range(count):
                await temp_memory_store.save(
                    category, 
                    f"key_{start_id + i}", 
                    f"value_{start_id + i}"
                )
        
        # Run concurrent saves
        tasks = [
            save_worker("cat1", 0, 10),
            save_worker("cat2", 10, 10),
            save_worker("cat3", 20, 10)
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify all data was saved
        for category in ["cat1", "cat2", "cat3"]:
            entries = await temp_memory_store.search("", category=category, limit=20)
            assert len(entries) == 10

    @pytest.mark.asyncio
    async def test_concurrent_saves_same_category_race_condition(self, temp_memory_store):
        """Test race conditions in concurrent saves to same category."""
        await temp_memory_store.initialize()
        
        async def save_worker(worker_id: int):
            for i in range(5):
                await temp_memory_store.save(
                    "shared",
                    f"worker_{worker_id}_key_{i}",
                    f"worker_{worker_id}_value_{i}"
                )
        
        # Run multiple workers on same category
        tasks = [save_worker(i) for i in range(3)]
        await asyncio.gather(*tasks)
        
        # Verify all entries exist (no data loss)
        entries = await temp_memory_store.search("", category="shared", limit=20)
        assert len(entries) == 15  # 3 workers * 5 entries each
        
        # Check for specific entries
        for worker_id in range(3):
            for i in range(5):
                entry = await temp_memory_store.get(
                    "shared", 
                    f"worker_{worker_id}_key_{i}"
                )
                assert entry is not None
                assert entry.value == f"worker_{worker_id}_value_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_read_write_operations(self, temp_memory_store):
        """Test concurrent read and write operations."""
        await temp_memory_store.initialize()
        
        # Pre-populate some data
        for i in range(10):
            await temp_memory_store.save("data", f"key_{i}", f"value_{i}")
        
        async def reader_worker():
            for i in range(20):
                entry = await temp_memory_store.get("data", f"key_{i % 10}")
                assert entry is not None if i < 10 else entry is None
        
        async def writer_worker():
            for i in range(10, 20):
                await temp_memory_store.save("data", f"key_{i}", f"value_{i}")
        
        # Run concurrent readers and writers
        tasks = [reader_worker() for _ in range(3)] + [writer_worker() for _ in range(2)]
        await asyncio.gather(*tasks)
        
        # Verify all data is present
        entries = await temp_memory_store.search("", category="data", limit=30)
        assert len(entries) == 20

    def test_thread_safety_with_file_locking_simulation(self, temp_memory_store):
        """Test thread safety with simulated file locking."""
        import threading
        
        temp_memory_store.initialize()
        
        def worker_thread(thread_id: int, results: list):
            """Worker that saves and retrieves data."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def async_work():
                for i in range(5):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    
                    # Save
                    await temp_memory_store.save("threads", key, value)
                    
                    # Retrieve
                    entry = await temp_memory_store.get("threads", key)
                    results.append((thread_id, i, entry.value if entry else None))
            
            loop.run_until_complete(async_work())
            loop.close()
        
        # Run multiple threads
        results = []
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        assert len(results) == 15  # 3 threads * 5 operations each
        
        for thread_id, i, value in results:
            expected = f"thread_{thread_id}_value_{i}"
            assert value == expected

    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, temp_memory_store):
        """Test concurrent search operations."""
        await temp_memory_store.initialize()
        
        # Add test data
        categories = ["cat1", "cat2", "cat3"]
        for cat in categories:
            for i in range(10):
                await temp_memory_store.save(cat, f"key_{i}", f"value_{i}")
        
        async def search_worker(query: str):
            results = await temp_memory_store.search(query, limit=20)
            return len(results)
        
        # Run concurrent searches
        tasks = [
            search_worker("value"),
            search_worker("key"),
            search_worker("value_1"),
            search_worker("key_2")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All searches should return results
        for result_count in results:
            assert result_count > 0

    @pytest.mark.asyncio
    async def test_concurrent_format_for_prompt(self, temp_memory_store):
        """Test concurrent format_for_prompt operations."""
        await temp_memory_store.initialize()
        
        # Add substantial data
        for i in range(50):
            await temp_memory_store.save(
                "data", 
                f"key_{i}", 
                f"This is a longer value for key {i} to test formatting"
            )
        
        async def format_worker(max_chars: int):
            return await temp_memory_store.format_for_prompt(max_chars)
        
        # Run concurrent formatting with different limits
        tasks = [
            format_worker(100),
            format_worker(500),
            format_worker(1000),
            format_worker(2000)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Results should be different lengths based on limits
        assert len(results[0]) < len(results[1]) < len(results[2]) < len(results[3])


class TestJsonMemoryStoreSearch:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_with_results(self, temp_memory_store):
        """Test search that returns results."""
        await temp_memory_store.initialize()
        
        # Add test data
        await temp_memory_store.save("test", "apple", "red fruit")
        await temp_memory_store.save("test", "banana", "yellow fruit")
        await temp_memory_store.save("test", "car", "vehicle")
        
        results = await temp_memory_store.search("fruit", category="test")
        
        assert len(results) == 2
        values = [r.value for r in results]
        assert "red fruit" in values
        assert "yellow fruit" in values

    @pytest.mark.asyncio
    async def test_search_no_results(self, temp_memory_store):
        """Test search with no results."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("test", "key", "value")
        
        results = await temp_memory_store.search("nonexistent", category="test")
        
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, temp_memory_store):
        """Test case insensitive search."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("test", "Key", "Value")
        await temp_memory_store.save("test", "another", "AnotherValue")
        
        results = await temp_memory_store.search("key", category="test")
        assert len(results) == 1
        assert results[0].key == "Key"
        
        results = await temp_memory_store.search("value", category="test")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_key(self, temp_memory_store):
        """Test searching by key."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("test", "searchable_key", "some value")
        await temp_memory_store.save("test", "other", "value with searchable_key in text")
        
        results = await temp_memory_store.search("searchable_key", category="test")
        
        # Should find both key and value matches
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_limit(self, temp_memory_store):
        """Test search result limit."""
        await temp_memory_store.initialize()
        
        # Add many matching entries
        for i in range(10):
            await temp_memory_store.save("test", f"key_{i}", "matching value")
        
        results = await temp_memory_store.search("matching", category="test", limit=3)
        
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_all_categories(self, temp_memory_store):
        """Test search across all categories."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("cat1", "key1", "target value")
        await temp_memory_store.save("cat2", "key2", "another target")
        await temp_memory_store.save("cat3", "key3", "different")
        
        results = await temp_memory_store.search("target")  # No category specified
        
        assert len(results) == 2
        categories = {r.category for r in results}
        assert "cat1" in categories
        assert "cat2" in categories

    @pytest.mark.asyncio
    async def test_search_empty_query(self, temp_memory_store):
        """Test search with empty query."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("test", "key", "value")
        
        # Empty query should not crash
        results = await temp_memory_store.search("", category="test")
        assert len(results) == 0


class TestJsonMemoryStoreFormatting:
    """Test formatting functionality."""

    @pytest.mark.asyncio
    async def test_format_for_prompt_basic(self, temp_memory_store):
        """Test basic formatting for prompt."""
        await temp_memory_store.initialize()
        
        await temp_memory_store.save("preferences", "theme", "dark")
        await temp_memory_store.save("preferences", "language", "en")
        await temp_memory_store.save("notes", "important", "remember this")
        
        formatted = await temp_memory_store.format_for_prompt()
        
        assert "[preferences] theme: dark" in formatted
        assert "[preferences] language: en" in formatted
        assert "[notes] important: remember this" in formatted

    @pytest.mark.asyncio
    async def test_format_for_prompt_with_limit(self, temp_memory_store):
        """Test formatting with character limit."""
        await temp_memory_store.initialize()
        
        # Add data that will exceed limit
        long_value = "x" * 1000
        await temp_memory_store.save("test", "long", long_value)
        await temp_memory_store.save("test", "short", "short")
        
        formatted = await temp_memory_store.format_for_prompt(max_chars=500)
        
        assert len(formatted) <= 500
        assert "short" in formatted or "long" in formatted

    @pytest.mark.asyncio
    async def test_format_for_prompt_empty_store(self, temp_memory_store):
        """Test formatting empty store."""
        await temp_memory_store.initialize()
        
        formatted = await temp_memory_store.format_for_prompt()
        
        assert formatted == ""

    @pytest.mark.asyncio
    async def test_format_for_prompt_unicode_content(self, temp_memory_store):
        """Test formatting with unicode content."""
        await temp_memory_store.initialize()
        
        unicode_text = "Test with émojis 🎉 and accents café"
        await temp_memory_store.save("unicode", "test", unicode_text)
        
        formatted = await temp_memory_store.format_for_prompt()
        
        assert unicode_text in formatted

    @pytest.mark.asyncio
    async def test_format_for_prompt_special_characters(self, temp_memory_store):
        """Test formatting with special characters."""
        await temp_memory_store.initialize()
        
        special_text = "Special chars: @#$%^&*()[]{}|\\:;<>?,./"
        await temp_memory_store.save("special", "chars", special_text)
        
        formatted = await temp_memory_store.format_for_prompt()
        
        assert special_text in formatted


class TestJsonMemoryStoreCategories:
    """Test category management."""

    @pytest.mark.asyncio
    async def test_list_categories_default(self, temp_memory_store):
        """Test listing default categories."""
        await temp_memory_store.initialize()
        
        categories = await temp_memory_store.list_categories()
        
        for cat in temp_memory_store.DEFAULT_CATEGORIES:
            assert cat in categories

    @pytest.mark.asyncio
    async def test_list_categories_with_custom(self, temp_memory_store):
        """Test listing categories with custom additions."""
        await temp_memory_store.initialize()
        
        # Add custom category
        await temp_memory_store.save("custom_category", "key", "value")
        
        categories = await temp_memory_store.list_categories()
        
        assert "custom_category" in categories
        for cat in temp_memory_store.DEFAULT_CATEGORIES:
            assert cat in categories

    @pytest.mark.asyncio
    async def test_list_categories_empty_store(self, temp_memory_store):
        """Test listing categories on empty store."""
        await temp_memory_store.initialize()
        
        categories = await temp_memory_store.list_categories()
        
        assert len(categories) == len(temp_memory_store.DEFAULT_CATEGORIES)


class TestJsonMemoryStoreEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_very_long_key_and_value(self, temp_memory_store):
        """Test with very long keys and values."""
        await temp_memory_store.initialize()
        
        long_key = "k" * 1000
        long_value = "v" * 10000
        
        await temp_memory_store.save("test", long_key, long_value)
        
        entry = await temp_memory_store.get("test", long_key)
        assert entry is not None
        assert entry.value == long_value

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, temp_memory_store):
        """Test special characters in keys."""
        await temp_memory_store.initialize()
        
        special_keys = [
            "key with spaces",
            "key-with-dashes",
            "key_with_underscores",
            "key.with.dots",
            "key/with/slashes",
            "key\\with\\backslashes"
        ]
        
        for key in special_keys:
            await temp_memory_store.save("test", key, f"value_for_{key}")
        
        # Verify all can be retrieved
        for key in special_keys:
            entry = await temp_memory_store.get("test", key)
            assert entry is not None

    @pytest.mark.asyncio
    async def test_null_and_none_values(self, temp_memory_store):
        """Test handling of null and None values."""
        await temp_memory_store.initialize()
        
        # These should be converted to strings
        await temp_memory_store.save("test", "null_key", None)
        await temp_memory_store.save("test", "empty_key", "")
        
        entry_null = await temp_memory_store.get("test", "null_key")
        entry_empty = await temp_memory_store.get("test", "empty_key")
        
        assert entry_null is not None
        assert entry_null.value == ""
        assert entry_empty is not None
        assert entry_empty.value == ""

    @pytest.mark.asyncio
    async def test_metadata_with_complex_types(self, temp_memory_store):
        """Test metadata with complex data types."""
        await temp_memory_store.initialize()
        
        complex_metadata = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "number": 42,
            "boolean": True,
            "none": None
        }
        
        await temp_memory_store.save("test", "complex", "value", complex_metadata)
        
        entry = await temp_memory_store.get("test", "complex")
        assert entry is not None
        assert entry.metadata == complex_metadata

    def test_close_method(self, temp_memory_store):
        """Test close method (no-op for JSON store)."""
        # Should not raise any exception
        result = temp_memory_store.close()
        assert result is None

    @pytest.mark.asyncio
    async def test_load_async_wrapper(self, temp_memory_store):
        """Test async wrapper for load method."""
        await temp_memory_store.initialize()
        
        data = await temp_memory_store._load_async()
        assert isinstance(data, dict)
        assert len(data) > 0


class TestJsonMemoryStorePerformance:
    """Test performance and large datasets."""

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, temp_memory_store):
        """Test performance with large dataset."""
        import time
        
        await temp_memory_store.initialize()
        
        # Measure save performance
        start_time = time.time()
        
        for i in range(100):
            await temp_memory_store.save(
                "performance", 
                f"key_{i}", 
                f"value_{i}" * 10  # Longer values
            )
        
        save_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust as needed)
        assert save_time < 5.0  # 5 seconds for 100 entries
        
        # Measure search performance
        start_time = time.time()
        
        results = await temp_memory_store.search("value_50", category="performance")
        
        search_time = time.time() - start_time
        
        assert len(results) > 0
        assert search_time < 1.0  # Search should be fast

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_values(self, temp_memory_store):
        """Test memory usage with very large values."""
        await temp_memory_store.initialize()
        
        # Create very large values
        large_value = "x" * 100000  # 100KB per entry
        
        # Save multiple large entries
        for i in range(10):
            await temp_memory_store.save("large", f"big_{i}", large_value)
        
        # Should be able to retrieve them
        for i in range(10):
            entry = await temp_memory_store.get("large", f"big_{i}")
            assert entry is not None
            assert len(entry.value) == 100000
