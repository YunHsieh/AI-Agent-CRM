import json

import pytest
from agents.order_query_agent import order_data


def test_order_data():
    result = order_data("我要查詢我的訂單 u_12345")
    assert isinstance(result, str)

def test_order_validation():
    result = order_data("我要查詢 u_invalid")
    assert "用戶必須提供" in result
