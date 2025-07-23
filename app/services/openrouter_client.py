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
        
        # Determine models to try
        target_model = model or settings.default_model
        models_to_try = [target_model]
        
        # Add fallback models if enabled
        if settings.fallback_enabled and target_model not in settings.fallback_models_list:
            models_to_try.extend(settings.fallback_models_list)
        elif settings.fallback_enabled:
            # If target model is in fallback list, try others as backup
            fallback_list = [m for m in settings.fallback_models_list if m != target_model]
            models_to_try.extend(fallback_list)
        
        last_error = None
        
        for attempt, current_model in enumerate(models_to_try):
            try:
                # Get all available tools in OpenAI format
                tools = get_tools_for_openai()
                
                # Debug logging
                print(f"[DEBUG] Attempt {attempt + 1}: Using model: {current_model}")
                if attempt > 0:
                    print(f"[DEBUG] Fallback attempt after error: {last_error}")
                
                # Make the API call0
                response = await self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",  # Let the model decide when to use tools
                    temperature=temperature or settings.temperature,
                    max_tokens=max_tokens or settings.max_tokens
                )
                
                # If successful, break the loop
                print(f"[DEBUG] Success with model: {current_model}")
                break
                
            except Exception as e:
                last_error = str(e)
                print(f"[DEBUG] Model {current_model} failed: {str(e)}")
                
                # If this is the last model to try, return error
                if attempt == len(models_to_try) - 1:
                    print(f"[ERROR] All models failed. Last error: {str(e)}")
                    return {
                        "content": f"Error: All models failed. Last error: {str(e)}",
                        "tool_calls": [],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    }
                
                # Continue to next model
                continue
        
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
        
        # Determine models to try
        target_model = model or settings.default_model
        models_to_try = [target_model]
        
        # Add fallback models if enabled
        if settings.fallback_enabled and target_model not in settings.fallback_models_list:
            models_to_try.extend(settings.fallback_models_list)
        elif settings.fallback_enabled:
            # If target model is in fallback list, try others as backup
            fallback_list = [m for m in settings.fallback_models_list if m != target_model]
            models_to_try.extend(fallback_list)
        
        last_error = None
        
        for attempt, current_model in enumerate(models_to_try):
            try:
                # Debug logging
                print(f"[DEBUG Simple] Attempt {attempt + 1}: Using model: {current_model}")
                if attempt > 0:
                    print(f"[DEBUG Simple] Fallback attempt after error: {last_error}")
                
                response = await self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature or settings.temperature,
                    max_tokens=max_tokens or settings.max_tokens
                )
                
                # If successful, break the loop
                print(f"[DEBUG Simple] Success with model: {current_model}")
                break
                
            except Exception as e:
                last_error = str(e)
                print(f"[DEBUG Simple] Model {current_model} failed: {str(e)}")
                
                # If this is the last model to try, return error
                if attempt == len(models_to_try) - 1:
                    print(f"[ERROR Simple] All models failed. Last error: {str(e)}")
                    return {
                        "content": f"Error: All models failed. Last error: {str(e)}",
                        "tool_calls": [],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    }
                
                # Continue to next model
                continue
        
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