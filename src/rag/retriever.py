"""RAG检索器模块，负责从向量存储中检索相关文档"""
from loguru import logger
from src.rag.vector_store import vector_store
from typing import List, Dict


class RAGRetriever:
    """RAG检索器，从向量存储中检索相关文档作为上下文"""

    def __init__(self):
        """初始化RAG检索器"""
        self.vector_store = vector_store

    def retrieve(self, query: str, n_results: int = 5) -> str:
        """
        检索相关文档并返回格式化的上下文字符串

        Args:
            query: 查询文本
            n_results: 返回结果数量

        Returns:
            格式化的上下文字符串
        """
        results = self.vector_store.search(query, n_results)

        if not results:
            return "无相关历史信息"

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[参考{i}] {result['text']}"
            )

        context = "\n\n".join(context_parts)
        logger.info(f"RAG检索: 查询'{query}'，返回 {len(results)} 条")
        return context

    def retrieve_by_entity(self, entity: str, n_results: int = 3) -> List[Dict]:
        """
        根据实体名称检索相关文档

        Args:
            entity: 实体名称
            n_results: 返回结果数量

        Returns:
            检索结果列表
        """
        results = self.vector_store.search(entity, n_results)
        logger.info(f"实体检索: '{entity}'，返回 {len(results)} 条")
        return results


# 全局RAG检索器实例
rag_retriever = RAGRetriever()
