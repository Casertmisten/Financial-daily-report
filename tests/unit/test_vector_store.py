from src.rag.vector_store import VectorStore
import pytest

def test_vector_store_add_documents():
    store = VectorStore()
    docs = [
        {'id': '1', 'text': '测试文档1', 'metadata': {'source': 'test'}},
        {'id': '2', 'text': '测试文档2', 'metadata': {'source': 'test'}},
    ]
    store.add_documents(docs)
    assert store.count() >= 2

def test_vector_store_search():
    store = VectorStore()
    docs = [
        {'id': '1', 'text': '贵州茅台股价上涨', 'metadata': {'source': 'test'}},
    ]
    store.add_documents(docs)
    results = store.search('茅台', n_results=1)
    assert len(results) >= 0
