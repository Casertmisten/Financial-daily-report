"""向量存储模块，基于ChromaDB实现文档向量化存储和检索"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import chromadb
from chromadb.config import Settings
from config.settings import config


class VectorStore:
    """向量存储类，使用ChromaDB进行文档存储和相似度搜索"""

    def __init__(
        self,
        collection_name: str = "financial_news",
        persist_directory: Optional[Path] = None
    ):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录，默认使用配置中的chroma_path
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or config.database.chroma_path

        # 确保持久化目录存在
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Financial news vector storage"}
        )

        logger.info(f"向量存储初始化完成，集合: {self.collection_name}, 路径: {self.persist_directory}")

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表，每个文档包含:
                - id: 文档唯一标识
                - text: 文档文本内容
                - metadata: 文档元数据（可选）
            embeddings: 预计算的向量列表（可选），如果为None则使用ChromaDB的默认embedding函数
        """
        if not documents:
            logger.warning("添加文档列表为空，跳过操作")
            return

        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            doc_id = doc.get('id')
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            if not doc_id:
                logger.warning(f"文档缺少id字段，跳过: {text[:50]}...")
                continue

            ids.append(doc_id)
            texts.append(text)
            metadatas.append(metadata)

        if not ids:
            logger.warning("没有有效的文档可添加")
            return

        try:
            # 添加文档到集合
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"成功添加 {len(ids)} 个文档到向量存储")
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        在向量存储中搜索相似文档

        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 元数据过滤条件（可选）
            where_document: 文档内容过滤条件（可选）

        Returns:
            搜索结果列表，每个结果包含:
                - id: 文档ID
                - text: 文档内容
                - metadata: 文档元数据
                - distance: 相似度距离
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            # 格式化结果
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'text': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })

            logger.info(f"搜索完成，查询: {query}, 返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    def count(self) -> int:
        """
        获取向量存储中的文档数量

        Returns:
            文档总数
        """
        try:
            count = self.collection.count()
            logger.debug(f"向量存储文档数量: {count}")
            return count
        except Exception as e:
            logger.error(f"获取文档数量失败: {e}")
            return 0

    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        从向量存储中删除文档

        Args:
            ids: 要删除的文档ID列表
            where: 元数据过滤条件，删除满足条件的所有文档
        """
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"删除 {len(ids)} 个文档")
            elif where:
                # ChromaDB不直接支持通过where删除，需要先查询再删除
                results = self.collection.get(where=where)
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                    logger.info(f"通过条件删除 {len(results['ids'])} 个文档")
            else:
                logger.warning("删除操作需要指定ids或where条件")
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            raise

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档

        Args:
            doc_id: 文档ID

        Returns:
            文档内容，如果不存在则返回None
        """
        try:
            results = self.collection.get(ids=[doc_id])
            if results['ids'] and results['ids'][0]:
                return {
                    'id': results['ids'][0],
                    'text': results['documents'][0] if results['documents'] else '',
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            return None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None

    def clear(self) -> None:
        """清空向量存储中的所有文档"""
        try:
            # 删除并重新创建集合
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Financial news vector storage"}
            )
            logger.info(f"已清空向量存储集合: {self.collection_name}")
        except Exception as e:
            logger.error(f"清空向量存储失败: {e}")
            raise


# 全局向量存储实例
vector_store = VectorStore()
