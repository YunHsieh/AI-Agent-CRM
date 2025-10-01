import traceback
from http.client import HTTPException

import uvicorn
import logfire

from fastapi import FastAPI
from cores.settings import SETTINGS
from orchestrator import Orchestrator
from pydantic import BaseModel

logfire.configure(
    send_to_logfire=False,
    service_name='ai_agent_crm-dev',
    inspect_arguments=True,
    scrubbing=False,
)

app = FastAPI()
orchestrator = Orchestrator()

logfire.instrument_fastapi(app)


class ProcessRequest(BaseModel):
    message: str


class ProcessResponse(BaseModel):
    status: str
    result: str
    error: str = None


@app.post("/chat", response_model=ProcessResponse)
async def process_request(payload: ProcessRequest):
    try:
        reference_result = await orchestrator.route_task(payload.model_dump())
        result = await orchestrator.preprocess_answer(payload.model_dump(), reference_result)
        return ProcessResponse(status="success", result=result)
    except Exception as e:
        logfire.error(f"Processing error: {str(e)}", exc_info=traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 運行主要的協調服務
    uvicorn.run(app, host="0.0.0.0", port=8000)
