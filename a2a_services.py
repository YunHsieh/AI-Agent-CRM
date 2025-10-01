import uvicorn
import asyncio
from cores.settings import SETTINGS
import logfire
from agents.a2a_apps import (
    order_query_app,
    product_recommendation_app,
    technical_support_app,
    policy_information_app,
    payment_shipping_app,
    human_escalation_app,
    inventory_management_app,
)

logfire.configure(
    send_to_logfire=False,
    service_name='a2a_services-dev',
    inspect_arguments=True,
    scrubbing=False,
)

logfire.instrument_fastapi(order_query_app)
logfire.instrument_fastapi(product_recommendation_app)
logfire.instrument_fastapi(technical_support_app)
logfire.instrument_fastapi(policy_information_app)
logfire.instrument_fastapi(payment_shipping_app)
logfire.instrument_fastapi(human_escalation_app)
logfire.instrument_fastapi(inventory_management_app)


async def log_rpc_params_middleware(request, call_next, service_name: str):
    """通用的 RPC 參數記錄中間件"""
    if request.method == "POST":
        body = await request.body()
        logfire.info(f"{service_name} RPC Request",
                     method=request.method,
                     url=str(request.url),
                     body=body.decode() if body else None,
                     service=service_name)

    response = await call_next(request)
    return response


@order_query_app.middleware("http")
async def log_order_query_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "order_query_agent")

@product_recommendation_app.middleware("http")
async def log_product_recommendation_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "product_recommendation_agent")

@technical_support_app.middleware("http")
async def log_technical_support_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "technical_support_agent")

@policy_information_app.middleware("http")
async def log_policy_information_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "policy_information_agent")

@payment_shipping_app.middleware("http")
async def log_payment_shipping_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "payment_shipping_agent")

@human_escalation_app.middleware("http")
async def log_human_escalation_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "human_escalation_agent")

@inventory_management_app.middleware("http")
async def log_inventory_management_rpc(request, call_next):
    return await log_rpc_params_middleware(request, call_next, "inventory_management_agent")


async def run_order_query_agent_service():
    config = uvicorn.Config(order_query_app, host="0.0.0.0", port=8001)
    server = uvicorn.Server(config)
    await server.serve()


async def run_product_recommendation_agent_service():
    config = uvicorn.Config(product_recommendation_app, host="0.0.0.0", port=8002)
    server = uvicorn.Server(config)
    await server.serve()


async def run_technical_support_agent_service():
    config = uvicorn.Config(technical_support_app, host="0.0.0.0", port=8003)
    server = uvicorn.Server(config)
    await server.serve()


async def run_policy_information_agent_service():
    config = uvicorn.Config(policy_information_app, host="0.0.0.0", port=8004)
    server = uvicorn.Server(config)
    await server.serve()


async def run_payment_shipping_agent_service():
    config = uvicorn.Config(payment_shipping_app, host="0.0.0.0", port=8005)
    server = uvicorn.Server(config)
    await server.serve()


async def run_human_escalation_agent_service():
    config = uvicorn.Config(human_escalation_app, host="0.0.0.0", port=8006)
    server = uvicorn.Server(config)
    await server.serve()


async def run_inventory_management_agent_service():
    config = uvicorn.Config(inventory_management_app, host="0.0.0.0", port=8007)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main function to run all services concurrently"""
    await asyncio.gather(
        run_order_query_agent_service(),
        run_product_recommendation_agent_service(),
        run_technical_support_agent_service(),
        run_policy_information_agent_service(),
        run_payment_shipping_agent_service(),
        run_human_escalation_agent_service(),
        run_inventory_management_agent_service(),
    )

if __name__ == "__main__":
    # Run all services concurrently
    asyncio.run(main())
