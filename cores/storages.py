import json
import pathlib
import logfire
import time

from cores.settings import SETTINGS
from pymilvus import MilvusClient, DataType
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Union

# Global variables
_client: Optional[MilvusClient] = None
_model: Optional[SentenceTransformer] = None


def initialize_milvus(uri: str = "", model_name: str = "all-MiniLM-L6-v2"):
    """Initializes the Milvus client, embedding model, and ensures the 'products' collection is ready."""
    global _client, _model
    if not uri:
        uri = SETTINGS.MILVUS_URI
    try:
        if _client is None:
            _client = MilvusClient(uri)
        if _model is None:
            _model = SentenceTransformer(model_name)
        logfire.info(f"Milvus client and model initialized successfully: {uri}")

        # Initialize products collection
        COLLECTION_NAME = "products"
        if _client.has_collection(collection_name=COLLECTION_NAME):
            _client.drop_collection(collection_name=COLLECTION_NAME)

        dimension = _model.get_sentence_embedding_dimension()
        _client.create_collection(
            collection_name=COLLECTION_NAME,
            dimension=dimension,
            primary_field_name="id",
            vector_field_name="vector",
            id_type="int",
            metric_type="L2",
            auto_id=True,
        )
        logfire.info(f"Collection '{COLLECTION_NAME}' created.")

        products_path = pathlib.Path(__file__).parent.parent / "dummy_data/products.json"
        if products_path.exists():
            with open(products_path, "r", encoding="utf-8") as f:
                products = json.load(f)

            for product in products:
                product["vector"] = generate_embedding(product["content"])

            _client.insert(collection_name=COLLECTION_NAME, data=products)
            _client.load_collection(collection_name=COLLECTION_NAME)
            # Add a short delay to ensure data is queryable after loading.
            # This is a pragmatic workaround for a potential race condition in the test environment.
            time.sleep(2)
            logfire.info(f"Inserted {len(products)} products and loaded collection '{COLLECTION_NAME}'.")

        return True
    except Exception as e:
        logfire.error(f"Initialization failed: {e}")
        raise


def get_client() -> MilvusClient:
    """Gets the Milvus client instance."""
    if _client is None:
        raise RuntimeError("Milvus client not initialized. Call initialize_milvus() first.")
    return _client


def get_model() -> SentenceTransformer:
    """Gets the embedding model instance."""
    if _model is None:
        raise RuntimeError("Embedding model not initialized. Call initialize_milvus() first.")
    return _model


def generate_embedding(text: str) -> List[float]:
    """Generates a text embedding vector."""
    try:
        model = get_model()
        return model.encode(text).tolist()
    except Exception as e:
        logfire.error(f"Failed to generate embedding: {e}")
        raise


def create_collection(collection_name: str, dimension: int = 384,
                      metric_type: str = "COSINE", consistency_level: str = "Strong",
                      recreate: bool = False) -> bool:
    try:
        client = get_client()

        if recreate and client.has_collection(collection_name):
            client.drop_collection(collection_name)
            logfire.info(f"已刪除現有集合: {collection_name}")

        if not client.has_collection(collection_name):
            client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                metric_type=metric_type,
                consistency_level=consistency_level
            )
            logfire.info(f"集合建立成功: {collection_name}")
            return True
        else:
            logfire.info(f"集合已存在: {collection_name}")
            return True

    except Exception as e:
        logfire.error(f"建立集合失敗: {e}")
        raise


def insert_data(collection_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        client = get_client()
        result = client.insert(collection_name=collection_name, data=data)
        logfire.info(f"成功插入 {len(data)} 筆資料到 {collection_name}")
        return {
            "success": True,
            "inserted_count": len(data),
            "ids": result.get("ids", []),
            "message": f"成功插入 {len(data)} 筆資料"
        }
    except Exception as e:
        logfire.error(f"插入資料失敗: {e}")
        raise


def search_data(collection_name: str, query: str, limit: int = 5,
                output_fields: List[str] = None, filter_expr: str = None) -> List[Dict[str, Any]]:
    """Searches for similar data."""
    try:
        client = get_client()
        query_embedding = generate_embedding(query)
        if output_fields is None:
            output_fields = ["doc_id", "doc_type", "title", "content", "metadata"]
        search_results = client.search(
            collection_name=collection_name,
            data=[query_embedding],
            limit=limit,
            output_fields=output_fields,
            filter=filter_expr
        )
        results = []
        if search_results:
            for hit in search_results[0]:
                entity = hit.get('entity', {})
                result_item = {
                    "id": hit.get("id"),
                    "score": hit.get("distance"),
                    "doc_id": entity.get("doc_id"),
                    "doc_type": entity.get("doc_type"),
                    "title": entity.get("title"),
                    "content": entity.get("content"),
                    "metadata": entity.get("metadata")
                }
                results.append(result_item)
        return results
    except Exception as e:
        logfire.error(f"Search failed: {e}")
        return []


def query_data(collection_name: str, filter_expr: str,
               output_fields: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """查詢資料（基於條件過濾）"""
    try:
        client = get_client()

        if output_fields is None:
            output_fields = ["doc_id", "doc_type", "title", "content", "metadata"]

        results = client.query(
            collection_name=collection_name,
            filter=filter_expr,
            output_fields=output_fields,
            limit=limit
        )

        return results

    except Exception as e:
        logfire.error(f"查詢失敗: {e}")
        return []


def get_by_ids(collection_name: str, ids: List[Union[int, str]],
               output_fields: List[str] = None) -> List[Dict[str, Any]]:
    """根據 ID 獲取資料"""
    try:
        client = get_client()

        if output_fields is None:
            output_fields = ["doc_id", "doc_type", "title", "content", "metadata"]

        results = client.get(
            collection_name=collection_name,
            ids=ids,
            output_fields=output_fields
        )

        return results

    except Exception as e:
        logfire.error(f"根據 ID 獲取資料失敗: {e}")
        return []


def delete_by_ids(collection_name: str, ids: List[Union[int, str]]) -> Dict[str, Any]:
    """根據 ID 刪除資料"""
    try:
        client = get_client()
        result = client.delete(collection_name=collection_name, ids=ids)

        return {
            "success": True,
            "deleted_count": len(ids),
            "message": f"成功刪除 {len(ids)} 筆資料"
        }

    except Exception as e:
        logfire.error(f"刪除資料失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "刪除資料失敗"
        }


def delete_by_filter(collection_name: str, filter_expr: str) -> Dict[str, Any]:
    """根據條件刪除資料"""
    try:
        client = get_client()
        result = client.delete(collection_name=collection_name, filter=filter_expr)

        return {
            "success": True,
            "message": "根據條件刪除資料成功"
        }

    except Exception as e:
        logfire.error(f"根據條件刪除資料失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "刪除資料失敗"
        }


def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """獲取集合統計資訊"""
    try:
        client = get_client()
        stats = client.get_collection_stats(collection_name)
        return stats
    except Exception as e:
        logfire.error(f"獲取集合統計失敗: {e}")
        return {}


def list_collections() -> List[str]:
    """列出所有集合"""
    try:
        client = get_client()
        return client.list_collections()
    except Exception as e:
        logfire.error(f"列出集合失敗: {e}")
        return []


def drop_collection(collection_name: str) -> bool:
    """刪除集合"""
    try:
        client = get_client()
        if client.has_collection(collection_name):
            client.drop_collection(collection_name)
            logfire.info(f"集合已刪除: {collection_name}")
            return True
        else:
            logfire.warning(f"集合不存在: {collection_name}")
            return False
    except Exception as e:
        logfire.error(f"刪除集合失敗: {e}")
        return False


def close_connection():
    """關閉連線"""
    global _client
    if _client:
        _client.close()
        _client = None
