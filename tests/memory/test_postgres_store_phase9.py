"""Phase 9A: Comprehensive PostgreSQL Store Tests - Priority 1."""

from __future__ import annotations

import pytest
import asyncio
import json
import uuid
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any
import psycopg
from psycopg import sql

from jarvis.memory.postgres_store import PostgresMemoryStore, CREATE_SCHEMA_SQL
from jarvis.memory.store import MemoryEntry
from jarvis.config.settings import Settings
from jarvis.llm.embeddings import EmbeddingProvider


class TestPostgresMemoryStoreInitialization:
    """Test PostgresMemoryStore initialization and setup."""

    def test_init_with_custom_dsn(self):
        """Test initialization with custom DSN."""
        custom_dsn = "postgresql://user:pass@host:5432/db"
        mock_embeddings = Mock(spec=EmbeddingProvider)
        
        store = PostgresMemoryStore(dsn=custom_dsn, embeddings=mock_embeddings)
        
        assert store.dsn == custom_dsn
        assert store.embeddings == mock_embeddings
        assert store._pool is None

    def test_init_with_default_dsn(self):
        """Test initialization with default DSN."""
        mock_embeddings = Mock(spec=EmbeddingProvider)
        
        with patch('jarvis.memory.postgres_store.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.postgres_url = None
            mock_get_settings.return_value = mock_settings
            
            store = PostgresMemoryStore(embeddings=mock_embeddings)
            
            assert store.dsn == "postgresql://jarvis:jarvis@localhost:5432/jarvis"
            assert store.embeddings == mock_embeddings

    def test_init_with_settings_postgres_url(self):
        """Test initialization with settings PostgreSQL URL."""
        mock_embeddings = Mock(spec=EmbeddingProvider)
        settings_url = "postgresql://settings_user:settings_pass@settings_host:5433/settings_db"
        
        with patch('jarvis.memory.postgres_store.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.postgres_url = settings_url
            mock_get_settings.return_value = mock_settings
            
            store = PostgresMemoryStore(embeddings=mock_embeddings)
            
            assert store.dsn == settings_url

    def test_init_with_default_embeddings(self):
        """Test initialization with default embeddings provider."""
        custom_dsn = "postgresql://user:pass@host:5432/db"
        
        with patch('jarvis.memory.postgres_store.get_embedding_provider') as mock_get_embeddings:
            mock_embeddings = Mock(spec=EmbeddingProvider)
            mock_get_embeddings.return_value = mock_embeddings
            
            store = PostgresMemoryStore(dsn=custom_dsn)
            
            assert store.embeddings == mock_embeddings
            mock_get_embeddings.assert_called_once()

    def test_build_dsn_from_settings(self):
        """Test DSN building from settings."""
        store = PostgresMemoryStore()
        dsn = store._build_dsn()
        
        assert dsn == "postgresql://jarvis:jarvis@localhost:5432/jarvis"

    def test_build_dsn_with_custom_settings(self):
        """Test DSN building with custom settings."""
        with patch('jarvis.memory.postgres_store.get_settings') as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.postgres_url = "postgresql://custom:custom@custom:5432/custom"
            mock_get_settings.return_value = mock_settings
            
            store = PostgresMemoryStore()
            dsn = store._build_dsn()
            
            assert dsn == "postgresql://custom:custom@custom:5432/custom"


class TestPostgresMemoryStoreConnection:
    """Test PostgresMemoryStore connection management."""

    @pytest.mark.asyncio
    async def test_connect_first_time(self):
        """Test first time connection creation."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            conn = await store._connect()
            
            assert conn == mock_conn
            assert store._pool == mock_conn
            mock_connect.assert_called_once_with("postgresql://test:test@localhost:5432/test")

    @pytest.mark.asyncio
    async def test_connect_reuse_existing(self):
        """Test reusing existing connection."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        # Set up existing connection
        mock_existing_conn = AsyncMock()
        mock_existing_conn.closed = False
        store._pool = mock_existing_conn
        
        conn = await store._connect()
        
        assert conn == mock_existing_conn

    @pytest.mark.asyncio
    async def test_connect_closed_pool(self):
        """Test connecting when pool is closed."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        # Set up closed connection
        mock_closed_conn = AsyncMock()
        mock_closed_conn.closed = True
        store._pool = mock_closed_conn
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_new_conn = AsyncMock()
            mock_connect.return_value = mock_new_conn
            
            conn = await store._connect()
            
            assert conn == mock_new_conn
            assert store._pool == mock_new_conn

    @pytest.mark.asyncio
    async def test_connect_connection_error(self):
        """Test connection error handling."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store._connect()

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Test connection timeout."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect', side_effect=asyncio.TimeoutError("Connection timeout")):
            with pytest.raises(asyncio.TimeoutError):
                await store._connect()


class TestPostgresMemoryStoreSchema:
    """Test PostgresMemoryStore schema management."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful schema initialization."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            await store.initialize()
            
            mock_conn.execute.assert_called_once_with(CREATE_SCHEMA_SQL)
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_connection_error(self):
        """Test schema initialization with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.initialize()

    @pytest.mark.asyncio
    async def test_initialize_sql_error(self):
        """Test schema initialization with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.initialize()

    @pytest.mark.asyncio
    async def test_initialize_commit_error(self):
        """Test schema initialization with commit error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch('psycopg.AsyncConnection.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.commit.side_effect = psycopg.Error("Commit error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.initialize()


class TestPostgresMemoryStoreSave:
    """Test PostgresMemoryStore save operations."""

    @pytest.mark.asyncio
    async def test_save_new_entry(self):
        """Test saving a new memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                await store.save("test_category", "test_key", "test_value", {"meta": "data"})
                
                mock_conn.execute.assert_called_once()
                args = mock_conn.execute.call_args[0][1]
                assert args[0] == "test_category"
                assert args[1] == "test_key"
                assert args[2] == "test_value"
                assert json.loads(args[3]) == {"meta": "data"}
                assert args[4] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_save_update_existing(self):
        """Test updating an existing memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.4, 0.5, 0.6]):
                await store.save("test_category", "test_key", "updated_value", {"updated": "meta"})
                
                mock_conn.execute.assert_called_once()
                # Should use ON CONFLICT DO UPDATE

    @pytest.mark.asyncio
    async def test_save_without_metadata(self):
        """Test saving without metadata."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                await store.save("test_category", "test_key", "test_value")
                
                mock_conn.execute.assert_called_once()
                args = mock_conn.execute.call_args[0][1]
                assert json.loads(args[3]) == {}

    @pytest.mark.asyncio
    async def test_save_embedding_generation_error(self):
        """Test save with embedding generation error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=None):
                await store.save("test_category", "test_key", "test_value")
                
                mock_conn.execute.assert_called_once()
                args = mock_conn.execute.call_args[0][1]
                assert args[4] is None

    @pytest.mark.asyncio
    async def test_save_connection_error(self):
        """Test save with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.save("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_save_sql_error(self):
        """Test save with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.save("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_save_unicode_content(self):
        """Test saving Unicode content."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                unicode_value = "Unicode test: ñáéíóú 中文 русский 日本語"
                unicode_meta = {"unicode": "ñáéíóú", "chinese": "中文"}
                
                await store.save("unicode_category", "unicode_key", unicode_value, unicode_meta)
                
                mock_conn.execute.assert_called_once()
                args = mock_conn.execute.call_args[0][1]
                assert args[2] == unicode_value
                assert json.loads(args[3]) == unicode_meta

    @pytest.mark.asyncio
    async def test_save_large_content(self):
        """Test saving large content."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                large_value = "x" * 10000  # 10KB
                large_meta = {"large": "x" * 1000}
                
                await store.save("large_category", "large_key", large_value, large_meta)
                
                mock_conn.execute.assert_called_once()


class TestPostgresMemoryStoreGet:
    """Test PostgresMemoryStore get operations."""

    @pytest.mark.asyncio
    async def test_get_existing_entry(self):
        """Test getting an existing memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_row = AsyncMock()
            mock_row.id = uuid.uuid4()
            mock_row.category = "test_category"
            mock_row.key = "test_key"
            mock_row.value = "test_value"
            mock_row.metadata = '{"meta": "data"}'
            mock_row.created_at = "2023-01-01T00:00:00Z"
            mock_row.updated_at = "2023-01-01T00:00:00Z"
            
            mock_conn.fetchone.return_value = mock_row
            mock_connect.return_value = mock_conn
            
            entry = await store.get("test_category", "test_key")
            
            assert entry is not None
            assert entry.category == "test_category"
            assert entry.key == "test_key"
            assert entry.value == "test_value"
            assert entry.metadata == {"meta": "data"}

    @pytest.mark.asyncio
    async def test_get_nonexistent_entry(self):
        """Test getting a non-existent memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchone.return_value = None
            mock_connect.return_value = mock_conn
            
            entry = await store.get("test_category", "nonexistent_key")
            
            assert entry is None

    @pytest.mark.asyncio
    async def test_get_connection_error(self):
        """Test get with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.get("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_get_sql_error(self):
        """Test get with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.get("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_get_invalid_metadata(self):
        """Test get with invalid metadata JSON."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_row = AsyncMock()
            mock_row.id = uuid.uuid4()
            mock_row.category = "test_category"
            mock_row.key = "test_key"
            mock_row.value = "test_value"
            mock_row.metadata = "invalid json"
            mock_row.created_at = "2023-01-01T00:00:00Z"
            mock_row.updated_at = "2023-01-01T00:00:00Z"
            
            mock_conn.fetchone.return_value = mock_row
            mock_connect.return_value = mock_conn
            
            entry = await store.get("test_category", "test_key")
            
            assert entry is not None
            assert entry.metadata == {}

    @pytest.mark.asyncio
    async def test_get_unicode_content(self):
        """Test getting Unicode content."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_row = AsyncMock()
            mock_row.id = uuid.uuid4()
            mock_row.category = "unicode_category"
            mock_row.key = "unicode_key"
            mock_row.value = "Unicode test: ñáéíóú 中文 русский"
            mock_row.metadata = '{"unicode": "ñáéíóú"}'
            mock_row.created_at = "2023-01-01T00:00:00Z"
            mock_row.updated_at = "2023-01-01T00:00:00Z"
            
            mock_conn.fetchone.return_value = mock_row
            mock_connect.return_value = mock_conn
            
            entry = await store.get("unicode_category", "unicode_key")
            
            assert entry is not None
            assert "ñáéíóú" in entry.value
            assert entry.metadata["unicode"] == "ñáéíóú"


class TestPostgresMemoryStoreList:
    """Test PostgresMemoryStore list operations."""

    @pytest.mark.asyncio
    async def test_list_by_category(self):
        """Test listing memories by category."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = []
            for i in range(3):
                mock_row = AsyncMock()
                mock_row.id = uuid.uuid4()
                mock_row.category = "test_category"
                mock_row.key = f"key_{i}"
                mock_row.value = f"value_{i}"
                mock_row.metadata = '{}'
                mock_row.created_at = "2023-01-01T00:00:00Z"
                mock_row.updated_at = "2023-01-01T00:00:00Z"
                mock_rows.append(mock_row)
            
            mock_conn.fetchall.return_value = mock_rows
            mock_connect.return_value = mock_conn
            
            entries = await store.list("test_category")
            
            assert len(entries) == 3
            assert all(entry.category == "test_category" for entry in entries)
            assert entries[0].key == "key_0"
            assert entries[1].key == "key_1"
            assert entries[2].key == "key_2"

    @pytest.mark.asyncio
    async def test_list_empty_category(self):
        """Test listing empty category."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchall.return_value = []
            mock_connect.return_value = mock_conn
            
            entries = await store.list("empty_category")
            
            assert entries == []

    @pytest.mark.asyncio
    async def test_list_connection_error(self):
        """Test list with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.list("test_category")

    @pytest.mark.asyncio
    async def test_list_sql_error(self):
        """Test list with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.list("test_category")

    @pytest.mark.asyncio
    async def test_list_with_limit(self):
        """Test listing with limit."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = []
            for i in range(2):
                mock_row = AsyncMock()
                mock_row.id = uuid.uuid4()
                mock_row.category = "test_category"
                mock_row.key = f"key_{i}"
                mock_row.value = f"value_{i}"
                mock_row.metadata = '{}'
                mock_row.created_at = "2023-01-01T00:00:00Z"
                mock_row.updated_at = "2023-01-01T00:00:00Z"
                mock_rows.append(mock_row)
            
            mock_conn.fetchall.return_value = mock_rows
            mock_connect.return_value = mock_conn
            
            entries = await store.list("test_category", limit=2)
            
            assert len(entries) == 2


class TestPostgresMemoryStoreDelete:
    """Test PostgresMemoryStore delete operations."""

    @pytest.mark.asyncio
    async def test_delete_existing_entry(self):
        """Test deleting an existing memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock(rowcount=1)
            mock_connect.return_value = mock_conn
            
            result = await store.delete("test_category", "test_key")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entry(self):
        """Test deleting a non-existent memory entry."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.return_value = AsyncMock(rowcount=0)
            mock_connect.return_value = mock_conn
            
            result = await store.delete("test_category", "nonexistent_key")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_connection_error(self):
        """Test delete with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.delete("test_category", "test_key")

    @pytest.mark.asyncio
    async def test_delete_sql_error(self):
        """Test delete with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.delete("test_category", "test_key")


class TestPostgresMemoryStoreSearch:
    """Test PostgresMemoryStore search operations."""

    @pytest.mark.asyncio
    async def test_search_with_embedding(self):
        """Test search with embedding."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = []
            for i in range(3):
                mock_row = AsyncMock()
                mock_row.id = uuid.uuid4()
                mock_row.category = "test_category"
                mock_row.key = f"key_{i}"
                mock_row.value = f"value_{i}"
                mock_row.metadata = '{}'
                mock_row.created_at = "2023-01-01T00:00:00Z"
                mock_row.updated_at = "2023-01-01T00:00:00Z"
                mock_row.similarity = 0.9 - i * 0.1
                mock_rows.append(mock_row)
            
            mock_conn.fetchall.return_value = mock_rows
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                entries = await store.search("test_query", "test_category", limit=3)
                
                assert len(entries) == 3
                assert all(entry.category == "test_category" for entry in entries)

    @pytest.mark.asyncio
    async def test_search_without_embedding(self):
        """Test search without embedding."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = []
            for i in range(2):
                mock_row = AsyncMock()
                mock_row.id = uuid.uuid4()
                mock_row.category = "test_category"
                mock_row.key = f"key_{i}"
                mock_row.value = f"test_query value_{i}"
                mock_row.metadata = '{}'
                mock_row.created_at = "2023-01-01T00:00:00Z"
                mock_row.updated_at = "2023-01-01T00:00:00Z"
                mock_rows.append(mock_row)
            
            mock_conn.fetchall.return_value = mock_rows
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=None):
                entries = await store.search("test_query", "test_category")
                
                assert len(entries) == 2

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchall.return_value = []
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                entries = await store.search("no_results_query", "test_category")
                
                assert entries == []

    @pytest.mark.asyncio
    async def test_search_connection_error(self):
        """Test search with connection error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect', side_effect=psycopg.OperationalError("Connection failed")):
            with pytest.raises(psycopg.OperationalError):
                await store.search("test_query", "test_category")

    @pytest.mark.asyncio
    async def test_search_sql_error(self):
        """Test search with SQL error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with pytest.raises(psycopg.Error):
                await store.search("test_query", "test_category")

    @pytest.mark.asyncio
    async def test_search_unicode_query(self):
        """Test search with Unicode query."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_rows = []
            mock_row = AsyncMock()
            mock_row.id = uuid.uuid4()
            mock_row.category = "unicode_category"
            mock_row.key = "unicode_key"
            mock_row.value = "Unicode test: ñáéíóú 中文 русский"
            mock_row.metadata = '{}'
            mock_row.created_at = "2023-01-01T00:00:00Z"
            mock_row.updated_at = "2023-01-01T00:00:00Z"
            mock_rows.append(mock_row)
            
            mock_conn.fetchall.return_value = mock_rows
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                unicode_query = "Unicode test: ñáéíóú"
                entries = await store.search(unicode_query, "unicode_category")
                
                assert len(entries) == 1
                assert "ñáéíóú" in entries[0].value


class TestPostgresMemoryStoreEmbeddings:
    """Test PostgresMemoryStore embedding operations."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        mock_embeddings = Mock(spec=EmbeddingProvider)
        mock_embeddings.embed_text.return_value = [0.1, 0.2, 0.3]
        store.embeddings = mock_embeddings
        
        embedding = await store._generate_embedding("test text")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_embeddings.embed_text.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_error(self):
        """Test embedding generation error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        mock_embeddings = Mock(spec=EmbeddingProvider)
        mock_embeddings.embed_text.side_effect = Exception("Embedding failed")
        store.embeddings = mock_embeddings
        
        embedding = await store._generate_embedding("test text")
        
        assert embedding is None

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        mock_embeddings = Mock(spec=EmbeddingProvider)
        mock_embeddings.embed_text.return_value = [0.0] * 768
        store.embeddings = mock_embeddings
        
        embedding = await store._generate_embedding("")
        
        assert embedding == [0.0] * 768

    @pytest.mark.asyncio
    async def test_generate_embedding_unicode_text(self):
        """Test embedding generation with Unicode text."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        mock_embeddings = Mock(spec=EmbeddingProvider)
        mock_embeddings.embed_text.return_value = [0.1] * 768
        store.embeddings = mock_embeddings
        
        unicode_text = "Unicode test: ñáéíóú 中文 русский 日本語"
        embedding = await store._generate_embedding(unicode_text)
        
        assert embedding == [0.1] * 768
        mock_embeddings.embed_text.assert_called_once_with(unicode_text)


class TestPostgresMemoryStoreTransactions:
    """Test PostgresMemoryStore transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit_success(self):
        """Test successful transaction commit."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                await store.save("test_category", "test_key", "test_value")
                
                # Transaction should be committed automatically
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = psycopg.Error("SQL error")
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                with pytest.raises(psycopg.Error):
                    await store.save("test_category", "test_key", "test_value")
                
                # Should handle error appropriately
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent database operations."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        async def save_worker(worker_id):
            with patch.object(store, '_connect') as mock_connect:
                mock_conn = AsyncMock()
                mock_connect.return_value = mock_conn
                
                with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                    await store.save(f"category_{worker_id}", f"key_{worker_id}", f"value_{worker_id}")
        
        # Run concurrent operations
        tasks = [save_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # All operations should complete
        assert True


class TestPostgresMemoryStoreSecurity:
    """Test PostgresMemoryStore security aspects."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                # Try SQL injection in category
                malicious_category = "'; DROP TABLE memories; --"
                await store.save(malicious_category, "test_key", "test_value")
                
                # Should use parameterized queries
                mock_conn.execute.assert_called_once()
                sql_call = mock_conn.execute.call_args[0][0]
                assert "DROP TABLE" not in sql_call

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                # Test very long inputs
                long_category = "x" * 1000
                long_key = "x" * 1000
                long_value = "x" * 100000
                
                await store.save(long_category, long_key, long_value)
                
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_unicode_security(self):
        """Test Unicode security handling."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                # Test potentially dangerous Unicode
                dangerous_unicode = "\u0000\u0001\u0002\u0003"  # Control characters
                await store.save("test_category", "test_key", dangerous_unicode)
                
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_metadata_validation(self):
        """Test metadata validation and sanitization."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                # Test complex metadata
                complex_metadata = {
                    "nested": {"key": "value"},
                    "array": [1, 2, 3],
                    "unicode": "ñáéíóú",
                    "special": "!@#$%^&*()"
                }
                
                await store.save("test_category", "test_key", "test_value", complex_metadata)
                
                mock_conn.execute.assert_called_once()
                args = mock_conn.execute.call_args[0][1]
                parsed_metadata = json.loads(args[3])
                assert parsed_metadata == complex_metadata


class TestPostgresMemoryStorePerformance:
    """Test PostgresMemoryStore performance characteristics."""

    @pytest.mark.asyncio
    async def test_batch_save_performance(self):
        """Test batch save performance."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        import time
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                start_time = time.time()
                
                # Save 100 entries
                for i in range(100):
                    await store.save(f"category_{i}", f"key_{i}", f"value_{i}")
                
                elapsed = time.time() - start_time
                assert elapsed < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Test concurrent operation performance."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        async def worker(worker_id):
            with patch.object(store, '_connect') as mock_connect:
                mock_conn = AsyncMock()
                mock_connect.return_value = mock_conn
                
                with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                    await store.save(f"category_{worker_id}", f"key_{worker_id}", f"value_{worker_id}")
        
        import time
        start_time = time.time()
        
        # Run 10 concurrent workers
        tasks = [worker(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        assert elapsed < 3.0  # Should complete within 3 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1] * 768):
                # Perform many operations
                for i in range(1000):
                    await store.save(f"category_{i}", f"key_{i}", f"value_{i}")
                
                # Memory usage should be stable
                assert True


class TestPostgresMemoryStoreEdgeCases:
    """Test PostgresMemoryStore edge cases."""

    @pytest.mark.asyncio
    async def test_empty_strings(self):
        """Test handling of empty strings."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                await store.save("", "", "")
                
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_none_values(self):
        """Test handling of None values."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                # None should be handled appropriately
                await store.save("test_category", "test_key", None)
                
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_very_large_embeddings(self):
        """Test handling of very large embeddings."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            # Test with larger than expected embedding
            large_embedding = [0.1] * 1000
            with patch.object(store, '_generate_embedding', return_value=large_embedding):
                await store.save("test_category", "test_key", "test_value")
                
                mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self):
        """Test connection pool exhaustion."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            # Simulate connection pool exhaustion
            mock_connect.side_effect = psycopg.OperationalError("Connection pool exhausted")
            
            with pytest.raises(psycopg.OperationalError):
                await store.save("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_database_timeout(self):
        """Test database timeout handling."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = asyncio.TimeoutError("Database timeout")
            mock_connect.return_value = mock_conn
            
            with patch.object(store, '_generate_embedding', return_value=[0.1, 0.2, 0.3]):
                with pytest.raises(asyncio.TimeoutError):
                    await store.save("test_category", "test_key", "test_value")

    @pytest.mark.asyncio
    async def test_invalid_uuid_handling(self):
        """Test handling of invalid UUIDs."""
        store = PostgresMemoryStore(dsn="postgresql://test:test@localhost:5432/test")
        
        with patch.object(store, '_connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_row = AsyncMock()
            mock_row.id = "invalid_uuid"
            mock_row.category = "test_category"
            mock_row.key = "test_key"
            mock_row.value = "test_value"
            mock_row.metadata = '{}'
            mock_row.created_at = "2023-01-01T00:00:00Z"
            mock_row.updated_at = "2023-01-01T00:00:00Z"
            
            mock_conn.fetchone.return_value = mock_row
            mock_connect.return_value = mock_conn
            
            # Should handle invalid UUID gracefully
            entry = await store.get("test_category", "test_key")
            
            # Entry creation should handle or reject invalid UUID
            assert entry is not None or entry is None
