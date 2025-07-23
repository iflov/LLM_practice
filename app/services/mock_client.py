"""
Mock OpenRouter client for testing when rate limits are hit
"""
from typing import List, Dict, Any, Optional
import json
import asyncio
import random
from app.tools import get_tool

class MockOpenRouterClient:
    """Rate limit 상황에서 사용할 수 있는 Mock 클라이언트"""
    
    def __init__(self):
        self.mock_responses = {
            "greetings": [
                "Hello! I'm a mock AI assistant. How can I help you today?",
                "Hi there! I'm here to help with your questions.",
                "Greetings! What would you like to know?"
            ],
            "general": [
                "I understand your question. Let me help you with that.",
                "That's an interesting question. Here's what I think...",
                "Based on your request, I can provide some information."
            ]
        }
    
    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        use_tools: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock 채팅 완성 with tool support"""
        
        # 마지막 사용자 메시지 가져오기
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Tool 사용이 필요한지 판단
        tool_calls = []
        response_content = ""
        
        if use_tools:
            # 계산 요청 감지
            if any(word in user_message.lower() for word in ["calculate", "multiply", "*", "+", "-", "/"]):
                if any(char.isdigit() for char in user_message):
                    # Calculator tool 사용
                    tool_calls = await self._mock_calculator_call(user_message)
                    response_content = f"I'll calculate that for you using the calculator tool. The result is {tool_calls[0]['result'] if tool_calls else 'unknown'}."
            
            # 날씨 요청 감지
            elif any(word in user_message.lower() for word in ["weather", "temperature", "climate"]):
                tool_calls = await self._mock_weather_call(user_message)
                response_content = f"Let me check the weather for you. {tool_calls[0]['result'] if tool_calls else 'Weather information not available'}."
            
            # 검색 요청 감지
            elif any(word in user_message.lower() for word in ["search", "find", "look up"]):
                tool_calls = await self._mock_search_call(user_message)
                response_content = f"I'll search for information about that. {tool_calls[0]['result'] if tool_calls else 'Search results not available'}."
        
        # Tool을 사용하지 않는 경우 일반 응답
        if not tool_calls:
            if any(word in user_message.lower() for word in ["hello", "hi", "hey", "greetings"]):
                response_content = random.choice(self.mock_responses["greetings"])
            else:
                response_content = random.choice(self.mock_responses["general"])
            
            response_content += f" (This is a mock response due to API rate limits)"
        
        # 약간의 지연 시뮬레이션
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return {
            "content": response_content,
            "tool_calls": tool_calls,
            "model_used": "mock-model-v1.0",
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(user_message.split()) + len(response_content.split())
            }
        }
    
    async def _mock_calculator_call(self, message: str) -> List[Dict[str, Any]]:
        """Mock calculator tool call"""
        # 간단한 수식 추출 시도
        import re
        
        # 숫자와 연산자 패턴 찾기
        patterns = [
            r'(\d+)\s*\*\s*(\d+)',  # multiplication
            r'(\d+)\s*\+\s*(\d+)',  # addition
            r'(\d+)\s*-\s*(\d+)',   # subtraction
            r'(\d+)\s*/\s*(\d+)'    # division
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                num1, num2 = int(match.group(1)), int(match.group(2))
                if '*' in pattern:
                    result = num1 * num2
                    expression = f"{num1} * {num2}"
                elif '+' in pattern:
                    result = num1 + num2
                    expression = f"{num1} + {num2}"
                elif '-' in pattern:
                    result = num1 - num2
                    expression = f"{num1} - {num2}"  
                elif '/' in pattern:
                    result = num1 / num2 if num2 != 0 else "Error: Division by zero"
                    expression = f"{num1} / {num2}"
                
                return [{
                    "tool_call_id": "mock_calc_001",
                    "tool_name": "calculator", 
                    "tool_args": {"expression": expression},
                    "result": {"success": True, "result": result, "expression": expression}
                }]
        
        # 패턴을 찾지 못한 경우
        return [{
            "tool_call_id": "mock_calc_001",
            "tool_name": "calculator",
            "tool_args": {"expression": "2 + 2"},
            "result": {"success": True, "result": 4, "expression": "2 + 2"}
        }]
    
    async def _mock_weather_call(self, message: str) -> List[Dict[str, Any]]:
        """Mock weather tool call"""
        # 도시명 추출 시도
        import re
        
        cities = ["Seoul", "Tokyo", "New York", "London", "Paris", "Berlin", "Sydney"]
        city = "Seoul"  # default
        
        for c in cities:
            if c.lower() in message.lower():
                city = c
                break
        
        # 랜덤 날씨 데이터
        weather_conditions = ["clear", "cloudy", "rainy", "sunny", "partly cloudy"]
        temperature = random.randint(15, 30)
        humidity = random.randint(40, 80)
        condition = random.choice(weather_conditions)
        
        return [{
            "tool_call_id": "mock_weather_001",
            "tool_name": "weather",
            "tool_args": {"city": city},
            "result": {
                "success": True,
                "city": city,
                "temperature": f"{temperature}°C",
                "condition": condition,
                "humidity": f"{humidity}%"
            }
        }]
    
    async def _mock_search_call(self, message: str) -> List[Dict[str, Any]]:
        """Mock search tool call"""
        # 검색어 추출
        query = message.replace("search", "").replace("find", "").replace("look up", "").strip()
        if not query:
            query = "general information"
        
        return [{
            "tool_call_id": "mock_search_001", 
            "tool_name": "search",
            "tool_args": {"query": query},
            "result": {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": f"Mock search result for '{query}'",
                        "snippet": f"This is a mock search result about {query}. In a real scenario, this would contain actual search results.",
                        "url": f"https://example.com/search?q={query.replace(' ', '+')}"
                    }
                ]
            }
        }]