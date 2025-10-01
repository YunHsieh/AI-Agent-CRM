import pathlib

import pandas as pd
import json

from typing import List, Dict, Any
from datetime import datetime
from agents.models import Brand, User, Order, Item, Product
from cores.storages import generate_embedding


def prepare_faq_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """準備 FAQ 資料用於插入"""
    data_list = []

    for _, row in df.iterrows():
        # 組合文字內容用於嵌入
        content_text = f"{row['title']} {row['content']}"

        # 處理標籤
        tags = []
        for i in range(3):  # tags/0, tags/1, tags/2
            tag_col = f'tags/{i}'
            if tag_col in row and pd.notna(row[tag_col]):
                tags.append(row[tag_col])

        embedding = generate_embedding(content_text)

        data_item = {
            "id": hash(row['id']) & 0x7FFFFFFF,
            "doc_id": row['id'],
            "doc_type": "faq",
            "title": row['title'],
            "content": row['content'],
            "vector": embedding,
            "metadata": {
                "url_label": row.get('urls/0/label', ''),
                "url_href": row.get('urls/0/href', ''),
                "image": row.get('images/0', ''),
                "tags": tags
            }
        }
        data_list.append(data_item)

    return data_list


def prepare_classification_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """準備 Classification 資料用於插入"""
    data_list = []

    for _, row in df.iterrows():
        embedding = generate_embedding(row['faq_id'] + row['agent_type'])
        data_item = {
            "id": hash(row['faq_id']) & 0x7FFFFFFF,
            "faq_id": row['faq_id'],
            "agent_type": row['agent_type'],
            "vector": embedding,
        }
        data_list.append(data_item)
    return data_list


def prepare_product_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """準備產品資料用於插入"""
    data_list = []

    for _, row in df.iterrows():
        # 組合文字內容用於嵌入
        content_text = f"{row['name']} {row.get('compatibility_notes', '')}"

        # 處理規格資訊
        specs = {}
        for col in df.columns:
            if col.startswith('specs/'):
                spec_key = col.replace('specs/', '')
                if pd.notna(row[col]):
                    specs[spec_key] = row[col]

        # 生成嵌入向量
        embedding = generate_embedding(content_text)

        data_item = {
            "id": hash(row['sku']) & 0x7FFFFFFF,
            "doc_id": row['sku'],
            "doc_type": "product",
            "title": row['name'],
            "content": content_text,
            "vector": embedding,
            "metadata": {
                "sku": row['sku'],
                "url": row.get('url', ''),
                "image": row.get('images/0', ''),
                "specs": specs,
                "compatibility_notes": row.get('compatibility_notes', '')
            }
        }
        data_list.append(data_item)

    return data_list


def prepare_order_data(json_file_path: str) -> List[dict[str, Any]]:
    """準備訂單資料用於插入"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    orders = []

    for user_id, user_orders in data['orders_db'].items():
        for order_data in user_orders['orders']:
            order = Order(
                id=order_data['order_id'],
                name=f"Order {order_data['order_id']}",
                status=order_data['status'],
                carrier=order_data.get('carrier', ''),
                tracking=order_data.get('tracking', ''),
                eta=datetime.fromisoformat(order_data['eta'].replace('Z', '+00:00')) if order_data.get(
                    'eta') else datetime.now(),
                shipping_address=order_data['shipping_address'],
                contact_phone=order_data['contact_phone'],
                order_url=order_data['order_url'],
                placed_at=datetime.fromisoformat(order_data['placed_at'].replace('Z', '+00:00')),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            orders.append(order.model_dump())

    return orders


def prepare_product_data_from_orders(json_file_path: str) -> List[dict[str, Any]]:
    """從訂單中提取產品資料用於插入"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products_seen = set()
    products = []

    for user_orders in data['orders_db'].values():
        for order in user_orders['orders']:
            for item in order['items']:
                if item['sku'] not in products_seen:
                    products_seen.add(item['sku'])

                    product = Product(
                        id=item['sku'],
                        sku=item['sku'],
                        name=item['name'],
                        quantity=0,  # 庫存資訊在這個資料中不可用
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    products.append(product.model_dump())

    return products


def prepare_user_data_from_orders(json_file_path: str) -> List[dict[str, Any]]:
    """從訂單中提取用戶資料用於插入"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    users = []
    for user_id in data['orders_db'].keys():
        user = User(
            id=user_id,
            name=f"User {user_id}",  # 實際姓名不在資料中
            email=f"{user_id}@example.com",  # 實際 email 不在資料中
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        users.append(user.model_dump())

    return users


def prepare_brand_data_from_orders(json_file_path: str) -> Brand:
    """從訂單資料中提取品牌資料"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return Brand(
        id="jtcg_shop",
        name=data['brand'],
        description=f"{data['brand']} - 專業螢幕支架品牌",
        created_at=datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00'))
    )


def prepare_item_data_from_orders(json_file_path: str) -> List[dict[str, Any]]:
    """從訂單中提取商品項目資料用於插入"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = []
    item_counter = 1

    for user_orders in data['orders_db'].values():
        for order in user_orders['orders']:
            for item_data in order['items']:
                item = Item(
                    id=f"item_{item_counter:06d}",
                    product_id=item_data['sku'],
                    order_id=order['order_id'],
                    created_at=datetime.now()
                )
                items.append(item.model_dump())
                item_counter += 1

    return items
