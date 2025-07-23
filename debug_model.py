"""
모델 설정 디버깅
"""
import os
from dotenv import load_dotenv

# .env 파일 다시 로드
load_dotenv(override=True)

# 현재 설정 확인
print("=== 환경 변수 확인 ===")
print(f"DEFAULT_MODEL: {os.getenv('DEFAULT_MODEL')}")
print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')[:20]}...")

# 설정 모듈 임포트
from app.core.config import settings
print(f"\n=== Settings 모듈 확인 ===")
print(f"settings.default_model: {settings.default_model}")
print(f"settings.openrouter_base_url: {settings.openrouter_base_url}")

# OpenRouter API로 직접 테스트
import httpx
import asyncio

async def test_direct_api():
    """OpenRouter API 직접 호출 테스트"""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    # DeepSeek 모델로 테스트
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [{"role": "user", "content": "Hi, just testing. Reply with 'OK'"}],
        "max_tokens": 10
    }
    
    print("\n=== DeepSeek 모델 직접 테스트 ===")
    print(f"Model: {payload['model']}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result['choices'][0]['message']['content']}")
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Exception: {str(e)}")

# 실행
if __name__ == "__main__":
    asyncio.run(test_direct_api())