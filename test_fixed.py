"""
수정된 Fallback 시스템 테스트
Rate limit 문제 고려하여 개선된 버전
"""
import httpx
import asyncio
import json
import time

BASE_URL = "http://localhost:8000"

async def test_basic_functionality():
    """기본 기능 테스트 (Rate limit 문제 고려)"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== 기본 기능 테스트 ===\n")
        
        # 1. 헬스체크
        print("1. 서버 상태 확인")
        try:
            resp = await client.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                print("   ✅ 서버 정상 작동")
            else:
                print(f"   ❌ 서버 오류: {resp.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 서버 연결 실패: {str(e)}")
            return False
        
        # 2. 세션 생성
        print("\n2. 세션 생성")
        try:
            resp = await client.post(f"{BASE_URL}/api/chat/session")
            if resp.status_code == 200:
                session_id = resp.json()["session_id"]
                print(f"   ✅ 세션 생성 성공: {session_id}")
            else:
                print(f"   ❌ 세션 생성 실패: {resp.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 세션 생성 예외: {str(e)}")
            return False
        
        # 3. 도구 목록 확인
        print("\n3. 사용 가능한 도구 확인")
        try:
            resp = await client.get(f"{BASE_URL}/api/chat/tools")
            if resp.status_code == 200:
                tools = resp.json()["tools"]
                print(f"   ✅ {len(tools)}개 도구 사용 가능:")
                for tool in tools:
                    print(f"     - {tool['name']}: {tool['description']}")
            else:
                print(f"   ❌ 도구 목록 조회 실패: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 도구 목록 조회 예외: {str(e)}")
        
        return session_id

async def test_chat_messages(session_id: str):
    """채팅 메시지 테스트"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n=== 채팅 메시지 테스트 ===\n")
        
        # 간단한 테스트 케이스들 (Rate limit 고려)
        test_cases = [
            {
                "message": "Hello! Can you help me?",
                "description": "기본 인사",
                "use_tools": False,
                "expected_tools": []
            },
            {
                "message": "Calculate 123 * 456",
                "description": "복잡한 계산 (Tool 사용 기대)",
                "use_tools": True,
                "expected_tools": ["calculator"]
            },
            {
                "message": "What's the weather like in Tokyo?",
                "description": "날씨 조회 (Tool 사용)",
                "use_tools": True,
                "expected_tools": ["weather"]
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"{i}. {test['description']}")
            print(f"   질문: {test['message']}")
            print(f"   Tool 사용: {test['use_tools']}")
            
            start_time = time.time()
            
            try:
                resp = await client.post(
                    f"{BASE_URL}/api/chat/message",
                    json={
                        "session_id": session_id,
                        "message": test['message'],
                        "use_tools": test['use_tools']
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if resp.status_code == 200:
                    result = resp.json()
                    print(f"   ✅ 성공 (응답시간: {response_time:.2f}초)")
                    print(f"   사용 모델: {result.get('model_used', 'Unknown')}")
                    
                    # 응답 내용 출력 (짧게)
                    content = result['response']
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"   응답: {content}")
                    
                    # 도구 사용 확인
                    tools_used = result.get('tools_used', [])
                    if tools_used:
                        print(f"   사용된 도구:")
                        for tool in tools_used:
                            tool_name = tool.get('tool', 'Unknown')
                            print(f"     - {tool_name}")
                            if 'result' in tool:
                                result_str = str(tool['result'])
                                if len(result_str) > 50:
                                    result_str = result_str[:50] + "..."
                                print(f"       결과: {result_str}")
                    else:
                        print(f"   사용된 도구: 없음")
                    
                    # Rate limit 체크
                    if "Rate limit exceeded" in result['response']:
                        print(f"   ⚠️  Rate limit 감지됨")
                        return False  # 더 이상 테스트하지 않음
                        
                elif resp.status_code == 500:
                    error_detail = resp.json().get('detail', 'Unknown error')
                    print(f"   ❌ 서버 내부 오류: {error_detail}")
                    
                    if "Rate limit exceeded" in error_detail:
                        print(f"   ⚠️  OpenRouter Rate limit 도달")
                        print(f"   💡 잠시 후 다시 시도하거나 유료 크레딧 추가 필요")
                        return False
                        
                else:
                    print(f"   ❌ HTTP 오류: {resp.status_code}")
                    print(f"   오류 내용: {resp.text}")
                    
            except Exception as e:
                print(f"   ❌ 예외 발생: {str(e)}")
            
            print()
            
            # Rate limit 회피를 위한 짧은 대기
            if i < len(test_cases):
                await asyncio.sleep(1)
        
        return True

async def test_chat_history(session_id: str):
    """대화 기록 조회 테스트"""
    print("=== 대화 기록 조회 테스트 ===\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{BASE_URL}/api/chat/history/{session_id}")
            
            if resp.status_code == 200:
                history = resp.json()
                print(f"✅ 대화 기록 조회 성공")
                print(f"   총 대화 수: {len(history)}")
                
                if history:
                    last_msg = history[-1]
                    print(f"   마지막 메시지 시간: {last_msg.get('created_at', 'Unknown')}")
                    model_used = last_msg.get('metadata', {}).get('model', 'Unknown')
                    print(f"   마지막 사용 모델: {model_used}")
                    
            elif resp.status_code == 404:
                print(f"❌ 세션을 찾을 수 없음")
            elif resp.status_code == 500:
                print(f"❌ 서버 내부 오류 (대화 기록 조회)")
                print(f"   세부 정보: {resp.json().get('detail', 'Unknown error')}")
            else:
                print(f"❌ HTTP 오류: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 대화 기록 조회 예외: {str(e)}")

async def main():
    print("📋 수정된 Fallback 시스템 테스트")
    print("=" * 50)
    print("Rate limit 문제를 고려한 개선된 테스트입니다.")
    print("서버가 실행 중인지 확인하세요: http://localhost:8000")
    print("-" * 50)
    
    try:
        # 1. 기본 기능 테스트
        session_id = await test_basic_functionality()
        if not session_id:
            return
        
        # 2. 채팅 메시지 테스트
        continue_test = await test_chat_messages(session_id)
        if not continue_test:
            print("⚠️  Rate limit으로 인해 테스트를 조기 종료합니다.")
        
        # 3. 대화 기록 테스트
        await test_chat_history(session_id)
        
        print("\n" + "=" * 50)
        print("✅ 테스트 완료!")
        print("\n💡 Rate limit 해결 방법:")
        print("   1. OpenRouter에서 크레딧 추가 ($1-5)")
        print("   2. 다른 시간대에 다시 테스트")
        print("   3. 유료 모델 사용 고려")
        
    except httpx.ConnectError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("다음 명령으로 서버를 실행하세요: python main.py")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())