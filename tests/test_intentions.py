import pytest
import json

from intentions.agent import IntentionRouter
from . import constants
import json

@pytest.fixture
def dummy_intention_file(tmp_path):
    """建立假 intentions.json 檔案"""
    path = tmp_path / "intentions.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(constants.DUMMY_INTENTIONS, f, ensure_ascii=False)
    return path


@pytest.fixture
def router(monkeypatch, dummy_intention_file):
    """建立 IntentionRouter，並覆蓋掉預設路徑"""
    def dummy_init(self):
        self.intentions_config = constants.DUMMY_INTENTIONS
        from sentence_transformers import SentenceTransformer
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self._build_intention_index()

    monkeypatch.setattr(IntentionRouter, "__init__", dummy_init)
    return IntentionRouter()


def test_build_categories_description(router):
    desc = router.build_categories_description()
    for k in constants.DUMMY_INTENTIONS:
        assert k in desc


@pytest.mark.parametrize("text,answer", [
    ("發票可以開三聯式嗎？結帳時要填什麼？", "policy_information_agent"),
    ("我想查詢訂單狀態", "order_query_agent"),
    ("請問有什麼優惠活動", "payment_shipping_agent"),
    ("香草今天想要退貨", "policy_information_agent"),
    ("我要查詢訂單", "order_query_agent"),
    pytest.param("複雜的查詢", "human_escalation_agent", id="complex_query"),
])
def test_find_best_agent_product(router, text, answer):
    scores = router.find_best_agent(text)
    max_key = max(scores, key=scores.get)
    assert max_key == answer


def test_route_with_context_order(router):
    result = router.route_with_context("查詢訂單", context={"user_id": "12345"})
    assert result["selected_agent"] == "order_query_agent"
    assert result["confidence"] > 0.5
    assert "基於語意相似度" in result["reasoning"]
