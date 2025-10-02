import pathlib
import logfire
import pandas as pd

from cores.storages import initialize_milvus, create_collection, insert_data, get_client
from utils.parser import (
    prepare_faq_data,
    prepare_product_data,
    prepare_order_data,
    prepare_user_data_from_orders,
    prepare_brand_data_from_orders,
    prepare_item_data_from_orders,
    prepare_classification_data,
)
logfire.configure(
    send_to_logfire=False,
    service_name='ai_agent_crm-dev',
)
initialize_milvus()
faqs = prepare_faq_data(pd.read_csv(pathlib.Path('dummy_data/ai-eng-test-sample-knowledges.csv')))
classification = prepare_classification_data(pd.read_csv(pathlib.Path('dummy_data/faq-classification.csv')))
products = prepare_product_data(pd.read_csv(pathlib.Path('dummy_data/ai-eng-test-sample-products.csv')))
# 直接得到 Pydantic 模型實例
orders = prepare_order_data('dummy_data/orders.json')
users = prepare_user_data_from_orders('dummy_data/orders.json')
brand = prepare_brand_data_from_orders('dummy_data/orders.json')
items = prepare_item_data_from_orders('dummy_data/orders.json')

create_collection("faqs", recreate=True)
insert_data("faqs", faqs)
create_collection("products", recreate=True)
insert_data("products", products)
create_collection("classification", recreate=True)
insert_data("classification", classification)
# create_collection("orders", recreate=True)
# insert_data("orders", orders)
# create_collection("users", recreate=True)
# insert_data("users", users)
# create_collection("items", recreate=True)
# insert_data("items", items)

client = get_client()
results = client.query(
    collection_name="products",
    filter="id > 0",
    output_fields=["id","doc_id","doc_type","title","content","metadata",],
    limit=10
)
print(results)
