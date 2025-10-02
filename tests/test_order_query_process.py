import json

import pytest
from agents.order_query_agent import order_data


def test_order_data():
    result = order_data("")
    assert isinstance(result, str)
