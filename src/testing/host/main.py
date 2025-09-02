"""
A2A Testing Host Main Application

Entry point for the A2A testing framework.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional

import click

from .agent_discovery import AgentDiscovery
from ..utils.a2a_client import EnhancedA2AClient
from ..utils.test_helpers import TestSuite, TestCase, TestResult, TestStatus
from ..config import DEFAULT_AGENTS, LOGGING_CONFIG


# Configure logging
logging.basicConfig(**{
    "level": logging.INFO,
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
})
logger = logging.getLogger(__name__)


class A2ATestingHost:
    """Main A2A testing host application."""
    
    def __init__(self):
        self.discovery = None
        self.client = None
        self.discovered_agents = {}
        
    async def run_discovery_mode(self):
        """Run agent discovery mode."""
        print("\n🔍 A2A Agent Discovery Mode")
        print("=" * 50)
        
        async with AgentDiscovery() as discovery:
            self.discovery = discovery
            
            # Discover agents
            agents = await discovery.discover_agents()
            
            if not agents:
                print("❌ No agents discovered.")
                return
                
            print(f"\n✅ Discovered {len(agents)} agents:")
            print("-" * 30)
            
            for i, agent in enumerate(agents, 1):
                status_emoji = "✅" if agent["status"] == "available" else "❌"
                print(f"{i}. {status_emoji} {agent['name']}")
                print(f"   Endpoint: {agent['endpoint']}")
                print(f"   Status: {agent['status']}")
                
                if agent["status"] == "available":
                    skills = agent.get("skills", [])
                    if skills:
                        print(f"   Skills: {', '.join([skill['name'] for skill in skills])}")
                    
                    capabilities = agent.get("capabilities", {})
                    if capabilities.get("streaming"):
                        print("   🌊 Streaming supported")
                        
                else:
                    error = agent.get("error", "Unknown error")
                    print(f"   Error: {error}")
                    
                print()
                
            # Test connectivity for available agents
            print("\n🔧 Testing Connectivity...")
            print("-" * 30)
            
            for agent in agents:
                if agent["status"] == "available":
                    result = await discovery.test_agent_connectivity(agent["name"])
                    status_emoji = "✅" if result.status == TestStatus.PASSED else "❌"
                    print(f"{status_emoji} {agent['name']}: {result.message}")
                    
                    if result.details:
                        response_time = result.details.get("response_time", 0)
                        print(f"   Response time: {response_time:.3f}s")
                        
    async def run_interactive_mode(self):
        """Run interactive mode for manual testing."""
        print("\n💬 A2A Interactive Mode")
        print("=" * 50)
        print("Type 'help' for commands, 'quit' to exit\n")
        
        # First discover agents
        async with AgentDiscovery() as discovery:
            agents = await discovery.discover_agents()
            available_agents = [a for a in agents if a["status"] == "available"]
            
            if not available_agents:
                print("❌ No available agents found. Please start some agents first.")
                return
                
            print(f"Available agents: {', '.join([a['name'] for a in available_agents])}")
            print()
            
            # Interactive loop
            async with EnhancedA2AClient() as client:
                # Register agents
                for agent in available_agents:
                    agent_card = discovery.get_agent_card(agent["name"])
                    if agent_card:
                        client.register_agent(agent_card)
                        
                while True:
                    try:
                        user_input = input(">>> ").strip()
                        
                        if user_input.lower() in ['quit', 'exit', 'q']:
                            break
                            
                        elif user_input.lower() == 'help':
                            self._print_help()
                            continue
                            
                        elif user_input.lower() == 'agents':
                            print("Available agents:")
                            for agent in available_agents:
                                print(f"  - {agent['name']}: {agent['endpoint']}")
                            continue
                            
                        elif user_input.startswith('@'):
                            # Direct agent communication: @agent_name message
                            parts = user_input[1:].split(' ', 1)
                            if len(parts) < 2:
                                print("Usage: @agent_name your message")
                                continue
                                
                            agent_name, message = parts
                            await self._send_to_agent(client, agent_name, message)
                            
                        elif user_input:
                            # Broadcast to all agents
                            await self._broadcast_message(client, available_agents, user_input)
                            
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                        
        print("\nGoodbye! 👋")
        
    async def run_test_suite_mode(self):
        """Run comprehensive test suite."""
        print("\n🧪 A2A Test Suite Mode")
        print("=" * 50)
        
        # Create test suite
        suite = TestSuite(
            name="A2A System Test Suite",
            description="Comprehensive testing of A2A agents and protocol"
        )
        
        async with AgentDiscovery() as discovery:
            agents = await discovery.discover_agents()
            available_agents = [a for a in agents if a["status"] == "available"]
            
            if not available_agents:
                print("❌ No available agents found for testing.")
                return
                
            # Test agent discovery and connectivity
            suite.start_time = datetime.now()
            
            print("\n1️⃣ Testing Agent Discovery...")
            for agent in agents:
                result = await discovery.test_agent_connectivity(agent["name"])
                suite.add_result(result)
                status_emoji = "✅" if result.status == TestStatus.PASSED else "❌"
                print(f"   {status_emoji} {agent['name']}: {result.message}")
                
            # Test agent functionality
            print("\n2️⃣ Testing Agent Functionality...")
            
            async with EnhancedA2AClient() as client:
                for agent in available_agents:
                    agent_card = discovery.get_agent_card(agent["name"])
                    if agent_card:
                        connection = client.register_agent(agent_card)
                        
                        # Test basic communication
                        test_result = await self._test_agent_basic_communication(
                            connection, agent["name"]
                        )
                        suite.add_result(test_result)
                        
                        status_emoji = "✅" if test_result.status == TestStatus.PASSED else "❌"
                        print(f"   {status_emoji} {agent['name']}: {test_result.message}")
                        
            suite.end_time = datetime.now()
            
            # Print summary
            print("\n📊 Test Results Summary:")
            print("-" * 30)
            summary = suite.summary
            total_tests = sum(summary.values())
            
            for status, count in summary.items():
                if count > 0:
                    percentage = (count / total_tests) * 100
                    print(f"   {status.upper()}: {count} ({percentage:.1f}%)")
                    
            print(f"\nTotal Duration: {suite.duration:.2f}s")
            
            # Save results
            from ..config import OUTPUT_DIR
            results_file = OUTPUT_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            suite.save_to_file(str(results_file))
            print(f"\nResults saved to: {results_file}")
            
    async def run_orchestration_mode(self):
        """Run multi-agent orchestration testing."""
        print("\n🎭 A2A Orchestration Mode")
        print("=" * 50)
        
        async with AgentDiscovery() as discovery:
            agents = await discovery.discover_agents()
            available_agents = [a for a in agents if a["status"] == "available"]
            
            if len(available_agents) < 2:
                print("❌ Need at least 2 agents for orchestration testing.")
                return
                
            print(f"\nTesting orchestration with {len(available_agents)} agents...")
            
            # Example orchestration scenarios
            scenarios = [
                {
                    "name": "Multi-Agent Query",
                    "message": "What is 25 + 17 and what's the weather like?",
                    "description": "Testing parallel agent execution"
                },
                {
                    "name": "Sequential Processing",
                    "message": "Calculate the square root of 144, then search for information about that number",
                    "description": "Testing sequential agent coordination"
                }
            ]
            
            async with EnhancedA2AClient() as client:
                # Register all agents
                for agent in available_agents:
                    agent_card = discovery.get_agent_card(agent["name"])
                    if agent_card:
                        client.register_agent(agent_card)
                        
                for i, scenario in enumerate(scenarios, 1):
                    print(f"\n{i}️⃣ {scenario['name']}")
                    print(f"   {scenario['description']}")
                    print(f"   Message: '{scenario['message']}'\n")
                    
                    # Send to relevant agents based on message content
                    relevant_agents = self._identify_relevant_agents(
                        available_agents, scenario["message"]
                    )
                    
                    if relevant_agents:
                        await self._orchestrate_agents(client, relevant_agents, scenario["message"])
                    else:
                        print("   ⚠️ No relevant agents identified for this scenario")
                        
    def _identify_relevant_agents(self, agents: List[Dict], message: str) -> List[str]:
        """Simple heuristic to identify relevant agents for a message."""
        relevant = []
        message_lower = message.lower()
        
        for agent in agents:
            agent_name = agent["name"].lower()
            
            # Simple keyword matching
            if "calculator" in agent_name and any(word in message_lower for word in ["calculate", "math", "+", "-", "*", "/", "square", "root"]):
                relevant.append(agent["name"])
            elif "weather" in agent_name and "weather" in message_lower:
                relevant.append(agent["name"])
            elif "research" in agent_name and any(word in message_lower for word in ["search", "research", "information", "find"]):
                relevant.append(agent["name"])
            elif "base" in agent_name:  # Base agent can handle general queries
                relevant.append(agent["name"])
                
        return relevant
        
    async def _orchestrate_agents(self, client: EnhancedA2AClient, agent_names: List[str], message: str):
        """Orchestrate multiple agents for a complex task."""
        tasks = []
        
        for agent_name in agent_names:
            connection = client.agent_connections.get(agent_name)
            if connection:
                task = asyncio.create_task(
                    self._send_to_agent_with_timeout(connection, message),
                    name=f"agent_{agent_name}"
                )
                tasks.append((agent_name, task))
                
        # Wait for all agents to respond
        for agent_name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=30.0)
                if result:
                    print(f"   📤 {agent_name}: Success")
                else:
                    print(f"   ⚠️ {agent_name}: No response")
            except asyncio.TimeoutError:
                print(f"   ⏰ {agent_name}: Timeout")
            except Exception as e:
                print(f"   ❌ {agent_name}: Error - {e}")
                
    async def _send_to_agent_with_timeout(self, connection, message: str):
        """Send message to agent with timeout handling."""
        try:
            return await connection.send_message(message)
        except Exception as e:
            logger.error(f"Error sending to agent: {e}")
            return None
            
    async def _send_to_agent(self, client: EnhancedA2AClient, agent_name: str, message: str):
        """Send a message to a specific agent."""
        connection = client.agent_connections.get(agent_name)
        if not connection:
            print(f"❌ Agent '{agent_name}' not found.")
            return
            
        try:
            print(f"📤 Sending to {agent_name}...")
            result = await connection.send_message(message)
            
            if result:
                print(f"📥 {agent_name} responded:")
                self._print_response(result)
            else:
                print(f"⚠️ No response from {agent_name}")
                
        except Exception as e:
            print(f"❌ Error communicating with {agent_name}: {e}")
            
    async def _broadcast_message(self, client: EnhancedA2AClient, agents: List[Dict], message: str):
        """Broadcast a message to all available agents."""
        print(f"📡 Broadcasting to {len(agents)} agents...")
        
        tasks = []
        for agent in agents:
            connection = client.agent_connections.get(agent["name"])
            if connection:
                task = asyncio.create_task(
                    self._send_to_agent_with_timeout(connection, message),
                    name=f"broadcast_{agent['name']}"
                )
                tasks.append((agent["name"], task))
                
        # Wait for all responses
        for agent_name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=10.0)
                if result:
                    print(f"\n📥 {agent_name}:")
                    self._print_response(result)
                else:
                    print(f"\n⚠️ {agent_name}: No response")
            except asyncio.TimeoutError:
                print(f"\n⏰ {agent_name}: Timeout")
            except Exception as e:
                print(f"\n❌ {agent_name}: {e}")
                
    def _print_response(self, response):
        """Print agent response in a formatted way."""
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'text'):
                    print(f"   {part.text}")
        else:
            print(f"   {response}")
            
    async def _test_agent_basic_communication(self, connection, agent_name: str) -> TestResult:
        """Test basic communication with an agent."""
        start_time = datetime.now()
        
        try:
            # Send a simple test message
            test_message = "Hello! Can you respond to this test message?"
            result = await asyncio.wait_for(
                connection.send_message(test_message), 
                timeout=10.0
            )
            
            end_time = datetime.now()
            
            if result:
                return TestResult(
                    test_name=f"basic_communication_{agent_name}",
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=end_time,
                    message=f"Successfully communicated with {agent_name}",
                    details={"response_received": True}
                )
            else:
                return TestResult(
                    test_name=f"basic_communication_{agent_name}",
                    status=TestStatus.FAILED,
                    start_time=start_time,
                    end_time=end_time,
                    message=f"No response from {agent_name}"
                )
                
        except asyncio.TimeoutError:
            return TestResult(
                test_name=f"basic_communication_{agent_name}",
                status=TestStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Timeout communicating with {agent_name}",
                error=TimeoutError("Communication timeout")
            )
        except Exception as e:
            return TestResult(
                test_name=f"basic_communication_{agent_name}",
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=datetime.now(),
                message=f"Error communicating with {agent_name}: {str(e)}",
                error=e
            )
            
    def _print_help(self):
        """Print help information for interactive mode."""
        print("\nAvailable commands:")
        print("  help          - Show this help message")
        print("  agents        - List available agents")
        print("  @agent_name   - Send message to specific agent")
        print("  quit/exit/q   - Exit interactive mode")
        print("  <message>     - Broadcast message to all agents\n")


@click.command()
@click.option('--mode', default='interactive', help='Testing mode: interactive, test-suite, orchestration, discovery')
def main(mode):
    """A2A Testing Host - Main entry point."""
    host = A2ATestingHost()
    
    try:
        if mode == 'discovery':
            asyncio.run(host.run_discovery_mode())
        elif mode == 'interactive':
            asyncio.run(host.run_interactive_mode())
        elif mode == 'test-suite':
            asyncio.run(host.run_test_suite_mode())
        elif mode == 'orchestration':
            asyncio.run(host.run_orchestration_mode())
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Available modes: discovery, interactive, test-suite, orchestration")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Host error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
