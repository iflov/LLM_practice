"""
Real web search tool using DuckDuckGo
"""
from typing import Dict, Any, List
from datetime import datetime
from app.tools.base_tool import BaseTool, ToolParameter
from duckduckgo_search import DDGS
import asyncio
import logging

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Real web search tool using DuckDuckGo"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web using DuckDuckGo for real-time information and current events"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query (e.g., 'latest AI news', 'weather in Seoul today')",
                required=True
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum number of results to return (default: 5)",
                required=False
            )
        ]
    
    async def execute(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute real web search using DuckDuckGo"""
        try:
            # DuckDuckGo search is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=limit))
            )
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                    "position": i + 1
                })
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "DuckDuckGo"
            }
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": [],
                "timestamp": datetime.utcnow().isoformat()
            }