# OpenRouter 무료 Tool Use 지원 모델

## 추천 모델들 (Tool Calling 성능 순)

### 1. **Kimi K2** ⭐️
- **ID**: `moonshotai/kimi-k2:free`
- **Context**: 65K
- **특징**: MoE 모델, advanced tool use 최적화
- **장점**: Tool use 벤치마크에서 높은 성능

### 2. **DeepSeek Chat V3**
- **ID**: `deepseek/deepseek-chat-v3-0324:free`
- **Context**: 32K
- **특징**: Function calling 지원
- **장점**: 안정적인 tool calling

### 3. **Qwen3 235B** (대형 모델)
- **ID**: `qwen/qwen3-235b-a22b-07-25:free`
- **Context**: 262K (매우 큼)
- **특징**: 거대 모델, 긴 컨텍스트
- **장점**: 복잡한 추론 가능

### 4. **DeepSeek R1T2 Chimera**
- **ID**: `tngtech/deepseek-r1t2-chimera:free`
- **특징**: 강한 reasoning 능력
- **장점**: 복잡한 도구 사용 시나리오

## Tool Use 테스트 방법

```python
# .env 파일에서 모델 변경
DEFAULT_MODEL=moonshotai/kimi-k2:free

# 서버 재시작 후 테스트
python3 test_kimi_tools.py
```

## 주의사항

1. **Rate Limit**: 무료 모델은 사용량 제한이 있을 수 있음
2. **성능 차이**: 유료 모델(GPT-4, Claude)보다는 성능이 낮을 수 있음
3. **응답 시간**: 무료 모델은 응답이 느릴 수 있음

## 유료 대안 (더 나은 성능)

- `openai/gpt-4-turbo`: 최고 성능
- `anthropic/claude-3-opus`: 복잡한 추론
- `openai/gpt-3.5-turbo`: 빠르고 저렴