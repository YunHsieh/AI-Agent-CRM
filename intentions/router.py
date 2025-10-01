"""
這邊可以使用 vector 做 intentions 的加強
"""

import json
import pathlib
from typing import Dict
import logfire
from pydantic import BaseModel, Field
import numpy as np
from sentence_transformers import SentenceTransformer
from pydantic_ai import Agent


class RouterOutput(BaseModel):
    """路由器輸出格式"""
    selected_agent: str = Field(description="選中的代理")
    confidence: float = Field(description="置信度")
    reasoning: str = Field(description="推理過程")


class IntentionRouter:
    """用向量的方式分配路由"""

    def __init__(self):
        # 載入意圖配置
        intentions_path = pathlib.Path("dummy_data/intentions.json")
        self.intentions_config = json.load(intentions_path.open())

        # 初始化語意編碼器
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # 建立意圖向量索引
        self._build_intention_index()

    def _build_intention_index(self):
        """建立意圖向量索引"""
        self.agent_examples = {}
        self.agent_embeddings = {}

        for agent_name, examples in self.intentions_config.items():
            self.agent_examples[agent_name] = examples
            # 將所有範例編碼為向量
            embeddings = self.encoder.encode(examples)
            self.agent_embeddings[agent_name] = embeddings

    def build_categories_description(self) -> str:
        """建構分類描述"""
        descriptions = []
        for agent_name, examples in self.intentions_config.items():
            descriptions.append(f"- {agent_name}: {','.join(examples)}")
        return "\n".join(descriptions)

    def find_best_agent(self, query: str, threshold: float = 0.5) -> Dict[str, float]:
        """找到最適合的代理"""
        query_embedding = self.encoder.encode([query])

        agent_scores = {}

        for agent_name, examples_embeddings in self.agent_embeddings.items():
            # 計算查詢與所有範例的相似度
            similarities = np.dot(query_embedding, examples_embeddings.T)[0]

            # 使用最高相似度作為該代理的分數
            max_similarity = np.max(similarities)

            if max_similarity > threshold:
                agent_scores[agent_name] = float(max_similarity)

        return agent_scores

    def route_with_context(self, query: str, context: Dict = None) -> Dict:
        """帶上下文的路由"""
        # 基本意圖匹配
        agent_scores = self.find_best_agent(query)

        # 如果有上下文，可以調整分數
        if context:
            agent_scores = self._adjust_scores_with_context(agent_scores, context)

        if not agent_scores:
            return {
                "selected_agent": "human_escalation_agent",
                "confidence": 0.3,
                "reasoning": "無法識別用戶意圖，轉接人工客服"
            }

        # 選擇分數最高的代理
        best_agent = max(agent_scores, key=agent_scores.get)
        confidence = agent_scores[best_agent]

        return {
            "selected_agent": best_agent,
            "confidence": confidence,
            "reasoning": f"基於語意相似度匹配，置信度: {confidence:.2f}",
            "all_scores": agent_scores
        }

    def _adjust_scores_with_context(self, scores: Dict[str, float], context: Dict) -> Dict[str, float]:
        """根據上下文調整分數"""
        adjusted_scores = scores.copy()

        # 如果有用戶ID或訂單號，提升訂單查詢代理分數
        if any(key in str(context).lower() for key in ['user_id', 'order', 'jtcg-']):
            if 'order_query_agent' in adjusted_scores:
                adjusted_scores['order_query_agent'] *= 1.2

        # 如果提到具體產品規格，提升產品推薦代理分數
        if any(key in str(context).lower() for key in ['吋', 'vesa', '支架', 'mm']):
            if 'product_recommendation_agent' in adjusted_scores:
                adjusted_scores['product_recommendation_agent'] *= 1.1
            if 'technical_support_agent' in adjusted_scores:
                adjusted_scores['technical_support_agent'] *= 1.1

        return adjusted_scores
