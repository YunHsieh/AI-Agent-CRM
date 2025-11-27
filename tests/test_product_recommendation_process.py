import pytest

from agents.product_recommendation_agent import get_related_products, process_data
from cores.storages import generate_embedding, initialize_milvus


@pytest.fixture(scope="module", autouse=True)
def setup_milvus():
    """Initializes Milvus before running tests in this module."""
    initialize_milvus()


@pytest.mark.parametrize("text", [
    "我想直接看重載臂，請挑一支最穩的給我。",
])
def test_product_recommendation_agent(text):
    """Tests both get_related_products and process_data with the same input."""
    # Test get_related_products
    query_vector = generate_embedding(text)
    related_products = get_related_products(query_vector)
    assert len(related_products) > 0, "get_related_products should return results"

    # Test process_data
    processed_result = process_data(text)
    assert len(processed_result) > 0, "process_data should return a non-empty string"
    assert "根據查詢" in processed_result, "process_data output should contain the original query"
