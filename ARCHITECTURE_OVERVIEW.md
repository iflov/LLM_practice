# 아키텍처 개요

## 🎯 프로젝트 목표

LLM Agent 개발 경험을 쌓기 위한 POC 프로젝트로, 다음을 학습하고 구현:
- Agent 시스템의 기본 구조
- Tool calling 메커니즘
- 프롬프트 엔지니어링
- 대화 상태 관리

## 🏛️ 시스템 아키텍처

### 레이어드 아키텍처

```
┌────────────────────────────────────────────────┐
│                  Presentation Layer             │
│                   (FastAPI Routes)              │
├────────────────────────────────────────────────┤
│                  Business Layer                 │
│               (Agents & Tools)                  │
├────────────────────────────────────────────────┤
│                  Service Layer                  │
│        (OpenRouter, Session Manager)            │
├────────────────────────────────────────────────┤
│                    Data Layer                   │
│             (Redis, SQLite)                     │
└────────────────────────────────────────────────┘
```

### 컴포넌트 다이어그램

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │ HTTP/SSE
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │   Server    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼───────┐  ┌──────▼──────┐
│    Agent     │  │Session Manager │  │   Router    │
│   Manager    │  │    (Redis)     │  │   (API)     │
└───────┬──────┘  └────────────────┘  └─────────────┘
        │
┌───────▼──────────────────────────┐
│         LangChain Agent          │
│  ┌─────────┐  ┌──────────────┐  │
│  │ Memory  │  │Tool Executor │  │
│  └─────────┘  └──────┬───────┘  │
└───────────────────────┼──────────┘
                        │
              ┌─────────┼─────────┐
       ┌──────▼──┐ ┌───▼───┐ ┌───▼────┐
       │Calculator│ │Weather│ │ Search │
       └─────────┘ └───────┘ └────────┘
```

## 🔄 데이터 플로우

### 1. 메시지 처리 플로우
```
User Input → API Gateway → Session Validation → Agent Processing
    ↓                                               ↓
Response ← Format Response ← Save History ← Execute Tools
```

### 2. Tool Calling 플로우
```
1. User: "What's the weather in Seoul?"
2. Agent: Analyze intent → Need weather tool
3. Tool: Execute weather.run(city="Seoul")
4. Agent: Format tool result
5. Response: "The weather in Seoul is..."
```

## 💾 데이터 모델

### Redis 세션 구조
```json
{
  "session_id": "uuid",
  "created_at": "2024-01-01T00:00:00",
  "messages": [
    {
      "role": "user|assistant",
      "content": "message text",
      "timestamp": "2024-01-01T00:00:00",
      "metadata": {}
    }
  ],
  "context": {
    "current_tool": "calculator",
    "last_action": "calculate"
  }
}
```

### SQLite 스키마
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(100),
    user_message TEXT,
    assistant_message TEXT,
    tools_used JSON,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost FLOAT,
    created_at DATETIME,
    extra_metadata JSON
);
```

## 🔐 보안 고려사항

1. **API Key 관리**: 환경 변수로 관리
2. **세션 검증**: 모든 요청에서 세션 유효성 확인
3. **입력 검증**: Pydantic 모델로 자동 검증
4. **Rate Limiting**: (TODO) 구현 필요
5. **CORS 설정**: 허용된 도메인만 접근 가능

## 🚀 확장 가능성

### 1. 추가 가능한 도구들
- **Database Query**: SQL 쿼리 실행
- **File Operations**: 파일 읽기/쓰기
- **External APIs**: 실제 날씨, 뉴스 API 연동
- **Code Execution**: 코드 실행 환경

### 2. Agent 개선 방향
- **Multi-Agent**: 전문 분야별 Agent 협업
- **Memory 개선**: 장기 기억, 사용자 선호도
- **Planning**: 복잡한 작업을 위한 계획 수립
- **Self-Reflection**: Agent의 자기 평가

### 3. 인프라 개선
- **Message Queue**: RabbitMQ/Kafka for 비동기 처리
- **Vector DB**: 의미 검색을 위한 Pinecone/Weaviate
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker/Kubernetes 배포

## 📊 성능 고려사항

1. **캐싱 전략**
   - Redis: 활성 세션 (TTL 1시간)
   - LRU 캐시: 자주 사용되는 도구 결과

2. **비동기 처리**
   - 모든 I/O 작업은 async/await
   - 동시 요청 처리 가능

3. **토큰 최적화**
   - 대화 기록 압축
   - 불필요한 컨텍스트 제거

## 🧪 테스트 전략

1. **단위 테스트**: 각 도구 및 서비스
2. **통합 테스트**: API 엔드포인트
3. **E2E 테스트**: 전체 대화 플로우
4. **부하 테스트**: 동시 접속자 처리