# AI Agent CRM Architecture Documentation

## Project Overview

AI Agent CRM is an intelligent customer service system designed for JTCG Shop (工作空間配件專門店), specializing in monitor arms, wall mounts, and workspace accessories. The system uses a microservices architecture with specialized AI agents to handle different types of customer inquiries.

## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Client Applications]
        API[REST API Requests]
    end
    
    subgraph "Gateway Layer"
        Main[Main Service :8000<br/>FastAPI Gateway]
        Orchestrator[Orchestrator<br/>Request Router & Processor]
    end
    
    subgraph "Intelligence Layer"
        IntentionRouter[Intention Router<br/>Vector-based Intent Classification]
        IntentionAgent[Intention Agent<br/>LLM-based Intent Verification]
    end
    
    subgraph "Microservices Layer"
        A2A_Services[A2A Services Manager]
        subgraph "Specialized Agents"
            OrderAgent[Order Query Agent :8001]
            ProductAgent[Product Recommendation Agent :8002]
            TechAgent[Technical Support Agent :8003]
            PolicyAgent[Policy Information Agent :8004]
            PaymentAgent[Payment & Shipping Agent :8005]
            HumanAgent[Human Escalation Agent :8006]
            InventoryAgent[Inventory Management Agent :8007]
        end
    end
    
    subgraph "Data Layer"
        Milvus[(Milvus Vector DB<br/>FAQ & Product Search)]
        JsonData[(JSON Data Files<br/>Orders & Configuration)]
    end
    
    subgraph "External Services"
        OpenAI[OpenAI GPT-4<br/>Language Model]
        Logfire[Logfire<br/>Monitoring & Logging]
        Jaeger[Jaeger<br/>Distributed Tracing]
    end
    
    Client --> API
    API --> Main
    Main --> Orchestrator
    Orchestrator --> IntentionRouter
    IntentionRouter --> IntentionAgent
    Orchestrator --> A2A_Services
    A2A_Services --> OrderAgent
    A2A_Services --> ProductAgent
    A2A_Services --> TechAgent
    A2A_Services --> PolicyAgent
    A2A_Services --> PaymentAgent
    A2A_Services --> HumanAgent
    A2A_Services --> InventoryAgent
    
    OrderAgent --> Milvus
    ProductAgent --> Milvus
    TechAgent --> Milvus
    PolicyAgent --> Milvus
    OrderAgent --> JsonData
    
    IntentionRouter --> OpenAI
    IntentionAgent --> OpenAI
    OrderAgent --> OpenAI
    ProductAgent --> OpenAI
    TechAgent --> OpenAI
    PolicyAgent --> OpenAI
    PaymentAgent --> OpenAI
    HumanAgent --> OpenAI
    InventoryAgent --> OpenAI
    
    Main --> Logfire
    A2A_Services --> Logfire
    Main --> Jaeger
```

### Request Flow Architecture

```mermaid
sequenceDiagram
    participant Client
    participant MainService as Main Service
    participant Orchestrator
    participant IntentionRouter as Intention Router
    participant IntentionAgent as Intention Agent
    participant A2AClient as A2A Client
    participant SpecializedAgent as Specialized Agent
    participant VectorDB as Milvus Vector DB
    participant LLM as OpenAI GPT-4

    Client->>MainService: POST /chat {"message": "query"}
    MainService->>Orchestrator: route_task(payload)
    
    Note over Orchestrator,IntentionAgent: Intent Classification Phase
    Orchestrator->>IntentionRouter: find_best_agent(query, context)
    IntentionRouter->>VectorDB: Vector similarity search
    VectorDB-->>IntentionRouter: Similarity scores
    
    alt Confidence < 0.7
        IntentionRouter->>IntentionAgent: LLM verification
        IntentionAgent->>LLM: Classify intent
        LLM-->>IntentionAgent: Verified classification
        IntentionAgent-->>IntentionRouter: RouterOutput
    else Confidence >= 0.7
        IntentionRouter-->>Orchestrator: Direct classification
    end
    
    Note over Orchestrator,SpecializedAgent: Service Dispatch Phase
    Orchestrator->>A2AClient: call_a2a_services(service_contexts)
    
    loop For each service context
        A2AClient->>SpecializedAgent: send_message(message)
        SpecializedAgent->>VectorDB: Search relevant data
        SpecializedAgent->>LLM: Process with context
        SpecializedAgent-->>A2AClient: Processed response
    end
    
    A2AClient-->>Orchestrator: Combined responses
    
    Note over Orchestrator,LLM: Response Processing Phase
    Orchestrator->>LLM: preprocess_answer(query, responses)
    LLM-->>Orchestrator: Final formatted answer
    Orchestrator-->>MainService: Final response
    MainService-->>Client: ProcessResponse
```

### Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Input Processing"
        UserQuery[User Query]
        Context[Context Extraction]
        VectorEmbedding[Vector Embedding Generation]
    end
    
    subgraph "Intent Classification"
        VectorSearch[Vector Similarity Search]
        ConfidenceCheck{Confidence >= 0.7?}
        LLMVerification[LLM Intent Verification]
        IntentResult[Selected Agent & Confidence]
    end
    
    subgraph "Knowledge Retrieval"
        FAQRetrieval[FAQ Retrieval from Milvus]
        ProductRetrieval[Product Data Retrieval]
        OrderRetrieval[Order Data from JSON]
        PolicyRetrieval[Policy Information Retrieval]
    end
    
    subgraph "Agent Processing"
        AgentContext[Agent-specific Context Building]
        LLMProcessing[LLM Processing with RAG]
        ResponseGeneration[Structured Response Generation]
    end
    
    subgraph "Output Processing"
        ResponseCombination[Multi-agent Response Combination]
        Preprocessing[Response Preprocessing]
        FinalOutput[Final User Response]
    end
    
    UserQuery --> Context
    UserQuery --> VectorEmbedding
    VectorEmbedding --> VectorSearch
    VectorSearch --> ConfidenceCheck
    
    ConfidenceCheck -->|No| LLMVerification
    ConfidenceCheck -->|Yes| IntentResult
    LLMVerification --> IntentResult
    
    IntentResult --> FAQRetrieval
    IntentResult --> ProductRetrieval
    IntentResult --> OrderRetrieval
    IntentResult --> PolicyRetrieval
    
    FAQRetrieval --> AgentContext
    ProductRetrieval --> AgentContext
    OrderRetrieval --> AgentContext
    PolicyRetrieval --> AgentContext
    
    AgentContext --> LLMProcessing
    LLMProcessing --> ResponseGeneration
    ResponseGeneration --> ResponseCombination
    ResponseCombination --> Preprocessing
    Preprocessing --> FinalOutput
```

## Component Details

### 1. Main Service (`main.py`)
- **Purpose**: FastAPI gateway service
- **Port**: 8000
- **Responsibilities**:
  - Handle incoming HTTP requests
  - Route to orchestrator
  - Return formatted responses
  - Logging and error handling

### 2. Orchestrator (`orchestrator.py`)
- **Purpose**: Central coordination service
- **Responsibilities**:
  - Intent classification coordination
  - A2A service orchestration
  - Response preprocessing
  - Context management

### 3. Intention System (`intentions/`)

#### IntentionRouter (`intentions/router.py`)
- **Purpose**: Vector-based intent classification
- **Technology**: SentenceTransformer + numpy
- **Features**:
  - Multi-language support (paraphrase-multilingual-MiniLM-L12-v2)
  - Context-aware scoring adjustments
  - Similarity threshold filtering
  - Fallback to human escalation

#### IntentionAgent (`intentions/agent.py`)
- **Purpose**: LLM-based intent verification
- **Model**: GPT-4
- **Use Case**: Low confidence intent classification verification

### 4. Specialized Agents (`agents/`)

Each agent follows the same pattern:
- Pydantic AI Agent with OpenAI GPT-4.1
- Tool-based architecture for data retrieval
- Vector search integration (Milvus)
- Structured response formatting

#### Agent Details:

| Agent | Port | Primary Function | Data Sources |
|-------|------|------------------|--------------|
| Order Query Agent | 8001 | Order status, tracking, history | JSON files, FAQ database |
| Product Recommendation Agent | 8002 | Product suggestions, compatibility | Product database, specifications |
| Technical Support Agent | 8003 | Installation help, troubleshooting | FAQ database, technical docs |
| Policy Information Agent | 8004 | Returns, warranty, invoicing | Policy database |
| Payment & Shipping Agent | 8005 | Payment methods, shipping info | Shipping policies, payment options |
| Human Escalation Agent | 8006 | Complex queries, escalation | N/A (routes to human support) |
| Inventory Management Agent | 8007 | Stock status, availability | Inventory database |

### 5. Data Storage Layer

#### Milvus Vector Database
- **Collections**:
  - `faqs`: FAQ content with vector embeddings
  - `products`: Product information with embeddings
  - `classification`: Agent-FAQ mapping relationships

#### JSON Data Files
- `orders.json`: Order information database
- `intentions.json`: Intent classification examples
- `custom.json`: Custom configuration data

### 6. Core Services (`cores/`)

#### Settings (`cores/settings.py`)
- Environment variable management
- Configuration centralization
- API key handling

#### Constants (`cores/constants.py`)
- Service endpoint definitions
- A2A service URL mapping

#### Storage (`cores/storages.py`)
- Milvus client management
- Vector embedding generation
- CRUD operations for vector data

### 7. A2A (Agent-to-Agent) Communication

The system uses the FastA2A framework for agent communication:
- Asynchronous message passing
- Task-based execution
- Standardized message formats
- Service discovery and routing

## Key Design Patterns

### 1. Microservices Architecture
- Each agent runs as an independent service
- Horizontal scaling capability
- Service isolation and fault tolerance

### 2. RAG (Retrieval-Augmented Generation)
- Vector similarity search for relevant information
- Context injection into LLM prompts
- Knowledge base integration

### 3. Multi-Agent Orchestration
- Centralized coordination through orchestrator
- Context-aware agent selection
- Multi-agent response synthesis

### 4. Event-Driven Architecture
- Asynchronous processing
- Task queuing and management
- Real-time monitoring and logging

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and settings management
- **Pydantic AI**: AI agent framework

### AI/ML Components
- **OpenAI GPT-4/4.1**: Large language models
- **SentenceTransformers**: Text embedding generation
- **Milvus**: Vector database for similarity search
- **NumPy**: Numerical computing

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Uvicorn**: ASGI server

### Monitoring & Observability
- **Logfire**: Application monitoring
- **Jaeger**: Distributed tracing
- **OpenTelemetry**: Observability framework

### Development & Testing
- **Pytest**: Testing framework
- **Poetry**: Dependency management (planned migration)

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=ai-agent-crm-dev
AGENT_URL=http://localhost
TOKENIZERS_PARALLELISM=false
MILVUS_URI=http://localhost:19530
```

### Service Ports
- Main Service: 8000
- Order Query Agent: 8001
- Product Recommendation Agent: 8002
- Technical Support Agent: 8003
- Policy Information Agent: 8004
- Payment & Shipping Agent: 8005
- Human Escalation Agent: 8006
- Inventory Management Agent: 8007

### External Services
- Milvus: 19530
- Jaeger UI: 16686
- Attu (Milvus Admin): 3000
- OTLP Collector: 4318

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Environment"
        subgraph "Application Services"
            MainApp[Main FastAPI App<br/>Port: 8000]
            A2AServices[A2A Services Runner<br/>Ports: 8001-8007]
        end
        
        subgraph "Vector Database"
            Milvus[Milvus Standalone<br/>Port: 19530]
            Etcd[etcd<br/>Metadata Store]
            MinIO[MinIO<br/>Object Storage]
        end
        
        subgraph "Monitoring Stack"
            Jaeger[Jaeger All-in-One<br/>Port: 16686]
            Attu[Attu Web UI<br/>Port: 3000]
        end
    end
    
    subgraph "External Dependencies"
        OpenAI[OpenAI API]
        Logfire[Logfire SaaS]
    end
    
    MainApp --> A2AServices
    A2AServices --> Milvus
    Milvus --> Etcd
    Milvus --> MinIO
    
    MainApp --> Jaeger
    A2AServices --> Jaeger
    MainApp --> Logfire
    A2AServices --> Logfire
    MainApp --> OpenAI
    A2AServices --> OpenAI
    
    Attu --> Milvus
```

## Data Models

### Core Entities

```mermaid
erDiagram
    User ||--o{ Order : places
    Order ||--o{ Item : contains
    Item }o--|| Product : references
    Product }o--|| Brand : belongs_to
    
    User {
        string id PK
        string name
        string email
        datetime created_at
        datetime updated_at
    }
    
    Order {
        string order_id PK
        string status
        string carrier
        string tracking
        date eta
        string shipping_address
        string contact_phone
        string order_url
        datetime placed_at
        string user_id FK
        list items
    }
    
    Product {
        string id PK
        string sku
        string name
        int quantity
        datetime created_at
        datetime updated_at
    }
    
    Item {
        string id PK
        string product_id FK
        string order_id FK
        datetime created_at
    }
    
    Brand {
        string id PK
        string name
        string description
        datetime created_at
    }
```

### Vector Data Structure

```mermaid
graph TD
    subgraph "Milvus Collections"
        subgraph "FAQs Collection"
            FAQID[doc_id: FAQ unique ID]
            FAQType[doc_type: 'faq']
            FAQTitle[title: FAQ title]
            FAQContent[content: FAQ content]
            FAQVector[vector: Embedding vector]
            FAQMeta[metadata: URLs, images, tags]
        end
        
        subgraph "Products Collection"
            ProdID[doc_id: Product SKU]
            ProdType[doc_type: 'product']
            ProdTitle[title: Product name]
            ProdContent[content: Combined text]
            ProdVector[vector: Embedding vector]
            ProdMeta[metadata: Specs, compatibility]
        end
        
        subgraph "Classification Collection"
            ClassFAQ[faq_id: FAQ reference]
            ClassAgent[agent_type: Target agent]
            ClassVector[vector: Classification embedding]
        end
    end
```

## API Documentation

### Main Endpoints

#### POST `/chat`
Process customer queries and return AI-generated responses.

**Request:**
```json
{
    "message": "查詢我的訂單狀態"
}
```

**Response:**
```json
{
    "status": "success",
    "result": "根據您的查詢，我需要您的用戶ID來為您查詢訂單資訊...",
    "error": null
}
```

## Performance Considerations

### Scalability
- Horizontal scaling of individual agent services
- Vector database sharding for large datasets
- Async processing for better throughput

### Optimization
- Vector embedding caching
- Intent classification result caching
- Connection pooling for external services

### Monitoring
- Response time tracking
- Agent performance metrics
- Vector search latency monitoring

## Security Considerations

### API Security
- API key management through environment variables
- Request validation using Pydantic models
- Error handling without sensitive data exposure

### Data Protection
- No hardcoded credentials
- Environment-based configuration
- Secure vector database access

## Future Enhancements

### Planned Features
1. **Database Integration**: Replace JSON files with PostgreSQL
2. **Advanced RAG**: Implement hybrid search (vector + keyword)
3. **Multi-language Support**: Extend beyond Chinese/English
4. **Real-time Learning**: Dynamic intent model updates
5. **A/B Testing**: Intent classification model comparison

### Scalability Improvements
1. **Load Balancing**: Agent service load distribution
2. **Caching Layer**: Redis integration for performance
3. **Queue System**: Async task processing with Celery
4. **Model Serving**: Dedicated embedding service

## Troubleshooting Guide

### Common Issues

1. **Module Import Errors**
   - Solution: Set `PYTHONPATH` to project root
   - Alternative: Install package in development mode

2. **Vector Database Connection**
   - Check Milvus service status
   - Verify connection URI configuration

3. **Agent Communication Failures**
   - Verify all A2A services are running
   - Check service port accessibility

### Development Setup
```bash
# Set environment variables
export PYTHONPATH=$PWD
source .env

# Start infrastructure
docker compose up -d

# Run services
python3 a2a_services.py &  # Background process
python3 main.py           # Main service
```

This architecture provides a robust, scalable, and maintainable foundation for the AI Agent CRM system, with clear separation of concerns and comprehensive monitoring capabilities.