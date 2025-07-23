from typing import Dict, Type
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


def get_tool(tool_name: str) -> BaseTool:
    """Get tool instance by name"""
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    return AVAILABLE_TOOLS[tool_name]()


def get_all_tools() -> Dict[str, BaseTool]:
    """Get all available tool instances"""
    return {name: tool_class() for name, tool_class in AVAILABLE_TOOLS.items()}


def get_tools_for_openai() -> list:
    """Get all tools in OpenAI function calling format"""
    tools = get_all_tools()
    return [tool.to_openai_function() for tool in tools.values()]