"""Simple embeddings tests using only MockEmbeddingProvider - no external dependencies."""

from __future__ import annotations

import pytest
from jarvis.llm.embeddings import MockEmbeddingProvider, get_embedding_provider
from jarvis.config.settings import Settings


class TestMockEmbeddingProvider:
    """Test MockEmbeddingProvider - always available, no dependencies."""

    def test_mock_provider_basic_functionality(self):
        """Test basic embedding generation."""
        provider = MockEmbeddingProvider(dim=384)
        
        text = "Hello world"
        embedding = provider.encode(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_mock_provider_dimension_property(self):
        """Test dimension property."""
        provider = MockEmbeddingProvider(dim=512)
        assert provider.dimension == 512

    def test_mock_provider_default_dimension(self):
        """Test default dimension is used."""
        provider = MockEmbeddingProvider()
        assert provider.dimension == 768

    def test_mock_provider_deterministic(self):
        """Test that same text produces same embedding."""
        provider = MockEmbeddingProvider(dim=100)
        
        text = "test text"
        embedding1 = provider.encode(text)
        embedding2 = provider.encode(text)
        
        assert embedding1 == embedding2

    def test_mock_provider_different_texts(self):
        """Test that different texts produce different embeddings."""
        provider = MockEmbeddingProvider(dim=100)
        
        embedding1 = provider.encode("text1")
        embedding2 = provider.encode("text2")
        
        assert embedding1 != embedding2

    def test_mock_provider_unicode_handling(self):
        """Test unicode text handling."""
        provider = MockEmbeddingProvider(dim=100)
        
        unicode_text = "Test with émojis 🎉 and accents café"
        embedding = provider.encode(unicode_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 100

    def test_mock_provider_empty_text(self):
        """Test empty text handling."""
        provider = MockEmbeddingProvider(dim=100)
        
        embedding = provider.encode("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 100

    def test_mock_provider_large_text(self):
        """Test large text handling."""
        provider = MockEmbeddingProvider(dim=100)
        
        large_text = "x" * 1000000  # 1MB text
        embedding = provider.encode(large_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 100


class TestEmbeddingProviderFactory:
    """Test embedding provider factory with fallbacks."""

    def test_get_embedding_provider_default_fallback(self):
        """Test that factory returns MockEmbeddingProvider as fallback."""
        # Create settings with fallback enabled
        settings = Settings(
            embedding_provider="sentence-transformers",
            embedding_fallback_to_mock=True,
            vector_dim=384
        )
        
        provider = get_embedding_provider(settings)
        
        # Should return MockEmbeddingProvider due to missing dependency
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 384

    def test_get_embedding_provider_litellm_fallback(self):
        """Test LiteLLM provider fallback to mock."""
        settings = Settings(
            embedding_provider="litellm",
            embedding_fallback_to_mock=True,
            vector_dim=1536
        )
        
        provider = get_embedding_provider(settings)
        
        # Should return MockEmbeddingProvider due to missing dependency
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 1536

    def test_get_embedding_provider_unknown_provider(self):
        """Test unknown provider falls back to mock."""
        settings = Settings(
            embedding_provider="unknown",
            embedding_fallback_to_mock=True,
            vector_dim=512
        )
        
        provider = get_embedding_provider(settings)
        
        # Should return MockEmbeddingProvider
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimension == 512


class TestEmbeddingProviderInterface:
    """Test that all providers implement the interface correctly."""

    def test_mock_provider_interface_compliance(self):
        """Test MockEmbeddingProvider implements interface correctly."""
        provider = MockEmbeddingProvider(dim=256)
        
        # Test encode method
        embedding = provider.encode("test")
        assert isinstance(embedding, list)
        assert len(embedding) == 256
        
        # Test dimension property
        assert provider.dimension == 256
        
        # Test that encode returns floats
        assert all(isinstance(x, float) for x in embedding)


class TestEmbeddingProviderEdgeCases:
    """Test edge cases and error handling."""

    def test_provider_with_none_text(self):
        """Test provider with None input."""
        provider = MockEmbeddingProvider(dim=100)
        
        # Should handle None gracefully
        with pytest.raises((TypeError, AttributeError)):
            provider.encode(None)

    def test_provider_with_numeric_input(self):
        """Test provider with numeric input."""
        provider = MockEmbeddingProvider(dim=100)
        
        # Should handle numeric input gracefully
        with pytest.raises((TypeError, AttributeError)):
            provider.encode(123)

    def test_provider_with_bytes_input(self):
        """Test provider with bytes input."""
        provider = MockEmbeddingProvider(dim=100)
        
        # Should handle bytes input gracefully
        with pytest.raises((TypeError, AttributeError)):
            provider.encode(b"bytes")


class TestEmbeddingProviderPerformance:
    """Test performance characteristics."""

    def test_mock_provider_performance(self):
        """Test MockEmbeddingProvider performance."""
        import time
        
        provider = MockEmbeddingProvider(dim=768)
        
        # Test encoding speed
        start_time = time.time()
        for _ in range(100):
            provider.encode("test text")
        end_time = time.time()
        
        # Should be fast (less than 1 second for 100 encodings)
        assert end_time - start_time < 1.0

    def test_concurrent_embedding_performance(self):
        """Test concurrent embedding performance."""
        import threading
        import time
        
        provider = MockEmbeddingProvider(dim=384)
        results = []
        
        def encode_worker(text):
            results.append(provider.encode(text))
        
        # Test concurrent encoding
        threads = []
        start_time = time.time()
        
        for i in range(10):
            thread = threading.Thread(target=encode_worker, args=(f"text_{i}",))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All should succeed
        assert len(results) == 10
        assert all(isinstance(r, list) and len(r) == 384 for r in results)
        
        # Should be reasonably fast
        assert end_time - start_time < 2.0
