# AI-Agent-CRM

Customer service multi-agent system for JTCG Shop (workspace accessories).

## Stack
- Python 3.11+, FastAPI, Pydantic AI, OpenAI GPT-4.1
- Milvus (vector DB), SentenceTransformers, FastA2A
- Docker Compose for all services

## Run
```bash
poetry install
docker compose up -d      # starts Milvus, Jaeger, Attu
python3 a2a_services.py   # starts agent services on ports 8001–8007
python3 main.py           # starts API gateway on port 8000
```

## Test
```bash
. ./.env && pytest tests/
```

## Environment Variables
```
OPENAI_API_KEY=
MILVUS_URI=http://localhost:19530
AGENT_URL=http://localhost
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=ai-agent-crm-dev
TOKENIZERS_PARALLELISM=false
```

## Service Ports
| Service | Port |
|---|---|
| API Gateway | 8000 |
| Order Query | 8001 |
| Product Recommendation | 8002 |
| Technical Support | 8003 |
| Policy Information | 8004 |
| Payment & Shipping | 8005 |
| Human Escalation | 8006 |
| Inventory Management | 8007 |

## Agent Instruction Files
All subagent definitions live in `.claude/agents/`. Each file follows the Claude Code subagent format (YAML frontmatter + instructions).

## Design & Frontend Workflow
```
f2e → (implementation report) → design → (review + requirements) → spec
```
- `f2e` implements UI; reports to `design` after each component/page
- `design` reviews against spec, sends design decisions to `spec`
- `spec` maintains the authoritative UI/UX design spec in `.claude/agents/spec.md`

## Key Architecture Notes
- Intent classification is two-stage: vector similarity first, GPT-4 LLM verification when confidence < 0.7
- All agents use RAG via Milvus `faqs` or `products` collections — never fabricate data
- `order_query_agent` requires user_id validation (`u_XXXXXX`) before returning any data
- A2A communication is async; orchestrator polls until task completes or 5-min timeout
