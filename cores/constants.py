from cores.settings import SETTINGS

A2A_SERVICES = {
    "order_query_agent": f"{SETTINGS.AGENT_URL}:8001",
    "product_recommendation_agent": f"{SETTINGS.AGENT_URL}:8002",
    "technical_support_agent": f"{SETTINGS.AGENT_URL}:8003",
    "policy_information_agent": f"{SETTINGS.AGENT_URL}:8004",
    "payment_shipping_agent": f"{SETTINGS.AGENT_URL}:8005",
    "human_escalation_agent": f"{SETTINGS.AGENT_URL}:8006",
    "inventory_management_agent": f"{SETTINGS.AGENT_URL}:8007",
}
