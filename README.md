# AI Agent CRM

## Installation

install dependencies
```bash
# install dependencies
poetry install

# run the apps
docker compose up -d
```

Run the services
```bash
# run a2a services
python3 a2a_services.py

# run main service
python3 main.py
```

## Environment Variables

you'll need to set the following environment variables or add them to your .env file:
```bash
OPENAI_API_KEY={your_api_key}

OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
OTEL_SERVICE_NAME="ai-agent-crm-dev"

AGENT_URL=http://localhost
TOKENIZERS_PARALLELISM=false

MILVUS_URI=http://localhost:19530
```

## Test
```bash
. ./.env
pytest tests/
```

your can test your api with cli
```bash
curl --location 'http://localhost:8000/chat' \
--header 'Content-Type: application/json' \
--data '{
    "message": "發票可以開三聯式嗎？結帳時要填什麼？"
}'
```

```bash
# in the project root directory
export PYTHONPATH=$PWD
python3 scripts/agent_test.py
```
