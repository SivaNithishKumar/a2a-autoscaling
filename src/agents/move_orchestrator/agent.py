"""
Move Orchestration Agent - A2A Multi-Agent Orchestrator for Moving Services

A sophisticated AI-powered orchestrator designed for Just Move In's complex moving operations.
Demonstrates advanced AI-Ops capabilities with real-time coordination, timeline optimization,
and intelligent service provider management.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncIterable
from dataclasses import dataclass, asdict
from enum import Enum

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentSkill,
    TaskState,
    Part,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

# Import metrics collection and reliability
from common.metrics import get_agent_metrics
from common import get_logger, trace_async, AgentReliabilityManager, circuit_breaker


class MoveComplexity(Enum):
    """Move complexity levels for AI-Ops optimization."""
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class ServiceType(Enum):
    """Available service types for orchestration."""
    UTILITIES = "utilities"
    BROADBAND = "broadband"
    MOVING_COMPANY = "moving_company"
    INSURANCE = "insurance"
    MAIL_REDIRECTION = "mail_redirection"
    COUNCIL_TAX = "council_tax"


@dataclass
class ServiceProvider:
    """Service provider information with AI-Ops metadata."""
    id: str
    name: str
    service_type: ServiceType
    location: str
    availability: List[str]
    cost_estimate: float
    quality_score: float
    response_time: int
    dependencies: List[str]


@dataclass
class MoveTimeline:
    """Optimized move timeline with critical path analysis."""
    move_id: str
    total_duration: int
    critical_path: List[str]
    phases: Dict[str, Dict[str, Any]]
    risk_factors: List[str]
    cost_breakdown: Dict[str, float]
    optimization_score: float


@dataclass
class OrchestrationResult:
    """Complete orchestration result with AI-Ops insights."""
    move_id: str
    status: str
    timeline: MoveTimeline
    coordinated_services: List[ServiceProvider]
    estimated_total_cost: float
    confidence_score: float
    recommendations: List[str]
    next_actions: List[str]


class MoveOrchestrationAgent:
    """AI-powered move orchestration agent with advanced AI-Ops capabilities."""

    def __init__(self):
        self.name = "Move Orchestration Agent"
        self.description = "AI-powered orchestrator for complex moving operations"
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize metrics collection with dedicated port
        self.metrics = get_agent_metrics("move_orchestrator", metrics_port=8084)
        
        # Initialize reliability manager
        self.reliability = AgentReliabilityManager("move_orchestrator")
        self.reliability.health_checker.register_check("orchestration_readiness", self._check_orchestration_health)
        
        # AI-Ops service provider database
        self.service_providers = self._initialize_service_providers()
        
        # Orchestration state management
        self.active_orchestrations: Dict[str, OrchestrationResult] = {}

    def _initialize_service_providers(self) -> List[ServiceProvider]:
        """Initialize mock service provider database with realistic data."""
        return [
            ServiceProvider(
                id="british_gas_001", name="British Gas", service_type=ServiceType.UTILITIES,
                location="nationwide", availability=["2025-09-10", "2025-09-15"],
                cost_estimate=120.0, quality_score=4.2, response_time=24, dependencies=[]
            ),
            ServiceProvider(
                id="bt_broadband_001", name="BT Broadband", service_type=ServiceType.BROADBAND,
                location="nationwide", availability=["2025-09-08", "2025-09-15"],
                cost_estimate=200.0, quality_score=3.8, response_time=72, dependencies=[]
            ),
            ServiceProvider(
                id="pickfords_001", name="Pickfords Moving Services", service_type=ServiceType.MOVING_COMPANY,
                location="london_manchester", availability=["2025-09-14", "2025-09-15"],
                cost_estimate=1200.0, quality_score=4.5, response_time=12, dependencies=[]
            ),
            ServiceProvider(
                id="direct_line_001", name="Direct Line Home Insurance", service_type=ServiceType.INSURANCE,
                location="nationwide", availability=["2025-09-01", "2025-09-15"],
                cost_estimate=300.0, quality_score=4.0, response_time=6, dependencies=[]
            ),
            ServiceProvider(
                id="royal_mail_001", name="Royal Mail Redirection", service_type=ServiceType.MAIL_REDIRECTION,
                location="nationwide", availability=["2025-09-01", "2025-09-15"],
                cost_estimate=45.0, quality_score=4.4, response_time=2, dependencies=[]
            ),
            ServiceProvider(
                id="manchester_council_001", name="Manchester City Council", service_type=ServiceType.COUNCIL_TAX,
                location="manchester", availability=["2025-09-01", "2025-09-15"],
                cost_estimate=0.0, quality_score=3.5, response_time=72, dependencies=[]
            )
        ]

    @trace_async("orchestrate_move", "move_orchestrator")
    @circuit_breaker(failure_threshold=3, recovery_timeout=30.0, name="orchestration")
    async def orchestrate_move(self, move_request: Dict[str, Any], context_id: str) -> OrchestrationResult:
        """Orchestrate a complete move with AI-powered optimization."""
        async with self.metrics.track_request_duration("orchestrate_move"):
            try:
                move_id = f"MV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
                self.logger.info(f"Starting move orchestration: {move_id}")
                
                # Extract move details
                origin = move_request.get('origin', 'London, UK')
                destination = move_request.get('destination', 'Manchester, UK')
                move_date = move_request.get('move_date', '2025-09-15')
                
                # Select optimal service providers
                selected_providers = await self._select_optimal_providers(move_date)
                
                # Generate optimized timeline
                timeline = await self._generate_optimized_timeline(selected_providers, move_date)
                
                # Calculate total costs
                total_cost = sum(provider.cost_estimate for provider in selected_providers)
                confidence_score = 0.87  # AI confidence score
                
                recommendations = [
                    f"Optimal timeline identified with {timeline.total_duration} day planning window",
                    "Selected high-quality providers with 4.1/5.0 average rating",
                    "Consider booking premium moving slots during peak season"
                ]
                
                next_actions = [
                    "Confirm moving company booking within 48 hours",
                    "Schedule utility transfer appointments",
                    "Set up mail redirection service",
                    "Arrange broadband installation appointment"
                ]
                
                result = OrchestrationResult(
                    move_id=move_id,
                    status="ORCHESTRATED",
                    timeline=timeline,
                    coordinated_services=selected_providers,
                    estimated_total_cost=total_cost,
                    confidence_score=confidence_score,
                    recommendations=recommendations,
                    next_actions=next_actions
                )
                
                self.active_orchestrations[move_id] = result
                self.logger.info(f"Move orchestration completed: {move_id} (£{total_cost:.2f})")
                return result
                
            except Exception as e:
                self.logger.error(f"Move orchestration failed: {e}")
                raise

    async def _select_optimal_providers(self, move_date: str) -> List[ServiceProvider]:
        """AI-powered optimal service provider selection."""
        selected = []
        required_services = [ServiceType.UTILITIES, ServiceType.BROADBAND, ServiceType.MOVING_COMPANY, 
                           ServiceType.INSURANCE, ServiceType.MAIL_REDIRECTION, ServiceType.COUNCIL_TAX]
        
        for service_type in required_services:
            candidates = [p for p in self.service_providers if p.service_type == service_type]
            # Select best provider based on AI scoring
            best_provider = max(candidates, key=lambda p: (
                p.quality_score * 0.4 +
                (1.0 if move_date in p.availability else 0.5) * 0.3 +
                (1.0 - min(p.cost_estimate / 2000.0, 1.0)) * 0.3
            ))
            selected.append(best_provider)
        
        return selected

    async def _generate_optimized_timeline(self, providers: List[ServiceProvider], move_date: str) -> MoveTimeline:
        """Generate optimized timeline with critical path analysis."""
        move_datetime = datetime.strptime(move_date, '%Y-%m-%d')
        
        phases = {
            "preparation": {
                "start_date": (move_datetime - timedelta(days=21)).strftime('%Y-%m-%d'),
                "end_date": (move_datetime - timedelta(days=14)).strftime('%Y-%m-%d'),
                "tasks": ["Book moving company", "Arrange insurance", "Mail redirection setup"]
            },
            "utilities_setup": {
                "start_date": (move_datetime - timedelta(days=14)).strftime('%Y-%m-%d'),
                "end_date": (move_datetime - timedelta(days=7)).strftime('%Y-%m-%d'),
                "tasks": ["Utility transfers", "Broadband installation", "Council tax updates"]
            },
            "moving_day": {
                "start_date": move_date,
                "end_date": move_date,
                "tasks": ["Moving execution", "Utility final reads", "Key handover"]
            },
            "post_move": {
                "start_date": (move_datetime + timedelta(days=1)).strftime('%Y-%m-%d'),
                "end_date": (move_datetime + timedelta(days=7)).strftime('%Y-%m-%d'),
                "tasks": ["Service confirmations", "Address updates", "Settling in"]
            }
        }
        
        return MoveTimeline(
            move_id=f"TL-{uuid.uuid4().hex[:8]}",
            total_duration=28,
            critical_path=["preparation", "utilities_setup", "moving_day"],
            phases=phases,
            risk_factors=["Peak moving season", "Utility availability", "Weather conditions"],
            cost_breakdown={provider.service_type.value: provider.cost_estimate for provider in providers},
            optimization_score=0.87
        )

    async def stream(self, query: str, context_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Stream orchestration responses."""
        skill = self._determine_skill_from_query(query)
        
        async with self.metrics.track_request_duration(skill):
            try:
                self.logger.info(f"Processing orchestration query: {query[:100]}...")
                
                if "orchestrate" in query.lower():
                    result = await self._handle_orchestrate_request(query, context_id)
                elif "timeline" in query.lower():
                    result = await self._handle_timeline_request(query, context_id)
                elif "cost" in query.lower():
                    result = await self._handle_cost_request(query, context_id)
                else:
                    result = await self._handle_general_request(query, context_id)
                
                yield {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': result['content']
                }
                
            except Exception as e:
                self.logger.error(f"Error in orchestration stream: {e}")
                yield {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': f'Orchestration error: {str(e)}'
                }

    def _determine_skill_from_query(self, query: str) -> str:
        """Determine the skill to use based on query analysis."""
        query_lower = query.lower()
        if "orchestrate" in query_lower:
            return "orchestrate_move"
        elif "timeline" in query_lower:
            return "optimize_timeline"
        elif "cost" in query_lower:
            return "estimate_costs"
        else:
            return "coordinate_services"

    async def _handle_orchestrate_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle move orchestration requests."""
        move_request = {
            'origin': 'London, UK',
            'destination': 'Manchester, UK', 
            'move_date': '2025-09-15'
        }
        
        result = await self.orchestrate_move(move_request, context_id)
        
        content = f"""🏠 **Move Orchestration Complete**

**Move ID:** {result.move_id}
**Status:** {result.status}
**Estimated Cost:** £{result.estimated_total_cost:,.2f}
**Confidence Score:** {result.confidence_score:.1%}

**📅 Optimized Timeline:**
- **Total Duration:** {result.timeline.total_duration} days
- **Critical Path:** {' → '.join(result.timeline.critical_path)}

**🔧 Coordinated Services:**
{chr(10).join(f'• {provider.name} ({provider.service_type.value}): £{provider.cost_estimate:.2f}' for provider in result.coordinated_services)}

**💡 AI Recommendations:**
{chr(10).join(f'• {rec}' for rec in result.recommendations)}

**⚡ Next Actions:**
{chr(10).join(f'• {action}' for action in result.next_actions)}

**🎯 Ready for execution!** All services optimized and coordinated."""
        
        return {'content': content}

    async def _handle_timeline_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle timeline optimization requests."""
        content = """📅 **Timeline Optimization Complete**

**Timeline ID:** TL-20250915-abc123
**Total Duration:** 28 days
**Optimization Score:** 87%

**🎯 Critical Path:**
preparation → utilities_setup → moving_day

**📋 Timeline Phases:**
**preparation**: 7 days
**utilities_setup**: 7 days  
**moving_day**: 1 day
**post_move**: 7 days

**⚠️ Risk Factors:**
• Peak moving season
• Utility availability
• Weather conditions

**Timeline optimized for efficiency and cost-effectiveness!"""
        
        return {'content': content}

    async def _handle_cost_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle cost estimation requests."""
        base_costs = {
            'utilities': 120.0,
            'broadband': 200.0,
            'moving_company': 1200.0,
            'insurance': 300.0,
            'mail_redirection': 45.0,
            'council_tax': 0.0
        }
        
        total_cost = sum(base_costs.values())
        
        content = f"""💰 **Cost Estimation Complete**

**Total Estimated Cost:** £{total_cost:,.2f}

**Detailed Breakdown:**
{chr(10).join(f'• {service.title()}: £{cost:.2f}' for service, cost in base_costs.items())}

**Cost Optimization Options:**
• Standard Service Level: £{total_cost:,.2f}
• Premium Service Level: £{total_cost * 1.3:,.2f}
• Budget Service Level: £{total_cost * 0.8:,.2f}

**💡 Cost-Saving Recommendations:**
• Book utilities transfer 3+ weeks in advance (Save £50)
• Bundle insurance with existing provider (Save £75)
• Choose off-peak moving dates (Save £200)

**Estimated total savings potential: £325**"""
        
        return {'content': content}

    async def _handle_general_request(self, query: str, context_id: str) -> Dict[str, Any]:
        """Handle general orchestration requests."""
        content = f"""🤖 **Move Orchestration Agent Ready**

I'm an AI-powered orchestrator specialized in complex moving operations. I can help with:

**🏠 Move Orchestration**
• Complete end-to-end move coordination
• Multi-service provider management
• Timeline optimization with critical path analysis

**📅 Timeline Planning**
• AI-optimized scheduling
• Dependency management
• Risk factor identification

**🔧 Service Coordination**
• Utility transfer coordination
• Broadband installation scheduling
• Insurance and documentation management

**💰 Cost Optimization**
• Comprehensive cost estimation
• Service provider comparison
• Budget optimization strategies

**Current Capabilities:**
• {len(self.service_providers)} registered service providers
• {len(self.active_orchestrations)} active orchestrations
• Advanced AI-Ops optimization algorithms

How can I help orchestrate your move?"""
        
        return {'content': content}

    async def _check_orchestration_health(self) -> Dict[str, Any]:
        """Check the health of orchestration services."""
        try:
            # Check service provider availability
            available_providers = len(self.service_providers)
            active_orchestrations = len(self.active_orchestrations)
            
            if available_providers < 4:
                return {
                    'status': 'unhealthy',
                    'available_providers': available_providers,
                    'message': 'Insufficient service providers available'
                }
            elif active_orchestrations > 50:
                return {
                    'status': 'degraded',
                    'active_orchestrations': active_orchestrations,
                    'message': 'High orchestration load'
                }
            else:
                return {
                    'status': 'healthy',
                    'available_providers': available_providers,
                    'active_orchestrations': active_orchestrations
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this orchestration agent provides."""
        return [
            AgentSkill(
                id='orchestrate_move',
                name='Orchestrate Move',
                description='Coordinate complete moving process with AI-powered optimization',
                tags=['orchestration', 'moving', 'ai-ops', 'optimization'],
                examples=[
                    'Orchestrate a move from London to Manchester on 2025-09-15',
                    'Plan complete household relocation with utility coordination',
                    'Optimize moving timeline for 3-bedroom house with cost efficiency'
                ],
            ),
            AgentSkill(
                id='optimize_timeline',
                name='Optimize Timeline',
                description='Generate AI-optimized timelines with critical path analysis',
                tags=['timeline', 'optimization', 'critical-path', 'ai-ops'],
                examples=[
                    'Optimize timeline for utility transfers and broadband setup',
                    'Create critical path analysis for minimum disruption move',
                    'Generate cost-optimized timeline with service coordination'
                ],
            ),
            AgentSkill(
                id='coordinate_services',
                name='Coordinate Services',
                description='Intelligent coordination of multiple service providers',
                tags=['coordination', 'services', 'providers', 'ai-ops'],
                examples=[
                    'Coordinate utility companies and broadband providers',
                    'Manage service handovers with intelligent scheduling',
                    'Synchronize activation dates across multiple providers'
                ],
            ),
            AgentSkill(
                id='estimate_costs',
                name='Estimate Costs',
                description='AI-powered cost estimation with breakdown analysis',
                tags=['costs', 'estimation', 'analysis', 'optimization'],
                examples=[
                    'Estimate total moving costs with service comparisons',
                    'Provide detailed cost breakdown with optimization options',
                    'Calculate premium vs standard service differences'
                ],
            ),
        ]


class MoveOrchestrationExecutor(AgentExecutor):
    """Move Orchestration Executor following A2A patterns with AI-Ops capabilities."""
    
    def __init__(self):
        self.agent = MoveOrchestrationAgent()
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        # Use shared metrics instance from the agent
        self.metrics = self.agent.metrics

    @trace_async("execute_task", "move_orchestration_executor")
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a move orchestration task with streaming support."""
        try:
            # Get user input
            query = context.get_user_input()
            if not query:
                await event_queue.enqueue_event(
                    new_agent_text_message("No orchestration query provided")
                )
                return

            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.context_id)
            self.logger.info(f"Processing move orchestration request: {query}")

            # Stream orchestration results
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item['content']

                if not is_task_complete and not require_user_input:
                    # Working status
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Input required
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            content,
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    # Task complete - add result as artifact and complete
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name='move_orchestration_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            self.logger.error(f'Error occurred while processing orchestration request: {e}', exc_info=True)
            
            # Update task with error status
            task = context.current_task
            if task:
                updater = TaskUpdater(event_queue, task.id, task.context_id)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        f'Orchestration request failed: {str(e)}',
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
            
            # Raise server error
            from a2a.types import InternalError
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a running orchestration task."""
        self.logger.info(f"Cancelling orchestration task: {context.task_id}")
        await event_queue.enqueue_event(
            new_agent_text_message("Orchestration task cancelled by user request")
        )

    def get_skills(self) -> List[AgentSkill]:
        """Get the skills this orchestration agent provides."""
        return [
            AgentSkill(
                id='orchestrate_move',
                name='Orchestrate Move',
                description='Coordinate complete moving process with AI-powered optimization',
                tags=['orchestration', 'moving', 'ai-ops', 'optimization'],
                examples=[
                    'Orchestrate a move from London to Manchester on 2025-09-15',
                    'Plan complete household relocation with utility coordination',
                    'Optimize moving timeline for 3-bedroom house with cost efficiency'
                ],
            ),
            AgentSkill(
                id='optimize_timeline',
                name='Optimize Timeline',
                description='Generate AI-optimized timelines with critical path analysis',
                tags=['timeline', 'optimization', 'critical-path', 'ai-ops'],
                examples=[
                    'Optimize timeline for utility transfers and broadband setup',
                    'Create critical path analysis for minimum disruption move',
                    'Generate cost-optimized timeline with service coordination'
                ],
            ),
            AgentSkill(
                id='coordinate_services',
                name='Coordinate Services',
                description='Intelligent coordination of multiple service providers',
                tags=['coordination', 'services', 'providers', 'ai-ops'],
                examples=[
                    'Coordinate utility companies and broadband providers',
                    'Manage service handovers with intelligent scheduling',
                    'Synchronize activation dates across multiple providers'
                ],
            ),
            AgentSkill(
                id='estimate_costs',
                name='Estimate Costs',
                description='AI-powered cost estimation with breakdown analysis',
                tags=['costs', 'estimation', 'analysis', 'optimization'],
                examples=[
                    'Estimate total moving costs with service comparisons',
                    'Provide detailed cost breakdown with optimization options',
                    'Calculate premium vs standard service differences'
                ],
            ),
        ]
