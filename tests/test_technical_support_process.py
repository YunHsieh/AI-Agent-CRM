import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.technical_support_agent import (
    get_related_faq,
    get_faq_by_ids,
    process_data,
    technical_support_agent
)


class TestGetRelatedFaq:
    """測試 get_related_faq 函數"""

    @patch('agents.technical_support_agent.get_client')
    def test_get_related_faq_success(self, mock_get_client):
        """測試成功獲取相關FAQ"""
        # 模擬客戶端和搜索結果
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = [
            {
                "id": "1",
                "doc_id": "faq_001",
                "doc_type": "FAQ",
                "title": "螢幕支架安裝問題",
                "content": "如果螢幕沒有VESA孔，可以使用夾式支架",
                "metadata": {"category": "技術支援"}
            }
        ]
        mock_client.search.return_value = mock_results

        query_vector = [0.1, 0.2, 0.3]
        faq_ids = ["faq_001", "faq_002"]

        result = get_related_faq(query_vector, faq_ids)

        # 驗證結果
        assert result == mock_results
        mock_client.search.assert_called_once_with(
            collection_name="faqs",
            data=[query_vector],
            filter=f"doc_id in {faq_ids}",
            output_fields=["id", "doc_id", "doc_type", "title", "content", "metadata"],
            limit=3
        )

    def test_get_related_faq_empty_ids(self):
        """測試空的FAQ ID列表"""
        query_vector = [0.1, 0.2, 0.3]
        faq_ids = []

        result = get_related_faq(query_vector, faq_ids)

        assert result == []


class TestGetFaqByIds:
    """測試 get_faq_by_ids 函數"""

    @patch('agents.technical_support_agent.get_client')
    def test_get_faq_by_ids_success(self, mock_get_client):
        """測試成功獲取FAQ ID列表"""
        # 模擬客戶端和查詢結果
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = [
            {"faq_id": "faq_001"},
            {"faq_id": "faq_002"},
            {"faq_id": "faq_003"}
        ]
        mock_client.query.return_value = mock_results

        result = get_faq_by_ids()

        # 驗證結果
        expected_ids = ["faq_001", "faq_002", "faq_003"]
        assert result == expected_ids

        mock_client.query.assert_called_once_with(
            collection_name="classification",
            filter='agent_type == "technical_support_agent"',
            output_fields=["faq_id"],
            limit=100
        )

    @patch('agents.technical_support_agent.get_client')
    def test_get_faq_by_ids_with_missing_faq_id(self, mock_get_client):
        """測試結果中有缺少faq_id的情況"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = [
            {"faq_id": "faq_001"},
            {"other_field": "value"},  # 缺少faq_id
            {"faq_id": "faq_003"}
        ]
        mock_client.query.return_value = mock_results

        result = get_faq_by_ids()

        # 應該只返回有faq_id的結果
        expected_ids = ["faq_001", "faq_003"]
        assert result == expected_ids


class TestProcessData:
    """測試 process_data 函數"""

    @patch('agents.technical_support_agent.get_related_faq')
    @patch('agents.technical_support_agent.get_faq_by_ids')
    @patch('agents.technical_support_agent.generate_embedding')
    def test_process_data_success(self, mock_generate_embedding, mock_get_faq_by_ids, mock_get_related_faq):
        """測試成功處理數據"""
        # 設置模擬數據
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_faq_by_ids.return_value = ["faq_001", "faq_002"]

        mock_faq_results = [[
            {
                "title": "螢幕支架安裝問題",
                "content": "如果螢幕沒有VESA孔，可以使用夾式支架或者轉接器",
                "url_href": "https://example.com/faq/001"
            },
            {
                "title": "支架重量承載",
                "content": "一般支架可承載5-10公斤重量",
                "url_href": "https://example.com/faq/002"
            }
        ]]
        mock_get_related_faq.return_value = mock_faq_results

        query = "螢幕沒有VESA孔可以怎麼裝"
        result = process_data(query)

        # 驗證結果格式
        assert "根據查詢「螢幕沒有VESA孔可以怎麼裝」找到以下相關FAQ：" in result
        assert "1. 螢幕支架安裝問題" in result
        assert "如果螢幕沒有VESA孔，可以使用夾式支架或者轉接器" in result
        assert "2. 支架重量承載" in result

        # 驗證函數調用
        mock_generate_embedding.assert_called_once_with(query)
        mock_get_faq_by_ids.assert_called_once()
        mock_get_related_faq.assert_called_once_with([0.1, 0.2, 0.3], ["faq_001", "faq_002"])

    @patch('agents.technical_support_agent.get_faq_by_ids')
    @patch('agents.technical_support_agent.generate_embedding')
    def test_process_data_no_faq_ids(self, mock_generate_embedding, mock_get_faq_by_ids):
        """測試沒有找到FAQ ID的情況"""
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_faq_by_ids.return_value = []

        query = "測試查詢"
        result = process_data(query)

        assert result == "未找到相關FAQ資料。原始查詢：測試查詢"

    @patch('agents.technical_support_agent.get_related_faq')
    @patch('agents.technical_support_agent.get_faq_by_ids')
    @patch('agents.technical_support_agent.generate_embedding')
    def test_process_data_no_related_faqs(self, mock_generate_embedding, mock_get_faq_by_ids, mock_get_related_faq):
        """測試沒有找到相關FAQ的情況"""
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_faq_by_ids.return_value = ["faq_001"]
        mock_get_related_faq.return_value = []

        query = "無關查詢"
        result = process_data(query)

        assert result == "未找到與查詢相關的FAQ。原始查詢：無關查詢"

    @patch('agents.technical_support_agent.get_related_faq')
    @patch('agents.technical_support_agent.get_faq_by_ids')
    @patch('agents.technical_support_agent.generate_embedding')
    def test_process_data_with_missing_fields(self, mock_generate_embedding, mock_get_faq_by_ids, mock_get_related_faq):
        """測試FAQ結果中缺少某些字段的情況"""
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_get_faq_by_ids.return_value = ["faq_001"]

        # 模擬缺少某些字段的FAQ結果
        mock_faq_results = [[
            {
                "content": "只有內容沒有標題",
                # 缺少 title 和 url_href
            },
            {
                "title": "只有標題",
                # 缺少 content 和 url_href
            }
        ]]
        mock_get_related_faq.return_value = mock_faq_results

        query = "測試查詢"
        result = process_data(query)

        # 驗證默認值被使用
        assert "1. 未知標題" in result
        assert "只有內容沒有標題" in result
        assert "無參考連結" in result
        assert "2. 只有標題" in result
        assert "無內容" in result

    @patch('agents.technical_support_agent.generate_embedding')
    def test_process_data_exception_handling(self, mock_generate_embedding):
        """測試異常處理"""
        # 模擬生成embedding時拋出異常
        mock_generate_embedding.side_effect = Exception("Connection error")

        query = "測試查詢"

        with pytest.raises(Exception):
            process_data(query)


# 集成測試
class TestIntegration:
    """集成測試"""

    @patch('agents.technical_support_agent.get_client')
    @patch('agents.technical_support_agent.generate_embedding')
    def test_full_workflow(self, mock_generate_embedding, mock_get_client):
        """測試完整的工作流程"""
        # 模擬整個流程
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 模擬 get_faq_by_ids 的結果
        mock_client.query.return_value = [
            {"faq_id": "faq_001"},
            {"faq_id": "faq_002"}
        ]

        # 模擬 get_related_faq 的結果
        mock_client.search.return_value = [[
            {
                "title": "VESA支架安裝指南",
                "content": "使用轉接器或夾式支架解決無VESA孔問題",
                "url_href": "https://example.com/guide"
            }
        ]]

        query = "螢幕沒有VESA孔怎麼辦"
        result = process_data(query)

        # 驗證完整流程
        assert "根據查詢「螢幕沒有VESA孔怎麼辦」找到以下相關FAQ：" in result
        assert "VESA支架安裝指南" in result
        assert "使用轉接器或夾式支架解決無VESA孔問題" in result


# 測試夾具 (Fixtures)
@pytest.fixture
def sample_faq_data():
    """提供示例FAQ數據"""
    return [
        {
            "id": "1",
            "doc_id": "faq_001",
            "title": "螢幕支架安裝",
            "content": "安裝步驟說明",
            "url_href": "https://example.com/faq1"
        },
        {
            "id": "2",
            "doc_id": "faq_002",
            "title": "重量承載",
            "content": "承載重量說明",
            "url_href": "https://example.com/faq2"
        }
    ]


@pytest.fixture
def sample_query_vector():
    """提供示例查詢向量"""
    return [0.1, 0.2, 0.3, 0.4, 0.5]
