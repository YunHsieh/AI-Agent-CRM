import json
import pathlib

from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.models.openai import OpenAIChatModel

from agents.models import Order
from cores.storages import get_client, generate_embedding

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
    # 修正 query 方法的使用
    results = client.query(
        collection_name="classification",
        filter='agent_type == "order_query_agent"',
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

def order_data(data: str) -> str:
    '''TODO: it will be get information from DB
    '''
    order = pathlib.Path('dummy_data/orders.json')
    orders = []

    for user_id, user_data in json.load(order.open())['orders_db'].items():
        for order_info in user_data["orders"]:
            order = Order(
                order_id=order_info["order_id"],
                status=order_info["status"],
                carrier=order_info.get("carrier"),
                tracking=order_info.get("tracking"),
                eta=order_info.get("eta"),
                shipping_address=order_info["shipping_address"],
                contact_phone=order_info["contact_phone"],
                order_url=order_info["order_url"],
                placed_at=order_info["placed_at"],
                user_id=user_id,
                items=order_info.get("items", [])
            )
            orders.append(order)

    return json.dumps(
        [order.model_dump() for order in orders],
        default=str,
        ensure_ascii=False,
        indent=2
    )


# 創建 pydantic-ai Agent
# TODO: check 訂單 id 正確性
order_query_agent = Agent(
    model,
    system_prompt='''你是一個訂單處理專家，專門針對訂單相關資訊回覆
    
如需要查詢訂單，必須要提供 order_id 

當用戶詢問政策相關問題時，你必須使用 process_data 工具來搜尋相關的FAQ資料。

基於工具返回的資料提供準確、完整的政策說明，不要編造或臆測任何資訊。
如果工具沒有返回相關資料，請告知用戶無法找到相關政策資訊。
    ''',
    tools=[Tool(process_data, name='process_data'),
           Tool(order_data, name='order_data')],
)
