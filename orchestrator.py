import asyncio
from uuid import uuid4

import httpx
import logfire
from fasta2a.schema import MessageSendConfiguration

from pydantic import Field
from typing import Any, List
from pydantic_ai import Agent
from pydantic_ai.tools import Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic import BaseModel

from fasta2a.client import A2AClient, Message

from cores import constants
from cores.settings import SETTINGS
from intentions.agent import router_config, classify_intent

model = OpenAIChatModel("gpt-4.1", provider='openai')


class ServiceContext(BaseModel):
    """Service context for A2A calls"""
    service: str = Field(..., description="Service name")
    msg: str = Field(..., description="Specific message for service")


class Orchestrator:
    def __init__(self):
        # A2A 服務端點
        self.services = constants.A2A_SERVICES
        self.default_timeout = httpx.Timeout(
            connect=10,
            read=60 * 2,  # 2分鐘讀取超時
            write=10,
            pool=10
        )

        self.orchestrator_agent = Agent(
            model,
            system_prompt='你是一個協調者，負責分派任務給適當的服務。並且回傳詳細的資料給使用者。',
            tools=[Tool(self.call_a2a_services, name='call_services')]
        )

    @logfire.instrument('ai-agent-dispatcher')
    async def call_a2a_services(self, service_ctx: List[ServiceContext]) -> str | List[Any]:
        """呼叫 A2A 服務 並根據各種意圖去查詢"""
        result = []
        for _ctx in service_ctx:
            if _ctx.service not in self.services:
                result.append(f"未知的服務: {_ctx.service}: {_ctx.msg}")
                continue
            async with httpx.AsyncClient(timeout=self.default_timeout) as http_client:
                a2a_client = A2AClient(
                    base_url=self.services[_ctx.service],
                    http_client=http_client
                )

                # 設定 blocking 配置
                configuration = MessageSendConfiguration(
                    accepted_output_modes=["text/plain", "application/json"],
                    blocking=False
                )

                message = Message(
                    role='user',
                    kind='message',
                    message_id=f"msg_{_ctx.service}_{uuid4().hex[:8]}",
                    parts=[{"kind": "text", "text": _ctx.msg}]
                )

                response = await a2a_client.send_message(
                    message=message,
                    configuration=configuration
                )
                task_status = response
                if task_id := response["result"]["id"]:
                    _c = 0
                    # 輪詢直到完成
                    while _c <= 30:
                        task_status = await a2a_client.get_task(task_id)
                        logfire.info(f"A2A get task route", task_status=task_status)
                        if task_status["result"]["status"]["state"] in ['completed', 'failed']:
                            break
                        await asyncio.sleep(1)
                        _c += 1

                logfire.info(f"A2A send message route", response=task_status)

                if 'result' in task_status and 'artifacts' in task_status['result']:
                    combine_text = ''
                    for artifact in task_status['result']['artifacts']:
                        for part in artifact.get('parts', []):
                            if part.get('kind') == 'text':
                                combine_text += part.get('text', '') + '\n'
                    result.append(combine_text.strip())
                else:
                    result.append(f"服務 {_ctx.service} 沒有返回預期結果")
        return '\n'.join(result)

    @logfire.instrument('ai-agent-router')
    async def route_task(self, payload: dict) -> str:
        """路由任務到適當的服務"""
        text = payload["message"]

        # 提取可能的上下文信息
        context = {
            "user_info": payload.get("user_info"),
            "session_id": payload.get("session_id"),
            "previous_queries": payload.get("history", [])
        }

        # 根據意圖結果構建服務調用
        intent_result = await classify_intent(text, context)
        selected_agent = intent_result.selected_agent

        enhanced_prompt = f'''
基於意圖分析結果：
- 選定代理：{selected_agent}
- 置信度：{intent_result.confidence:.2f}
- 推理：{intent_result.reasoning}

用戶原始請求：{text}

請將此請求轉換為適當的服務調用。可調用多個相關服務以提供更全面的回答。

可用服務 maintains：
{router_config.build_categories_description()}
'''
        logfire.info("enhanced prompt", enhanced_prompt=enhanced_prompt)
        # 使用 orchestrator agent 來決定如何處理
        result = await self.orchestrator_agent.run(enhanced_prompt)
        return result.output

    @logfire.instrument('ai-agent-preprocess')
    async def preprocess_answer(self, payload: dict, data: str) -> str:
        preprocess_agent = Agent(
            model=model,
            retries=3,
            system_prompt="""你是 JTCG Shop 的 AI 客服助手，專門協助螢幕臂、壁掛支架等工作空間配件的諮詢服務。""",
            instrument=True,
        )

        enhanced_prompt = f'''
## 回應原則
- **語言一致**：立即跟隨用戶最新訊息的語言
- **字詞精簡**：將回應濃縮成 50 字左右並且使用建議的方式，再透過延伸方式給予使用者適合的提問進而補充
- **有憑有據**：只使用工具返回的資料，不臆測編造
- **下一步明確**：每次回覆都給出可立即執行的行動建議的問題

## 邊界處理
- 非相關問題：禮貌重導回四大功能範圍
- 資料不足：說明「目前無法確認」並提供替代方案
- 只使用工具提供的圖片連結，不外抓圖片

使用者的問題: {payload["message"]}
回應: {data}
        '''
        result = await preprocess_agent.run(enhanced_prompt)
        return result.output
