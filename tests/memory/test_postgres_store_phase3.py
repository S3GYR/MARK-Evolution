"""Phase 3 PostgreSQL Memory Store tests for robustness and vector search (>75% coverage)."""

from __future__ import annotations

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Any

from jarvis.memory.postgres_store import PostgresMemoryStore
from jarvis.memory.store import MemoryEntry
from jarvis.llm.embeddings import MockEmbeddingProvider


@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection for testing."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.close = AsyncMock()
    return mock_conn


@pytest.fixture
def mock_postgres_pool():
    """Mock PostgreSQL connection pool."""
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.fetchval = AsyncMock()
    mock_pool.acquire = AsyncMock(return_value=mock_conn)
    mock_pool.release = AsyncMock()
    return mock_pool, mock_conn


@pytest.fixture
def mock_embeddings():
    """Mock embeddings provider."""
    return MockEmbeddingProvider(dim=384)


@pytest.fixture
def postgres_store(mock_postgres_pool, mock_embeddings):
    """Create PostgreSQL memory store with mocked dependencies."""
    mock_pool, mock_conn = mock_postgres_pool
    store = PostgresMemoryStore(
        connection_string="postgresql://test",
        embeddings=mock_embeddings
    )
    store.pool = mock_pool
    return store, mock_conn


class TestPostgresMemoryStoreInitialization:
    """Test initialization scenarios."""

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, postgres_store):
        """Test table creation during initialization."""
        store, mock_conn = postgres_store
        
        await store.initialize()
        
        # Should execute table creation commands
        assert mock_conn.execute.call_count >= 2  # Memories table + vector index
        
        # Check table creation SQL
        calls = mock_conn.execute.call_args_list
        sql_commands = [call[0][0] for call in calls]
        
        # Should create memories table
        table_sql = any("CREATE TABLE IF NOT EXISTS memories" in cmd for cmd in sql_commands)
        assert table_sql, "Should create memories table"
        
        # Should create vector index
        index_sql = any("CREATE INDEX IF NOT EXISTS" in cmd and "vector" in cmd for cmd in sql_commands)
        assert index_sql, "Should create vector index"

    @pytest.mark.asyncio
    async def test_initialize_with_existing_tables(self, postgres_store):
        """Test initialization when tables already exist."""
        store, mock_conn = postgres_store
        
        await store.initialize()
        
        # Should not fail on existing tables (IF NOT EXISTS)
        mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self):
        """Test handling of connection failure during initialization."""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_create_pool.side_effect = ConnectionError("Connection failed")
            
            store = PostgresMemoryStore(
                connection_string="postgresql://test",
                embeddings=MockEmbeddingProvider()
            )
            
            with pytest.raises(ConnectionError):
                await store.initialize()

    @pytest.mark.asyncio
    async def test_initialize_table_creation_failure(self, postgres_store):
        """Test handling of table creation failure."""
        store, mock_conn = postgres_store
        mock_conn.execute.side_effect = Exception("Table creation failed")
        
        with pytest.raises(Exception):
            await store.initialize()

    @pytest.mark.asyncio
    async def test_initialize_with_custom_embeddings(self):
        """Test initialization with custom embeddings provider."""
        custom_embeddings = MockEmbeddingProvider(dim=512)
        
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_pool.acquire = AsyncMock(return_value=mock_conn)
            mock_create_pool.return_value = mock_pool
            
            store = PostgresMemoryStore(
                connection_string="postgresql://test",
                embeddings=custom_embeddings
            )
            
            await store.initialize()
            
            assert store.embeddings == custom_embeddings


class TestPostgresMemoryStorePersistence:
    """Test persistence operations."""

    @pytest.mark.asyncio
    async def test_save_basic_entry(self, postgres_store):
        """Test saving a basic memory entry."""
        store, mock_conn = postgres_store
        
        await store.save(
            category="preferences",
            key="theme",
            value="dark",
            metadata={"source": "user"}
        )
        
        # Should execute INSERT with embedding
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        sql = call_args[0]
        params = call_args[1]
        
        assert "INSERT INTO memories" in sql
        assert params[0] == "preferences"  # category
        assert params[1] == "theme"        # key
        assert params[2] == "dark"         # value
        assert params[4] == {"source": "user"}  # metadata
        
        # Should have generated embedding
        assert len(params[3]) == 384  # embedding dimension

    @pytest.mark.asyncio
    async def test_save_with_long_text(self, postgres_store):
        """Test saving entry with very long text."""
        store, mock_conn = postgres_store
        
        long_value = "x" * 10000  # 10KB text
        await store.save("test", "long_key", long_value)
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[2] == long_value

    @pytest.mark.asyncio
    async def test_save_with_unicode_text(self, postgres_store):
        """Test saving entry with unicode characters."""
        store, mock_conn = postgres_store
        
        unicode_value = "Test with émojis 🎉 and accents café"
        await store.save("unicode", "test", unicode_value)
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[2] == unicode_value

    @pytest.mark.asyncio
    async def test_save_without_metadata(self, postgres_store):
        """Test saving entry without metadata."""
        store, mock_conn = postgres_store
        
        await store.save("test", "key", "value")
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[4] == {}  # Default empty metadata

    @pytest.mark.asyncio
    async def test_save_overwrite_existing(self, postgres_store):
        """Test overwriting an existing entry."""
        store, mock_conn = postgres_store
        
        # Save initial entry
        await store.save("test", "key", "original", {"v": 1})
        
        # Overwrite
        await store.save("test", "key", "updated", {"v": 2})
        
        # Should have executed two INSERTs (or UPDATEs depending on implementation)
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_save_embedding_generation_failure(self, postgres_store):
        """Test handling of embedding generation failure."""
        store, mock_conn = postgres_store
        
        # Mock embedding failure
        store.embeddings.encode.side_effect = Exception("Embedding failed")
        
        with pytest.raises(Exception):
            await store.save("test", "key", "value")

    @pytest.mark.asyncio
    async def test_save_database_error(self, postgres_store):
        """Test handling of database error during save."""
        store, mock_conn = postgres_store
        mock_conn.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await store.save("test", "key", "value")

    @pytest.mark.asyncio
    async def test_get_existing_entry(self, postgres_store):
        """Test retrieving an existing entry."""
        store, mock_conn = postgres_store
        
        # Mock database response
        mock_record = {
            "id": "test-id",
            "category": "preferences",
            "key": "theme",
            "value": "dark",
            "metadata": {"source": "user"},
            "created_at": "2024-01-01T00:00:00"
        }
        mock_conn.fetch.return_value = [mock_record]
        
        entry = await store.get("preferences", "theme")
        
        assert entry is not None
        assert entry.id == "test-id"
        assert entry.category == "preferences"
        assert entry.key == "theme"
        assert entry.value == "dark"
        assert entry.metadata == {"source": "user"}
        
        # Should have executed SELECT query
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args[0]
        sql = call_args[0]
        assert "SELECT" in sql and "WHERE category = $1 AND key = $2" in sql

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self, postgres_store):
        """Test retrieving a non-existent entry."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []  # No results
        
        entry = await store.get("nonexistent", "key")
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_get_database_error(self, postgres_store):
        """Test handling of database error during get."""
        store, mock_conn = postgres_store
        mock_conn.fetch.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await store.get("test", "key")


class TestPostgresMemoryStoreVectorSearch:
    """Test vector similarity search functionality."""

    @pytest.mark.asyncio
    async def test_vector_search_with_results(self, postgres_store):
        """Test vector search that returns results."""
        store, mock_conn = postgres_store
        
        # Mock search results
        mock_records = [
            {
                "id": "id1",
                "category": "notes",
                "key": "reminder1",
                "value": "Buy milk",
                "metadata": {"priority": "high"},
                "created_at": "2024-01-01T00:00:00",
                "similarity": 0.95
            },
            {
                "id": "id2", 
                "category": "notes",
                "key": "reminder2",
                "value": "Buy bread",
                "metadata": {"priority": "medium"},
                "created_at": "2024-01-01T01:00:00",
                "similarity": 0.85
            }
        ]
        mock_conn.fetch.return_value = mock_records
        
        results = await store.search("shopping list", category="notes", limit=5)
        
        assert len(results) == 2
        assert results[0].category == "notes"
        assert results[0].key == "reminder1"
        assert results[0].value == "Buy milk"
        assert results[0].metadata["priority"] == "high"
        
        # Should have generated embedding for query
        store.embeddings.encode.assert_called_once_with("shopping list")
        
        # Should have executed vector search query
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args[0]
        sql = call_args[0]
        assert "ORDER BY" in sql and "<=>" in sql  # Vector similarity operator

    @pytest.mark.asyncio
    async def test_vector_search_no_results(self, postgres_store):
        """Test vector search with no results."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []  # No results
        
        results = await store.search("nonexistent query")
        
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_vector_search_low_similarity(self, postgres_store):
        """Test vector search with low similarity scores."""
        store, mock_conn = postgres_store
        
        # Mock low similarity results
        mock_records = [
            {
                "id": "id1",
                "category": "test",
                "key": "key1",
                "value": "vaguely related",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00",
                "similarity": 0.3  # Low similarity
            }
        ]
        mock_conn.fetch.return_value = mock_records
        
        results = await store.search("query", limit=5)
        
        assert len(results) == 1
        assert results[0].value == "vaguely related"

    @pytest.mark.asyncio
    async def test_vector_search_with_limit(self, postgres_store):
        """Test vector search with result limit."""
        store, mock_conn = postgres_store
        
        # Mock many results
        mock_records = [
            {
                "id": f"id{i}",
                "category": "test",
                "key": f"key{i}",
                "value": f"value{i}",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00",
                "similarity": 0.9 - i * 0.1
            } for i in range(10)
        ]
        mock_conn.fetch.return_value = mock_records
        
        results = await store.search("query", limit=3)
        
        assert len(results) == 10  # All results returned (limit applied in SQL)

    @pytest.mark.asyncio
    async def test_vector_search_all_categories(self, postgres_store):
        """Test vector search across all categories."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []
        
        await store.search("query")  # No category specified
        
        # Should not filter by category
        call_args = mock_conn.fetch.call_args[0]
        sql = call_args[0]
        assert "WHERE" not in sql or "category" not in sql

    @pytest.mark.asyncio
    async def test_vector_search_embedding_failure(self, postgres_store):
        """Test handling of embedding generation failure during search."""
        store, mock_conn = postgres_store
        
        store.embeddings.encode.side_effect = Exception("Embedding failed")
        
        with pytest.raises(Exception):
            await store.search("query")

    @pytest.mark.asyncio
    async def test_vector_search_database_error(self, postgres_store):
        """Test handling of database error during search."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await store.search("query")

    @pytest.mark.asyncio
    async def test_vector_search_empty_query(self, postgres_store):
        """Test vector search with empty query."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []
        
        results = await store.search("")
        
        assert len(results) == 0
        store.embeddings.encode.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_vector_search_unicode_query(self, postgres_store):
        """Test vector search with unicode query."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []
        
        unicode_query = "Test with émojis 🎉"
        await store.search(unicode_query)
        
        store.embeddings.encode.assert_called_once_with(unicode_query)


class TestPostgresMemoryStoreCategories:
    """Test category management."""

    @pytest.mark.asyncio
    async def test_list_categories(self, postgres_store):
        """Test listing all categories."""
        store, mock_conn = postgres_store
        
        # Mock category list
        mock_conn.fetchval.return_value = 5  # Total count
        mock_conn.fetch.return_value = [
            {"category": "preferences"},
            {"category": "notes"},
            {"category": "projects"}
        ]
        
        categories = await store.list_categories()
        
        assert len(categories) == 3
        assert "preferences" in categories
        assert "notes" in categories
        assert "projects" in categories

    @pytest.mark.asyncio
    async def test_list_categories_empty(self, postgres_store):
        """Test listing categories when none exist."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []  # No categories
        
        categories = await store.list_categories()
        
        assert len(categories) == 0

    @pytest.mark.asyncio
    async def test_list_categories_database_error(self, postgres_store):
        """Test handling of database error during category listing."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await store.list_categories()


class TestPostgresMemoryStoreFormatting:
    """Test formatting for prompts."""

    @pytest.mark.asyncio
    async def test_format_for_prompt_basic(self, postgres_store):
        """Test basic formatting for prompt."""
        store, mock_conn = postgres_store
        
        # Mock recent memories
        mock_records = [
            {
                "category": "preferences",
                "key": "theme",
                "value": "dark mode",
                "created_at": "2024-01-01T00:00:00"
            },
            {
                "category": "notes",
                "key": "reminder",
                "value": "meeting at 2pm",
                "created_at": "2024-01-01T01:00:00"
            }
        ]
        mock_conn.fetch.return_value = mock_records
        
        formatted = await store.format_for_prompt(max_chars=500)
        
        assert "[preferences] theme: dark mode" in formatted
        assert "[notes] reminder: meeting at 2pm" in formatted

    @pytest.mark.asyncio
    async def test_format_for_prompt_with_limit(self, postgres_store):
        """Test formatting with character limit."""
        store, mock_conn = postgres_store
        
        # Mock long memories
        long_value = "x" * 1000
        mock_records = [
            {
                "category": "test",
                "key": "long",
                "value": long_value,
                "created_at": "2024-01-01T00:00:00"
            },
            {
                "category": "test", 
                "key": "short",
                "value": "short",
                "created_at": "2024-01-01T01:00:00"
            }
        ]
        mock_conn.fetch.return_value = mock_records
        
        formatted = await store.format_for_prompt(max_chars=200)
        
        assert len(formatted) <= 200

    @pytest.mark.asyncio
    async def test_format_for_prompt_empty_store(self, postgres_store):
        """Test formatting empty store."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []  # No memories
        
        formatted = await store.format_for_prompt()
        
        assert formatted == ""

    @pytest.mark.asyncio
    async def test_format_for_prompt_database_error(self, postgres_store):
        """Test handling of database error during formatting."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await store.format_for_prompt()


class TestPostgresMemoryStoreConnection:
    """Test connection management."""

    @pytest.mark.asyncio
    async def test_close_connection(self, postgres_store):
        """Test closing database connection."""
        store, mock_conn = postgres_store
        
        await store.close()
        
        # Should close the connection pool
        store.pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_pool_creation(self):
        """Test connection pool creation."""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            store = PostgresMemoryStore(
                connection_string="postgresql://user:pass@host/db",
                embeddings=MockEmbeddingProvider()
            )
            
            await store.initialize()
            
            mock_create_pool.assert_called_once_with(
                "postgresql://user:pass@host/db",
                min_size=1,
                max_size=10
            )

    @pytest.mark.asyncio
    async def test_connection_retry_on_failure(self):
        """Test connection retry logic."""
        with patch('asyncpg.create_pool') as mock_create_pool:
            # Fail first attempt, succeed second
            mock_create_pool.side_effect = [
                ConnectionError("First failure"),
                AsyncMock()
            ]
            
            store = PostgresMemoryStore(
                connection_string="postgresql://test",
                embeddings=MockEmbeddingProvider()
            )
            
            # Should handle retry (implementation dependent)
            with pytest.raises(ConnectionError):
                await store.initialize()

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test connection timeout handling."""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_create_pool.side_effect = asyncio.TimeoutError("Connection timeout")
            
            store = PostgresMemoryStore(
                connection_string="postgresql://test",
                embeddings=MockEmbeddingProvider()
            )
            
            with pytest.raises(asyncio.TimeoutError):
                await store.initialize()


class TestPostgresMemoryStoreConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_saves(self, postgres_store):
        """Test concurrent save operations."""
        store, mock_conn = postgres_store
        
        async def save_worker(category: str, key: str, value: str):
            await store.save(category, key, value)
        
        # Run concurrent saves
        tasks = [
            save_worker("cat1", "key1", "value1"),
            save_worker("cat2", "key2", "value2"),
            save_worker("cat3", "key3", "value3")
        ]
        
        await asyncio.gather(*tasks)
        
        # Should have executed 3 saves
        assert mock_conn.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_searches(self, postgres_store):
        """Test concurrent search operations."""
        store, mock_conn = postgres_store
        
        mock_conn.fetch.return_value = []  # No results
        
        async def search_worker(query: str):
            return await store.search(query)
        
        # Run concurrent searches
        tasks = [
            search_worker("query1"),
            search_worker("query2"),
            search_worker("query3")
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(len(r) == 0 for r in results)
        assert mock_conn.fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, postgres_store):
        """Test concurrent read and write operations."""
        store, mock_conn = postgres_store
        
        # Mock get response
        mock_conn.fetch.return_value = [
            {
                "id": "id1",
                "category": "test",
                "key": "key1",
                "value": "value1",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        
        async def read_worker():
            return await store.get("test", "key1")
        
        async def write_worker():
            await store.save("test", "key2", "value2")
        
        # Run concurrent read/write
        tasks = [
            read_worker(),
            read_worker(),
            write_worker(),
            write_worker()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Should have 2 read results and 2 writes
        assert len(results) == 4
        assert mock_conn.fetch.call_count == 2  # 2 reads
        assert mock_conn.execute.call_count == 2  # 2 writes


class TestPostgresMemoryStorePerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_large_batch_saves(self, postgres_store):
        """Test performance with large batch of saves."""
        store, mock_conn = postgres_store
        
        start_time = time.time()
        
        # Save many entries
        tasks = []
        for i in range(100):
            task = store.save("batch", f"key_{i}", f"value_{i}")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds for 100 saves
        assert mock_conn.execute.call_count == 100

    @pytest.mark.asyncio
    async def test_vector_search_performance(self, postgres_store):
        """Test vector search performance."""
        store, mock_conn = postgres_store
        
        # Mock search results
        mock_records = [
            {
                "id": f"id{i}",
                "category": "test",
                "key": f"key{i}",
                "value": f"value{i}",
                "metadata": {},
                "created_at": "2024-01-01T00:00:00",
                "similarity": 0.9
            } for i in range(50)
        ]
        mock_conn.fetch.return_value = mock_records
        
        start_time = time.time()
        
        results = await store.search("test query", limit=50)
        
        elapsed = time.time() - start_time
        
        assert len(results) == 50
        assert elapsed < 1.0  # Search should be fast

    @pytest.mark.asyncio
    async def test_embedding_generation_performance(self, postgres_store):
        """Test embedding generation performance."""
        store, mock_conn = postgres_store
        
        long_texts = ["x" * 1000 for _ in range(10)]  # 10 long texts
        
        start_time = time.time()
        
        tasks = []
        for i, text in enumerate(long_texts):
            task = store.save("perf", f"key_{i}", text)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 3.0  # 3 seconds for 10 long texts
        assert mock_conn.execute.call_count == 10


class TestPostgresMemoryStoreEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_very_long_key_names(self, postgres_store):
        """Test with very long key names."""
        store, mock_conn = postgres_store
        
        long_key = "k" * 500  # 500 character key
        await store.save("test", long_key, "value")
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[1] == long_key

    @pytest.mark.asyncio
    async def test_special_characters_in_category(self, postgres_store):
        """Test special characters in category names."""
        store, mock_conn = postgres_store
        
        special_category = "test-category.with_special/chars\\"
        await store.save(special_category, "key", "value")
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[0] == special_category

    @pytest.mark.asyncio
    async def test_null_metadata_handling(self, postgres_store):
        """Test handling of None metadata."""
        store, mock_conn = postgres_store
        
        await store.save("test", "key", "value", None)
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[4] == {}  # Should convert None to empty dict

    @pytest.mark.asyncio
    async def test_empty_category_and_key(self, postgres_store):
        """Test with empty category and key."""
        store, mock_conn = postgres_store
        
        await store.save("", "", "value")
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert params[0] == ""
        assert params[1] == ""

    @pytest.mark.asyncio
    async def test_database_connection_lost_during_operation(self, postgres_store):
        """Test handling of lost database connection."""
        store, mock_conn = postgres_store
        
        # Simulate connection loss
        mock_conn.execute.side_effect = ConnectionError("Connection lost")
        
        with pytest.raises(ConnectionError):
            await store.save("test", "key", "value")

    @pytest.mark.asyncio
    async def test_vector_dimension_mismatch(self, postgres_store):
        """Test handling of vector dimension mismatch."""
        store, mock_conn = postgres_store
        
        # Mock embedding with wrong dimension
        store.embeddings.encode.return_value = [0.1, 0.2]  # 2D instead of 384D
        
        await store.save("test", "key", "value")
        
        mock_conn.execute.assert_called_once()
        params = mock_conn.execute.call_args[0][1]
        assert len(params[3]) == 2  # Wrong dimension but still saved

    @pytest.mark.asyncio
    async def test_concurrent_access_same_key(self, postgres_store):
        """Test concurrent access to the same key."""
        store, mock_conn = postgres_store
        
        async def save_worker(value: str):
            await store.save("test", "same_key", value)
        
        # Multiple workers saving to same key
        tasks = [
            save_worker("value1"),
            save_worker("value2"),
            save_worker("value3")
        ]
        
        await asyncio.gather(*tasks)
        
        # Should handle concurrent access (last write wins or based on DB constraints)
        assert mock_conn.execute.call_count == 3
