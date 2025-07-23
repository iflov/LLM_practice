"""
Fallback 시스템 테스트
존재하지 않는 모델을 먼저 시도하고, fallback이 정상 작동하는지 확인
"""
import httpx
import asyncio
import json
import time

BASE_URL = "http://localhost:8000"

async def test_fallback_system():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Fallback System Test ===\n")
        
        # 1. 현재 설정 확인
        print("1. 환경 설정 확인")
        with open('.env', 'r') as f:
            env_content = f.read()
            fallback_enabled = 'FALLBACK_ENABLED=true' in env_content
            print(f"   Fallback Enabled: {fallback_enabled}")
            if 'FALLBACK_MODELS=' in env_content:
                fallback_models = env_content.split('FALLBACK_MODELS=')[1].split('\n')[0]
                print(f"   Fallback Models: {fallback_models}")
        print()
        
        # 2. 세션 생성
        print("2. 세션 생성")
        resp = await client.post(f"{BASE_URL}/api/chat/session")
        session_id = resp.json()["session_id"]
        print(f"   Session ID: {session_id}\n")
        
        # 3. Fallback 테스트 케이스들
        test_cases = [
            {
                "message": "Hello, can you introduce yourself?",
                "description": "기본 대화 (fallback 테스트)",
                "expected": "정상 응답"
            },
            {
                "message": "What is 25 * 16?",
                "description": "계산 도구 사용 (fallback + tool calling)",
                "expected": "Calculator 도구 사용"
            },
            {
                "message": "What's the weather in Tokyo?",
                "description": "날씨 도구 사용 (fallback + tool calling)",
                "expected": "Weather 도구 사용"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"{i}. {test['description']}")
            print(f"   질문: {test['message']}")
            print(f"   예상: {test['expected']}")
            
            start_time = time.time()
            
            try:
                resp = await client.post(
                    f"{BASE_URL}/api/chat/message",
                    json={
                        "session_id": session_id,
                        "message": test['message'],
                        "use_tools": True
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if resp.status_code == 200:
                    result = resp.json()
                    print(f"   ✅ 성공 (응답시간: {response_time:.2f}초)")
                    print(f"   응답: {result['response'][:100]}...")
                    
                    if result['tools_used']:
                        print(f"   사용된 도구:")
                        for tool in result['tools_used']:
                            print(f"     - {tool['tool']}")
                    else:
                        print(f"   사용된 도구: 없음")
                else:
                    print(f"   ❌ HTTP 오류: {resp.status_code}")
                    print(f"   오류 내용: {resp.text}")
                    
            except Exception as e:
                print(f"   ❌ 예외 발생: {str(e)}")
            
            print()
        
        # 4. 대화 기록 확인
        print("4. 대화 기록 확인")
        try:
            resp = await client.get(f"{BASE_URL}/api/chat/history/{session_id}")
            if resp.status_code == 200:
                history = resp.json()
                print(f"   총 대화 수: {len(history)}")
                
                # 마지막 대화의 메타데이터 확인
                if history:
                    last_msg = history[-1]
                    print(f"   마지막 사용 모델: {last_msg.get('model_used', 'Unknown')}")
                    if last_msg.get('tools_used'):
                        print(f"   마지막 사용 도구: {last_msg['tools_used']}")
            else:
                print(f"   ❌ 기록 조회 실패: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 기록 조회 예외: {str(e)}")

async def test_manual_model_fallback():
    """수동으로 존재하지 않는 모델을 지정해서 fallback 테스트"""
    print("\n=== Manual Model Fallback Test ===")
    
    # 직접 OpenRouter 클라이언트 테스트
    from app.services.openrouter_client import OpenRouterClient
    from app.core.config import settings
    
    client = OpenRouterClient()
    
    # 존재하지 않는 모델로 테스트
    messages = [{"role": "user", "content": "Hello, test fallback"}]
    
    print("1. 존재하지 않는 모델로 테스트")
    print("   목표 모델: non-existent-model")
    print(f"   Fallback 활성화: {settings.fallback_enabled}")
    print(f"   Fallback 모델들: {settings.fallback_models_list}")
    
    try:
        result = await client.simple_chat_completion(
            messages=messages,
            model="non-existent-model"  # 존재하지 않는 모델
        )
        
        print(f"   결과: {result['content'][:100]}...")
        if "Error" not in result['content']:
            print("   ✅ Fallback 성공!")
        else:
            print("   ❌ Fallback 실패")
            
    except Exception as e:
        print(f"   ❌ 예외 발생: {str(e)}")

if __name__ == "__main__":
    print("Fallback 시스템 테스트 시작...")
    print("서버가 실행 중인지 확인하세요: http://localhost:8000")
    print("-" * 60)
    
    try:
        # API 테스트
        asyncio.run(test_fallback_system())
        
        # 직접 클라이언트 테스트
        asyncio.run(test_manual_model_fallback())
        
        print("\n" + "="*60)
        print("Fallback 테스트 완료!")
        print("로그를 확인하여 실제 사용된 모델을 확인하세요.")
        
    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("python main.py로 서버를 먼저 실행하세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")