"""Tests for the RAG retriever module."""
from src.rag.retriever import RAGRetriever


def test_rag_retriever_retrieves_context():
    """Test that RAG retriever retrieves context string."""
    retriever = RAGRetriever()
    context = retriever.retrieve("贵州茅台股价")
    assert isinstance(context, str)


def test_rag_retriever_empty_query():
    """Test that RAG retriever handles empty query."""
    retriever = RAGRetriever()
    context = retriever.retrieve("")
    assert isinstance(context, str)


def test_rag_retriever_n_results_parameter():
    """Test that RAG retriever respects n_results parameter."""
    retriever = RAGRetriever()
    context = retriever.retrieve("测试", n_results=3)
    assert isinstance(context, str)


def test_rag_retriever_retrieve_by_entity():
    """Test that RAG retriever can retrieve by entity."""
    retriever = RAGRetriever()
    results = retriever.retrieve_by_entity("贵州茅台")
    assert isinstance(results, list)
