# LLM Agent Backend Server

> Agent 기반 LLM 백엔드 서버 POC (Proof of Concept) 프로젝트

## 🎯 프로젝트 개요

이 프로젝트는 OpenRouter를 통해 다양한 LLM 모델을 사용하고, Agent 시스템을 통해 지능적으로 사용자 요청을 처리하는 백엔드 서버입니다.

### 주요 기능

- **API Gateway**: FastAPI 기반의 RESTful API + SSE (Server-Sent Events) 지원
- **OpenRouter 통합**: 다양한 LLM 모델 (Claude, GPT-4 등) 통합 관리
- **Agent 시스템**: 
  - Analyzer Agent: 사용자 요청 분석
  - Planner Agent: 실행 계획 수립
  - 추가 Agent 확장 가능
- **실시간 스트리밍**: SSE를 통한 실시간 응답 스트리밍

## 🚀 Quick Start

### Option 1: Using pip (Recommended for beginners)

1. Clone the repository and set up environment:
```bash
# Clone repository
git clone <repository-url>
cd LLM_practice

# Copy environment variables
cp .env.example .env
# Edit .env and set your OPENROUTER_API_KEY
```

2. Run the server:
```bash
# Use the provided script
./run_server.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Option 2: Using uv (Faster package manager)

1. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create Python environment and install dependencies:
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Run the server:
```bash
uv run python main.py
# or if venv is activated
python main.py
```

## 📁 Project Structure

```
.
├── src/
│   ├── api/         # API endpoints
│   ├── agents/      # Agent implementations
│   ├── core/        # Core configurations
│   ├── db/          # Database models
│   ├── services/    # Business logic
│   └── utils/       # Utilities
├── tests/           # Test files
├── docs/            # Documentation
├── main.py          # Application entry point
├── pyproject.toml   # Project configuration
└── .env.example     # Environment variables template
```

## 🛠️ Development

### Run with auto-reload:
```bash
uv run python main.py
```

### Run tests:
```bash
uv run pytest
```

### Format code:
```bash
uv run black .
uv run ruff check . --fix
```

### Type checking:
```bash
uv run mypy src/
```

## 📡 API Usage

### Test the API

Run the test script:
```bash
python test_api.py
```

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. List Available Models
```bash
curl http://localhost:8000/api/v1/chat/models
```

#### 3. Chat Completion (Regular)
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

#### 4. Chat Completion (Agent System)
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "/agent Write a Python function"}],
    "stream": true
  }'
```

### API Documentation

Once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Agent     │
└─────────────┘     └─────────────┘     │   Manager   │
       SSE                │             └─────────────┘
                          │                     │
                          ▼                     ▼
                   ┌─────────────┐     ┌─────────────┐
                   │ OpenRouter  │     │   Agents    │
                   └─────────────┘     │ - Analyzer  │
                                       │ - Planner   │
                                       │ - Executor  │
                                       └─────────────┘
```

### Components

- **API Gateway**: FastAPI with SSE support
- **LLM Routing**: OpenRouter integration
- **Agent System**: Autonomous agents for task execution
- **Caching**: Redis for session and response caching (planned)
- **Database**: SQLite for metadata persistence (planned)
- **Protocol**: JSON-RPC for inter-agent communication


## 🚦 Development Status

### Completed ✅
- Project structure and dependency management
- API Gateway with SSE support
- OpenRouter integration module
- Basic Agent system (Analyzer, Planner)
- Streaming response handling

### In Progress 🚧
- Agent routing and response aggregation
- Additional agent implementations

### Planned 📋
- Redis caching layer
- SQLite database schema
- Executor, Router, and Aggregator agents
- Enhanced error handling
- Performance optimizations

## 🤝 Contributing

This is a POC project. Feel free to open issues for suggestions or improvements.

## 📝 License

This project is under the MIT License.
