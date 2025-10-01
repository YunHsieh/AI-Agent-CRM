from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.models.openai import OpenAIChatModel

from cores.storages import generate_embedding, get_client

model = OpenAIChatModel("gpt-4.1", provider='openai')

def get_related_faq(query_vector, faq_ids: list):
    """根據查詢向量和FAQ ID列表搜尋相關FAQ"""
    if not faq_ids:
        return []

    client = get_client()
    results = client.search(
        collection_name="faqs",
        data=[query_vector],
        filter=f"doc_id in {faq_ids}",
        output_fields=["id", "doc_id", "doc_type", "title", "content", "metadata"],
        limit=3
    )
    return results


def get_faq_by_ids():
    """獲取技術支援相關的FAQ ID列表"""
    client = get_client()
    results = client.query(
        collection_name="classification",
        filter='agent_type == "inventory_management_agent"',
        output_fields=["faq_id"],
        limit=100
    )
    # 提取 faq_id 列表
    faq_ids = [result["faq_id"] for result in results if "faq_id" in result]
    return faq_ids


def process_data(data: str) -> str:
    """處理資料並返回相關FAQ信息"""
    try:
        # 生成查詢向量
        query_vector = generate_embedding(data)
        faq_ids = get_faq_by_ids()

        if not faq_ids:
            return f"未找到相關FAQ資料。原始查詢：{data}"

        related_faqs = get_related_faq(query_vector, faq_ids)
        if not related_faqs:
            return f"未找到與查詢相關的FAQ。原始查詢：{data}"
        hits = related_faqs[0] if related_faqs and len(related_faqs) > 0 else []
        # 格式化返回結果
        result_text = f"根據查詢「{data}」找到以下相關FAQ：\n\n"
        for i, faq in enumerate(hits, 1):
            title = faq.get("title", "未知標題")
            content = faq.get("content", "無內容")
            ref_url = faq.get("metadata", {}).get("url_href", "無參考連結")
            result_text += f"{i}. {title}\n說明: {content}\n參考連結: {ref_url}\n"

        return result_text

    except Exception as e:
        raise

inventory_management_agent = Agent(
    model,
    system_prompt='你是一個庫存管理的系統，根據相關庫存內容給予回應',
    tools=[Tool(process_data, name='process_data')]
)
