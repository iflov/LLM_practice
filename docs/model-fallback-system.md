# 🔄 모델 폴백(Fallback) 시스템

무료 모델의 사용량 제한(Rate Limit)에 도달했을 때 자동으로 다른 무료 모델로 전환하는 시스템입니다.

## 🚀 주요 기능

1. **자동 모델 전환**: Rate limit 에러 발생 시 자동으로 다음 모델로 전환
2. **우선순위 관리**: 성능이 좋은 모델부터 순차적으로 사용
3. **실패 추적**: 모델별 실패 횟수를 추적하여 문제 있는 모델 회피
4. **Tool 지원 확인**: Tool calling이 필요한 경우 지원 모델만 선택

## 📋 지원 모델 목록

### Tool Calling 지원 무료 모델 (우선순위 순)
1. `google/gemini-2.0-flash-exp:free` - Google의 최신 무료 모델
2. `deepseek/deepseek-chat-v3-0324:free` - DeepSeek의 강력한 무료 모델
3. `google/gemini-1.5-flash:free` - Gemini 1.5 무료 버전
4. `google/gemini-1.5-flash-8b:free` - 경량화된 Gemini 모델

### 백업 모델 (Tool 미지원)
- `meta-llama/llama-3.2-3b-instruct:free` - 기본 대화용 백업

## 🛠️ 설정 방법

### 1. 파일 구조
```
app/
├── core/
│   └── model_config.py  # 모델 설정 및 관리
├── agents/
│   └── langchain_agent.py  # 폴백 로직 구현
└── routers/
    └── chat.py  # API 엔드포인트
```

### 2. 환경 변수 (.env)
```bash
# Model (자동 관리됨)
DEFAULT_MODEL=google/gemini-2.0-flash-exp:free
```

## 📊 작동 방식

1. **초기 모델 선택**: 우선순위가 가장 높은 모델로 시작
2. **에러 감지**: 429 에러, rate limit, quota 관련 에러 감지
3. **실패 카운트**: 실패 시 해당 모델의 실패 횟수 증가
4. **모델 전환**: 3회 실패 시 다음 우선순위 모델로 자동 전환
5. **성공 시 복구**: 성공하면 실패 카운트 감소

## 🧪 테스트 방법

### 1. 서버 실행
```bash
python3 main.py
```

### 2. 모델 상태 확인
```bash
# 현재 모델 상태 조회
curl http://localhost:8000/api/chat/models
```

### 3. 폴백 테스트
```bash
python3 test_model_fallback.py
```

## 📡 API 엔드포인트

### GET /api/chat/models
현재 모델 상태 및 사용 가능한 모델 목록 조회

**응답 예시**:
```json
{
  "current_model": "google/gemini-2.0-flash-exp:free",
  "models": [
    {
      "id": "google/gemini-2.0-flash-exp:free",
      "name": "Gemini 2.0 Flash Experimental",
      "supports_tools": true,
      "is_current": true,
      "failure_count": 0,
      "is_available": true
    },
    {
      "id": "deepseek/deepseek-chat-v3-0324:free",
      "name": "DeepSeek Chat V3",
      "supports_tools": true,
      "is_current": false,
      "failure_count": 0,
      "is_available": true
    }
  ]
}
```

## ⚡ 성능 최적화

1. **캐싱**: 성공한 모델은 우선적으로 재사용
2. **병렬 처리**: 가능한 경우 여러 모델 동시 시도
3. **타임아웃**: 응답이 없는 모델은 빠르게 스킵

## 🐛 문제 해결

### Rate Limit 계속 발생하는 경우
1. 모든 무료 모델의 사용량을 초과했을 수 있습니다
2. 잠시 기다린 후 다시 시도하세요
3. 유료 모델 사용을 고려하세요

### 특정 모델이 계속 실패하는 경우
1. `model_config.py`에서 해당 모델의 우선순위를 낮추거나 제거
2. OpenRouter 대시보드에서 모델 상태 확인

## 🔍 로그 확인

```bash
# 모델 전환 로그 확인
tail -f logs/app.log | grep -E "(Switching from|Rate limit|Model .* failed)"
```

## 📈 향후 개선 사항

1. **동적 우선순위**: 성공률에 따른 자동 우선순위 조정
2. **비용 최적화**: 무료 한도 내에서 최대한 활용
3. **모델별 특성 활용**: 각 모델의 강점에 맞는 작업 할당
4. **실시간 모니터링**: 모델 상태 대시보드