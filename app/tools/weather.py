from typing import Dict, Any, List
import httpx
from app.tools.base_tool import BaseTool, ToolParameter


class WeatherTool(BaseTool):
    """Weather information tool (mock implementation for POC)"""
    
    @property
    def name(self) -> str:
        return "weather"
    
    @property
    def description(self) -> str:
        return "Get current weather information for a specific city"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="city",
                type="string",
                description="City name to get weather for (e.g., 'Seoul', 'New York')",
                required=True
            )
        ]
    
    async def execute(self, city: str) -> Dict[str, Any]:
        """Get weather information (mock implementation)"""
        # This is a mock implementation for POC
        # In production, you would call a real weather API
        
        mock_weather = {
            "seoul": {"temp": 25, "condition": "Partly cloudy", "humidity": 60},
            "new york": {"temp": 18, "condition": "Sunny", "humidity": 45},
            "london": {"temp": 15, "condition": "Rainy", "humidity": 80},
            "tokyo": {"temp": 28, "condition": "Clear", "humidity": 55},
        }
        
        city_lower = city.lower()
        
        if city_lower in mock_weather:
            weather_data = mock_weather[city_lower]
            return {
                "success": True,
                "city": city,
                "temperature": weather_data["temp"],
                "condition": weather_data["condition"],
                "humidity": weather_data["humidity"],
                "unit": "celsius"
            }
        else:
            # Return random weather for unknown cities
            return {
                "success": True,
                "city": city,
                "temperature": 20,
                "condition": "Partly cloudy",
                "humidity": 50,
                "unit": "celsius",
                "note": "Mock data - real API integration needed"
            }