from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json
from app.core.config import settings
from app.tools import get_tools_for_openai, get_tool


class OpenRouterClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",  # Optional
                "X-Title": "Agent LLM POC"  # Optional
            }
        )
    
    async def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Chat completion with tool calling support"""
        
        try:
            # Get all available tools in OpenAI format
            tools = get_tools_for_openai()
            
            # Debug logging
            print(f"[DEBUG] Using model: {model or settings.default_model}")
            print(f"[DEBUG] API Key (first 10 chars): {settings.openrouter_api_key[:10]}...")
            print(f"[DEBUG] Base URL: {settings.openrouter_base_url}")
            
            # Make the API call
            response = await self.client.chat.completions.create(
                model=model or settings.default_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let the model decide when to use tools
                temperature=temperature or settings.temperature,
                max_tokens=max_tokens or settings.max_tokens
            )
            
            # Debug response
            print(f"[DEBUG] Response: {response}")
            
        except Exception as e:
            print(f"OpenRouter API Error: {str(e)}")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            return {
                "content": f"Error: API call failed - {str(e)}",
                "tool_calls": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        # Extract the response
        if not response.choices:
            return {
                "content": "Error: No response from model",
                "tool_calls": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        message = response.choices[0].message
        
        # Check if the model wants to use any tools
        if message.tool_calls:
            tool_results = []
            
            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Get and execute the tool
                tool = get_tool(tool_name)
                if tool is None:
                    result = {"error": f"Tool '{tool_name}' not found"}
                else:
                    try:
                        result = await tool.execute(**tool_args)
                    except Exception as e:
                        result = {"error": f"Tool execution failed: {str(e)}"}
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "result": result
                })
            
            # Add the assistant's message with tool calls to history
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
            
            # Add tool results to messages
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": json.dumps(tool_result["result"])
                })
            
            # Make another API call with the tool results
            final_response = await self.client.chat.completions.create(
                model=model or settings.default_model,
                messages=messages,
                temperature=temperature or settings.temperature,
                max_tokens=max_tokens or settings.max_tokens
            )
            
            return {
                "content": final_response.choices[0].message.content,
                "tool_calls": tool_results,
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) + getattr(final_response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0) + getattr(final_response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0) + getattr(final_response.usage, 'total_tokens', 0)
                }
            }
        else:
            # No tool calls, return the response directly
            return {
                "content": message.content,
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            }
    
    async def simple_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Simple chat completion without tools"""
        
        try:
            # Debug logging
            print(f"[DEBUG Simple] Using model: {model or settings.default_model}")
            print(f"[DEBUG Simple] Messages: {messages}")
            
            response = await self.client.chat.completions.create(
                model=model or settings.default_model,
                messages=messages,
                temperature=temperature or settings.temperature,
                max_tokens=max_tokens or settings.max_tokens
            )
            
            print(f"[DEBUG Simple] Response: {response}")
            
        except Exception as e:
            print(f"OpenRouter API Error: {str(e)}")
            print(f"[DEBUG Simple] Error type: {type(e).__name__}")
            return {
                "content": f"Error: API call failed - {str(e)}",
                "tool_calls": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        if not response.choices:
            return {
                "content": "Error: No response from model",
                "tool_calls": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        
        return {
            "content": response.choices[0].message.content or "No response",
            "tool_calls": [],
            "usage": {
                "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0)
            }
        }