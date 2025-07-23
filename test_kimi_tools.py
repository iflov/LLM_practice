"""
Kimi K2 모델의 Tool Calling 테스트
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_kimi_tools():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== Kimi K2 Tool Calling Test ===\n")
        
        # 1. 세션 생성
        resp = await client.post(f"{BASE_URL}/api/chat/session")
        session_id = resp.json()["session_id"]
        print(f"Session ID: {session_id}\n")
        
        # Tool을 사용하는 테스트 케이스들
        test_cases = [
            {
                "message": "What is 156 * 89?",
                "expected_tool": "Calculator",
                "description": "수학 계산"
            },
            {
                "message": "What's the weather like in Seoul?",
                "expected_tool": "Weather",
                "description": "날씨 조회"
            },
            {
                "message": "Search for information about LangChain agents",
                "expected_tool": "Search",
                "description": "검색"
            },
            {
                "message": "Calculate the square root of 144 and then multiply it by 5",
                "expected_tool": "Calculator",
                "description": "복잡한 계산"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"{i}. {test['description']} 테스트")
            print(f"   질문: {test['message']}")
            
            resp = await client.post(
                f"{BASE_URL}/api/chat/message",
                json={
                    "session_id": session_id,
                    "message": test['message'],
                    "use_tools": True
                }
            )
            
            result = resp.json()
            print(f"   응답: {result['response'][:100]}...")
            
            if result['tools_used']:
                print(f"   사용된 도구:")
                for tool in result['tools_used']:
                    print(f"     - {tool['tool']}: {tool.get('args', {})}")
                    print(f"       결과: {tool.get('result', 'N/A')}")
            else:
                print(f"   사용된 도구: 없음")
            
            print()
        
        # 대화 기록 확인
        print("\n=== 전체 대화 기록 ===")
        resp = await client.get(f"{BASE_URL}/api/chat/history/{session_id}")
        history = resp.json()
        
        for msg in history[-3:]:  # 마지막 3개만
            print(f"User: {msg['user_message']}")
            print(f"Assistant: {msg['assistant_message'][:100]}...")
            if msg.get('tools_used'):
                print(f"Tools: {msg['tools_used']}")
            print()

if __name__ == "__main__":
    print("Kimi K2 모델 Tool Calling 테스트 시작...")
    print("서버가 실행 중인지 확인하세요: http://localhost:8000")
    print("-" * 50)
    
    try:
        asyncio.run(test_kimi_tools())
    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("python3 main.py로 서버를 먼저 실행하세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")