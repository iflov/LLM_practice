from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class ToolParameter(BaseModel):
    name: str
    type: str  # "string", "number", "boolean", etc.
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]


class BaseTool(ABC):
    """Base class for all tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Tool parameters"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def run(self, *args, **kwargs) -> str:
        """Synchronous wrapper for LangChain compatibility"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute(**kwargs))
                    result = future.result()
            else:
                result = loop.run_until_complete(self.execute(**kwargs))
            
            # Convert result to string for LangChain
            if isinstance(result, dict):
                if result.get("success", False):
                    if "results" in result:
                        # For search results
                        output = f"Found {len(result['results'])} results for '{result.get('query', '')}':\n"
                        for i, res in enumerate(result['results'], 1):
                            output += f"\n{i}. {res.get('title', 'No title')}\n"
                            output += f"   {res.get('snippet', 'No snippet')[:200]}...\n"
                            output += f"   URL: {res.get('url', 'No URL')}\n"
                        return output
                    else:
                        # For other tools
                        return str(result)
                else:
                    return f"Error: {result.get('error', 'Unknown error')}"
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }