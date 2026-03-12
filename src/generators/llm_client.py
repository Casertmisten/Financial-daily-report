"""LLM客户端模块，提供统一的LLM调用接口"""
from typing import List, Dict, Optional
from loguru import logger
import json
from openai import OpenAI
from config.settings import config


class LLMClient:
    """LLM客户端，支持聊天、清洗和向量化功能"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        clean_model: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        初始化LLM客户端

        Args:
            base_url: API基础URL
            api_key: API密钥
            chat_model: 聊天模型名称
            clean_model: 清洗模型名称
            embedding_model: 向量化模型名称
        """
        self.base_url = base_url or config.llm.base_url
        self.api_key = api_key or config.llm.api_key
        self.chat_model = chat_model or config.llm.chat_model
        self.clean_model = clean_model or config.llm.clean_model
        self.embedding_model = embedding_model or config.embedding.embedding_model

        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.embedding_client = OpenAI(
            base_url=config.embedding.base_url,
            api_key=config.embedding.api_key
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        通用聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 使用的模型，默认使用chat_model
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型回复的文本内容
        """
        model = model or self.chat_model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            content = response.choices[0].message.content
            logger.debug(f"LLM chat成功，模型: {model}")
            return content
        except Exception as e:
            logger.error(f"LLM chat失败: {e}")
            raise

    def clean(
        self,
        text: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> Dict:
        """
        数据清洗接口，返回结构化的清洗结果

        Args:
            text: 待清洗的文本
            model: 使用的模型，默认使用clean_model
            temperature: 温度参数，清洗任务使用较低温度
            **kwargs: 其他参数

        Returns:
            清洗结果字典，包含：
            - cleaned_content: 清洗后的内容
            - entities: 提取的实体列表
            - sentiment: 情感倾向
            - importance: 重要性评分(1-5)
            - tags: 标签列表
            - is_trash: 是否为垃圾信息
        """
        model = model or self.clean_model

        system_prompt = """你是一个专业的金融新闻数据清洗助手。请对输入的新闻内容进行清洗和结构化提取。

请严格按照以下JSON格式返回结果：
{
    "cleaned_content": "清洗后的新闻内容，去除HTML标签和冗余信息",
    "entities": ["提取的实体列表，如公司名、人名等"],
    "sentiment": "情感倾向，可选值: positive/neutral/negative",
    "importance": 1-5的整数，表示新闻重要性",
    "tags": ["相关标签，如行业、概念等"],
    "is_trash": false
}

判断标准：
- importance: 5=重大突发, 4=重要公告, 3=常规新闻, 2=轻微影响, 1=无实际内容
- is_trash: 广告、重复内容、无实际信息等应标记为true
- sentiment: 根据对公司/市场的影响判断"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            logger.debug(f"LLM clean成功，模型: {model}")
            return result
        except Exception as e:
            logger.error(f"LLM clean失败: {e}")
            # 返回默认值，确保不会中断流程
            return {
                "cleaned_content": text,
                "entities": [],
                "sentiment": "neutral",
                "importance": 3,
                "tags": [],
                "is_trash": False
            }

    def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[List[float]]:
        """
        向量化接口，将文本转换为向量

        Args:
            texts: 待向量化的文本列表
            model: 使用的模型，默认使用embedding_model
            **kwargs: 其他参数

        Returns:
            向量列表，每个向量是一个浮点数列表
        """
        model = model or self.embedding_model

        try:
            # 批量处理，每次最多处理100个文本
            all_embeddings = []
            batch_size = 100

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self.embedding_client.embeddings.create(
                    model=model,
                    input=batch,
                    **kwargs
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

            logger.debug(f"LLM embed成功，处理 {len(texts)} 个文本，模型: {model}")
            return all_embeddings
        except Exception as e:
            logger.error(f"LLM embed失败: {e}")
            raise


# 全局LLM客户端实例
llm_client = LLMClient()
