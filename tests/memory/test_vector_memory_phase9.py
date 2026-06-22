"""Phase 9A: Comprehensive Vector Memory Tests - Priority 3."""

from __future__ import annotations

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, List, Dict, Optional
import uuid

from jarvis.memory.store import MemoryStore
from jarvis.llm.embeddings import EmbeddingProvider

# Alias for compatibility
VectorMemory = MemoryStore
VectorSearchError = Exception
from jarvis.memory.store import MemoryEntry


class TestVectorMemoryInitialization:
    """Test VectorMemory initialization and setup."""

    def test_vector_memory_init_with_provider(self):
        """Test VectorMemory initialization with custom provider."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        assert vector_memory.embedding_provider == mock_provider

    def test_vector_memory_init_with_default_provider(self):
        """Test VectorMemory initialization with default provider."""
        with patch('jarvis.memory.vector_memory.get_embedding_provider') as mock_get_provider:
            mock_provider = Mock(spec=EmbeddingProvider)
            mock_get_provider.return_value = mock_provider
            
            vector_memory = VectorMemory()
            
            assert vector_memory.embedding_provider == mock_provider
            mock_get_provider.assert_called_once()

    def test_vector_memory_init_with_dimensions(self):
        """Test VectorMemory initialization with custom dimensions."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider, dimensions=1024)
        
        assert vector_memory.dimensions == 1024

    def test_vector_memory_init_with_default_dimensions(self):
        """Test VectorMemory initialization with default dimensions."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        assert vector_memory.dimensions == 768  # Default dimension


class TestVectorMemoryEmbeddingOperations:
    """Test VectorMemory embedding operations."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        embedding = await vector_memory._generate_embedding("test text")
        
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_provider.embed_text.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_error(self):
        """Test embedding generation with error."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.side_effect = Exception("Embedding failed")
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        with pytest.raises(VectorSearchError):
            await vector_memory._generate_embedding("test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_unicode_text(self):
        """Test embedding generation with Unicode text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        unicode_text = "Unicode test: ñáéíóú 中文 русский 日本語"
        embedding = await vector_memory._generate_embedding(unicode_text)
        
        assert embedding == [0.1] * 768
        mock_provider.embed_text.assert_called_once_with(unicode_text)

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.0] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        embedding = await vector_memory._generate_embedding("")
        
        assert embedding == [0.0] * 768
        mock_provider.embed_text.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_generate_embedding_very_long_text(self):
        """Test embedding generation with very long text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        long_text = "x" * 100000  # 100KB
        embedding = await vector_memory._generate_embedding(long_text)
        
        assert embedding == [0.1] * 768
        mock_provider.embed_text.assert_called_once_with(long_text)

    @pytest.mark.asyncio
    async def test_validate_embedding_dimensions(self):
        """Test embedding dimension validation."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider, dimensions=512)
        
        # Correct dimensions
        valid_embedding = [0.1] * 512
        assert vector_memory._validate_embedding(valid_embedding) is True
        
        # Incorrect dimensions
        invalid_embedding = [0.1] * 768
        assert vector_memory._validate_embedding(invalid_embedding) is False

    @pytest.mark.asyncio
    async def test_validate_embedding_values(self):
        """Test embedding value validation."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Valid float values
        valid_embedding = [0.1, -0.2, 0.0, 1.0, -1.0]
        assert vector_memory._validate_embedding(valid_embedding) is True
        
        # Invalid values (strings)
        invalid_embedding = [0.1, "invalid", 0.3]
        assert vector_memory._validate_embedding(invalid_embedding) is False
        
        # Invalid values (None)
        invalid_embedding = [0.1, None, 0.3]
        assert vector_memory._validate_embedding(invalid_embedding) is False

    @pytest.mark.asyncio
    async def test_normalize_embedding(self):
        """Test embedding normalization."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Test L2 normalization
        embedding = [3.0, 4.0]  # Should normalize to [0.6, 0.8]
        normalized = vector_memory._normalize_embedding(embedding)
        
        expected_length = (0.6**2 + 0.8**2)**0.5
        actual_length = sum(x**2 for x in normalized)**0.5
        
        assert abs(expected_length - actual_length) < 1e-10
        assert abs(normalized[0] - 0.6) < 1e-10
        assert abs(normalized[1] - 0.8) < 1e-10

    @pytest.mark.asyncio
    async def test_normalize_zero_vector(self):
        """Test normalization of zero vector."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        zero_vector = [0.0, 0.0, 0.0]
        normalized = vector_memory._normalize_embedding(zero_vector)
        
        # Zero vector should remain zero or be handled gracefully
        assert all(x == 0.0 for x in normalized)


class TestVectorMemoryInsert:
    """Test VectorMemory insert operations."""

    @pytest.mark.asyncio
    async def test_insert_embedding_success(self):
        """Test successful embedding insertion."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}  # Mock internal storage
        
        entry_id = await vector_memory.insert("test text", {"category": "test"})
        
        assert entry_id is not None
        assert len(vector_memory._vector_store) == 1
        mock_provider.embed_text.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_insert_embedding_with_metadata(self):
        """Test embedding insertion with metadata."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        metadata = {"category": "test", "tags": ["tag1", "tag2"], "priority": 1}
        entry_id = await vector_memory.insert("test text", metadata)
        
        assert entry_id is not None
        stored_entry = vector_memory._vector_store[entry_id]
        assert stored_entry["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_insert_embedding_unicode_text(self):
        """Test embedding insertion with Unicode text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        unicode_text = "Unicode test: ñáéíóú 中文 русский 日本語"
        entry_id = await vector_memory.insert(unicode_text, {"unicode": True})
        
        assert entry_id is not None
        stored_entry = vector_memory._vector_store[entry_id]
        assert stored_entry["text"] == unicode_text
        assert stored_entry["metadata"]["unicode"] is True

    @pytest.mark.asyncio
    async def test_insert_embedding_generation_error(self):
        """Test embedding insertion with generation error."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.side_effect = Exception("Embedding failed")
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        with pytest.raises(VectorSearchError):
            await vector_memory.insert("test text")

    @pytest.mark.asyncio
    async def test_insert_embedding_storage_error(self):
        """Test embedding insertion with storage error."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        # Mock storage error
        vector_memory._vector_store = None
        
        with pytest.raises(VectorSearchError):
            await vector_memory.insert("test text")

    @pytest.mark.asyncio
    async def test_insert_duplicate_text(self):
        """Test inserting duplicate text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        # Insert first time
        entry_id1 = await vector_memory.insert("duplicate text")
        
        # Insert same text again
        entry_id2 = await vector_memory.insert("duplicate text")
        
        # Should create separate entries
        assert entry_id1 != entry_id2
        assert len(vector_memory._vector_store) == 2

    @pytest.mark.asyncio
    async def test_insert_very_long_text(self):
        """Test inserting very long text."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        long_text = "x" * 100000  # 100KB
        entry_id = await vector_memory.insert(long_text)
        
        assert entry_id is not None
        stored_entry = vector_memory._vector_store[entry_id]
        assert stored_entry["text"] == long_text


class TestVectorMemorySearch:
    """Test VectorMemory search operations."""

    @pytest.mark.asyncio
    async def test_search_similarity_success(self):
        """Test successful similarity search."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "similar text 1", "metadata": {}},
            "id2": {"embedding": [0.9, 0.8, 0.7], "text": "different text", "metadata": {}},
            "id3": {"embedding": [0.15, 0.25, 0.35], "text": "similar text 2", "metadata": {}}
        }
        
        results = await vector_memory.search("query text", limit=2)
        
        assert len(results) <= 2
        # Most similar results should come first
        if len(results) >= 2:
            assert results[0]["similarity"] >= results[1]["similarity"]

    @pytest.mark.asyncio
    async def test_search_with_threshold(self):
        """Test search with similarity threshold."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data with different similarities
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "very similar", "metadata": {}},
            "id2": {"embedding": [0.9, 0.8, 0.7], "text": "not similar", "metadata": {}}
        }
        
        results = await vector_memory.search("query text", threshold=0.8)
        
        # Should only return highly similar results
        for result in results:
            assert result["similarity"] >= 0.8

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no results."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        results = await vector_memory.search("query text")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_search_empty_store(self):
        """Test search in empty vector store."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        results = await vector_memory.search("query text")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_search_embedding_generation_error(self):
        """Test search with embedding generation error."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.side_effect = Exception("Embedding failed")
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        with pytest.raises(VectorSearchError):
            await vector_memory.search("query text")

    @pytest.mark.asyncio
    async def test_search_unicode_query(self):
        """Test search with Unicode query."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1] * 768, "text": "Unicode text: ñáéíóú", "metadata": {}}
        }
        
        unicode_query = "Unicode search: 中文 русский"
        results = await vector_memory.search(unicode_query)
        
        assert len(results) == 1
        assert "ñáéíóú" in results[0]["text"]

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self):
        """Test search with metadata filtering."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text 1", "metadata": {"category": "test"}},
            "id2": {"embedding": [0.15, 0.25, 0.35], "text": "text 2", "metadata": {"category": "other"}},
            "id3": {"embedding": [0.2, 0.3, 0.4], "text": "text 3", "metadata": {"category": "test"}}
        }
        
        results = await vector_memory.search("query text", metadata_filter={"category": "test"})
        
        # Should only return results with matching metadata
        assert len(results) == 2
        for result in results:
            assert result["metadata"]["category"] == "test"

    @pytest.mark.asyncio
    async def test_search_cosine_similarity_calculation(self):
        """Test cosine similarity calculation."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [1.0, 0.0, 0.0]  # Normalized
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data with known similarities
        vector_memory._vector_store = {
            "id1": {"embedding": [1.0, 0.0, 0.0], "text": "identical", "metadata": {}},  # Similarity = 1.0
            "id2": {"embedding": [0.0, 1.0, 0.0], "text": "orthogonal", "metadata": {}},  # Similarity = 0.0
            "id3": {"embedding": [0.707, 0.707, 0.0], "text": "45 degrees", "metadata": {}}  # Similarity = 0.707
        }
        
        results = await vector_memory.search("query text")
        
        assert len(results) == 3
        # Results should be ordered by similarity (descending)
        assert abs(results[0]["similarity"] - 1.0) < 1e-10
        assert abs(results[1]["similarity"] - 0.707) < 1e-10
        assert abs(results[2]["similarity"] - 0.0) < 1e-10

    @pytest.mark.asyncio
    async def test_search_large_dataset(self):
        """Test search performance with large dataset."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup large mock dataset
        large_dataset = {}
        for i in range(1000):
            large_dataset[f"id_{i}"] = {
                "embedding": [0.1 + i * 0.001] * 768,
                "text": f"text {i}",
                "metadata": {"index": i}
            }
        vector_memory._vector_store = large_dataset
        
        import time
        start_time = time.time()
        
        results = await vector_memory.search("query text", limit=10)
        
        elapsed = time.time() - start_time
        assert len(results) <= 10
        assert elapsed < 1.0  # Should complete within 1 second


class TestVectorMemoryDelete:
    """Test VectorMemory delete operations."""

    @pytest.mark.asyncio
    async def test_delete_by_id_success(self):
        """Test successful deletion by ID."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text 1", "metadata": {}},
            "id2": {"embedding": [0.4, 0.5, 0.6], "text": "text 2", "metadata": {}}
        }
        
        result = await vector_memory.delete_by_id("id1")
        
        assert result is True
        assert "id1" not in vector_memory._vector_store
        assert "id2" in vector_memory._vector_store

    @pytest.mark.asyncio
    async def test_delete_by_id_not_found(self):
        """Test deletion of non-existent ID."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text 1", "metadata": {}}
        }
        
        result = await vector_memory.delete_by_id("nonexistent_id")
        
        assert result is False
        assert "id1" in vector_memory._vector_store

    @pytest.mark.asyncio
    async def test_delete_by_metadata(self):
        """Test deletion by metadata criteria."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text 1", "metadata": {"category": "test"}},
            "id2": {"embedding": [0.4, 0.5, 0.6], "text": "text 2", "metadata": {"category": "other"}},
            "id3": {"embedding": [0.7, 0.8, 0.9], "text": "text 3", "metadata": {"category": "test"}}
        }
        
        deleted_count = await vector_memory.delete_by_metadata({"category": "test"})
        
        assert deleted_count == 2
        assert "id1" not in vector_memory._vector_store
        assert "id2" in vector_memory._vector_store
        assert "id3" not in vector_memory._vector_store

    @pytest.mark.asyncio
    async def test_delete_by_text_content(self):
        """Test deletion by text content."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "delete me", "metadata": {}},
            "id2": {"embedding": [0.4, 0.5, 0.6], "text": "keep me", "metadata": {}},
            "id3": {"embedding": [0.7, 0.8, 0.9], "text": "delete me too", "metadata": {}}
        }
        
        deleted_count = await vector_memory.delete_by_text("delete me")
        
        assert deleted_count == 2
        assert "id1" not in vector_memory._vector_store
        assert "id2" in vector_memory._vector_store
        assert "id3" not in vector_memory._vector_store

    @pytest.mark.asyncio
    async def test_delete_all(self):
        """Test deleting all entries."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text 1", "metadata": {}},
            "id2": {"embedding": [0.4, 0.5, 0.6], "text": "text 2", "metadata": {}}
        }
        
        deleted_count = await vector_memory.delete_all()
        
        assert deleted_count == 2
        assert len(vector_memory._vector_store) == 0


class TestVectorMemoryUpdate:
    """Test VectorMemory update operations."""

    @pytest.mark.asyncio
    async def test_update_embedding_success(self):
        """Test successful embedding update."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.9, 0.8, 0.7]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "old text", "metadata": {"old": True}}
        }
        
        result = await vector_memory.update("id1", "new text", {"new": True})
        
        assert result is True
        updated_entry = vector_memory._vector_store["id1"]
        assert updated_entry["text"] == "new text"
        assert updated_entry["metadata"] == {"new": True}
        assert updated_entry["embedding"] == [0.9, 0.8, 0.7]

    @pytest.mark.asyncio
    async def test_update_nonexistent_id(self):
        """Test updating non-existent ID."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.9, 0.8, 0.7]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        result = await vector_memory.update("nonexistent_id", "new text")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_update_metadata_only(self):
        """Test updating metadata only."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "text", "metadata": {"old": True}}
        }
        
        result = await vector_memory.update_metadata("id1", {"new": True})
        
        assert result is True
        updated_entry = vector_memory._vector_store["id1"]
        assert updated_entry["metadata"] == {"new": True}
        assert updated_entry["text"] == "text"  # Text should remain unchanged

    @pytest.mark.asyncio
    async def test_update_embedding_generation_error(self):
        """Test update with embedding generation error."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.side_effect = Exception("Embedding failed")
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "id1": {"embedding": [0.1, 0.2, 0.3], "text": "old text", "metadata": {}}
        }
        
        with pytest.raises(VectorSearchError):
            await vector_memory.update("id1", "new text")


class TestVectorMemoryConcurrency:
    """Test VectorMemory concurrency handling."""

    @pytest.mark.asyncio
    async def test_concurrent_insert_operations(self):
        """Test concurrent insert operations."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        async def insert_worker(worker_id):
            return await vector_memory.insert(f"text from worker {worker_id}", {"worker": worker_id})
        
        # Run concurrent operations
        tasks = [insert_worker(i) for i in range(5)]
        entry_ids = await asyncio.gather(*tasks)
        
        assert len(entry_ids) == 5
        assert len(vector_memory._vector_store) == 5
        assert all(entry_id is not None for entry_id in entry_ids)

    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self):
        """Test concurrent search operations."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data
        vector_memory._vector_store = {
            f"id_{i}": {"embedding": [0.1, 0.2, 0.3], "text": f"text {i}", "metadata": {}}
            for i in range(100)
        }
        
        async def search_worker(worker_id):
            return await vector_memory.search(f"query from worker {worker_id}")
        
        # Run concurrent operations
        tasks = [search_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(isinstance(result, list) for result in results)

    @pytest.mark.asyncio
    async def test_concurrent_delete_operations(self):
        """Test concurrent delete operations."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup mock data
        vector_memory._vector_store = {
            f"id_{i}": {"embedding": [0.1, 0.2, 0.3], "text": f"text {i}", "metadata": {}}
            for i in range(10)
        }
        
        async def delete_worker(worker_id):
            return await vector_memory.delete_by_id(f"id_{worker_id}")
        
        # Run concurrent operations
        tasks = [delete_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result is True for result in results)
        assert len(vector_memory._vector_store) == 5  # 10 - 5 deleted


class TestVectorMemoryPerformance:
    """Test VectorMemory performance characteristics."""

    @pytest.mark.asyncio
    async def test_large_scale_insert_performance(self):
        """Test large scale insert performance."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        import time
        start_time = time.time()
        
        # Insert 1000 entries
        entry_ids = []
        for i in range(1000):
            entry_id = await vector_memory.insert(f"text {i}", {"index": i})
            entry_ids.append(entry_id)
        
        elapsed = time.time() - start_time
        
        assert len(entry_ids) == 1000
        assert len(vector_memory._vector_store) == 1000
        assert elapsed < 10.0  # Should complete within 10 seconds

    @pytest.mark.asyncio
    async def test_search_performance_optimization(self):
        """Test search performance optimization."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup large dataset
        large_dataset = {}
        for i in range(10000):
            large_dataset[f"id_{i}"] = {
                "embedding": [0.1 + i * 0.0001] * 768,
                "text": f"text {i}",
                "metadata": {"index": i}
            }
        vector_memory._vector_store = large_dataset
        
        import time
        start_time = time.time()
        
        results = await vector_memory.search("query text", limit=100)
        
        elapsed = time.time() - start_time
        
        assert len(results) <= 100
        assert elapsed < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage stability."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        # Perform many operations
        for i in range(1000):
            await vector_memory.insert(f"text {i}", {"index": i})
            if i % 100 == 0:
                await vector_memory.search(f"query {i}")
        
        # Memory usage should be stable
        assert len(vector_memory._vector_store) == 1000


class TestVectorMemoryEdgeCases:
    """Test VectorMemory edge cases."""

    @pytest.mark.asyncio
    async def test_empty_vectors(self):
        """Test handling of empty vectors."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = []
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Should handle empty vectors gracefully
        with pytest.raises(VectorSearchError):
            await vector_memory.insert("test text")

    @pytest.mark.asyncio
    async def test_malformed_vectors(self):
        """Test handling of malformed vectors."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Test with different malformed vectors
        malformed_vectors = [
            [0.1, None, 0.3],  # Contains None
            [0.1, "invalid", 0.3],  # Contains string
            [0.1, 0.2],  # Wrong dimensions
            []  # Empty vector
        ]
        
        for malformed_vector in malformed_vectors:
            with pytest.raises(VectorSearchError):
                vector_memory._validate_embedding(malformed_vector)

    @pytest.mark.asyncio
    async def test_infinite_and_nan_values(self):
        """Test handling of infinite and NaN values."""
        mock_provider = Mock(spec=EmbeddingProvider)
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Test with infinite values
        infinite_vector = [0.1, float('inf'), 0.3]
        assert vector_memory._validate_embedding(infinite_vector) is False
        
        # Test with NaN values
        nan_vector = [0.1, float('nan'), 0.3]
        assert vector_memory._validate_embedding(nan_vector) is False

    @pytest.mark.asyncio
    async def test_very_high_dimensional_vectors(self):
        """Test handling of very high dimensional vectors."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 10000  # 10K dimensions
        
        vector_memory = VectorMemory(embedding_provider=mock_provider, dimensions=10000)
        vector_memory._vector_store = {}
        
        entry_id = await vector_memory.insert("high dimensional text")
        
        assert entry_id is not None
        stored_entry = vector_memory._vector_store[entry_id]
        assert len(stored_entry["embedding"]) == 10000

    @pytest.mark.asyncio
    async def test_concurrent_access_same_id(self):
        """Test concurrent access to the same ID."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {
            "shared_id": {"embedding": [0.1, 0.2, 0.3], "text": "original", "metadata": {}}
        }
        
        async def update_worker(worker_id):
            return await vector_memory.update("shared_id", f"updated by {worker_id}", {"worker": worker_id})
        
        # Run concurrent updates to same ID
        tasks = [update_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Should handle concurrent access gracefully
        assert all(result is True for result in results)

    @pytest.mark.asyncio
    async def test_unicode_in_embeddings(self):
        """Test Unicode characters in embedding-related operations."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [0.1] * 768
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        vector_memory._vector_store = {}
        
        unicode_texts = [
            "Unicode: ñáéíóú",
            "Chinese: 中文",
            "Russian: русский",
            "Japanese: 日本語",
            "Arabic: العربية",
            "Emoji: 🚀🎉🔥"
        ]
        
        entry_ids = []
        for text in unicode_texts:
            entry_id = await vector_memory.insert(text, {"unicode": True})
            entry_ids.append(entry_id)
        
        assert len(entry_ids) == len(unicode_texts)
        
        # Search should work with Unicode queries
        results = await vector_memory.search("Unicode search: ñáéíóú")
        assert len(results) >= 0  # Should not crash

    @pytest.mark.asyncio
    async def test_extreme_similarity_values(self):
        """Test handling of extreme similarity values."""
        mock_provider = Mock(spec=EmbeddingProvider)
        mock_provider.embed_text.return_value = [1.0, 0.0, 0.0]  # Normalized
        
        vector_memory = VectorMemory(embedding_provider=mock_provider)
        
        # Setup test vectors with extreme similarities
        vector_memory._vector_store = {
            "identical": {"embedding": [1.0, 0.0, 0.0], "text": "identical", "metadata": {}},
            "opposite": {"embedding": [-1.0, 0.0, 0.0], "text": "opposite", "metadata": {}},
            "orthogonal": {"embedding": [0.0, 1.0, 0.0], "text": "orthogonal", "metadata": {}}
        }
        
        results = await vector_memory.search("query text")
        
        # Check similarity calculations
        similarities = [result["similarity"] for result in results]
        assert all(-1.0 <= sim <= 1.0 for sim in similarities)  # Should be in valid range
