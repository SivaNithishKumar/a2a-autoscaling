"""
Smart Routing Client with Context-Aware Multi-Agent Orchestration

Provides intelligent routing with context awareness, multi-agent coordination,
and complex query decomposition.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from .ai_agent_router import AgentNetwork, LLMClient, RoutingResult

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Analysis of a user query."""
    query: str
    intent: str
    entities: List[str]
    complexity: str  # 'simple', 'medium', 'complex'
    requires_multiple_agents: bool
    suggested_agents: List[str]
    decomposition: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Plan for executing a complex query."""
    query: str
    steps: List[Dict[str, Any]]
    execution_type: str  # 'sequential', 'parallel', 'hybrid'
    estimated_time: float
    confidence: float


@dataclass
class ExecutionResult:
    """Result of query execution."""
    query: str
    plan: ExecutionPlan
    results: List[Dict[str, Any]]
    success: bool
    total_time: float
    errors: List[str] = field(default_factory=list)


class QueryAnalyzer:
    """Analyzes queries to determine complexity and routing needs."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    async def analyze_query(self, query: str, context: Dict = None) -> QueryAnalysis:
        """Analyze a query to determine routing strategy."""
        
        prompt = f"""
Analyze the following user query and provide a detailed analysis:

Query: "{query}"
Context: {json.dumps(context or {}, indent=2)}

Provide analysis in JSON format:
{{
    "intent": "calculation|weather|research|greeting|multi_task|other",
    "entities": ["list", "of", "extracted", "entities"],
    "complexity": "simple|medium|complex",
    "requires_multiple_agents": true/false,
    "suggested_agents": ["agent1", "agent2"],
    "decomposition": ["step1", "step2", "step3"]
}}

Guidelines:
- simple: Single task, one agent
- medium: Single task, might need clarification
- complex: Multiple tasks or requires coordination
- decomposition: Break complex queries into steps
- suggested_agents: base, calculator, weather, research
"""

        try:
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
                
            analysis_data = json.loads(result_text)
            
            return QueryAnalysis(
                query=query,
                intent=analysis_data.get("intent", "other"),
                entities=analysis_data.get("entities", []),
                complexity=analysis_data.get("complexity", "simple"),
                requires_multiple_agents=analysis_data.get("requires_multiple_agents", False),
                suggested_agents=analysis_data.get("suggested_agents", []),
                decomposition=analysis_data.get("decomposition", [])
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return self._fallback_analysis(query)
            
    def _fallback_analysis(self, query: str) -> QueryAnalysis:
        """Fallback analysis using simple heuristics."""
        
        query_lower = query.lower()
        
        # Simple intent detection
        if any(word in query_lower for word in ['calculate', 'compute', 'math', '+', '-', '*', '/']):
            intent = "calculation"
            suggested_agents = ["calculator"]
        elif any(word in query_lower for word in ['weather', 'temperature', 'forecast']):
            intent = "weather"
            suggested_agents = ["weather"]
        elif any(word in query_lower for word in ['research', 'find', 'search', 'who', 'what']):
            intent = "research"
            suggested_agents = ["research"]
        elif any(word in query_lower for word in ['hello', 'hi', 'help']):
            intent = "greeting"
            suggested_agents = ["base"]
        else:
            intent = "other"
            suggested_agents = ["base"]
            
        # Check for multiple tasks
        and_count = query_lower.count(' and ')
        comma_count = query_lower.count(',')
        requires_multiple = and_count > 0 or comma_count > 1
        
        complexity = "complex" if requires_multiple else "simple"
        
        return QueryAnalysis(
            query=query,
            intent=intent,
            entities=[],
            complexity=complexity,
            requires_multiple_agents=requires_multiple,
            suggested_agents=suggested_agents,
            decomposition=[]
        )


class ExecutionPlanner:
    """Creates execution plans for complex queries."""
    
    def __init__(self, llm_client: LLMClient, agent_network: AgentNetwork):
        self.llm_client = llm_client
        self.agent_network = agent_network
        
    async def create_execution_plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """Create an execution plan based on query analysis."""
        
        if analysis.complexity == "simple":
            return await self._create_simple_plan(analysis)
        elif analysis.requires_multiple_agents:
            return await self._create_multi_agent_plan(analysis)
        else:
            return await self._create_standard_plan(analysis)
            
    async def _create_simple_plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """Create a simple execution plan for straightforward queries."""
        
        agent = analysis.suggested_agents[0] if analysis.suggested_agents else "base"
        
        steps = [
            {
                "step": 1,
                "action": "execute_query",
                "agent": agent,
                "query": analysis.query,
                "expected_duration": 2.0
            }
        ]
        
        return ExecutionPlan(
            query=analysis.query,
            steps=steps,
            execution_type="sequential",
            estimated_time=2.0,
            confidence=0.9
        )
        
    async def _create_multi_agent_plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """Create a multi-agent execution plan for complex queries."""
        
        prompt = f"""
Create an execution plan for a complex query that requires multiple agents.

Query: "{analysis.query}"
Available agents: {[agent.name for agent in self.agent_network.agents.values()]}
Suggested agents: {analysis.suggested_agents}
Decomposition: {analysis.decomposition}

Create a JSON execution plan:
{{
    "execution_type": "sequential|parallel|hybrid",
    "steps": [
        {{
            "step": 1,
            "action": "execute_query|aggregate_results|coordinate",
            "agent": "agent_name",
            "query": "specific query for this step",
            "depends_on": [0], // step numbers this depends on
            "expected_duration": 2.5
        }}
    ],
    "estimated_time": 5.0,
    "confidence": 0.8
}}

Guidelines:
- Break complex queries into logical steps
- Use parallel execution when steps are independent
- Use sequential when steps depend on each other
- Include aggregation step if needed
"""

        try:
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
                
            plan_data = json.loads(result_text)
            
            return ExecutionPlan(
                query=analysis.query,
                steps=plan_data.get("steps", []),
                execution_type=plan_data.get("execution_type", "sequential"),
                estimated_time=plan_data.get("estimated_time", 5.0),
                confidence=plan_data.get("confidence", 0.7)
            )
            
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            return await self._create_fallback_plan(analysis)
            
    async def _create_standard_plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """Create a standard execution plan."""
        
        agent = analysis.suggested_agents[0] if analysis.suggested_agents else "base"
        
        steps = [
            {
                "step": 1,
                "action": "execute_query",
                "agent": agent,
                "query": analysis.query,
                "expected_duration": 3.0
            }
        ]
        
        if analysis.complexity == "medium":
            # Add clarification step
            steps.insert(0, {
                "step": 0,
                "action": "clarify_query",
                "agent": "base",
                "query": f"Clarify requirements for: {analysis.query}",
                "expected_duration": 1.0
            })
            
        return ExecutionPlan(
            query=analysis.query,
            steps=steps,
            execution_type="sequential",
            estimated_time=sum(step["expected_duration"] for step in steps),
            confidence=0.8
        )
        
    async def _create_fallback_plan(self, analysis: QueryAnalysis) -> ExecutionPlan:
        """Create a fallback plan when LLM planning fails."""
        
        if analysis.requires_multiple_agents and len(analysis.suggested_agents) > 1:
            # Create parallel execution for multiple agents
            steps = []
            for i, agent in enumerate(analysis.suggested_agents):
                steps.append({
                    "step": i + 1,
                    "action": "execute_query",
                    "agent": agent,
                    "query": analysis.query,
                    "expected_duration": 3.0
                })
                
            # Add aggregation step
            steps.append({
                "step": len(steps) + 1,
                "action": "aggregate_results", 
                "agent": "base",
                "query": "Aggregate and synthesize results",
                "depends_on": list(range(1, len(analysis.suggested_agents) + 1)),
                "expected_duration": 2.0
            })
            
            return ExecutionPlan(
                query=analysis.query,
                steps=steps,
                execution_type="hybrid",
                estimated_time=5.0,
                confidence=0.6
            )
        else:
            # Simple fallback
            return await self._create_simple_plan(analysis)


class SmartRoutingClient:
    """
    Smart routing client with context-aware multi-agent orchestration.
    
    Provides intelligent query analysis, execution planning, and coordinated
    multi-agent responses for complex queries.
    """
    
    def __init__(self, agent_network: AgentNetwork, llm_client: LLMClient):
        self.agent_network = agent_network
        self.llm_client = llm_client
        self.analyzer = QueryAnalyzer(llm_client)
        self.planner = ExecutionPlanner(llm_client, agent_network)
        self.execution_history: List[ExecutionResult] = []
        
    async def smart_execute(self, query: str, context: Dict = None) -> ExecutionResult:
        """
        Execute a query using smart routing and orchestration.
        """
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze the query
            analysis = await self.analyzer.analyze_query(query, context)
            logger.info(f"Query analysis: {analysis.intent}, complexity: {analysis.complexity}")
            
            # Step 2: Create execution plan
            plan = await self.planner.create_execution_plan(analysis)
            logger.info(f"Execution plan: {plan.execution_type}, {len(plan.steps)} steps")
            
            # Step 3: Execute the plan
            results = await self._execute_plan(plan)
            
            # Step 4: Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Step 5: Create result
            execution_result = ExecutionResult(
                query=query,
                plan=plan,
                results=results,
                success=all(r.get("success", False) for r in results),
                total_time=execution_time
            )
            
            # Store in history
            self.execution_history.append(execution_result)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Smart execution failed: {e}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ExecutionResult(
                query=query,
                plan=ExecutionPlan(query, [], "sequential", 0, 0),
                results=[],
                success=False,
                total_time=execution_time,
                errors=[str(e)]
            )
            
    async def _execute_plan(self, plan: ExecutionPlan) -> List[Dict[str, Any]]:
        """Execute an execution plan."""
        
        results = []
        step_results = {}
        
        if plan.execution_type == "sequential":
            # Execute steps sequentially
            for step in plan.steps:
                result = await self._execute_step(step, step_results)
                results.append(result)
                step_results[step["step"]] = result
                
        elif plan.execution_type == "parallel":
            # Execute independent steps in parallel
            tasks = []
            for step in plan.steps:
                if not step.get("depends_on"):
                    tasks.append(self._execute_step(step, step_results))
                    
            if tasks:
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        results.append({"success": False, "error": str(result)})
                    else:
                        results.append(result)
                        
        elif plan.execution_type == "hybrid":
            # Execute with dependency management
            results = await self._execute_hybrid_plan(plan)
            
        return results
        
    async def _execute_step(self, step: Dict[str, Any], previous_results: Dict = None) -> Dict[str, Any]:
        """Execute a single step."""
        
        try:
            agent_name = step["agent"]
            query = step["query"]
            action = step.get("action", "execute_query")
            
            if action == "execute_query":
                # Simulate agent execution (replace with actual A2A calls)
                response = await self._simulate_agent_execution(agent_name, query)
                
                return {
                    "step": step["step"],
                    "agent": agent_name,
                    "query": query,
                    "response": response,
                    "success": True,
                    "duration": step.get("expected_duration", 2.0)
                }
                
            elif action == "aggregate_results":
                # Aggregate results from previous steps
                dependent_steps = step.get("depends_on", [])
                dependent_results = [previous_results.get(s) for s in dependent_steps if s in previous_results]
                
                aggregated_response = await self._aggregate_results(dependent_results)
                
                return {
                    "step": step["step"],
                    "agent": agent_name,
                    "action": "aggregate_results",
                    "response": aggregated_response,
                    "success": True,
                    "duration": step.get("expected_duration", 1.0)
                }
                
            else:
                return {
                    "step": step["step"],
                    "agent": agent_name,
                    "action": action,
                    "response": f"Executed {action}",
                    "success": True,
                    "duration": 1.0
                }
                
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {
                "step": step["step"],
                "agent": step.get("agent", "unknown"),
                "success": False,
                "error": str(e),
                "duration": 0.0
            }
            
    async def _execute_hybrid_plan(self, plan: ExecutionPlan) -> List[Dict[str, Any]]:
        """Execute a hybrid plan with dependency management."""
        
        results = []
        step_results = {}
        completed_steps = set()
        
        while len(completed_steps) < len(plan.steps):
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = []
            
            for step in plan.steps:
                step_num = step["step"]
                if step_num in completed_steps:
                    continue
                    
                dependencies = step.get("depends_on", [])
                if all(dep in completed_steps for dep in dependencies):
                    ready_steps.append(step)
                    
            if not ready_steps:
                logger.error("Circular dependency detected in execution plan")
                break
                
            # Execute ready steps in parallel
            if len(ready_steps) == 1:
                # Single step - execute sequentially
                result = await self._execute_step(ready_steps[0], step_results)
                results.append(result)
                step_results[ready_steps[0]["step"]] = result
                completed_steps.add(ready_steps[0]["step"])
            else:
                # Multiple steps - execute in parallel
                tasks = [self._execute_step(step, step_results) for step in ready_steps]
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        result = {"success": False, "error": str(result)}
                    results.append(result)
                    step_results[ready_steps[i]["step"]] = result
                    completed_steps.add(ready_steps[i]["step"])
                    
        return results
        
    async def _simulate_agent_execution(self, agent_name: str, query: str) -> str:
        """Simulate agent execution (replace with actual A2A calls)."""
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        agent_responses = {
            "base": f"Base agent processing: {query}",
            "calculator": f"Calculator result for '{query}': [Mathematical calculation would be performed]",
            "weather": f"Weather information for '{query}': [Weather data would be retrieved]",
            "research": f"Research results for '{query}': [Research would be conducted]"
        }
        
        return agent_responses.get(agent_name, f"Agent {agent_name} processed: {query}")
        
    async def _aggregate_results(self, results: List[Dict[str, Any]]) -> str:
        """Aggregate results from multiple agents."""
        
        if not results:
            return "No results to aggregate"
            
        successful_results = [r for r in results if r and r.get("success")]
        
        if not successful_results:
            return "All agent calls failed"
            
        # Simple aggregation - in production, use LLM for better synthesis
        aggregated = "Combined results:\n"
        for i, result in enumerate(successful_results, 1):
            response = result.get("response", "No response")
            agent = result.get("agent", "Unknown")
            aggregated += f"{i}. {agent}: {response}\n"
            
        return aggregated.strip()
        
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        
        if not self.execution_history:
            return {"total_executions": 0}
            
        successful_executions = [e for e in self.execution_history if e.success]
        total_time = sum(e.total_time for e in self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful_executions),
            "success_rate": len(successful_executions) / len(self.execution_history),
            "average_execution_time": total_time / len(self.execution_history),
            "total_time": total_time
        }
        
    def get_recent_results(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent execution results."""
        
        recent = self.execution_history[-limit:] if self.execution_history else []
        
        return [
            {
                "query": result.query,
                "success": result.success,
                "execution_type": result.plan.execution_type,
                "steps": len(result.plan.steps),
                "total_time": result.total_time,
                "errors": result.errors
            }
            for result in recent
        ]


# Example usage
async def main():
    """Example usage of the Smart Routing Client."""
    
    print("🧠 Smart Routing Client Demo")
    print("=" * 50)
    
    # Set up components (you'll need actual OpenAI API key)
    try:
        from .ai_agent_router import create_ai_router
        
        # This requires OPENAI_API_KEY environment variable
        router = create_ai_router()
        
        smart_client = SmartRoutingClient(
            router.network,
            router.llm_client
        )
        
        # Test queries of varying complexity
        test_queries = [
            "What's 25 + 17?",  # Simple
            "What's the weather in London and calculate 100 * 50?",  # Complex multi-agent
            "Research the population of Tokyo and tell me the weather there",  # Complex sequential
            "Hello, how are you today?",  # Simple greeting
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            
            result = await smart_client.smart_execute(query)
            
            print(f"✅ Success: {result.success}")
            print(f"⏱️  Time: {result.total_time:.2f}s")
            print(f"🔄 Execution: {result.plan.execution_type}")
            print(f"📊 Steps: {len(result.plan.steps)}")
            
            if result.results:
                print("📋 Results:")
                for i, res in enumerate(result.results, 1):
                    if res.get("success"):
                        print(f"  {i}. {res.get('agent', 'N/A')}: {res.get('response', 'N/A')[:100]}...")
                    else:
                        print(f"  {i}. Error: {res.get('error', 'Unknown error')}")
                        
        # Show statistics
        print(f"\n📈 Execution Statistics:")
        stats = smart_client.get_execution_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Note: This demo requires OPENAI_API_KEY environment variable")


if __name__ == "__main__":
    asyncio.run(main())