from typing import Dict, Type
from functools import lru_cache
from app.tools.base_tool import BaseTool
from app.tools.calculator import CalculatorTool
from app.tools.weather import WeatherTool
from app.tools.search import SearchTool
from app.tools.web_search import WebSearchTool


# Registry of available tools
AVAILABLE_TOOLS: Dict[str, Type[BaseTool]] = {
    "calculator": CalculatorTool,
    "weather": WeatherTool,
    "search": SearchTool,
    "web_search": WebSearchTool,
}

# Tool instance cache
_tool_instances: Dict[str, BaseTool] = {}


def get_tool(tool_name: str) -> BaseTool:
    """Get tool instance by name (cached)"""
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # 캐시된 인스턴스 반환
    if tool_name not in _tool_instances:
        _tool_instances[tool_name] = AVAILABLE_TOOLS[tool_name]()
    
    return _tool_instances[tool_name]


def get_all_tools() -> Dict[str, BaseTool]:
    """Get all available tool instances (cached)"""
    for name in AVAILABLE_TOOLS:
        if name not in _tool_instances:
            _tool_instances[name] = AVAILABLE_TOOLS[name]()
    
    return _tool_instances.copy()


@lru_cache(maxsize=1)
def get_tools_for_openai() -> list:
    """Get all tools in OpenAI function calling format (cached)"""
    tools = get_all_tools()
    return [tool.to_openai_function() for tool in tools.values()]