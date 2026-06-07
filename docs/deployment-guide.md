# Deployment Guide

## Deployment Models

This platform supports three deployment models, each with increasing operational complexity and scalability.

| Model | Use Case | Complexity | Scalability |
|-------|----------|------------|-------------|
| Local Docker | Development, demos | Low | Single machine |
| AWS ECS/Fargate | Production SaaS | Medium | Auto-scaling |
| Kubernetes/EKS | Enterprise multi-tenant | High | Unlimited |

## Local Docker Deployment

### Prerequisites

- Docker 24+ and Docker Compose v2
- 4GB RAM minimum
- Optional: OpenAI API key

### Quick Start

```bash
# Clone and configure
git clone https://github.com/your-org/ai-agent-platform.git
cd ai-agent-platform
cp .env.example .env

# Start all services
cd docker
docker-compose up -d

# Verify health
curl http://localhost:8000/api/v1/health

# Execute a workflow
python ../examples/run_workflow.py
```

### Service Map

| Service | Port | Image |
|---------|------|-------|
| API | 8000 | Custom (Dockerfile) |
| PostgreSQL | 5432 | postgres:16-alpine |
| Qdrant | 6333 | qdrant/qdrant:v1.12.0 |
| Prometheus | 9090 | prom/prometheus |
| Grafana | 3000 | grafana/grafana |
| OTel Collector | 4317 | otel/opentelemetry-collector-contrib |

### Architecture

![Local Docker Deployment](../diagrams/deployment-local.svg)

*Source: [deployment-local.d2](../diagrams/deployment-local.d2)*

---

## AWS ECS/Fargate Deployment

### Architecture

![AWS ECS / Fargate Deployment](../diagrams/deployment-aws.svg)

*Source: [deployment-aws.d2](../diagrams/deployment-aws.d2)*

### Components

| Component | AWS Service | Configuration |
|-----------|------------|---------------|
| API | ECS Fargate | 2 vCPU, 4GB, auto-scaling 2-10 |
| PostgreSQL | RDS PostgreSQL 16 | db.r6g.large, Multi-AZ |
| Vector Store | Qdrant on EC2 or Qdrant Cloud | r6g.xlarge |
| Secrets | AWS Secrets Manager | API keys, DB credentials |
| Load Balancer | ALB | HTTPS termination |
| Observability | CloudWatch + AMP + AMG | Managed Prometheus/Grafana |
| LLM | OpenAI API | External |

### Deployment Steps

```bash
# 1. Build and push container
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker build -f docker/Dockerfile -t ai-agent-platform .
docker tag ai-agent-platform:latest $ECR_URL/ai-agent-platform:latest
docker push $ECR_URL/ai-agent-platform:latest

# 2. Deploy via ECS task definition
aws ecs update-service --cluster agent-platform --service api --force-new-deployment

# 3. Configure secrets
aws secretsmanager create-secret --name agent-platform/openai-key --secret-string "$OPENAI_API_KEY"
```

### Networking

Private subnet connectivity (RDS, Qdrant, Secrets Manager) is shown in the [AWS deployment diagram](../diagrams/deployment-aws.svg) above.

### Auto-Scaling

- **Target**: CPU utilization 70%
- **Min tasks**: 2
- **Max tasks**: 10
- **Scale-out cooldown**: 60s
- **Scale-in cooldown**: 300s

---

## Kubernetes / EKS Deployment

### Architecture

![Kubernetes / EKS Deployment](../diagrams/deployment-k8s.svg)

*Source: [deployment-k8s.d2](../diagrams/deployment-k8s.d2)*

### Manifests Overview

```yaml
# Recommended structure
k8s/
├── namespace.yaml
├── api/
│   ├── deployment.yaml    # 3 replicas, HPA 3-20
│   ├── service.yaml       # ClusterIP
│   └── ingress.yaml       # NGINX ingress + TLS
├── postgres/
│   └── statefulset.yaml   # Or use managed RDS
├── qdrant/
│   └── statefulset.yaml
├── observability/
│   ├── prometheus.yaml
│   ├── grafana.yaml
│   └── otel-collector.yaml
└── secrets/
    └── external-secrets.yaml  # External Secrets Operator
```

### Key Configurations

| Resource | Replicas | Resources | Notes |
|----------|----------|-----------|-------|
| API | 3-20 (HPA) | 1CPU/2GB | Stateless, scales horizontally |
| PostgreSQL | 1 (or RDS) | 2CPU/4GB | Stateful, persistent volume |
| Qdrant | 1-3 | 2CPU/4GB | Stateful, SSD storage |
| Prometheus | 1 | 1CPU/2GB | 90-day retention |
| Grafana | 1 | 0.5CPU/1GB | Dashboard provisioning |

### Secrets Management

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agent-platform-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
  target:
    name: agent-platform-secrets
  data:
    - secretKey: OPENAI_API_KEY
      remoteRef:
        key: agent-platform/openai-key
```

## Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Production | — | OpenAI API key |
| `POSTGRES_HOST` | Yes | localhost | PostgreSQL host |
| `QDRANT_HOST` | Yes | localhost | Qdrant host |
| `TOKEN_BUDGET_PER_REQUEST` | No | 8000 | Token limit |
| `OTEL_ENABLED` | No | true | Enable tracing |

## Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Metrics
curl http://localhost:8000/api/v1/metrics

# PostgreSQL
docker exec postgres pg_isready

# Qdrant
curl http://localhost:6333/healthz
```

## Production Checklist

- [ ] HTTPS/TLS configured
- [ ] Secrets in vault (not .env files)
- [ ] Database backups automated
- [ ] Auto-scaling configured
- [ ] Monitoring alerts set up
- [ ] Rate limiting enabled
- [ ] API authentication configured
- [ ] Log aggregation (CloudWatch/ELK)
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
