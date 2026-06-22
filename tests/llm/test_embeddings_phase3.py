"""Phase 3 Embeddings tests for robustness and error handling (>75% coverage)."""

from __future__ import annotations

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from jarvis.llm.embeddings import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    SentenceTransformerProvider,
    LiteLLMEmbeddingProvider,
    get_embedding_provider
)
from jarvis.config.settings import Settings


class TestMockEmbeddingProvider:
    """Test MockEmbeddingProvider for robustness."""

    def test_mock_provider_basic_functionality(self):
        """Test basic embedding generation."""
        provider = MockEmbeddingProvider(dim=384)
        
        text = "Hello world"
        embedding = provider.encode(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert all(-1.0 <= x <= 1.0 for x in embedding)

    def test_mock_provider_dimension_property(self):
        """Test dimension property."""
        provider = MockEmbeddingProvider(dim=512)
        assert provider.dimension == 512
        
        provider = MockEmbeddingProvider(dim=768)
        assert provider.dimension == 768

    def test_mock_provider_deterministic(self):
        """Test that embeddings are deterministic for same input."""
        provider = MockEmbeddingProvider(dim=384)
        
        text = "Test text"
        embedding1 = provider.encode(text)
        embedding2 = provider.encode(text)
        
        assert embedding1 == embedding2

    def test_mock_provider_different_inputs(self):
        """Test that different inputs produce different embeddings."""
        provider = MockEmbeddingProvider(dim=384)
        
        embedding1 = provider.encode("text1")
        embedding2 = provider.encode("text2")
        
        assert embedding1 != embedding2

    def test_mock_provider_empty_string(self):
        """Test embedding generation with empty string."""
        provider = MockEmbeddingProvider(dim=384)
        
        embedding = provider.encode("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_mock_provider_unicode_text(self):
        """Test embedding generation with unicode characters."""
        provider = MockEmbeddingProvider(dim=384)
        
        unicode_text = "Test with émojis 🎉 and accents café"
        embedding = provider.encode(unicode_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_mock_provider_very_long_text(self):
        """Test embedding generation with very long text."""
        provider = MockEmbeddingProvider(dim=384)
        
        long_text = "x" * 100000  # 100KB text
        embedding = provider.encode(long_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_mock_provider_special_characters(self):
        """Test embedding generation with special characters."""
        provider = MockEmbeddingProvider(dim=384)
        
        special_text = "Special chars: @#$%^&*()[]{}|\\:;<>?,./\n\t\r"
        embedding = provider.encode(special_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_mock_provider_default_dimension(self):
        """Test default dimension is used."""
        provider = MockEmbeddingProvider()
        assert provider.dimension == 768

    def test_mock_provider_hash_distribution(self):
        """Test that hash produces reasonable distribution."""
        provider = MockEmbeddingProvider(dim=1000)
        
        # Generate embeddings for many different texts
        embeddings = []
        for i in range(100):
            text = f"test text {i}"
            embedding = provider.encode(text)
            embeddings.append(embedding)
        
        # Check that we get different values
        unique_first_values = set(emb[0] for emb in embeddings)
        assert len(unique_first_values) > 50  # Should have good distribution


class TestSentenceTransformerProvider:
    """Test SentenceTransformerProvider for robustness."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence-transformers for testing."""
        with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = [[0.1, 0.2, 0.3] * 128]  # 384 dim
            mock_st.return_value = mock_model
            yield mock_model, mock_st

    def test_sentence_transformer_initialization(self, mock_sentence_transformer):
        """Test provider initialization."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            dim=384
        )
        
        assert provider.model_name == "all-MiniLM-L6-v2"
        assert provider.device == "cpu"
        assert provider._dim == 384
        assert provider._model is None  # Not loaded yet

    def test_sentence_transformer_model_loading(self, mock_sentence_transformer):
        """Test model loading on demand."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        # First access should load the model
        model = provider._load_model()
        
        assert model == mock_model
        mock_st.assert_called_once_with("test-model", device="cpu")
        mock_model.get_sentence_embedding_dimension.assert_called_once()

    def test_sentence_transformer_dimension_property(self, mock_sentence_transformer):
        """Test dimension property loads model if needed."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        # Accessing dimension should load model
        dim = provider.dimension
        
        assert dim == 384
        mock_st.assert_called_once()

    def test_sentence_transformer_encode(self, mock_sentence_transformer):
        """Test encoding functionality."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        embedding = provider.encode("Hello world")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        mock_model.encode.assert_called_once_with(
            "Hello world",
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def test_sentence_transformer_encode_caches_model(self, mock_sentence_transformer):
        """Test that model is cached after first use."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        # Multiple encodes should only load model once
        provider.encode("text1")
        provider.encode("text2")
        
        mock_st.assert_called_once()  # Only called once

    def test_sentence_transformer_different_devices(self, mock_sentence_transformer):
        """Test initialization with different devices."""
        mock_model, mock_st = mock_sentence_transformer
        
        # Test CPU
        provider_cpu = SentenceTransformerProvider("test-model", device="cpu")
        provider_cpu._load_model()
        mock_st.assert_called_with("test-model", device="cpu")
        
        # Reset mock
        mock_st.reset_mock()
        
        # Test CUDA
        provider_cuda = SentenceTransformerProvider("test-model", device="cuda")
        provider_cuda._load_model()
        mock_st.assert_called_with("test-model", device="cuda")

    def test_sentence_transformer_model_loading_failure(self):
        """Test handling of model loading failure."""
        with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
            mock_st.side_effect = ImportError("No module named 'sentence_transformers'")
            
            provider = SentenceTransformerProvider("test-model")
            
            with pytest.raises(ImportError):
                provider._load_model()

    def test_sentence_transformer_encode_failure(self, mock_sentence_transformer):
        """Test handling of encoding failure."""
        mock_model, mock_st = mock_sentence_transformer
        mock_model.encode.side_effect = RuntimeError("CUDA out of memory")
        
        provider = SentenceTransformerProvider("test-model")
        
        with pytest.raises(RuntimeError):
            provider.encode("test text")

    def test_sentence_transformer_large_text_handling(self, mock_sentence_transformer):
        """Test handling of large text inputs."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        large_text = "x" * 1000000  # 1MB text
        embedding = provider.encode(large_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        mock_model.encode.assert_called_once()

    def test_sentence_transformer_unicode_handling(self, mock_sentence_transformer):
        """Test unicode text handling."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        unicode_text = "Test with émojis 🎉 and accents café\n\t\r"
        embedding = provider.encode(unicode_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_sentence_transformer_empty_text(self, mock_sentence_transformer):
        """Test empty text handling."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        embedding = provider.encode("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        mock_model.encode.assert_called_once_with("", convert_to_numpy=True, normalize_embeddings=True)

    def test_sentence_transformer_concurrent_access(self, mock_sentence_transformer):
        """Test concurrent access to model loading."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        def encode_worker(text):
            return provider.encode(text)
        
        # Test concurrent encoding
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(encode_worker(f"text_{i}")))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(isinstance(r, list) and len(r) == 384 for r in results)
        
        # Model should only be loaded once
        mock_st.assert_called_once()


class TestLiteLLMEmbeddingProvider:
    """Test LiteLLMEmbeddingProvider for robustness."""

    @pytest.fixture
    def mock_litellm(self):
        """Mock LiteLLM for testing."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            mock_response = {
                "data": [
                    {
                        "embedding": [0.1, 0.2, 0.3] * 256  # 768 dim
                    }
                ]
            }
            mock_litellm.embedding.return_value = mock_response
            yield mock_litellm, mock_response

    def test_litellm_provider_initialization(self):
        """Test provider initialization."""
        provider = LiteLLMEmbeddingProvider(
            model="text-embedding-ada-002",
            api_key="test_key",
            dim=1536
        )
        
        assert provider.model == "text-embedding-ada-002"
        assert provider.api_key == "test_key"
        assert provider._dim == 1536

    def test_litellm_provider_without_api_key(self, mock_litellm):
        """Test provider without API key."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("text-embedding-ada-002")
        embedding = provider.encode("test")
        
        # Should not include api_key in kwargs
        call_args = mock_llm.embedding.call_args[1]
        assert "api_key" not in call_args

    def test_litellm_provider_with_api_key(self, mock_litellm):
        """Test provider with API key."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider(
            "text-embedding-ada-002",
            api_key="sk-test123"
        )
        embedding = provider.encode("test")
        
        # Should include api_key in kwargs
        call_args = mock_llm.embedding.call_args[1]
        assert call_args["api_key"] == "sk-test123"

    def test_litellm_encode_basic(self, mock_litellm):
        """Test basic encoding functionality."""
        mock_llm, mock_response = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("text-embedding-ada-002", dim=768)
        embedding = provider.encode("Hello world")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert embedding == [0.1, 0.2, 0.3] * 256
        
        mock_llm.embedding.assert_called_once_with(
            model="text-embedding-ada-002",
            input=["Hello world"]
        )

    def test_litellm_dimension_property(self):
        """Test dimension property."""
        provider = LiteLLMEmbeddingProvider("test-model", dim=1536)
        assert provider.dimension == 1536

    def test_litellm_empty_text(self, mock_litellm):
        """Test encoding empty text."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        embedding = provider.encode("")
        
        assert isinstance(embedding, list)
        mock_llm.embedding.assert_called_once_with(model="test-model", input=[""])

    def test_litellm_unicode_text(self, mock_litellm):
        """Test encoding unicode text."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        unicode_text = "Test with émojis 🎉 and accents café"
        embedding = provider.encode(unicode_text)
        
        assert isinstance(embedding, list)
        mock_llm.embedding.assert_called_once_with(model="test-model", input=[unicode_text])

    def test_litellm_very_long_text(self, mock_litellm):
        """Test encoding very long text."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        long_text = "x" * 100000  # 100KB text
        embedding = provider.encode(long_text)
        
        assert isinstance(embedding, list)
        mock_llm.embedding.assert_called_once_with(model="test-model", input=[long_text])

    def test_litellm_special_characters(self, mock_litellm):
        """Test encoding special characters."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        special_text = "Special chars: @#$%^&*()[]{}|\\:;<>?,./\n\t\r"
        embedding = provider.encode(special_text)
        
        assert isinstance(embedding, list)
        mock_llm.embedding.assert_called_once_with(model="test-model", input=[special_text])

    def test_litellm_api_error_handling(self):
        """Test handling of API errors."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            import litellm
            
            mock_litellm.embedding.side_effect = litellm.APIConnectionError("Connection failed")
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(litellm.APIConnectionError):
                provider.encode("test text")

    def test_litellm_rate_limit_handling(self):
        """Test handling of rate limiting."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            import litellm
            
            mock_litellm.embedding.side_effect = litellm.RateLimitError("Rate limit exceeded")
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(litellm.RateLimitError):
                provider.encode("test text")

    def test_litellm_timeout_handling(self):
        """Test handling of timeouts."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            import litellm
            
            mock_litellm.embedding.side_effect = litellm.Timeout("Request timeout")
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(litellm.Timeout):
                provider.encode("test text")

    def test_litellm_invalid_response_handling(self):
        """Test handling of invalid API response."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            # Missing data key
            mock_litellm.embedding.return_value = {"error": "invalid request"}
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(KeyError):
                provider.encode("test text")

    def test_litellm_empty_response_handling(self):
        """Test handling of empty response data."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            # Empty data array
            mock_litellm.embedding.return_value = {"data": []}
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(IndexError):
                provider.encode("test text")

    def test_litellm_malformed_embedding_handling(self):
        """Test handling of malformed embedding data."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            # Missing embedding key
            mock_litellm.embedding.return_value = {
                "data": [{"invalid": "data"}]
            }
            
            provider = LiteLLMEmbeddingProvider("test-model")
            
            with pytest.raises(KeyError):
                provider.encode("test text")

    def test_litellm_authentication_error(self):
        """Test handling of authentication errors."""
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            import litellm
            
            mock_litellm.embedding.side_effect = litellm.AuthenticationError("Invalid API key")
            
            provider = LiteLLMEmbeddingProvider("test-model", api_key="invalid")
            
            with pytest.raises(litellm.AuthenticationError):
                provider.encode("test text")

    def test_litellm_concurrent_requests(self, mock_litellm):
        """Test concurrent embedding requests."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        
        def encode_worker(text):
            return provider.encode(text)
        
        # Test concurrent encoding
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(encode_worker(f"text_{i}")))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        assert all(isinstance(r, list) for r in results)
        
        # Should have made 5 API calls
        assert mock_llm.embedding.call_count == 5


class TestEmbeddingProviderFactory:
    """Test the embedding provider factory function."""

    def test_get_embedding_provider_default_settings(self):
        """Test getting provider with default settings."""
        with patch('jarvis.llm.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.embeddings_provider = "mock"
            mock_settings.return_value.embeddings_model = "mock-model"
            
            provider = get_embedding_provider()
            
            assert isinstance(provider, MockEmbeddingProvider)

    def test_get_embedding_provider_custom_settings(self):
        """Test getting provider with custom settings."""
        custom_settings = Settings(
            embeddings_provider="sentence_transformers",
            embeddings_model="all-MiniLM-L6-v2"
        )
        
        with patch('jarvis.llm.embeddings.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_st.return_value = mock_model
            
            provider = get_embedding_provider(custom_settings)
            
            assert isinstance(provider, SentenceTransformerProvider)
            assert provider.model_name == "all-MiniLM-L6-v2"

    def test_get_embedding_provider_litellm_settings(self):
        """Test getting LiteLLM provider."""
        custom_settings = Settings(
            embeddings_provider="litellm",
            embeddings_model="text-embedding-ada-002"
        )
        
        with patch('jarvis.llm.embeddings.litellm') as mock_litellm:
            mock_litellm.embedding.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            
            provider = get_embedding_provider(custom_settings)
            
            assert isinstance(provider, LiteLLMEmbeddingProvider)
            assert provider.model == "text-embedding-ada-002"

    def test_get_embedding_provider_unknown_provider(self):
        """Test handling of unknown provider."""
        custom_settings = Settings(
            embeddings_provider="unknown_provider",
            embeddings_model="test-model"
        )
        
        provider = get_embedding_provider(custom_settings)
        
        # Should fallback to MockEmbeddingProvider
        assert isinstance(provider, MockEmbeddingProvider)

    def test_get_embedding_provider_no_settings(self):
        """Test getting provider without settings (uses defaults)."""
        with patch('jarvis.llm.embeddings.get_settings') as mock_settings:
            mock_settings.return_value.embeddings_provider = "mock"
            mock_settings.return_value.embeddings_model = "mock-model"
            
            provider = get_embedding_provider()
            
            assert isinstance(provider, MockEmbeddingProvider)


class TestEmbeddingProviderInterface:
    """Test the embedding provider interface compliance."""

    def test_mock_provider_interface_compliance(self):
        """Test MockEmbeddingProvider implements interface correctly."""
        provider = MockEmbeddingProvider()
        
        # Should have required methods
        assert hasattr(provider, 'encode')
        assert hasattr(provider, 'dimension')
        assert callable(provider.encode)
        
        # Should return correct types
        embedding = provider.encode("test")
        assert isinstance(embedding, list)
        assert isinstance(provider.dimension, int)

    def test_sentence_transformer_interface_compliance(self, mock_sentence_transformer):
        """Test SentenceTransformerProvider implements interface correctly."""
        mock_model, mock_st = mock_sentence_transformer
        
        provider = SentenceTransformerProvider("test-model")
        
        # Should have required methods
        assert hasattr(provider, 'encode')
        assert hasattr(provider, 'dimension')
        assert callable(provider.encode)
        
        # Should return correct types
        embedding = provider.encode("test")
        assert isinstance(embedding, list)
        assert isinstance(provider.dimension, int)

    def test_litellm_interface_compliance(self, mock_litellm):
        """Test LiteLLMEmbeddingProvider implements interface correctly."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        
        # Should have required methods
        assert hasattr(provider, 'encode')
        assert hasattr(provider, 'dimension')
        assert callable(provider.encode)
        
        # Should return correct types
        embedding = provider.encode("test")
        assert isinstance(embedding, list)
        assert isinstance(provider.dimension, int)


class TestEmbeddingProviderPerformance:
    """Test embedding provider performance characteristics."""

    def test_mock_provider_performance(self):
        """Test MockEmbeddingProvider performance."""
        provider = MockEmbeddingProvider(dim=384)
        
        # Test encoding speed
        start_time = time.time()
        
        for i in range(100):
            provider.encode(f"test text {i}")
        
        elapsed = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 encodings)
        assert elapsed < 1.0

    def test_mock_provider_memory_usage(self, mock_sentence_transformer):
        """Test memory usage with large embeddings."""
        # Test large dimension
        provider = MockEmbeddingProvider(dim=10000)
        
        embedding = provider.encode("test")
        
        assert len(embedding) == 10000
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_concurrent_embedding_performance(self, mock_litellm):
        """Test concurrent embedding performance."""
        mock_llm, _ = mock_litellm
        
        provider = LiteLLMEmbeddingProvider("test-model")
        
        async def encode_worker(text):
            return provider.encode(text)
        
        import asyncio
        
        # Test concurrent async operations
        tasks = [
            encode_worker(f"test text {i}")
            for i in range(10)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        assert len(results) == 10
        assert all(isinstance(r, list) for r in results)
        # Should complete in reasonable time
        assert elapsed < 5.0


class TestEmbeddingProviderEdgeCases:
    """Test embedding provider edge cases and error conditions."""

    def test_embedding_consistency_across_calls(self):
        """Test that embeddings are consistent across multiple calls."""
        provider = MockEmbeddingProvider(dim=384)
        
        text = "consistency test"
        embeddings = []
        
        for _ in range(10):
            embedding = provider.encode(text)
            embeddings.append(embedding)
        
        # All should be identical
        for i in range(1, len(embeddings)):
            assert embeddings[i] == embeddings[0]

    def test_embedding_dimension_validation(self):
        """Test embedding dimension validation."""
        # Test various dimensions
        dimensions = [1, 10, 100, 384, 512, 768, 1024, 1536, 2048]
        
        for dim in dimensions:
            provider = MockEmbeddingProvider(dim=dim)
            embedding = provider.encode("test")
            
            assert len(embedding) == dim
            assert provider.dimension == dim

    def test_embedding_value_range_validation(self):
        """Test that embedding values are in expected range."""
        provider = MockEmbeddingProvider(dim=1000)
        
        embedding = provider.encode("test")
        
        # Mock provider should produce values in [-1, 1] range
        for value in embedding:
            assert -1.0 <= value <= 1.0

    def test_provider_with_none_text(self):
        """Test handling of None text input."""
        provider = MockEmbeddingProvider()
        
        # Should handle None gracefully (convert to string)
        embedding = provider.encode(None)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768

    def test_provider_with_numeric_input(self):
        """Test handling of numeric input."""
        provider = MockEmbeddingProvider()
        
        # Should handle numbers (convert to string)
        embedding = provider.encode(123)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768

    def test_provider_with_bytes_input(self):
        """Test handling of bytes input."""
        provider = MockEmbeddingProvider()
        
        # Should handle bytes (convert to string)
        text_bytes = "hello world".encode('utf-8')
        embedding = provider.encode(text_bytes)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
