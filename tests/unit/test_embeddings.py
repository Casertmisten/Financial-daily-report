"""Tests for the embedding generator module."""
from unittest.mock import Mock
from src.rag.embeddings import EmbeddingGenerator


def test_embedding_generator_generates_vectors(monkeypatch):
    """Test that embedding generator generates vectors from texts."""
    mock_client = Mock()
    mock_client.embed.return_value = [[0.1] * 1536, [0.2] * 1536]

    from src.generators.llm_client import llm_client
    monkeypatch.setattr(llm_client, 'embed', mock_client.embed)

    generator = EmbeddingGenerator()
    texts = ["测试文本1", "测试文本2"]
    result = generator.generate(texts)

    assert len(result) == 2
    assert len(result[0]) == 1536
    assert len(result[1]) == 1536


def test_embedding_generator_empty_list():
    """Test that embedding generator handles empty list."""
    generator = EmbeddingGenerator()
    result = generator.generate([])

    assert result == []


def test_embedding_generator_uses_llm_client():
    """Test that embedding generator uses llm_client.embed method."""
    mock_client = Mock()
    mock_client.embed.return_value = [[0.1] * 1536]

    from src.generators.llm_client import llm_client
    monkeypatch = __import__('pytest').fixture
    # Use monkeypatch in the actual test function
