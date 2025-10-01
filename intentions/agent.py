from typing import Dict

import logfire
from pydantic_ai import Agent

from intentions.router import RouterOutput, IntentionRouter

router_config = IntentionRouter()

# 建立分類代理
router_agent = Agent(
    "openai:gpt-4",
    system_prompt=f"""你是一個智能客服路由器，負責將用戶查詢分派給最適合的專業代理。

可用的代理類型：
{router_config.build_categories_description()}

請根據用戶查詢內容，選擇最適合的代理並說明理由。
""",
    output_type=RouterOutput,
    instrument=True,
)


@logfire.instrument('ai-agent-classify_intent')
async def classify_intent(query: str, context: Dict = None):
    """分類用戶意圖"""
    # 先使用向量相似度快速匹配
    routing_result = router_config.route_with_context(query, context)
    logfire.info("classify_intent.routing_result", routing_result=routing_result)

    # 如果置信度較低，使用 LLM 進行二次判斷
    if routing_result["confidence"] < 0.7:
        prompt = f"""
用戶查詢："{query}"

初步匹配結果：
- 建議代理：{routing_result["selected_agent"]}
- 置信度：{routing_result["confidence"]:.2f}
- 其他候選：{routing_result.get("all_scores", {})}

請重新評估並選擇最適合的代理。
"""
        llm_result = await router_agent.run(prompt)
        return llm_result.output

    return RouterOutput(
        selected_agent=routing_result["selected_agent"],
        confidence=routing_result["confidence"],
        reasoning=routing_result["reasoning"]
    )
