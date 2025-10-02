import datetime
import pydantic

from typing import List, Literal, Optional
from pydantic import Field


class User(pydantic.BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class Order(pydantic.BaseModel):
    order_id: str
    status: str
    carrier: Optional[str] = None
    tracking: Optional[str] = None
    eta: Optional[datetime.date] = None
    shipping_address: str
    contact_phone: str
    order_url: str
    placed_at: datetime.datetime
    items: List[dict] = []
    user_id: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = datetime.datetime.now()


class Brand(pydantic.BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime.datetime


class Item(pydantic.BaseModel):
    id: str
    product_id: str
    order_id: str
    created_at: datetime.datetime


class Product(pydantic.BaseModel):
    id: str
    sku: str
    name: str
    quantity: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class IntentCategory(pydantic.BaseModel):
    name: Literal[
        "order_query_agent",
        "product_recommendation_agent",
        "technical_support_agent",
        "policy_information_agent",
        "payment_shipping_agent",
        "human_escalation_agent",
        "inventory_management_agent"
    ]
    description: str = Field(..., description="意圖類別的詳細描述")
    keywords: List[str] = Field(..., description="關鍵字範例列表")
    patterns: List[str] = Field(default=[], description="常見的查詢模式")


class IntentAnalysisWithContext(pydantic.BaseModel):
    query: str
    available_categories: List[IntentCategory]
    selected_category: str
    confidence: float
    reasoning: str


class OrderQueryInput(pydantic.BaseModel):
    """整理後的訂單查詢輸入"""
    user_id: Optional[str] = Field(None, description="用戶ID，格式如: u_123456")
    order_id: Optional[str] = Field(None, description="訂單ID，格式如: JTCG-202508-10001")
    original_message: str = Field(..., description="用戶的原始訊息")
