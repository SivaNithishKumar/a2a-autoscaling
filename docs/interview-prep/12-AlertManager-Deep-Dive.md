# AlertManager Deep Dive: How Alerts Work in the A2A System

*Comprehensive Guide to AlertManager Configuration, Alert Routing, and Notification Strategies*

## Overview

AlertManager is a critical component of the monitoring stack that handles alerts sent by Prometheus server. It takes care of deduplicating, grouping, and routing alerts to the correct receiver integrations such as email, Slack, or webhook endpoints.

---

## 1. AlertManager Architecture & Flow

### **Complete Alert Lifecycle**

```mermaid
graph TB
    A[Prometheus] -->|Evaluates Rules| B[Alert Rules]
    B -->|Triggers Alert| C[AlertManager]
    C -->|Groups & Routes| D[Routing Tree]
    D -->|Sends to| E[Receivers]
    E -->|Notifies| F1[Slack]
    E -->|Notifies| F2[Email]
    E -->|Notifies| F3[Webhooks]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#bbf,stroke:#333,stroke-width:2px
    style E fill:#bfb,stroke:#333,stroke-width:2px
```

### **Step-by-Step Alert Processing**

#### **Phase 1: Alert Generation (Prometheus)**
```yaml
# Prometheus evaluates alert rules every 30 seconds (default)
# Example: A2A Agent Down Alert
- alert: A2AAgentDown
  expr: up{job=~".*agent.*"} == 0  # Query returns 1 if agent is down
  for: 1m                          # Alert fires after 1 minute of being down
  labels:
    severity: critical
    team: platform
    service: "{{ $labels.job }}"
  annotations:
    summary: "A2A Agent is down (instance {{ $labels.instance }})"
    description: "A2A Agent {{ $labels.job }} has been down for more than 1 minute."
    runbook_url: "https://runbooks.company.com/agent-down"
```

#### **Phase 2: Alert Transmission**
```yaml
# Prometheus configuration (prometheus.yml)
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager-service.multi-agent-a2a.svc.cluster.local:9093
    timeout: 10s
    api_version: v2

# Prometheus sends alerts to AlertManager via HTTP POST
POST /api/v2/alerts
Content-Type: application/json

[
  {
    "labels": {
      "alertname": "A2AAgentDown",
      "severity": "critical", 
      "team": "platform",
      "service": "weather-agent",
      "instance": "weather-agent-pod-xyz"
    },
    "annotations": {
      "summary": "A2A Agent is down (instance weather-agent-pod-xyz)",
      "description": "A2A Agent weather-agent has been down for more than 1 minute."
    },
    "startsAt": "2025-09-18T10:30:00Z",
    "endsAt": "0001-01-01T00:00:00Z",  # Empty means ongoing
    "generatorURL": "http://prometheus:9090/graph?g0.expr=up%7Bjob%3D~%22.*agent.*%22%7D"
  }
]
```

#### **Phase 3: AlertManager Processing**

**Alert Grouping Logic:**
```yaml
# AlertManager groups alerts to reduce notification spam
route:
  group_by: ['alertname']      # Group alerts by alert name
  group_wait: 10s             # Wait 10s for more alerts before sending
  group_interval: 10s         # Wait 10s between sending groups
  repeat_interval: 1h         # Repeat notification every hour if not resolved
  receiver: 'web.hook'        # Default receiver
```

**How Grouping Works:**
```python
# Conceptual grouping algorithm
class AlertGrouper:
    def __init__(self):
        self.groups = {}
        self.group_wait_timer = {}
    
    def add_alert(self, alert):
        """Add alert to appropriate group"""
        
        # Generate group key based on group_by labels
        group_key = self.generate_group_key(alert, ['alertname'])
        
        if group_key not in self.groups:
            # New group - start wait timer
            self.groups[group_key] = [alert]
            self.start_group_wait_timer(group_key, 10)  # 10s wait
        else:
            # Add to existing group
            self.groups[group_key].append(alert)
            
        # Reset timer if group_interval hasn't passed
        self.reset_group_interval_timer(group_key)
    
    def send_group_notification(self, group_key):
        """Send notification for alert group"""
        alerts = self.groups[group_key]
        
        # Route to appropriate receiver
        receiver = self.route_alerts(alerts)
        
        # Send notification
        self.send_to_receiver(receiver, alerts)
        
        # Schedule repeat notification
        self.schedule_repeat(group_key, repeat_interval=3600)  # 1 hour
```

---

## 2. Alert Rules & When They Trigger

### **Kubernetes Infrastructure Alerts**

#### **Node-Level Alerts:**
```yaml
# Node becomes unready
- alert: KubernetesNodeReady
  expr: kube_node_status_condition{condition="Ready",status="true"} == 0
  for: 10m                    # Must be unready for 10 minutes
  labels:
    severity: critical
    team: infrastructure
  
# High CPU usage on nodes  
- alert: KubernetesNodeHighCPU
  expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100) > 80
  for: 2m                     # CPU > 80% for 2 minutes
  labels:
    severity: warning
    team: infrastructure

# Memory pressure on nodes
- alert: KubernetesMemoryPressure
  expr: kube_node_status_condition{condition="MemoryPressure",status="true"} == 1
  for: 2m                     # Memory pressure detected for 2 minutes
  labels:
    severity: critical
    team: infrastructure
```

#### **Application-Level Alerts:**
```yaml
# A2A Agent down
- alert: A2AAgentDown
  expr: up{job=~".*agent.*"} == 0
  for: 1m                     # Agent unreachable for 1 minute
  labels:
    severity: critical
    team: platform
    service: "{{ $labels.job }}"

# Agent high CPU usage
- alert: A2AAgentHighCPU
  expr: rate(container_cpu_usage_seconds_total{pod=~".*agent.*"}[5m]) * 100 > 80
  for: 5m                     # CPU > 80% for 5 minutes
  labels:
    severity: warning
    team: platform

# Agent crash looping
- alert: KubernetesPodCrashLooping
  expr: max_over_time(kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}[5m]) >= 1
  for: 2m                     # Crash looping for 2 minutes
  labels:
    severity: warning
    team: platform
```

### **Custom A2A Business Logic Alerts**
```yaml
# High error rate in A2A requests
- alert: A2AHighErrorRate
  expr: |
    (
      rate(a2a_requests_total{status="error"}[5m]) /
      rate(a2a_requests_total[5m])
    ) * 100 > 5
  for: 2m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "High error rate in A2A requests"
    description: "Error rate is {{ $value }}% for agent {{ $labels.agent_name }}"

# A2A Agent response time too high
- alert: A2AHighLatency
  expr: |
    histogram_quantile(0.95, 
      rate(a2a_request_duration_seconds_bucket[5m])
    ) > 2
  for: 3m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "A2A Agent high response time"
    description: "95th percentile response time is {{ $value }}s"

# Too many active tasks (potential bottleneck)
- alert: A2ATooManyActiveTasks
  expr: a2a_active_tasks > 100
  for: 5m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "Too many active A2A tasks"
    description: "Agent {{ $labels.agent_name }} has {{ $value }} active tasks"
```

---

## 3. Alert Routing & Receivers

### **Routing Configuration**

#### **Basic Routing Tree:**
```yaml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s  
  repeat_interval: 1h
  receiver: 'web.hook'          # Default receiver
  
  routes:
  # Critical alerts go to multiple channels
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 5s              # Faster response for critical
    repeat_interval: 30m        # More frequent repeats
  
  # Platform team alerts
  - match:
      team: platform
    receiver: 'platform-team'
    
  # Infrastructure alerts
  - match:
      team: infrastructure  
    receiver: 'infrastructure-team'
    
  # Specific service routing
  - match_re:
      service: '.*agent.*'
    receiver: 'agent-alerts'
```

#### **Advanced Routing Logic:**
```yaml
# Time-based routing (work hours vs after hours)
- match:
    severity: warning
  receiver: 'daytime-alerts'
  active_time_intervals:
  - weekdays_9_to_5

- match:
    severity: critical
  receiver: 'oncall-alerts'     # Always goes to on-call
  
- match:
    severity: warning
  receiver: 'afterhours-alerts'
  active_time_intervals:
  - nights_and_weekends

# Time interval definitions
time_intervals:
- name: weekdays_9_to_5
  time_intervals:
  - times:
    - start_time: '09:00'
      end_time: '17:00'
    weekdays: ['monday:friday']
    
- name: nights_and_weekends
  time_intervals:
  - times:
    - start_time: '17:01'
      end_time: '08:59'
    weekdays: ['monday:friday']
  - weekdays: ['saturday', 'sunday']
```

### **Receiver Configurations**

#### **Slack Integration:**
```yaml
receivers:
- name: 'critical-alerts'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
    channel: '#critical-alerts'
    username: 'AlertManager'
    icon_emoji: ':rotating_light:'
    title: 'CRITICAL: {{ .GroupLabels.alertname }}'
    title_link: 'http://grafana.local/d/alerts'
    text: |
      {{ range .Alerts -}}
      *Alert:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      *Severity:* {{ .Labels.severity }}
      *Service:* {{ .Labels.service }}
      *Started:* {{ .StartsAt.Format "2006-01-02 15:04:05" }}
      {{ if .Annotations.runbook_url }}*Runbook:* {{ .Annotations.runbook_url }}{{ end }}
      {{ end }}
    actions:
    - type: button
      text: 'View in Grafana'
      url: 'http://grafana.local/d/alerts'
    - type: button  
      text: 'Silence Alert'
      url: 'http://alertmanager.local/#/silences/new'
    color: danger
    send_resolved: true

- name: 'platform-team'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00000000/B00000000/YYYYYYYYYYYYYYYYYYYYYYYY'
    channel: '#platform-alerts'
    username: 'AlertManager'
    icon_emoji: ':warning:'
    title: '{{ .GroupLabels.alertname }}'
    text: |
      {{ .CommonAnnotations.summary }}
      
      Affected Services:
      {{ range .Alerts -}}
      • {{ .Labels.service | default "unknown" }}
      {{ end }}
    color: '{{ if eq .Status "firing" }}warning{{ else }}good{{ end }}'
    send_resolved: true
```

#### **Email Integration:**
```yaml
- name: 'infrastructure-team'
  email_configs:
  - to: 'infrastructure@company.com'
    from: 'alertmanager@company.com'
    subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }} ({{ .Alerts | len }} alerts)'
    html: |
      <!DOCTYPE html>
      <html>
      <head>
          <title>Alert Notification</title>
          <style>
              body { font-family: Arial, sans-serif; }
              .alert { margin: 10px 0; padding: 15px; border-radius: 5px; }
              .critical { background-color: #ffebee; border-left: 5px solid #f44336; }
              .warning { background-color: #fff3e0; border-left: 5px solid #ff9800; }
              .resolved { background-color: #e8f5e8; border-left: 5px solid #4caf50; }
          </style>
      </head>
      <body>
          <h2>Alert Notification</h2>
          <p><strong>Status:</strong> {{ .Status | title }}</p>
          <p><strong>Group:</strong> {{ .GroupLabels.alertname }}</p>
          
          {{ range .Alerts }}
          <div class="alert {{ .Labels.severity }}">
              <h3>{{ .Annotations.summary }}</h3>
              <p><strong>Description:</strong> {{ .Annotations.description }}</p>
              <p><strong>Severity:</strong> {{ .Labels.severity }}</p>
              <p><strong>Service:</strong> {{ .Labels.service }}</p>
              <p><strong>Started:</strong> {{ .StartsAt.Format "2006-01-02 15:04:05 UTC" }}</p>
              {{ if .EndsAt.Before now }}
              <p><strong>Ended:</strong> {{ .EndsAt.Format "2006-01-02 15:04:05 UTC" }}</p>
              {{ end }}
              {{ if .Annotations.runbook_url }}
              <p><strong>Runbook:</strong> <a href="{{ .Annotations.runbook_url }}">{{ .Annotations.runbook_url }}</a></p>
              {{ end }}
          </div>
          {{ end }}
          
          <hr>
          <p><small>
              <a href="http://grafana.local/d/alerts">View in Grafana</a> | 
              <a href="http://alertmanager.local">AlertManager</a>
          </small></p>
      </body>
      </html>
    send_resolved: true

- name: 'oncall-alerts'
  email_configs:
  - to: 'oncall@company.com'
    from: 'alertmanager@company.com'
    subject: '[ONCALL ALERT] {{ .GroupLabels.alertname }}'
    body: |
      CRITICAL ALERT REQUIRES IMMEDIATE ATTENTION
      
      {{ range .Alerts -}}
      Alert: {{ .Annotations.summary }}
      Service: {{ .Labels.service }}
      Started: {{ .StartsAt.Format "2006-01-02 15:04:05 UTC" }}
      
      {{ .Annotations.description }}
      
      {{ if .Annotations.runbook_url }}Runbook: {{ .Annotations.runbook_url }}{{ end }}
      {{ end }}
      
      Dashboard: http://grafana.local/d/alerts
      AlertManager: http://alertmanager.local
    headers:
      X-Priority: '1'  # High priority email
    send_resolved: true
```

#### **Webhook Integration:**
```yaml
- name: 'web.hook'
  webhook_configs:
  - url: 'http://alert-webhook-service.multi-agent-a2a.svc.cluster.local:5001/webhook'
    max_alerts: 10
    send_resolved: true
    http_config:
      bearer_token: 'webhook-secret-token'
    retry_delay: 10s
```

**Webhook Payload Example:**
```json
{
  "receiver": "web.hook",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "A2AAgentDown",
        "severity": "critical",
        "service": "weather-agent",
        "team": "platform",
        "instance": "weather-agent-pod-xyz"
      },
      "annotations": {
        "description": "A2A Agent weather-agent has been down for more than 1 minute.",
        "summary": "A2A Agent is down (instance weather-agent-pod-xyz)"
      },
      "startsAt": "2025-09-18T10:30:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph?g0.expr=up%7Bjob%3D~%22.*agent.*%22%7D",
      "fingerprint": "5ef77f1f8a3ecde8"
    }
  ],
  "groupLabels": {
    "alertname": "A2AAgentDown"
  },
  "commonLabels": {
    "alertname": "A2AAgentDown",
    "severity": "critical",
    "team": "platform"
  },
  "commonAnnotations": {},
  "externalURL": "http://alertmanager:9093",
  "version": "4",
  "groupKey": "{}/{severity=\"critical\"}:{alertname=\"A2AAgentDown\"}"
}
```

---

## 4. Alert Suppression & Management

### **Inhibition Rules**
```yaml
# Suppress warning alerts when critical alerts are firing
inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'service', 'instance']

# Suppress agent-specific alerts when entire node is down
- source_match:
    alertname: 'KubernetesNodeReady'
  target_match_re:
    alertname: '.*Agent.*'
  equal: ['instance']

# Suppress memory alerts when node has memory pressure
- source_match:
    alertname: 'KubernetesMemoryPressure'
  target_match:
    alertname: 'A2AAgentHighMemory'
  equal: ['instance']
```

### **Silencing Alerts**
```bash
# Silence alerts via API
curl -X POST http://alertmanager:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "alertname",
        "value": "A2AAgentDown",
        "isRegex": false
      },
      {
        "name": "service", 
        "value": "weather-agent",
        "isRegex": false
      }
    ],
    "startsAt": "2025-09-18T10:00:00Z",
    "endsAt": "2025-09-18T12:00:00Z",
    "createdBy": "devops-team",
    "comment": "Planned maintenance window for weather service"
  }'

# Silence all alerts for specific agent during deployment
curl -X POST http://alertmanager:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "service",
        "value": "calculator-agent", 
        "isRegex": false
      }
    ],
    "startsAt": "2025-09-18T14:00:00Z",
    "endsAt": "2025-09-18T14:30:00Z",
    "createdBy": "deployment-pipeline",
    "comment": "Deployment window - calculator agent v1.2.0"
  }'
```

### **Alert States & Lifecycle**
```yaml
# Alert states in AlertManager
states:
  - pending     # Alert condition met but waiting for 'for' duration
  - firing      # Alert actively firing
  - resolved    # Alert condition no longer met
  - silenced    # Alert manually silenced
  - inhibited   # Alert suppressed by inhibition rule

# Example alert lifecycle
timeline:
  - "10:30:00": Alert condition detected (agent down)
  - "10:30:00": Alert enters "pending" state
  - "10:31:00": Alert moves to "firing" state (after 1m 'for' clause)
  - "10:31:10": AlertManager sends notification (after 10s group_wait)
  - "11:31:00": Repeat notification sent (after 1h repeat_interval)
  - "10:32:30": Agent comes back online
  - "10:32:30": Alert enters "resolved" state
  - "10:32:40": Resolved notification sent (if send_resolved: true)
```

---

## 5. Monitoring AlertManager Itself

### **AlertManager Health Checks**
```yaml
# Prometheus monitors AlertManager health
- alert: AlertManagerDown
  expr: up{job="alertmanager"} == 0
  for: 2m
  labels:
    severity: critical
    team: platform
  annotations:
    summary: "AlertManager is down"
    description: "AlertManager has been down for more than 2 minutes"

# Check if AlertManager is receiving alerts
- alert: AlertManagerNotReceivingAlerts
  expr: increase(alertmanager_alerts_received_total[5m]) == 0
  for: 10m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "AlertManager not receiving alerts"
    description: "AlertManager hasn't received any alerts in the last 10 minutes"

# Check notification success rate
- alert: AlertManagerNotificationsFailing
  expr: |
    (
      rate(alertmanager_notifications_failed_total[5m]) /
      rate(alertmanager_notifications_total[5m])
    ) * 100 > 10
  for: 5m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "AlertManager notifications failing"
    description: "{{ $value }}% of notifications are failing"
```

### **AlertManager Metrics**
```promql
# Key AlertManager metrics to monitor
alertmanager_alerts_total                    # Total alerts received
alertmanager_alerts_received_total           # Alerts received by status
alertmanager_notifications_total             # Total notifications sent
alertmanager_notifications_failed_total      # Failed notifications
alertmanager_silences_total                  # Active silences
alertmanager_inhibited_alerts_total          # Inhibited alerts
```

---

## 6. Real-World Alert Scenarios

### **Scenario 1: Weather Agent Pod Crashes**
```yaml
Timeline:
  "10:30:00": Weather agent pod crashes
  "10:30:00": Kubernetes restarts pod (restart policy: Always)
  "10:30:15": Pod fails to start (image pull error)
  "10:30:30": Pod enters CrashLoopBackOff
  "10:31:00": Prometheus detects up{job="weather-agent"} == 0
  "10:32:00": A2AAgentDown alert fires (after 1m 'for' duration)
  "10:32:00": KubernetesPodCrashLooping alert fires (after 2m 'for' duration)
  "10:32:10": AlertManager sends notifications:
    - Slack: #critical-alerts channel
    - Email: platform@company.com
    - Webhook: alert-webhook-service

Notifications sent:
  - Slack message with red color, mentions @platform-team
  - Email with high priority flag
  - Webhook triggers automated response (scale up other agents)
```

### **Scenario 2: High Memory Usage Cascade**
```yaml
Timeline:
  "11:00:00": Node memory usage hits 85%
  "11:02:00": KubernetesNodeHighMemory fires (warning)
  "11:03:00": Multiple agent pods show high memory usage
  "11:05:00": A2AAgentHighMemory fires for 3 agents (warning)
  "11:07:00": Node memory pressure detected
  "11:09:00": KubernetesMemoryPressure fires (critical)
  
Inhibition in action:
  - A2AAgentHighMemory alerts get inhibited
  - Only KubernetesMemoryPressure alert is sent
  - Platform team gets single critical alert instead of spam
```

### **Scenario 3: Planned Maintenance**
```bash
# 30 minutes before maintenance
curl -X POST alertmanager:9093/api/v1/silences -d '{
  "matchers": [{"name": "team", "value": "platform"}],
  "startsAt": "2025-09-18T02:00:00Z",
  "endsAt": "2025-09-18T04:00:00Z", 
  "createdBy": "maintenance-team",
  "comment": "Planned Kubernetes cluster upgrade"
}'

# During maintenance:
  - All platform alerts silenced
  - Critical infrastructure alerts still fire
  - Maintenance team gets notifications in #maintenance channel
```

This comprehensive guide shows exactly how AlertManager works in your A2A system, when alerts fire, who gets notified, and how the entire alert lifecycle is managed for production operations.