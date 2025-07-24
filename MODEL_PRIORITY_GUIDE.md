# Model Priority and Fallback System Guide

## Overview
이 가이드는 LLM Agent POC의 모델 우선순위 시스템과 폴백 메커니즘을 설명합니다.

## Model Priority System

### 1. DEFAULT_MODEL (최우선)
- `.env` 파일에 설정된 `DEFAULT_MODEL`이 항상 먼저 시도됩니다
- 현재 설정: `google/gemini-2.0-flash-exp:free`
- Tool calling 지원 여부와 무료 여부를 확인 후 사용

### 2. Fallback Models (차순위)
DEFAULT_MODEL이 실패하면 다음 순서로 시도합니다:

1. **moonshotai/kimi-k2:free** (priority: 0)
   - Tool calling 지원
   - 65,536 토큰 컨텍스트

2. **deepseek/deepseek-chat-v3-0324:free** (priority: 1)
   - Tool calling 지원
   - 32,768 토큰 컨텍스트

3. **google/gemini-2.0-flash-exp:free** (priority: 2)
   - Tool calling 지원
   - 1,000,000 토큰 컨텍스트
   - DEFAULT_MODEL과 동일한 경우 중복 제거

4. **google/gemini-flash-1.5-8b** (priority: 3)
   - Tool calling 지원
   - 1,000,000 토큰 컨텍스트

## Configuration

### .env 설정
```env
# 기본 모델 설정
DEFAULT_MODEL=google/gemini-2.0-flash-exp:free

# 폴백 모델 리스트 (우선순위 순서)
FALLBACK_MODELS=deepseek/deepseek-chat-v3-0324:free,google/gemini-2.0-flash-exp:free,qwen/qwen3-235b-a22b-07-25:free
```

### model_config.py 구조
```python
@dataclass
class ModelConfig:
    id: str              # 모델 ID
    name: str            # 표시 이름
    supports_tools: bool # Tool calling 지원 여부
    is_free: bool        # 무료 모델 여부
    context_length: int  # 최대 컨텍스트 길이
    priority: int        # 우선순위 (낮을수록 높음)
```

## 작동 방식

### 1. 모델 선택 프로세스
```
1. DEFAULT_MODEL 확인
   - model_config.py에서 모델 정보 조회
   - Tool/무료 요구사항 충족 확인
   
2. 폴백 모델 리스트 생성
   - get_fallback_models() 호출
   - priority 순으로 정렬
   
3. 중복 제거
   - DEFAULT_MODEL이 폴백 리스트에 있으면 제거
   
4. 순차적 시도
   - DEFAULT_MODEL → 폴백 모델 순서로 시도
```

### 2. 실패 처리
- **Rate Limit**: 다음 모델로 자동 전환
- **API Key Error**: 즉시 중단 (폴백 무의미)
- **모든 모델 실패**: Mock 모드로 전환

## 테스트 방법

### 1. 기본 테스트
```bash
python test_default_model.py
```

### 2. 로그 확인
서버 로그에서 다음 메시지 확인:
```
INFO: Will try DEFAULT_MODEL first: google/gemini-2.0-flash-exp:free
INFO: Trying model: google/gemini-2.0-flash-exp:free
```

### 3. 응답 메타데이터
API 응답의 `metadata.model_used` 필드에서 실제 사용된 모델 확인

## 문제 해결

### DEFAULT_MODEL이 사용되지 않는 경우
1. `.env` 파일 확인
2. `model_config.py`에 해당 모델이 정의되어 있는지 확인
3. 서버 재시작 (`python main.py`)

### 특정 모델 강제 사용
`chat_agent.py`에서 직접 모델 지정 가능:
```python
result = await self.client.chat_completion_with_fallback(
    messages=messages,
    use_tools=True,
    free_only=False  # 유료 모델도 사용
)
```

## 모델 추가 방법

### 1. model_config.py에 모델 추가
```python
ModelConfig(
    id="new-model-id",
    name="New Model Name",
    supports_tools=True,  # Tool calling 지원 여부
    is_free=True,         # 무료 여부
    context_length=32768, # 컨텍스트 길이
    priority=4            # 우선순위
),
```

### 2. .env에서 DEFAULT_MODEL 변경
```env
DEFAULT_MODEL=new-model-id
```

### 3. 서버 재시작
```bash
python main.py
```

## 주의사항

1. **Tool Calling 요구사항**: Tool calling이 필요한 요청은 지원하는 모델만 사용
2. **무료 모델 제한**: `free_only=True`일 때 유료 모델은 자동 제외
3. **Rate Limit**: 무료 모델은 rate limit이 있으므로 폴백 시스템 필수
4. **우선순위 vs DEFAULT_MODEL**: DEFAULT_MODEL이 항상 최우선