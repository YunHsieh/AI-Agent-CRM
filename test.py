from agents.inventory_management_agent import process_data
from cores.storages import initialize_milvus

initialize_milvus()
print(process_data("發票可以開三聯式嗎？結帳時要填什麼？"))
