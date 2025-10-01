import datetime
import pydantic

from typing import List, Literal
from pydantic import BaseModel, Field


class Brand(pydantic.BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime.datetime


class User(pydantic.BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class Order(pydantic.BaseModel):
    id: str
    name: str
    status: str
    carrier: str|None
    tracking: str|None
    eta: datetime.datetime
    shipping_address: str
    contact_phone: str
    order_url: str
    placed_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime


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


class IntentCategory(BaseModel):
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


class IntentAnalysisWithContext(BaseModel):
    query: str
    available_categories: List[IntentCategory]
    selected_category: str
    confidence: float
    reasoning: str
