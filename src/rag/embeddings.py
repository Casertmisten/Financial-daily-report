"""嵌入生成器模块，负责将文本转换为向量"""
from loguru import logger
from src.generators.llm_client import llm_client
from typing import List


class EmbeddingGenerator:
    """嵌入生成器，使用LLM客户端将文本转换为向量"""

    def __init__(self):
        """初始化嵌入生成器"""
        self.client = llm_client

    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本向量

        Args:
            texts: 待向量化的文本列表

        Returns:
            向量列表，每个向量是一个浮点数列表

        Raises:
            EmbeddingError: 向量生成失败时抛出
        """
        if not texts:
            return []

        try:
            embeddings = self.client.embed(texts)
            logger.info(f"生成向量: {len(embeddings)} 条")
            return embeddings
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            from src.utils.exceptions import EmbeddingError
            raise EmbeddingError(f"向量生成失败: {e}") from e


# 全局嵌入生成器实例
embedding_generator = EmbeddingGenerator()
