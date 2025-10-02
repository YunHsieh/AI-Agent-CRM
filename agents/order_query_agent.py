import json
import pathlib
import re

import logfire
from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings

from agents.models import Order, OrderQueryInput
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

@logfire.instrument('process_data')
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


def query_order_data():
    '''TODO: it will be get information from DB
    '''
    order_path = pathlib.Path('dummy_data/orders.json')
    orders = []

    for user_id, user_data in json.load(order_path.open())['orders_db'].items():
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

order_checker_agent = Agent(
    model,
    system_prompt=f"""根據輸入內容，記錄重要資訊""",
    output_type=OrderQueryInput,
)


@logfire.instrument('order-data')
def order_data(data: OrderQueryInput) -> str:
    # result = order_checker_agent.run_sync(data)
    # result = result.output
    logfire.info(f"agent data: {data}")
    is_complete = True
    content = '用戶必須提供\n'
    if not data.user_id or not re.match(r'u_\d{6}', data.user_id):
        content += "- user_id 格式應為 e.g. u_123456\n"
        is_complete = False
    # if not result.order_id or not re.match(r'JTCG-.*', result.order_id):
    #     content += "- order_id 格式應為 e.g. JTCG-202508-12345\n"
    #     is_complete = False
    if is_complete:
        return query_order_data()
    return content + "提供以上資訊才可以為用戶查詢相關資料"


# TODO: check 訂單 id 正確性
order_query_agent = Agent(
    model,
    system_prompt='''你是訂單處理專家。

**重要流程**:
1. 收到任何訂單查詢時,**第一步務必**呼叫 order_data 工具來驗證用戶身份與取得訂單資料
2. 如果 order_data 回傳驗證失敗訊息(包含「用戶必須提供」),直接將該訊息回覆給用戶
3. 如果 order_data 回傳 JSON 格式的訂單資料,請解析並提供完整說明
4. 如果用戶詢問 FAQ 相關問題,使用 process_data 工具搜尋相關資訊

**嚴格遵守**:
- 不要編造或臆測任何訂單資訊
- 只依據工具回傳的實際內容回答，工具沒有提供任何資訊就直接回傳「請提供 user_id 為您查詢」
- 工具未回傳相關資料時,明確告知用戶無法找到資訊
''',
    tools=[Tool(order_data, name='order_data', takes_ctx=False),
        Tool(process_data, name='process_data', takes_ctx=False),
    ],
    instrument=True,
)
