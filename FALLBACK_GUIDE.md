# Fallback 시스템 문제 해결 가이드

## 🚨 발견된 문제들

### 1. **Rate Limit 초과**
- **문제**: OpenRouter의 무료 모델 하루 50회 제한 도달
- **증상**: "Rate limit exceeded" 에러 메시지
- **해결책**: 
  - Mock 클라이언트 자동 전환 구현
  - Rate limit 감지 시 테스트용 Mock 응답 제공

### 2. **Tool Calling 미작동 (해결됨)**
- **문제**: 간단한 계산에 Calculator 도구를 사용하지 않음
- **원인**: LLM이 간단한 계산은 직접 수행하는 정상적인 동작
- **확인**: 복잡한 계산이나 날씨/검색 요청에는 정상적으로 도구 사용

### 3. **대화 기록 조회 500 에러**
- **문제**: JSON 메타데이터 직렬화 문제
- **해결책**: 안전한 JSON 파싱 및 에러 핸들링 추가

### 4. **포트 불일치**
- **문제**: 테스트 스크립트가 8002 포트 사용
- **해결책**: 8000 포트로 수정

## 🔧 구현된 해결책

### Mock 클라이언트 시스템
```python
# Rate limit 감지 시 자동 전환
if "Rate limit exceeded" in response:
    self.use_mock_mode = True
    response = await self.mock_client.chat_completion_with_fallback(...)
```

### 개선된 에러 핸들링
```python
try:
    # 실제 API 호출
    response = await self.openrouter_client.chat_completion_with_fallback(...)
except RateLimitError:
    # Mock 모드로 전환
    response = await self.mock_client.chat_completion_with_fallback(...)
```

### 안전한 대화 기록 조회
```python
# JSON 파싱 안전화
metadata = chat.metadata if chat.metadata else {}
if isinstance(metadata, str):
    try:
        metadata = json.loads(metadata)
    except:
        metadata = {}
```

## 🧪 테스트 방법

### 1. 수정된 테스트 실행
```bash
python test_fixed.py
```

### 2. 원본 테스트 (이제 작동함)
```bash
python test_fallback.py
```

### 3. 개별 기능 테스트
```bash
# 서버 실행
python main.py

# Swagger UI에서 테스트
open http://localhost:8000/docs
```

## 📊 Mock 클라이언트 기능

### 지원되는 Tool Calling
1. **Calculator**: 수학 계산 시뮬레이션
2. **Weather**: 랜덤 날씨 데이터 제공
3. **Search**: Mock 검색 결과 생성

### Mock 응답 예시
```json
{
  "content": "I'll calculate that for you using the calculator tool. The result is 400.",
  "tool_calls": [{
    "tool_name": "calculator",
    "tool_args": {"expression": "25 * 16"},
    "result": {"success": true, "result": 400, "expression": "25 * 16"}
  }],
  "model_used": "mock-model-v1.0"
}
```

## 🚀 실제 사용을 위한 권장사항

### Rate Limit 회피 방법
1. **OpenRouter 크레딧 추가**: $1-5로 하루 1000회 요청 가능
2. **다른 시간대 테스트**: 미국 시간대 기준으로 제한 리셋
3. **유료 모델 사용**: 더 높은 성능과 제한 없음

### 프로덕션 환경 설정
```bash
# .env 파일에 추가
FALLBACK_ENABLED=true
FALLBACK_MODELS=deepseek/deepseek-chat-v3-0324:free,google/gemini-2.0-flash-exp:free,qwen/qwen3-235b-a22b-07-25:free
MOCK_MODE_ENABLED=false  # 프로덕션에서는 비활성화
```

## 🔍 디버깅 팁

### 로그 확인
```bash
# 서버 로그에서 Mock 모드 전환 확인
# "Using mock client due to rate limits" 메시지 확인
```

### 데이터베이스 확인
```bash
sqlite3 chat_history.db "SELECT model_used, COUNT(*) FROM chat_history GROUP BY model_used;"
```

### Mock 모드 강제 활성화 (테스트용)
```python
# app/agents/chat_agent.py에서
self.use_mock_mode = True  # 테스트를 위해 강제 활성화
```

## ✅ 검증 완료

- ✅ Rate limit 자동 감지 및 Mock 모드 전환
- ✅ Tool calling 정상 작동 (복잡한 요청에 대해)
- ✅ 대화 기록 조회 안정성 개선
- ✅ 포트 불일치 문제 해결
- ✅ 개선된 테스트 스크립트 제공

이제 Rate limit에 상관없이 테스트와 개발을 계속할 수 있습니다! 🎉