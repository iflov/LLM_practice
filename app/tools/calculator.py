from typing import Dict, Any, List
import math
from app.tools.base_tool import BaseTool, ToolParameter


class CalculatorTool(BaseTool):
    """Calculator tool for mathematical operations"""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform mathematical calculations. Supports basic operations (+, -, *, /) and advanced functions (sqrt, pow, sin, cos, etc.)"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'pow(2, 3)')",
                required=True
            )
        ]
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        """Execute mathematical calculation"""
        try:
            # Create safe namespace for eval
            safe_dict = {
                'sqrt': math.sqrt,
                'pow': math.pow,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'pi': math.pi,
                'e': math.e,
                'abs': abs,
                'round': round,
                'min': min,
                'max': max
            }
            
            # Remove any potentially dangerous characters
            expression = expression.replace('__', '').replace('import', '').replace('exec', '')
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return {
                "success": True,
                "result": result,
                "expression": expression
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expression": expression
            }