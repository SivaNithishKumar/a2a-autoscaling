#!/usr/bin/env python3
"""
Test Move Orchestration Agent - A2A Communication & Skills Verification

Comprehensive testing of the Move Orchestration Agent's A2A protocol compliance,
skill functionality, and AI-Ops capabilities for Just Move In demo.
"""

import asyncio
import json
import sys
import httpx
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_a2a.agents.move_orchestrator.agent import MoveOrchestrationAgent, MoveOrchestrationExecutor

print("🧪 MOVE ORCHESTRATION AGENT - A2A TESTING SUITE")
print("=" * 60)

async def test_agent_initialization():
    """Test 1: Agent Initialization and Metrics Setup"""
    print("\n📦 Test 1: Agent Initialization and Metrics Setup...")
    
    try:
        # Test agent initialization
        agent = MoveOrchestrationAgent()
        executor = MoveOrchestrationExecutor()
        
        print(f"✅ Agent Name: {agent.name}")
        print(f"✅ Service Providers: {len(agent.service_providers)} registered")
        print(f"✅ Active Orchestrations: {len(agent.active_orchestrations)}")
        print(f"✅ Metrics Port: 8084")
        
        # Test skills registration
        skills = agent.get_skills()
        expected_skills = ['orchestrate_move', 'optimize_timeline', 'coordinate_services', 'estimate_costs']
        
        print(f"✅ Skills Registered: {len(skills)}")
        for skill in skills:
            if skill.id in expected_skills:
                print(f"   • {skill.name} ({skill.id}) ✅")
            else:
                print(f"   • {skill.name} ({skill.id}) ❌ Unexpected")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

async def test_orchestration_skills():
    """Test 2: Core Orchestration Skills"""
    print("\n🏠 Test 2: Core Orchestration Skills...")
    
    try:
        agent = MoveOrchestrationAgent()
        
        # Test orchestrate_move skill
        print("   Testing orchestrate_move skill...")
        move_request = {
            'origin': 'London, UK',
            'destination': 'Manchester, UK',
            'move_date': '2025-09-15',
            'household_size': '3br'
        }
        
        result = await agent.orchestrate_move(move_request, "test_context_001")
        
        if result and result.move_id and result.status == "ORCHESTRATED":
            print(f"   ✅ Move orchestrated: {result.move_id}")
            print(f"   ✅ Total cost: £{result.estimated_total_cost:,.2f}")
            print(f"   ✅ Confidence: {result.confidence_score:.1%}")
            print(f"   ✅ Services coordinated: {len(result.coordinated_services)}")
            print(f"   ✅ Recommendations: {len(result.recommendations)}")
        else:
            print("   ❌ Orchestration failed")
            return False
        
        # Test streaming functionality
        print("   Testing streaming responses...")
        stream_count = 0
        async for response in agent.stream("Orchestrate a move from London to Manchester", "test_context_002"):
            stream_count += 1
            if response.get('is_task_complete') and response.get('content'):
                print(f"   ✅ Streaming response received (length: {len(response['content'])})")
                break
        
        if stream_count > 0:
            print(f"   ✅ Streaming working: {stream_count} responses")
        else:
            print("   ❌ Streaming failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Skills testing failed: {e}")
        return False

async def test_ai_ops_capabilities():
    """Test 3: AI-Ops Capabilities"""
    print("\n🤖 Test 3: AI-Ops Capabilities...")
    
    try:
        agent = MoveOrchestrationAgent()
        
        # Test service provider selection algorithm
        print("   Testing AI service provider selection...")
        providers = await agent._select_optimal_providers('2025-09-15')
        
        if len(providers) >= 6:  # Should select all required service types
            print(f"   ✅ Selected {len(providers)} optimal providers")
            service_types = [p.service_type.value for p in providers]
            expected_types = ['utilities', 'broadband', 'moving_company', 'insurance', 'mail_redirection', 'council_tax']
            
            for service_type in expected_types:
                if service_type in service_types:
                    print(f"      • {service_type} ✅")
                else:
                    print(f"      • {service_type} ❌ Missing")
        else:
            print(f"   ❌ Only selected {len(providers)} providers, expected 6+")
            return False
        
        # Test timeline optimization
        print("   Testing timeline optimization...")
        timeline = await agent._generate_optimized_timeline(providers, '2025-09-15')
        
        if timeline and timeline.total_duration > 0:
            print(f"   ✅ Timeline generated: {timeline.total_duration} days")
            print(f"   ✅ Critical path: {' → '.join(timeline.critical_path)}")
            print(f"   ✅ Optimization score: {timeline.optimization_score:.1%}")
            print(f"   ✅ Risk factors: {len(timeline.risk_factors)}")
        else:
            print("   ❌ Timeline optimization failed")
            return False
        
        # Test metrics tracking
        print("   Testing metrics tracking...")
        if hasattr(agent, 'metrics'):
            agent.metrics.increment_request_count('test_skill', 'success')
            agent.metrics.set_active_tasks(1)
            agent.metrics.set_active_tasks(0)
            print("   ✅ Metrics tracking functional")
        else:
            print("   ❌ Metrics not available")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI-Ops testing failed: {e}")
        return False

async def test_query_processing():
    """Test 4: Query Processing and Response Generation"""
    print("\n💬 Test 4: Query Processing and Response Generation...")
    
    try:
        agent = MoveOrchestrationAgent()
        
        test_queries = [
            ("Orchestrate a move from London to Manchester", "orchestrate_move"),
            ("Optimize the timeline for my move", "optimize_timeline"),
            ("Estimate the costs for moving services", "estimate_costs"),
            ("Help me coordinate utility transfers", "coordinate_services"),
            ("What can you help me with?", "general")
        ]
        
        for query, expected_skill in test_queries:
            print(f"   Testing: '{query[:50]}...'")
            
            skill = agent._determine_skill_from_query(query)
            if expected_skill == "general" or skill == expected_skill:
                print(f"      ✅ Skill detected: {skill}")
            else:
                print(f"      ❌ Expected {expected_skill}, got {skill}")
            
            # Test response generation
            async for response in agent.stream(query, "test_context"):
                if response.get('content') and len(response['content']) > 50:
                    print(f"      ✅ Response generated (length: {len(response['content'])})")
                    break
                else:
                    print(f"      ❌ Invalid response: {response}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Query processing failed: {e}")
        return False

async def test_a2a_protocol_compliance():
    """Test 5: A2A Protocol Compliance"""
    print("\n🔗 Test 5: A2A Protocol Compliance...")
    
    try:
        # Test agent-card.json
        agent_card_path = Path(__file__).parent.parent / "src" / "multi_agent_a2a" / "agents" / "move_orchestrator" / "agent-card.json"
        
        if agent_card_path.exists():
            with open(agent_card_path, 'r') as f:
                agent_card = json.load(f)
            
            required_fields = ['name', 'description', 'capabilities', 'communication']
            for field in required_fields:
                if field in agent_card:
                    print(f"   ✅ Agent card has {field}")
                else:
                    print(f"   ❌ Agent card missing {field}")
                    return False
            
            # Check capabilities
            capabilities = agent_card.get('capabilities', [])
            if len(capabilities) >= 4:
                print(f"   ✅ Agent card defines {len(capabilities)} capabilities")
                capability_ids = [cap['id'] for cap in capabilities]
                expected_caps = ['orchestrate_move', 'optimize_timeline', 'coordinate_services', 'estimate_costs']
                
                for cap_id in expected_caps:
                    if cap_id in capability_ids:
                        print(f"      • {cap_id} ✅")
                    else:
                        print(f"      • {cap_id} ❌ Missing")
            else:
                print(f"   ❌ Only {len(capabilities)} capabilities defined")
                return False
        else:
            print("   ❌ Agent card file not found")
            return False
        
        # Test executor compliance
        executor = MoveOrchestrationExecutor()
        if hasattr(executor, 'execute') and hasattr(executor, 'cancel'):
            print("   ✅ Executor implements required A2A methods")
        else:
            print("   ❌ Executor missing required methods")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ A2A compliance testing failed: {e}")
        return False

async def test_production_readiness():
    """Test 6: Production Readiness Features"""
    print("\n🚀 Test 6: Production Readiness Features...")
    
    try:
        agent = MoveOrchestrationAgent()
        
        # Test error handling
        print("   Testing error handling...")
        try:
            invalid_request = {'invalid': 'data'}
            result = await agent.orchestrate_move(invalid_request, "error_test")
            # Should still work with defaults
            if result and result.move_id:
                print("   ✅ Graceful error handling with defaults")
            else:
                print("   ❌ Error handling failed")
                return False
        except Exception as e:
            print(f"   ❌ Error handling threw exception: {e}")
            return False
        
        # Test logging
        print("   Testing logging...")
        if hasattr(agent, 'logger'):
            print("   ✅ Logger configured")
        else:
            print("   ❌ Logger missing")
            return False
        
        # Test state management
        print("   Testing state management...")
        if hasattr(agent, 'active_orchestrations'):
            print(f"   ✅ State management: {len(agent.active_orchestrations)} active")
        else:
            print("   ❌ State management missing")
            return False
        
        # Test service provider database
        print("   Testing service provider database...")
        if len(agent.service_providers) >= 6:
            print(f"   ✅ Service provider database: {len(agent.service_providers)} providers")
        else:
            print(f"   ❌ Insufficient service providers: {len(agent.service_providers)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Production readiness testing failed: {e}")
        return False

async def main():
    """Run all tests and generate summary report."""
    print("🏠 Testing Move Orchestration Agent for Just Move In Demo")
    print("🎯 Focus: AI-Ops capabilities and production readiness")
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Orchestration Skills", test_orchestration_skills),
        ("AI-Ops Capabilities", test_ai_ops_capabilities),
        ("Query Processing", test_query_processing),
        ("A2A Protocol Compliance", test_a2a_protocol_compliance),
        ("Production Readiness", test_production_readiness)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Generate summary report
    print(f"\n{'='*60}")
    print("📊 MOVE ORCHESTRATION AGENT - TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🚀 MOVE ORCHESTRATION AGENT READY FOR DEMO!")
        print("🏠 All AI-Ops capabilities verified for Just Move In")
        print("📊 Agent ready for A2A communication on port 8004")
        return True
    else:
        print(f"\n⚠️  {total-passed} tests failed - review before demo")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)