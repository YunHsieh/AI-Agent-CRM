import json

import pytest

from agents.product_recommendation_agent import get_related_products, process_data
from cores.storages import generate_embedding, initialize_milvus


@pytest.mark.parametrize("text,answer", [
    ("我想直接看重載臂，請挑一支最穩的給我。", "policy_information_agent"),
])
def test_order_data(text, answer):
    initialize_milvus()
    query_vector = generate_embedding(text)
    result = get_related_products(query_vector)
    result = json.loads(result)
    assert len(result) > 0


@pytest.mark.parametrize("text,answer", [
    ("我想直接看重載臂，請挑一支最穩的給我。", "policy_information_agent"),
])
def test_order_data(text, answer):
    initialize_milvus()
    result = process_data(text)
    assert len(result) > 0
