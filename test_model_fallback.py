"""
Model Fallback 시스템 테스트
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_model_fallback():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Model Fallback System Test ===\n")
        
        # 1. 사용 가능한 모델 확인
        print("1. 사용 가능한 모델 리스트:")
        resp = await client.get(f"{BASE_URL}/api/chat/models")
        models_info = resp.json()
        
        print(f"   Default Model: {models_info['default_model']}")
        print(f"   Fallback Enabled: {models_info['fallback_enabled']}")
        print(f"   Free Models Only: {models_info['fallback_free_only']}")
        print(f"\n   Fallback Order:")
        for i, model_id in enumerate(models_info['fallback_order'], 1):
            print(f"   {i}. {model_id}")
        
        print("\n   All Available Models:")
        for model in models_info['available_models']:
            status = "FREE" if model['is_free'] else "PAID"
            tools = "TOOLS" if model['supports_tools'] else "NO-TOOLS"
            print(f"   - {model['id']} ({status}, {tools}) - Priority: {model['priority']}")
        
        print("\n")
        
        # 2. 세션 생성
        resp = await client.post(f"{BASE_URL}/api/chat/session")
        session_id = resp.json()["session_id"]
        print(f"2. Session created: {session_id}\n")
        
        # 3. 다양한 테스트 케이스
        test_cases = [
            {
                "message": "What is 25 * 13? Please calculate it.",
                "use_tools": True,
                "description": "Tool 사용 테스트 (계산기)"
            },
            {
                "message": "Hello! How are you today?",
                "use_tools": False,
                "description": "일반 대화 (Tool 미사용)"
            },
            {
                "message": "What's the weather like in Seoul?",
                "use_tools": True,
                "description": "Tool 사용 테스트 (날씨)"
            },
            {
                "message": "Search for information about Python decorators",
                "use_tools": True,
                "description": "Tool 사용 테스트 (검색)"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"3.{i}. {test['description']}")
            print(f"     Message: {test['message']}")
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                resp = await client.post(
                    f"{BASE_URL}/api/chat/message",
                    json={
                        "session_id": session_id,
                        "message": test['message'],
                        "use_tools": test['use_tools']
                    }
                )
                
                end_time = asyncio.get_event_loop().time()
                elapsed = end_time - start_time
                
                if resp.status_code == 200:
                    result = resp.json()
                    print(f"     Model Used: {result.get('model_used', 'unknown')}")
                    print(f"     Response Time: {elapsed:.2f}s")
                    print(f"     Response: {result['response'][:100]}...")
                    
                    if result.get('tools_used'):
                        print(f"     Tools Used:")
                        for tool in result['tools_used']:
                            print(f"       - {tool['tool']}")
                else:
                    print(f"     Error: {resp.status_code} - {resp.text}")
                    
            except Exception as e:
                print(f"     Exception: {str(e)}")
            
            print()
        
        # 4. 대화 기록 확인
        print("\n4. 대화 기록 확인:")
        resp = await client.get(f"{BASE_URL}/api/chat/history/{session_id}")
        history = resp.json()
        
        print(f"   Total messages: {len(history)}")
        
        # 사용된 모델 통계
        models_used = {}
        for msg in history:
            if 'metadata' in msg and 'model_used' in msg['metadata']:
                model = msg['metadata']['model_used']
                models_used[model] = models_used.get(model, 0) + 1
        
        print("\n   Models used in this session:")
        for model, count in models_used.items():
            print(f"   - {model}: {count} times")

if __name__ == "__main__":
    print("Model Fallback 시스템 테스트 시작...")
    print("서버가 실행 중인지 확인하세요: http://localhost:8000")
    print("-" * 60)
    
    try:
        asyncio.run(test_model_fallback())
    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("python3 main.py로 서버를 먼저 실행하세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")