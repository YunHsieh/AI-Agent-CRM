"""
將 agent 轉換為 A2A 應用程式
任務細分化
個別處理任務
"""
from agents.order_query_agent import order_query_agent
from agents.human_escalation_agent import human_escalation_agent
from agents.inventory_management_agent import inventory_management_agent
from agents.payment_shipping_agent import payment_shipping_agent
from agents.policy_information_agent import policy_information_agent
from agents.product_recommendation_agent import product_recommendation_agent
from agents.technical_support_agent import technical_support_agent
from cores import constants
from cores.settings import SETTINGS
from cores.storages import initialize_milvus

initialize_milvus()

order_query_app = order_query_agent.to_a2a(
    name="order_query_service",
    url=constants.A2A_SERVICES['order_query_agent'],
    description="訂單資訊服務",
    version="1.0.0"
)

product_recommendation_app = product_recommendation_agent.to_a2a(
    name="product_recommendation_service",
    url=constants.A2A_SERVICES['product_recommendation_agent'],
    description="商品建議服務",
    version="1.0.0"
)

technical_support_app = technical_support_agent.to_a2a(
    name="technical_support_service",
    url=constants.A2A_SERVICES['technical_support_agent'],
    description="技術支援服務",
    version="1.0.0"
)

policy_information_app = policy_information_agent.to_a2a(
    name="policy_information_service",
    url=constants.A2A_SERVICES['policy_information_agent'],
    description="政策訊息服務",
    version="1.0.0"
)

payment_shipping_app = payment_shipping_agent.to_a2a(
    name="payment_shipping_service",
    url=constants.A2A_SERVICES['payment_shipping_agent'],
    description="付款及配送服務",
    version="1.0.0"
)

human_escalation_app = human_escalation_agent.to_a2a(
    name="human_escalation_service",
    url=constants.A2A_SERVICES['human_escalation_agent'],
    description="真人客服",
    version="1.0.0"
)

inventory_management_app = inventory_management_agent.to_a2a(
    name="inventory_management_service",
    url=constants.A2A_SERVICES['inventory_management_agent'],
    description="庫存管理服務",
    version="1.0.0"
)
