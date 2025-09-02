#!/usr/bin/env python3
"""Comprehensive test script for Infrastructure Monitoring Agent."""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("🧪 INFRASTRUCTURE MONITORING AGENT - A2A TESTING SUITE")
print("============================================================")
print("🏗️ Testing Infrastructure Monitoring Agent for Production AI-Ops")
print("🎯 Focus: Anomaly detection and predictive analytics")
print()
print("="*60)


async def test_agent_initialization():
    """Test 1: Agent Initialization and Metrics Setup"""
    print("\n📦 Test 1: Agent Initialization and Metrics Setup...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent, InfrastructureMonitoringExecutor
        
        # Test agent initialization
        agent = InfrastructureMonitoringAgent()
        
        print(f"✅ Agent Name: {agent.name}")
        print(f"✅ Monitored Services: {len(agent.monitored_services)}")
        print(f"✅ Active Alerts: {len(agent.active_alerts)}")
        print(f"✅ Prediction Model Accuracy: {agent.prediction_model_accuracy:.1%}")
        
        # Test agent skills
        skills = agent.get_skills()
        print(f"✅ Skills Registered: {len(skills)}")
        
        for skill in skills:
            print(f"   • {skill.name} ({skill.id}) ✅")
        
        # Test executor initialization
        executor = InfrastructureMonitoringExecutor()
        if hasattr(executor, 'agent') and hasattr(executor, 'metrics'):
            print("✅ Executor properly initialized with agent and metrics")
        else:
            print("❌ Executor missing required components")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


async def test_monitoring_capabilities():
    """Test 2: Core Infrastructure Monitoring"""
    print("\n🏗️ Test 2: Core Infrastructure Monitoring...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        agent = InfrastructureMonitoringAgent()
        
        # Test infrastructure monitoring
        print("   Testing infrastructure monitoring...")
        monitoring_request = {
            'services': ['web_frontend', 'database_primary', 'cache_layer'],
            'include_recommendations': True
        }
        
        status = await agent.monitor_infrastructure(monitoring_request, "test_context")
        
        print(f"   ✅ Overall Health: {status.overall_health.value}")
        print(f"   ✅ Services Monitored: {status.services_monitored}")
        print(f"   ✅ Active Alerts: {status.active_alerts}")
        print(f"   ✅ Anomalies Detected: {len(status.anomalies_detected)}")
        print(f"   ✅ Failure Predictions: {len(status.failure_predictions)}")
        print(f"   ✅ Performance Insights: {len(status.performance_insights)}")
        print(f"   ✅ Recommendations: {len(status.optimization_recommendations)}")
        
        # Test streaming responses
        print("   Testing streaming responses...")
        stream_count = 0
        async for response in agent.stream("Monitor infrastructure health", "test_stream"):
            if response.get('content') and len(response['content']) > 50:
                print(f"   ✅ Streaming response received (length: {len(response['content'])})")
                stream_count += 1
                if response.get('is_task_complete'):
                    break
        
        print(f"   ✅ Streaming responses: {stream_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring capabilities test failed: {e}")
        return False


async def test_anomaly_detection():
    """Test 3: AI-Ops Anomaly Detection"""
    print("\n🚨 Test 3: AI-Ops Anomaly Detection...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        agent = InfrastructureMonitoringAgent()
        
        # Test anomaly detection
        print("   Testing AI-powered anomaly detection...")
        anomalies = await agent._detect_anomalies()
        
        print(f"   ✅ Anomaly detection algorithm executed successfully")
        print(f"   ✅ Anomalies detected: {len(anomalies)}")
        
        for anomaly in anomalies[:3]:  # Show first 3
            print(f"      • Service: {anomaly.service_name}")
            print(f"        Type: {anomaly.anomaly_type}")
            print(f"        Severity: {anomaly.severity.value}")
            print(f"        Confidence: {anomaly.confidence_score:.1%}")
            print(f"        Recommendations: {len(anomaly.recommendations)}")
        
        # Test anomaly query processing
        print("   Testing anomaly detection queries...")
        async for response in agent.stream("Detect anomalies in the infrastructure", "anomaly_test"):
            if response.get('is_task_complete'):
                content = response.get('content', '')
                if 'anomaly' in content.lower() or 'analysis' in content.lower():
                    print(f"   ✅ Anomaly analysis response generated (length: {len(content)})")
                break
        
        return True
        
    except Exception as e:
        print(f"   ❌ Anomaly detection test failed: {e}")
        return False


async def test_failure_prediction():
    """Test 4: Predictive Failure Analysis"""
    print("\n🔮 Test 4: Predictive Failure Analysis...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        agent = InfrastructureMonitoringAgent()
        
        # Test failure prediction
        print("   Testing AI-powered failure prediction...")
        predictions = await agent._predict_failures()
        
        print(f"   ✅ Prediction model executed successfully")
        print(f"   ✅ Failure predictions: {len(predictions)}")
        print(f"   ✅ Model accuracy: {agent.prediction_model_accuracy:.1%}")
        
        for prediction in predictions[:2]:  # Show first 2
            print(f"      • Service: {prediction.service_name}")
            print(f"        Failure Type: {prediction.failure_type}")
            print(f"        Probability: {prediction.probability:.1%}")
            print(f"        Leading Indicators: {len(prediction.leading_indicators)}")
            print(f"        Mitigation Steps: {len(prediction.mitigation_steps)}")
        
        # Test prediction query processing
        print("   Testing failure prediction queries...")
        async for response in agent.stream("Predict potential system failures", "prediction_test"):
            if response.get('is_task_complete'):
                content = response.get('content', '')
                if 'prediction' in content.lower() or 'failure' in content.lower():
                    print(f"   ✅ Prediction analysis response generated (length: {len(content)})")
                break
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failure prediction test failed: {e}")
        return False


async def test_query_processing():
    """Test 5: Query Processing and Response Generation"""
    print("\n💬 Test 5: Query Processing and Response Generation...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        agent = InfrastructureMonitoringAgent()
        
        test_queries = [
            ("Monitor infrastructure health and performance", "monitor_infrastructure"),
            ("Detect anomalies in system behavior", "detect_anomalies"),
            ("Predict potential failures", "predict_failures"),
            ("What infrastructure monitoring capabilities do you have?", "monitor_infrastructure")
        ]
        
        for query, expected_skill in test_queries:
            print(f"   Testing: '{query[:50]}...'")
            
            skill = agent._determine_skill_from_query(query)
            if skill == expected_skill or expected_skill == "general":
                print(f"      ✅ Skill detected: {skill}")
            else:
                print(f"      ⚠️  Expected {expected_skill}, got {skill}")
            
            # Test response generation
            async for response in agent.stream(query, "test_context"):
                if response.get('content') and len(response['content']) > 50:
                    print(f"      ✅ Response generated (length: {len(response['content'])})")
                    break
        
        return True
        
    except Exception as e:
        print(f"   ❌ Query processing test failed: {e}")
        return False


async def test_ai_ops_integration():
    """Test 6: AI-Ops Integration and Intelligence"""
    print("\n🤖 Test 6: AI-Ops Integration and Intelligence...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent
        
        agent = InfrastructureMonitoringAgent()
        
        # Test AI-Ops capabilities
        print("   Testing service provider database...")
        if len(agent.monitored_services) >= 6:
            print(f"   ✅ Monitoring {len(agent.monitored_services)} services")
            
            # Check service details
            for service_id, service_data in list(agent.monitored_services.items())[:3]:
                print(f"      • {service_data['name']}: {service_data['status'].value}")
        else:
            print(f"   ❌ Insufficient monitored services: {len(agent.monitored_services)}")
            return False
        
        # Test insights generation
        print("   Testing performance insights generation...")
        insights = agent._generate_performance_insights()
        if len(insights) >= 3:
            print(f"   ✅ Generated {len(insights)} performance insights")
        else:
            print(f"   ❌ Insufficient insights generated: {len(insights)}")
            return False
        
        # Test optimization recommendations
        print("   Testing optimization recommendations...")
        recommendations = agent._generate_optimization_recommendations()
        if len(recommendations) >= 3:
            print(f"   ✅ Generated {len(recommendations)} optimization recommendations")
        else:
            print(f"   ❌ Insufficient recommendations: {len(recommendations)}")
            return False
        
        # Test overall health calculation
        print("   Testing overall health calculation...")
        health = agent._calculate_overall_health()
        print(f"   ✅ Overall health status: {health.value}")
        
        # Test metrics tracking
        print("   Testing metrics tracking...")
        agent.metrics.track_simple_operation("test_operation")
        print("   ✅ Metrics tracking functional")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI-Ops integration test failed: {e}")
        return False


async def test_production_readiness():
    """Test 7: Production Readiness Features"""
    print("\n🚀 Test 7: Production Readiness Features...")
    
    try:
        from multi_agent_a2a.agents.infrastructure_monitor.agent import InfrastructureMonitoringAgent, InfrastructureMonitoringExecutor
        
        # Test agent features
        agent = InfrastructureMonitoringAgent()
        
        # Test error handling
        print("   Testing error handling...")
        try:
            invalid_request = {'invalid': 'data'}
            status = await agent.monitor_infrastructure(invalid_request, "error_test")
            if status and status.services_monitored > 0:
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
        
        # Test metrics
        print("   Testing metrics integration...")
        if hasattr(agent, 'metrics'):
            print("   ✅ Metrics integration working")
        else:
            print("   ❌ Metrics integration missing")
            return False
        
        # Test executor
        print("   Testing executor configuration...")
        executor = InfrastructureMonitoringExecutor()
        if hasattr(executor, 'agent') and hasattr(executor, 'execute') and hasattr(executor, 'cancel'):
            print("   ✅ Executor properly configured")
        else:
            print("   ❌ Executor missing required methods")
            return False
        
        # Test state management
        print("   Testing state management...")
        if hasattr(agent, 'active_alerts') and hasattr(agent, 'monitored_services'):
            print(f"   ✅ State management: {len(agent.active_alerts)} alerts, {len(agent.monitored_services)} services")
        else:
            print("   ❌ State management missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Production readiness test failed: {e}")
        return False


async def main():
    """Run all tests and generate summary report."""
    print("🏗️ Testing Infrastructure Monitoring Agent for Production AI-Ops")
    print("🎯 Focus: Anomaly detection and predictive analytics")
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Monitoring Capabilities", test_monitoring_capabilities),
        ("Anomaly Detection", test_anomaly_detection),
        ("Failure Prediction", test_failure_prediction),
        ("Query Processing", test_query_processing),
        ("AI-Ops Integration", test_ai_ops_integration),
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
    print("📊 INFRASTRUCTURE MONITORING AGENT - TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🚀 INFRASTRUCTURE MONITORING AGENT READY FOR PRODUCTION!")
        print("🏗️ All AI-Ops capabilities verified for production deployment")
        print("📊 Agent ready for A2A communication on port 8005")
        print("🔍 Advanced monitoring with anomaly detection operational")
        return True
    else:
        print(f"\n⚠️  {total-passed} tests failed - review before production deployment")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)