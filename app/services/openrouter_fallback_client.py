"""
OpenRouter client with model fallback support
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from app.core.config import settings
from app.core.model_config import get_fallback_models, get_model_by_id
from app.tools import get_tools_for_openai, get_tool
import logging

logger = logging.getLogger(__name__)


class OpenRouterFallbackClient:
    """Model fallback을 지원하는 OpenRouter 클라이언트"""
    
    def __init__(self):
        # Connection pooling과 timeout 설정 추가
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",  # Fixed port
                "X-Title": "Agent LLM POC"
            },
            timeout=30.0,  # 30초 타임아웃
            max_retries=1  # 재시도 1회
        )
        
    async def _try_model(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """단일 모델로 시도"""
        try:
            logger.info(f"Trying model: {model_id}")
            
            kwargs = {
                "model": model_id,
                "messages": messages,
                "temperature": temperature or settings.temperature,
                "max_tokens": max_tokens or settings.max_tokens
            }
            
            # Tool이 필요한 경우에만 추가
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            # 성공한 경우
            logger.info(f"Model {model_id} succeeded")
            return {
                "success": True,
                "response": response,
                "model_used": model_id
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Model {model_id} failed: {error_msg}")
            
            # 특정 에러는 다른 모델로도 해결 안될 수 있음
            if "Invalid API key" in error_msg or "Unauthorized" in error_msg:
                raise  # API 키 문제는 fallback 해도 소용없음
                
            return {
                "success": False,
                "error": error_msg,
                "model_used": model_id
            }
    
    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        use_tools: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        free_only: bool = True
    ) -> Dict[str, Any]:
        """Fallback을 지원하는 채팅 완성"""
        
        # Tool이 필요한 경우 OpenAI 형식으로 가져오기
        tools = get_tools_for_openai() if use_tools else None
        
        # 사용할 모델 리스트 가져오기
        fallback_models = get_fallback_models(
            require_tools=use_tools,
            free_only=free_only
        )
        
        if not fallback_models:
            return {
                "content": "No available models found",
                "tool_calls": [],
                "model_used": None,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        # 각 모델로 순서대로 시도
        last_error = None
        for model_config in fallback_models:
            try:
                result = await self._try_model(
                    model_id=model_config.id,
                    messages=messages,
                    tools=tools if model_config.supports_tools else None,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if result["success"]:
                    # 성공한 경우 응답 처리
                    response = result["response"]
                    return await self._process_response(
                        response=response,
                        messages=messages,
                        model_id=model_config.id,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                else:
                    last_error = result["error"]
                    
            except Exception as e:
                last_error = str(e)
                if "Invalid API key" in last_error:
                    break  # API 키 문제는 더 시도해도 소용없음
        
        # 모든 모델이 실패한 경우
        return {
            "content": f"All models failed. Last error: {last_error}",
            "tool_calls": [],
            "model_used": None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    
    async def _process_response(
        self,
        response,
        messages: List[Dict[str, str]],
        model_id: str,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """응답 처리 (tool calling 포함)"""
        
        if not response.choices:
            return {
                "content": "No response from model",
                "tool_calls": [],
                "model_used": model_id,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        message = response.choices[0].message
        
        # Tool calls가 있는 경우
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_results = []
            
            # 병렬로 tool 실행을 위한 태스크 준비
            async def execute_tool(tool_call):
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                tool = get_tool(tool_name)
                if tool is None:
                    result = {"error": f"Tool '{tool_name}' not found"}
                else:
                    try:
                        result = await tool.execute(**tool_args)
                    except Exception as e:
                        result = {"error": f"Tool execution failed: {str(e)}"}
                
                return {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "result": result
                }
            
            # 모든 tool을 병렬로 실행
            if len(message.tool_calls) > 1:
                # 여러 tool이 있으면 병렬 실행
                tool_results = await asyncio.gather(
                    *[execute_tool(tool_call) for tool_call in message.tool_calls]
                )
            else:
                # 단일 tool은 그냥 실행
                tool_results = [await execute_tool(message.tool_calls[0])]
            
            # Tool 결과를 메시지에 추가
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": json.dumps(tool_result["result"])
                })
            
            # Tool 결과로 다시 API 호출
            final_response = await self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature or settings.temperature,
                max_tokens=max_tokens or settings.max_tokens
            )
            
            return {
                "content": final_response.choices[0].message.content,
                "tool_calls": tool_results,
                "model_used": model_id,
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) + getattr(final_response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0) + getattr(final_response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0) + getattr(final_response.usage, 'total_tokens', 0)
                }
            }
        else:
            # Tool calls가 없는 경우
            return {
                "content": message.content or "No response",
                "tool_calls": [],
                "model_used": model_id,
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            }
    
    async def stream_chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        use_tools: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        free_only: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat completion with fallback support"""
        
        # Tool이 필요한 경우 OpenAI 형식으로 가져오기
        tools = get_tools_for_openai() if use_tools else None
        
        # 사용할 모델 리스트 가져오기
        fallback_models = get_fallback_models(
            require_tools=use_tools,
            free_only=free_only
        )
        
        if not fallback_models:
            yield {"type": "error", "error": "No available models found"}
            return
        
        # 각 모델로 순서대로 시도
        last_error = None
        for model_config in fallback_models:
            try:
                logger.info(f"Trying streaming with model: {model_config.id}")
                
                kwargs = {
                    "model": model_config.id,
                    "messages": messages,
                    "temperature": temperature or settings.temperature,
                    "max_tokens": max_tokens or settings.max_tokens,
                    "stream": True
                }
                
                # Tool이 필요한 경우에만 추가
                if tools and model_config.supports_tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                stream = await self.client.chat.completions.create(**kwargs)
                
                # 성공한 경우 스트림 처리
                full_content = ""
                tool_calls = []
                
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        
                        # 컨텐츠 스트리밍
                        if delta.content:
                            full_content += delta.content
                            yield {"type": "token", "content": delta.content}
                        
                        # Tool call 처리
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                if tool_call.function.name:
                                    tool_calls.append({
                                        "id": tool_call.id,
                                        "name": tool_call.function.name,
                                        "arguments": ""
                                    })
                                if tool_call.function.arguments:
                                    tool_calls[-1]["arguments"] += tool_call.function.arguments
                
                # Tool 실행 (있는 경우)
                if tool_calls:
                    for tool_call in tool_calls:
                        try:
                            tool_name = tool_call["name"]
                            tool_args = json.loads(tool_call["arguments"])
                            
                            yield {"type": "tool_call", "tool": tool_name, "args": tool_args}
                            
                            tool = get_tool(tool_name)
                            if tool:
                                result = await tool.execute(**tool_args)
                                yield {"type": "tool_result", "tool": tool_name, "result": result}
                            else:
                                yield {"type": "tool_result", "tool": tool_name, "result": {"error": f"Tool '{tool_name}' not found"}}
                        except Exception as e:
                            yield {"type": "tool_result", "tool": tool_name, "result": {"error": str(e)}}
                    
                    # Tool 결과로 다시 스트리밍 (필요한 경우)
                    messages.append({
                        "role": "assistant",
                        "content": full_content or "",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": tc["arguments"]
                                }
                            }
                            for tc in tool_calls
                        ]
                    })
                    
                    for tool_call in tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = json.loads(tool_call["arguments"])
                        tool = get_tool(tool_name)
                        if tool:
                            result = await tool.execute(**tool_args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": json.dumps(result)
                            })
                    
                    # Tool 결과로 다시 스트리밍
                    final_stream = await self.client.chat.completions.create(
                        model=model_config.id,
                        messages=messages,
                        temperature=temperature or settings.temperature,
                        max_tokens=max_tokens or settings.max_tokens,
                        stream=True
                    )
                    
                    async for chunk in final_stream:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            yield {"type": "token", "content": chunk.choices[0].delta.content}
                
                # 완료 신호
                yield {"type": "done", "model_used": model_config.id}
                return
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Streaming with model {model_config.id} failed: {last_error}")
                
                if "Invalid API key" in last_error:
                    break  # API 키 문제는 더 시도해도 소용없음
        
        # 모든 모델이 실패한 경우
        yield {"type": "error", "error": f"All models failed. Last error: {last_error}"}