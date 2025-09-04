"""
Calculator Agent - A2A Standard Implementation

A mathematical calculator agent that performs arithmetic operations, 
unit conversions, and statistical calculations following A2A samples patterns.
"""

import math
import re
import ast
import operator
import statistics
from collections.abc import AsyncIterable
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

import logging

# Import metrics collection
from common.metrics import get_agent_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safe mathematical operations for AST evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Mathematical functions
MATH_FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sqrt': math.sqrt,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'abs': abs,
    'round': round,
    'floor': math.floor,
    'ceil': math.ceil,
    'pi': math.pi,
    'e': math.e,
}

# Unit conversion factors
UNIT_CONVERSIONS = {
    'temperature': {
        'celsius_to_fahrenheit': lambda c: (c * 9/5) + 32,
        'fahrenheit_to_celsius': lambda f: (f - 32) * 5/9,
        'celsius_to_kelvin': lambda c: c + 273.15,
        'kelvin_to_celsius': lambda k: k - 273.15,
    },
    'length': {
        'meters_to_feet': lambda m: m * 3.28084,
        'feet_to_meters': lambda f: f / 3.28084,
        'meters_to_inches': lambda m: m * 39.3701,
        'inches_to_meters': lambda i: i / 39.3701,
        'kilometers_to_miles': lambda km: km * 0.621371,
        'miles_to_kilometers': lambda mi: mi / 0.621371,
    },
    'weight': {
        'kg_to_pounds': lambda kg: kg * 2.20462,
        'pounds_to_kg': lambda lb: lb / 2.20462,
        'grams_to_ounces': lambda g: g * 0.035274,
        'ounces_to_grams': lambda oz: oz / 0.035274,
    }
}


class ResponseFormat:
    """Response format for calculator results."""
    
    def __init__(self, status: Literal['input_required', 'completed', 'error'], 
                 message: str, calculation_result: Optional[float] = None):
        self.status = status
        self.message = message
        self.calculation_result = calculation_result


class CalculatorAgent:
    """Calculator Agent - A specialized assistant for mathematical calculations."""

    SYSTEM_INSTRUCTION = (
        'You are a specialized calculator assistant for mathematical calculations. '
        'Your capabilities include: arithmetic operations, unit conversions, '
        'statistical analysis, and mathematical functions. '
        'If the user asks about anything other than mathematics, '
        'politely state that you can only assist with mathematical calculations.'
    )

    FORMAT_INSTRUCTION = (
        'Set response status to input_required if the user needs to provide more information. '
        'Set response status to error if there is an error while processing the request. '
        'Set response status to completed if the calculation is complete.'
    )

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        """Initialize the Calculator Agent."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize metrics collection with separate metrics port
        self.metrics = get_agent_metrics("calculator", metrics_port=9081)

    async def stream(self, query: str, context_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        Stream calculation responses.
        
        Args:
            query: Mathematical query from user
            context_id: Context identifier for the conversation
            
        Yields:
            Dictionary with calculation progress and results
        """
        async with self.metrics.track_request_duration("calculation"):
            try:
                # Analyze the query to determine calculation type
                self.logger.info(f"Processing calculation query: {query}")
                
                # Try to perform the calculation
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Analyzing mathematical expression...',
                }
                
                result = await self._perform_calculation(query)
                
                if result.status == 'completed':
                    yield {
                        'is_task_complete': True,
                        'require_user_input': False,
                        'content': result.message,
                    }
                elif result.status == 'input_required':
                    yield {
                        'is_task_complete': False,
                        'require_user_input': True,
                        'content': result.message,
                    }
                else:  # error
                    yield {
                        'is_task_complete': False,
                        'require_user_input': True,
                        'content': result.message,
                    }
                    
            except Exception as e:
                self.logger.error(f"Error in calculation stream: {e}")
                yield {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': f'An error occurred during calculation: {str(e)}',
                }

    async def _perform_calculation(self, query: str) -> ResponseFormat:
        """
        Perform the actual calculation based on the query.
        
        Args:
            query: Mathematical query string
            
        Returns:
            ResponseFormat with calculation result
        """
        try:
            query_lower = query.lower().strip()
            
            # Check for unit conversions
            if 'convert' in query_lower or '°' in query:
                return await self._handle_unit_conversion(query)
            
            # Check for statistical operations
            if any(word in query_lower for word in ['average', 'mean', 'median', 'mode', 'std', 'variance']):
                return await self._handle_statistics(query)
            
            # Handle basic mathematical expressions
            return await self._handle_arithmetic(query)
            
        except Exception as e:
            self.logger.error(f"Calculation error: {e}")
            return ResponseFormat(
                status='error',
                message=f'Error performing calculation: {str(e)}'
            )

    async def _handle_arithmetic(self, expression: str) -> ResponseFormat:
        """Handle basic arithmetic expressions."""
        try:
            # Clean the expression
            cleaned = self._clean_expression(expression)
            
            if not cleaned:
                return ResponseFormat(
                    status='input_required',
                    message='Please provide a valid mathematical expression to calculate.'
                )
            
            # Evaluate the expression safely
            result = self._safe_eval(cleaned)
            
            return ResponseFormat(
                status='completed',
                message=f'Result: {cleaned} = {result}',
                calculation_result=float(result)
            )
            
        except Exception as e:
            return ResponseFormat(
                status='error',
                message=f'Invalid mathematical expression: {str(e)}'
            )

    async def _handle_unit_conversion(self, query: str) -> ResponseFormat:
        """Handle unit conversion requests."""
        try:
            # Parse conversion request
            conversion_result = self._parse_and_convert(query)
            
            if conversion_result:
                return ResponseFormat(
                    status='completed',
                    message=conversion_result
                )
            else:
                return ResponseFormat(
                    status='error',
                    message='Unable to parse unit conversion. Please specify the conversion clearly (e.g., "Convert 100°F to Celsius").'
                )
                
        except Exception as e:
            return ResponseFormat(
                status='error',
                message=f'Unit conversion error: {str(e)}'
            )

    async def _handle_statistics(self, query: str) -> ResponseFormat:
        """Handle statistical calculations."""
        try:
            # Extract numbers from the query
            numbers = self._extract_numbers(query)
            
            if not numbers:
                return ResponseFormat(
                    status='input_required',
                    message='Please provide numbers for statistical calculation.'
                )
            
            query_lower = query.lower()
            result_message = f'For the numbers {numbers}:\n'
            
            if 'mean' in query_lower or 'average' in query_lower:
                mean_val = statistics.mean(numbers)
                result_message += f'Mean (Average): {mean_val:.4f}'
            elif 'median' in query_lower:
                median_val = statistics.median(numbers)
                result_message += f'Median: {median_val}'
            elif 'mode' in query_lower:
                try:
                    mode_val = statistics.mode(numbers)
                    result_message += f'Mode: {mode_val}'
                except statistics.StatisticsError:
                    result_message += 'Mode: No unique mode found'
            elif 'std' in query_lower or 'standard deviation' in query_lower:
                std_val = statistics.stdev(numbers) if len(numbers) > 1 else 0
                result_message += f'Standard Deviation: {std_val:.4f}'
            elif 'variance' in query_lower:
                var_val = statistics.variance(numbers) if len(numbers) > 1 else 0
                result_message += f'Variance: {var_val:.4f}'
            else:
                # Provide all statistics
                mean_val = statistics.mean(numbers)
                median_val = statistics.median(numbers)
                result_message += f'Mean: {mean_val:.4f}\nMedian: {median_val}'
                if len(numbers) > 1:
                    std_val = statistics.stdev(numbers)
                    result_message += f'\nStandard Deviation: {std_val:.4f}'
            
            return ResponseFormat(
                status='completed',
                message=result_message
            )
            
        except Exception as e:
            return ResponseFormat(
                status='error',
                message=f'Statistical calculation error: {str(e)}'
            )

    def _clean_expression(self, expression: str) -> str:
        """Clean and validate mathematical expression."""
        # Remove common words and keep only mathematical content
        expression = re.sub(r'\b(what\s+is|calculate|compute|find|solve)\b', '', expression.lower())
        expression = re.sub(r'[^\d+\-*/().\s]', '', expression)
        expression = expression.strip()
        
        # Replace common patterns
        expression = expression.replace('x', '*').replace('÷', '/')
        
        return expression

    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression using AST."""
        try:
            node = ast.parse(expression, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expression}")

    def _eval_node(self, node):
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError("Unsupported operation")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError("Unsupported unary operation")
        else:
            raise ValueError("Unsupported expression")

    def _parse_and_convert(self, query: str) -> Optional[str]:
        """Parse and execute unit conversions."""
        query_lower = query.lower()
        
        # Temperature conversions
        if '°f' in query_lower or 'fahrenheit' in query_lower:
            numbers = self._extract_numbers(query)
            if numbers:
                if 'celsius' in query_lower or '°c' in query_lower:
                    celsius = UNIT_CONVERSIONS['temperature']['fahrenheit_to_celsius'](numbers[0])
                    return f'{numbers[0]}°F = {celsius:.2f}°C'
        
        if '°c' in query_lower or 'celsius' in query_lower:
            numbers = self._extract_numbers(query)
            if numbers:
                if 'fahrenheit' in query_lower or '°f' in query_lower:
                    fahrenheit = UNIT_CONVERSIONS['temperature']['celsius_to_fahrenheit'](numbers[0])
                    return f'{numbers[0]}°C = {fahrenheit:.2f}°F'
        
        # Length conversions
        if 'feet' in query_lower and 'meter' in query_lower:
            numbers = self._extract_numbers(query)
            if numbers:
                if 'feet' in query_lower and 'meter' in query_lower:
                    meters = UNIT_CONVERSIONS['length']['feet_to_meters'](numbers[0])
                    return f'{numbers[0]} feet = {meters:.2f} meters'
        
        return None

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text."""
        # Find all numbers (including decimals)
        pattern = r'-?\d+\.?\d*'
        matches = re.findall(pattern, text)
        return [float(match) for match in matches if match]
