import logfire
from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.models.openai import OpenAIChatModel

from cores.storages import get_client, generate_embedding

model = OpenAIChatModel("gpt-4.1", provider='openai')

# def get_related_faq(query_vector, faq_ids: list):
#     """根據查詢向量和FAQ ID列表搜尋相關FAQ"""
#     if not faq_ids:
#         return []
#
#     client = get_client()
#     results = client.search(
#         collection_name="faqs",
#         data=[query_vector],
#         filter=f"doc_id in {faq_ids}",
#         output_fields=["id", "doc_id", "doc_type", "title", "content", "metadata"],
#         limit=3
#     )
#     return results


# def get_faq_by_ids():
#     """獲取技術支援相關的FAQ ID列表"""
#     client = get_client()
#     # 修正 query 方法的使用
#     results = client.query(
#         collection_name="classification",
#         filter='agent_type == "technical_support_agent"',
#         output_fields=["faq_id"],
#         limit=100
#     )
#     # 提取 faq_id 列表
#     faq_ids = [result["faq_id"] for result in results if "faq_id" in result]
#     return faq_ids


def get_related_products(query_vector):
    """根據查詢向量列表搜尋相關的 products 資訊"""
    client = get_client()
    results = client.search(
        collection_name="products",
        data=[query_vector],
        output_fields=["id", "doc_id", "doc_type", "title", "content", "metadata"],
        limit=3
    )
    return results


@logfire.instrument('process_data')
def process_data(data: str) -> str:
    """處理資料並返回相關 Products 資訊"""
    try:
        query_vector = generate_embedding(data)
        related_products = get_related_products(query_vector)
        if not related_products:
            return f"未找到與查詢相關的 Product 資訊。原始查詢：{data}"
        hits = related_products[0] if related_products and len(related_products) > 0 else []
        if not hits:
            return f"未找到與查詢相關的 Product 資訊。原始查詢：{data}"
        # 格式化返回結果
        result_text = f"根據查詢「{data}」找到以下相關FAQ：\n\n"
        for i, faq in enumerate(hits, 1):
            title = faq.get("title", "未知標題")
            content = faq.get("content", "無內容")
            ref_url = faq.get("metadata", {}).get("url", "無參考連結")
            result_text += f"{i}. {title}\n說明: {content}\n參考連結: {ref_url}\n"
        return result_text
    except Exception as e:
        raise

# 創建 pydantic-ai Agent
product_recommendation_agent = Agent(
    model,
    system_prompt='''你是一個自家的產品推薦者

**嚴格只**依據 process_data 工具返回的內容。如果工具沒有找到相關或沒有匹配的資料，請**務必只回復「未找到相關產品」**，
**禁止**自行推薦、推論或引入任何資料庫外的產品品牌、資訊或建議。只可以將 process_data 返回文本原樣呈現。

基於工具返回的資料提供準確、完整的政策說明，不要編造或臆測任何資訊。
如果工具沒有返回相關資料，請告知用戶無法找到相關政策資訊。
''',
    tools=[Tool(process_data, name='process_data')],
    instrument=True,
)
