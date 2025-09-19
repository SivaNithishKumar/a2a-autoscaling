# System Architecture Deep Dive Q&A

*Comprehensive Analysis of the A2A Multi-Agent Autoscaling Platform*

## Overview

This document provides detailed answers to critical questions about the A2A Multi-Agent system architecture, request lifecycle, scaling mechanisms, infrastructure choices, and networking implementation.

---

## 1. Request Lifecycle from Streamlit Client

### **Complete Request Journey: From Client to Agent Response**

When a request comes from the Streamlit app, it follows this comprehensive lifecycle:

#### **Phase 1: Client Request Initiation**
```python
# 1. User inputs query in Streamlit web interface
user_query = "What's the weather in New York?"

# 2. Streamlit app performs intelligent agent routing using LLM
async def route_request_intelligently(query: str):
    """Use LLM to determine which agent should handle the request"""
    
    # Azure OpenAI GPT-4 analyzes the query
    routing_prompt = f"""
    Analyze this user query and determine the best agent:
    Query: "{query}"
    
    Available agents:
    - base: General conversation, greetings, coordination
    - calculator: Math, calculations, equations, numbers  
    - weather: Weather information, forecasts, climate
    - research: Research, information gathering, analysis
    - move_orchestrator: Moving, relocation, logistics
    - infrastructure_monitor: System monitoring, health checks
    """
    
    # LLM returns "weather" for weather-related queries
    selected_agent = await openai_client.complete(routing_prompt)
    return selected_agent
```

#### **Phase 2: Service Discovery & Load Balancing**
```python
# 3. Streamlit resolves agent endpoint
def get_agent_endpoints():
    # In Kubernetes environment
    if in_k8s:
        # Uses Kubernetes internal DNS
        base_url = "http://weather-agent-service.multi-agent-a2a.svc.cluster.local:8082"
    else:
        # Local development with port-forwarding
        base_url = "http://localhost:8002"  # Port-forwarded from K8s service
    
    return base_url
```

#### **Phase 3: Kubernetes Network Routing**
```yaml
# 4. Request hits Kubernetes Service (Load Balancer)
apiVersion: v1
kind: Service
metadata:
  name: weather-agent-service
  namespace: multi-agent-a2a
spec:
  selector:
    app: weather-agent  # Routes to any pod with this label
  ports:
  - port: 8082
    targetPort: 8080
  type: ClusterIP  # Internal cluster communication
```

#### **Phase 4: Pod Selection & Processing**
```python
# 5. Kubernetes selects healthy pod from available replicas
# Based on current load balancing algorithm (round-robin by default)

# 6. Request reaches weather-agent pod
@app.route('/api/v1/weather')
async def handle_weather_request(request):
    # Metrics collection starts
    async with metrics.track_request_duration("weather_forecast"):
        # Process A2A protocol request
        a2a_message = parse_a2a_request(request)
        
        # Call external weather API
        weather_data = await fetch_weather_data(location)
        
        # Format A2A response
        response = create_a2a_response(weather_data)
        
        # Update metrics
        metrics.increment_request_count("weather_forecast", "success")
        
        return response
```

#### **Phase 5: Monitoring & Observability Integration**

**Prometheus Metrics Collection:**
```python
# 7. During request processing, multiple metrics are recorded
from prometheus_client import Counter, Histogram, Gauge

# Request counting
REQUEST_COUNT.labels(
    agent_name="weather-agent",
    skill="weather_forecast", 
    status="success"
).inc()

# Response time tracking  
REQUEST_DURATION.labels(
    agent_name="weather-agent",
    skill="weather_forecast"
).observe(response_time_seconds)

# Active connection tracking
ACTIVE_TASKS.labels(agent_name="weather-agent").set(current_active_requests)
```

**Grafana Dashboard Updates:**
```promql
# 8. Grafana queries Prometheus for real-time metrics
# Request rate query
rate(a2a_requests_total{agent_name="weather-agent"}[5m])

# Response time percentiles
histogram_quantile(0.95, rate(a2a_request_duration_seconds_bucket{agent_name="weather-agent"}[5m]))

# Error rate calculation
rate(a2a_requests_total{agent_name="weather-agent",status="error"}[5m]) / 
rate(a2a_requests_total{agent_name="weather-agent"}[5m])
```

#### **Phase 6: Autoscaling Decision Making**
```yaml
# 9. HPA controller evaluates scaling metrics every 30 seconds
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: weather-agent-hpa
spec:
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods  
    pods:
      metric:
        name: a2a_requests_per_second  # Custom metric from Prometheus
      target:
        type: AverageValue
        averageValue: "30"  # Target 30 req/sec per pod
```

#### **Phase 7: Response Path**
```python
# 10. Response travels back through the same network path
weather_response = {
    "id": "msg-123",
    "type": "response", 
    "content": {
        "location": "New York",
        "temperature": "22°C",
        "condition": "Sunny",
        "forecast": "Clear skies expected"
    }
}

# 11. Streamlit receives response and updates UI
# 12. Metrics recorded for complete request cycle
```

---

## 2. Autoscaling Metrics and Mechanisms

### **Custom Metrics That Drive Scaling Decisions**

#### **Primary Scaling Metrics:**

**1. A2A Requests Per Second (Custom Metric):**
```python
# Prometheus metric definition
a2a_requests_per_second = Counter(
    'a2a_requests_total',
    'Total A2A requests processed', 
    ['agent_name', 'skill', 'status']
)

# Calculated as rate in PromQL
rate(a2a_requests_total{agent_name="weather-agent"}[2m])
```

**2. CPU Utilization (Resource Metric):**
```yaml
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70  # Scale up when CPU > 70%
```

**3. Memory Utilization (Resource Metric):**
```yaml
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 80  # Scale up when Memory > 80%
```

#### **How Scaling Decisions Are Made:**

**Scale-Up Conditions:**
```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 60  # Wait 60s before scaling up
    policies:
    - type: Percent
      value: 100        # Can double replicas
      periodSeconds: 60
    - type: Pods  
      value: 2          # Or add max 2 pods
      periodSeconds: 60
    selectPolicy: Max   # Choose more aggressive policy
```

**Scale-Down Conditions:**
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # Wait 5 minutes before scaling down
    policies:
    - type: Percent
      value: 25         # Remove max 25% of pods
      periodSeconds: 60
```

#### **Scaling Algorithm Logic:**

**1. Metric Collection (Every 30 seconds):**
```python
# HPA controller evaluates metrics
current_replicas = 3
target_cpu = 70%
current_cpu = 85%
target_rps = 30
current_rps = 45

# Calculate desired replicas for each metric
cpu_desired = current_replicas * (current_cpu / target_cpu)  # 3 * (85/70) = 3.6
rps_desired = current_replicas * (current_rps / target_rps)  # 3 * (45/30) = 4.5

# Take the maximum
desired_replicas = max(cpu_desired, rps_desired) = 4.5 → 5 pods
```

**2. Scaling Decision Process:**
```python
class HPAController:
    async def evaluate_scaling(self, agent_name: str):
        """HPA controller scaling logic"""
        
        # Get current metrics
        metrics = await self.get_current_metrics(agent_name)
        
        # Calculate desired replicas for each metric
        desired_replicas = []
        
        for metric in hpa_spec.metrics:
            if metric.type == "Resource":
                desired = self.calculate_resource_based_replicas(metric, metrics)
            elif metric.type == "Pods":
                desired = self.calculate_pods_based_replicas(metric, metrics)
            
            desired_replicas.append(desired)
        
        # Take maximum (most conservative scaling)
        target_replicas = max(desired_replicas)
        
        # Apply scaling policies and stabilization
        final_replicas = self.apply_scaling_policies(
            current_replicas=metrics.current_replicas,
            target_replicas=target_replicas,
            scaling_direction="up" if target_replicas > metrics.current_replicas else "down"
        )
        
        # Execute scaling if needed
        if final_replicas != metrics.current_replicas:
            await self.scale_deployment(agent_name, final_replicas)
```

**3. Custom Metrics Pipeline:**
```yaml
# ServiceMonitor scrapes metrics from agent pods
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: weather-agent-servicemonitor
spec:
  endpoints:
  - port: http
    interval: 30s      # Scrape every 30 seconds
    path: /metrics     # Prometheus format metrics
```

---

## 3. Infrastructure Technology Choices

### **Kubernetes Distribution: Local Development vs Production**

#### **Current Setup: Local Kubernetes Development**

**What We're Using:**
- **Local Kubernetes Cluster** (likely Docker Desktop, Minikube, or K3s)
- **Port-forwarding for external access**
- **Local container registry or image loading**

**Evidence from codebase:**
```bash
# setup_port_forwards.sh shows local development pattern
kubectl port-forward -n multi-agent-a2a svc/weather-agent-service 8002:8082
kubectl port-forward -n multi-agent-a2a svc/streamlit-a2a-service 8501:8501
```

```yaml
# base-agent.yaml shows local image pattern
spec:
  containers:
  - name: base-agent
    image: a2a-base-agent:latest
    imagePullPolicy: Never  # Never pull = use local images
```

#### **Why These Technology Choices:**

**1. Kubernetes Over Docker Compose:**
```yaml
# Kubernetes provides:
# - Native horizontal pod autoscaling (HPA)
# - Service discovery and load balancing  
# - Rolling updates and health checks
# - Resource quotas and limits
# - Network policies for security
# - Integration with monitoring (Prometheus Operator)

# Docker Compose limitations:
# - No built-in autoscaling
# - Basic load balancing
# - Limited monitoring integration
# - No advanced networking policies
```

**2. Local Development Cluster Options:**

**Minikube** (Most likely choice):
```bash
# Pros:
# - Full Kubernetes API compatibility
# - Supports LoadBalancer services with minikube tunnel
# - Built-in addons (metrics-server, ingress)
# - Multi-node simulation

minikube start --memory=8192 --cpus=4
minikube addons enable metrics-server
minikube addons enable ingress
```

**Docker Desktop Kubernetes:**
```bash
# Pros: 
# - Integrated with Docker Desktop
# - Automatic resource management
# - Easy setup for development

# Cons:
# - Limited to single node
# - Resource intensive
```

**K3s** (Lightweight option):
```bash
# Pros:
# - Minimal resource usage
# - Fast startup
# - Production-compatible

# Installation
curl -sfL https://get.k3s.io | sh -
```

#### **Production Alternatives:**

**1. Managed Kubernetes Services:**
```yaml
# AWS EKS
cluster_name: "ai-agents-prod"
node_groups:
  - name: "ai-workers"
    instance_types: ["m5.xlarge", "m5.2xlarge"]
    min_size: 3
    max_size: 20
    scaling_config:
      desired_size: 5

# Google GKE  
cluster:
  name: "ai-agents-prod"
  location: "us-central1-a"
  node_pools:
    - name: "ai-pool"
      initial_node_count: 3
      autoscaling:
        min_node_count: 2
        max_node_count: 15

# Azure AKS
cluster_name: "ai-agents-prod"
default_node_pool:
  vm_size: "Standard_D4s_v3"
  node_count: 3
  enable_auto_scaling: true
  min_count: 2
  max_count: 20
```

**2. Self-Managed Kubernetes:**
```bash
# Using kubeadm for on-premises deployment
kubeadm init --pod-network-cidr=10.244.0.0/16
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# Multi-master setup for high availability
kubeadm init --control-plane-endpoint="loadbalancer.example.com:6443"
```

---

## 4. Alternative Deployment Architectures

### **Beyond VM + Kubernetes: Modern Deployment Options**

#### **1. Serverless AI Agents**

**AWS Lambda + API Gateway:**
```python
# Lambda function for each agent
import json
import boto3

def lambda_handler(event, context):
    """Weather agent as serverless function"""
    
    # Parse A2A request
    request_body = json.loads(event['body'])
    
    # Process weather request
    weather_data = get_weather_data(request_body['location'])
    
    # Return A2A response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': weather_data,
            'agent': 'weather-lambda'
        })
    }

# Deployment with Serverless Framework
# serverless.yml
service: ai-agents-serverless

provider:
  name: aws
  runtime: python3.9
  
functions:
  weatherAgent:
    handler: weather_agent.lambda_handler
    events:
      - http:
          path: /weather
          method: post
    reservedConcurrency: 50  # Max concurrent executions
    timeout: 30
```

**Azure Functions + Service Bus:**
```python
# Function app for agent processing
import azure.functions as func
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Calculator agent as Azure Function"""
    
    # Auto-scales based on request volume
    # Pay-per-execution pricing
    # Built-in monitoring and logging
    
    calculation_request = req.get_json()
    result = perform_calculation(calculation_request)
    
    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json"
    )
```

**Google Cloud Functions + Pub/Sub:**
```python
# Event-driven agent processing
from google.cloud import functions_v1

def process_agent_request(cloud_event):
    """Research agent triggered by Pub/Sub message"""
    
    # Automatic scaling to zero when idle
    # Event-driven architecture
    # Integrated with Google AI services
    
    research_query = cloud_event.data
    results = conduct_research(research_query)
    
    # Publish results to response topic
    publish_response(results)
```

#### **2. Container-as-a-Service (CaaS)**

**AWS Fargate:**
```yaml
# ECS Task Definition
family: ai-agents-fargate
networkMode: awsvpc
requiresCompatibilities:
  - FARGATE
cpu: '512'    # 0.5 vCPU
memory: '1024' # 1 GB

containerDefinitions:
  - name: weather-agent
    image: your-registry/weather-agent:latest
    portMappings:
      - containerPort: 8080
        protocol: tcp
    logConfiguration:
      logDriver: awslogs
      options:
        awslogs-group: /ai-agents/weather
        awslogs-region: us-east-1

# Auto-scaling target
serviceDefinition:
  serviceName: weather-agent-service
  taskDefinition: ai-agents-fargate
  desiredCount: 2
  launchType: FARGATE
  networkConfiguration:
    awsvpcConfiguration:
      subnets:
        - subnet-12345
        - subnet-67890
      securityGroups:
        - sg-ai-agents
```

**Azure Container Instances:**
```yaml
# Container group for related agents
apiVersion: '2021-09-01'
location: eastus
name: ai-agents-group
type: Microsoft.ContainerInstance/containerGroups

properties:
  containers:
    - name: base-agent
      properties:
        image: your-registry/base-agent:latest
        ports:
          - port: 8080
        resources:
          requests:
            cpu: 0.5
            memoryInGb: 1
    
    - name: calculator-agent  
      properties:
        image: your-registry/calculator-agent:latest
        ports:
          - port: 8081
        resources:
          requests:
            cpu: 0.5
            memoryInGb: 1
  
  osType: Linux
  restartPolicy: Always
  
  # Auto-scaling with Azure Monitor
  autoscale:
    minReplicas: 1
    maxReplicas: 10
    targetCpuUtilization: 70
```

#### **3. Platform-as-a-Service (PaaS)**

**Heroku Dynos:**
```yaml
# Procfile for each agent
web: python weather_agent.py

# heroku.yml for container deployment
build:
  docker:
    web: docker/agents/weather/Dockerfile

run:
  web: python src/agents/weather/agent.py

# Auto-scaling configuration
formation:
  web:
    quantity: 2
    size: standard-1x
    
# Add-ons for monitoring
addons:
  - heroku-postgresql:hobby-dev
  - newrelic:wayne
  - papertrail:choklad
```

**Google App Engine:**
```yaml
# app.yaml for each agent service
runtime: python39
service: weather-agent
instance_class: F2

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.7
  target_throughput_utilization: 0.8

handlers:
- url: /.*
  script: auto

env_variables:
  WEATHER_API_KEY: your-api-key
  ENVIRONMENT: production
```

#### **4. Event-Driven Microservices**

**Apache Kafka + Stream Processing:**
```python
# Kafka-based agent communication
from kafka import KafkaProducer, KafkaConsumer
import json

class EventDrivenAgent:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        self.consumer = KafkaConsumer(
            f'{agent_name}-requests',
            bootstrap_servers=['kafka:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
    
    async def process_requests(self):
        """Process incoming requests from Kafka topic"""
        for message in self.consumer:
            request = message.value
            
            # Process the request
            response = await self.handle_request(request)
            
            # Send response to response topic
            self.producer.send(
                f'{request["requester"]}-responses',
                response
            )

# Kubernetes deployment with Kafka
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-agent-kafka
spec:
  template:
    spec:
      containers:
      - name: weather-agent
        image: weather-agent:kafka
        env:
        - name: KAFKA_BROKERS
          value: "kafka-cluster:9092"
        - name: AGENT_TOPIC
          value: "weather-requests"
```

#### **5. Edge Computing Deployment**

**AWS IoT Greengrass:**
```python
# Edge deployment for distributed AI agents
import greengrasssdk

# Initialize Greengrass client
client = greengrasssdk.client('iot-data')

def lambda_handler(event, context):
    """Weather agent running on edge devices"""
    
    # Process locally with cached models
    weather_data = get_local_weather_data(event['location'])
    
    # Sync with cloud when connected
    if is_connected_to_cloud():
        sync_with_central_service(weather_data)
    
    return weather_data

# Deployment configuration
{
  "ComponentName": "WeatherAgent",
  "ComponentVersion": "1.0.0",
  "ComponentType": "aws.greengrass.lambda",
  "ComponentConfiguration": {
    "LambdaFunction": {
      "Runtime": "python3.9",
      "Handler": "weather_agent.lambda_handler",
      "Timeout": 30
    }
  }
}
```

#### **6. Hybrid Multi-Cloud Architecture**

**Cross-Cloud Agent Distribution:**
```yaml
# Primary cluster (AWS EKS)
aws_cluster:
  agents: ["base", "calculator", "weather"]
  region: "us-east-1"
  instance_types: ["m5.large", "m5.xlarge"]

# Secondary cluster (Google GKE)  
gcp_cluster:
  agents: ["research", "move_orchestrator"]
  region: "us-central1"
  machine_types: ["n1-standard-2", "n1-standard-4"]

# Edge locations (Azure Container Instances)
azure_edge:
  agents: ["infrastructure_monitor"]
  regions: ["eastus", "westus", "westeurope"]

# Global load balancing
traffic_distribution:
  primary: 70%    # AWS
  secondary: 20%  # GCP
  edge: 10%       # Azure
```

---

## 5. Networking Architecture Deep Dive

### **Internal Networking (Within Kubernetes)**

#### **Pod-to-Pod Communication:**
```yaml
# Kubernetes internal DNS resolution
weather-agent-service.multi-agent-a2a.svc.cluster.local
#     |                     |            |        |
#  service-name        namespace    service  cluster-domain
```

**CNI Network Plugin (Container Network Interface):**
```yaml
# Typical CNI setup (using Calico/Flannel)
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-system/kube-proxy-config
data:
  config.conf: |
    apiVersion: kubeproxy.config.k8s.io/v1alpha1
    kind: KubeProxyConfiguration
    mode: "iptables"  # or "ipvs" for better performance
    clusterCIDR: "10.244.0.0/16"  # Pod network CIDR
```

**Service Mesh Communication (if using Istio):**
```yaml
# Envoy sidecar proxy for each agent pod
apiVersion: v1
kind: Pod
metadata:
  annotations:
    sidecar.istio.io/inject: "true"  # Auto-inject Envoy proxy
spec:
  containers:
  - name: weather-agent
    image: weather-agent:latest
  # Istio automatically injects envoy-proxy container
```

#### **Service Discovery Mechanism:**

**Native Kubernetes Service Discovery:**
```python
# Agent discovers other agents using Kubernetes DNS
async def discover_agents(self):
    """Discover other A2A agents in the cluster"""
    
    agents = {}
    agent_services = [
        "base-agent-service",
        "calculator-agent-service", 
        "weather-agent-service",
        "research-agent-service"
    ]
    
    for service in agent_services:
        try:
            # Kubernetes DNS resolution
            endpoint = f"http://{service}.multi-agent-a2a.svc.cluster.local:8080"
            
            # Health check
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{endpoint}/health")
                if response.status_code == 200:
                    agents[service] = endpoint
                    
        except Exception as e:
            logger.warning(f"Agent {service} not available: {e}")
    
    return agents
```

**A2A Protocol Discovery:**
```python
# Google A2A protocol agent discovery
from a2a.client import A2ACardResolver

class A2ADiscoveryManager:
    def __init__(self):
        self.resolver = A2ACardResolver()
    
    async def discover_a2a_agents(self):
        """Discover agents using A2A protocol"""
        
        discovered_agents = {}
        
        # Each agent exposes agent card at /.well-known/agent-card.json
        for service_endpoint in self.get_service_endpoints():
            try:
                agent_card = await self.resolver.resolve_agent_card(
                    f"{service_endpoint}/.well-known/agent-card.json"
                )
                
                discovered_agents[agent_card.name] = {
                    "endpoint": service_endpoint,
                    "capabilities": agent_card.capabilities,
                    "skills": agent_card.skills,
                    "version": agent_card.version
                }
                
            except Exception as e:
                logger.error(f"Failed to discover agent at {service_endpoint}: {e}")
        
        return discovered_agents
```

### **External Networking (Client Access)**

#### **Why Port-Forwarding is Used:**

**Development Convenience:**
```bash
# Port-forwarding creates secure tunnels from local machine to K8s services
kubectl port-forward -n multi-agent-a2a svc/streamlit-a2a-service 8501:8501

# This creates a tunnel:
# localhost:8501 -> Kubernetes API -> streamlit-a2a-service:8501 -> Pod:8501

# Benefits:
# 1. No need to expose services externally
# 2. Secure tunnel through kubectl authentication  
# 3. Easy access during development
# 4. No LoadBalancer or Ingress setup required
```

**Production Alternative - Ingress Controller:**
```yaml
# Production setup with NGINX Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - ai-agents.company.com
    secretName: ai-agents-tls
  rules:
  - host: ai-agents.company.com
    http:
      paths:
      - path: /streamlit
        pathType: Prefix
        backend:
          service:
            name: streamlit-a2a-service
            port:
              number: 8501
      - path: /api/weather
        pathType: Prefix  
        backend:
          service:
            name: weather-agent-service
            port:
              number: 8082
```

#### **Load Balancing and Traffic Distribution:**

**Kubernetes Service Load Balancing:**
```yaml
# Service automatically load balances across healthy pods
apiVersion: v1
kind: Service
metadata:
  name: weather-agent-service
spec:
  selector:
    app: weather-agent  # Routes to any pod with this label
  ports:
  - port: 8082
    targetPort: 8080
  type: ClusterIP
  
# Kubernetes uses iptables rules for load balancing:
# -A KUBE-SVC-WEATHER -m statistic --mode random --probability 0.33 -j KUBE-SEP-POD1
# -A KUBE-SVC-WEATHER -m statistic --mode random --probability 0.50 -j KUBE-SEP-POD2  
# -A KUBE-SVC-WEATHER -j KUBE-SEP-POD3
```

**Advanced Load Balancing with Istio:**
```yaml
# Weighted traffic distribution
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: weather-agent-routing
spec:
  hosts:
  - weather-agent-service
  http:
  - match:
    - headers:
        version:
          exact: "v2"
    route:
    - destination:
        host: weather-agent-service
        subset: v2
      weight: 100
  - route:
    - destination:
        host: weather-agent-service
        subset: v1
      weight: 90
    - destination:
        host: weather-agent-service  
        subset: v2
      weight: 10  # Gradual rollout

---
# Define service subsets
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: weather-agent-destination
spec:
  host: weather-agent-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

### **Network Security and Policies:**

**Network Policies for Micro-segmentation:**
```yaml
# Restrict agent-to-agent communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-communication-policy
  namespace: multi-agent-a2a
spec:
  podSelector:
    matchLabels:
      component: agent
  policyTypes:
  - Ingress
  - Egress
  
  # Ingress rules - what can connect to agents
  ingress:
  - from:
    # Allow from Streamlit app
    - podSelector:
        matchLabels:
          app: streamlit-a2a
    # Allow from other agents (for A2A communication)
    - podSelector:
        matchLabels:
          component: agent
    # Allow from monitoring
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 8080
  
  # Egress rules - what agents can connect to
  egress:
  # Allow DNS resolution
  - to: []
    ports:
    - protocol: UDP
      port: 53
  # Allow HTTPS to external APIs
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow inter-agent communication
  - to:
    - podSelector:
        matchLabels:
          component: agent
    ports:
    - protocol: TCP
      port: 8080
```

---

## 6. Additional Critical Questions & Answers

### **Q: How do you handle agent failures and ensure high availability?**

**A: Multi-layered Resilience Strategy:**

**Pod-level Resilience:**
```yaml
# Readiness and liveness probes
spec:
  containers:
  - name: weather-agent
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3  # Restart after 3 failures
    
    readinessProbe:
      httpGet:
        path: /.well-known/agent-card.json
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 3  # Remove from service after 3 failures
```

**Application-level Circuit Breakers:**
```python
import aiohttp
from circuit_breaker import CircuitBreaker

class ResilientA2AClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,    # Open after 5 failures
            recovery_timeout=30,    # Try again after 30 seconds
            expected_exception=aiohttp.ClientError
        )
    
    @circuit_breaker
    async def call_agent(self, agent_endpoint: str, request: dict):
        """Call agent with circuit breaker protection"""
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{agent_endpoint}/api/v1/process",
                    json=request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                # Try fallback agent or cached response
                return await self.get_fallback_response(request)
```

### **Q: How do you ensure data consistency across agents?**

**A: Event-Driven Architecture with State Management:**

**Conversation State Management:**
```python
class ConversationStateManager:
    def __init__(self):
        self.redis_client = redis.asyncio.Redis(host='redis-service')
        self.state_ttl = 3600  # 1 hour TTL
    
    async def save_conversation_state(self, conversation_id: str, state: dict):
        """Save conversation state for cross-agent context"""
        
        state_key = f"conversation:{conversation_id}"
        
        # Store with TTL
        await self.redis_client.setex(
            state_key,
            self.state_ttl,
            json.dumps(state)
        )
        
        # Update activity timestamp
        await self.redis_client.setex(
            f"{state_key}:last_activity",
            self.state_ttl,
            str(time.time())
        )
    
    async def get_conversation_context(self, conversation_id: str) -> dict:
        """Retrieve conversation context for agent processing"""
        
        state_key = f"conversation:{conversation_id}"
        state_data = await self.redis_client.get(state_key)
        
        if state_data:
            return json.loads(state_data)
        else:
            return {"conversation_id": conversation_id, "history": []}
```

**Event Sourcing for Agent Actions:**
```python
class AgentEventStore:
    async def record_agent_action(self, action: AgentAction):
        """Record agent action for audit and replay"""
        
        event = {
            "event_id": str(uuid.uuid4()),
            "agent_name": action.agent_name,
            "action_type": action.action_type,
            "input_data": action.input_data,
            "output_data": action.output_data,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": action.conversation_id
        }
        
        # Store in event log
        await self.event_store.append(
            stream_id=f"agent-{action.agent_name}",
            event_data=event
        )
        
        # Update aggregate state
        await self.update_agent_state(action.agent_name, event)
```

### **Q: How do you monitor and debug distributed agent interactions?**

**A: Distributed Tracing and Correlation:**

**OpenTelemetry Integration:**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup distributed tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

class TracedA2AAgent:
    async def process_request(self, request: dict):
        """Process request with distributed tracing"""
        
        with tracer.start_as_current_span("agent_request_processing") as span:
            span.set_attribute("agent.name", self.agent_name)
            span.set_attribute("request.id", request.get("id"))
            span.set_attribute("request.type", request.get("type"))
            
            try:
                # Add request details to span
                span.add_event("request_received", {
                    "request_size": len(json.dumps(request)),
                    "correlation_id": request.get("correlation_id")
                })
                
                # Process the request
                result = await self._handle_request(request)
                
                # Record success
                span.set_attribute("response.status", "success")
                span.add_event("request_completed", {
                    "response_size": len(json.dumps(result))
                })
                
                return result
                
            except Exception as e:
                # Record error details
                span.set_attribute("response.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.add_event("request_failed", {
                    "error": str(e)
                })
                raise
```

**Correlation ID Propagation:**
```python
class RequestCorrelationMiddleware:
    """Middleware to propagate correlation IDs across service calls"""
    
    async def __call__(self, request, call_next):
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID") or 
            str(uuid.uuid4())
        )
        
        # Add to request context
        request.state.correlation_id = correlation_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

# Use in agent HTTP calls
async def call_other_agent(self, target_agent: str, request_data: dict):
    """Call another agent with correlation ID propagation"""
    
    headers = {
        "X-Correlation-ID": self.current_correlation_id,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{target_agent}/api/v1/process",
            json=request_data,
            headers=headers
        )
        
        return response.json()
```

### **Q: How do you handle versioning and rolling updates of agents?**

**A: Blue-Green and Canary Deployment Strategies:**

**Rolling Update Configuration:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-agent
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1      # Keep at least 2 pods running
      maxSurge: 1           # Create at most 1 extra pod during update
  template:
    spec:
      containers:
      - name: weather-agent
        image: weather-agent:v1.2.0
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        # Zero-downtime deployment with proper health checks
```

**Version-aware A2A Protocol:**
```python
class VersionedA2AAgent:
    def __init__(self, version: str):
        self.version = version
        self.supported_protocols = ["a2a/v0.3.3", "a2a/v0.4.0"]
    
    async def handle_a2a_request(self, request: dict):
        """Handle A2A request with version compatibility"""
        
        client_protocol = request.get("protocol_version", "a2a/v0.3.3")
        
        if client_protocol not in self.supported_protocols:
            return {
                "error": "unsupported_protocol",
                "supported_versions": self.supported_protocols,
                "agent_version": self.version
            }
        
        # Route to appropriate handler based on protocol version
        if client_protocol == "a2a/v0.4.0":
            return await self.handle_v04_request(request)
        else:
            return await self.handle_v03_request(request)
    
    def get_agent_card(self):
        """Return A2A agent card with version info"""
        return {
            "name": self.agent_name,
            "version": self.version,
            "protocol_versions": self.supported_protocols,
            "capabilities": self.capabilities,
            "endpoints": {
                "process": "/api/v1/process",
                "health": "/health",
                "metrics": "/metrics"
            }
        }
```

This comprehensive deep dive covers the entire system architecture, from request lifecycle to deployment alternatives, providing the detailed technical understanding needed for expert-level discussions about the AI Ops platform.