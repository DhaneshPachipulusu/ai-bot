# Deployment Guide

Production-grade DevOps setup for the AI Interview Bot.

## Stack

| Layer        | Tech                                      |
|--------------|-------------------------------------------|
| Backend      | FastAPI (Python 3.11), Uvicorn            |
| Frontend     | Next.js 16 (standalone), Node 20          |
| Reverse proxy| Nginx 1.27 (rate-limited, gzip, headers)  |
| Container    | Docker (multi-stage, non-root, distroless-ish) |
| Orchestration| docker compose (single host) / Kubernetes |
| CI/CD        | GitHub Actions → GHCR → Trivy scan        |

---

## 1. Local development

```bash
cp .env.example .env       # add GEMINI_API_KEY
make up                    # docker compose up --build -d
make logs
```

- Backend: <http://localhost:8000>
- Frontend: <http://localhost:3000>
- Healthcheck: `curl localhost:8000/health`

## 2. Production (single VM, docker compose)

```bash
cp .env.example .env       # fill real secrets + NEXT_PUBLIC_API_URL
make prod-up               # builds, runs nginx → frontend + backend
```

Nginx terminates HTTP on `:80` and proxies:
- `/api/*` → backend:8000 (rate-limited 20 r/s, burst 40)
- `/api/login` → stricter 5 r/s
- `/*` → frontend:3000

To enable HTTPS, mount certs into `./nginx/certs/` and uncomment the 443 server block in `nginx/conf.d/default.conf`. Use [`certbot`](https://certbot.eff.org/) or Caddy as a sidecar.

## 3. Kubernetes

```bash
# Replace image refs in k8s/*-deployment.yaml first.
kubectl create namespace ai-interview-bot
kubectl -n ai-interview-bot create secret generic aibot-secrets \
    --from-env-file=.env
make k8s-apply             # kubectl apply -k k8s/
make k8s-status
```

Includes:
- Deployments (rolling, 2 replicas, non-root, dropped caps)
- Services (ClusterIP)
- Ingress (NGINX ingress controller, cert-manager TLS)
- HPA (CPU/memory based, min 2 / max 10)
- PVCs (data + uploads)
- ConfigMap + Secret separation

## 4. CI/CD (`.github/workflows/ci.yml`)

On every push to `main`:
1. Lint & test backend (ruff, pytest)
2. Lint & build frontend (eslint, `next build`)
3. Build multi-arch images, push to GHCR with tags: `sha-XXXX`, `latest`, semver on tags
4. Trivy scan for HIGH/CRITICAL CVEs

Required repo settings:
- `vars.NEXT_PUBLIC_API_URL` — public API URL baked into the frontend bundle
- Workflow has `packages: write` to push to GHCR

## 5. Production hardening checklist

- [x] Multi-stage Dockerfiles, non-root user (UID 1001)
- [x] Healthchecks (HTTP, container + k8s readiness/liveness)
- [x] Resource limits (cpu + mem) in compose & k8s
- [x] `no-new-privileges`, dropped Linux caps
- [x] Rate limiting at nginx
- [x] Log rotation (json-file, 10MB × 5)
- [x] Image vulnerability scanning (Trivy)
- [x] HPA for autoscaling
- [x] Persistent volumes for SQLite & uploads
- [ ] Replace SQLite with managed Postgres for HA
- [ ] Add OpenTelemetry tracing
- [ ] Add Prometheus `/metrics` endpoint + ServiceMonitor

## 6. Monitoring (Prometheus + Grafana)

```bash
make prod-up                # main stack (creates the network)
make monitoring-up          # adds prometheus, grafana, node-exporter, cAdvisor
```

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3001> (default admin/admin — override via `GRAFANA_USER` / `GRAFANA_PASSWORD`)

What's instrumented:
- **Backend** exposes `/metrics` via `prometheus-fastapi-instrumentator` (added conditionally — `pip install prometheus-fastapi-instrumentator==7.0.0`)
- **node-exporter** → host CPU/mem/disk
- **cAdvisor** → per-container resource use
- **Alerts** (`monitoring/prometheus/alerts.yml`): backend down, 5xx > 5%, p95 > 1.5s, host CPU > 85%, disk < 15%
- **Dashboard** auto-provisioned in Grafana → "AI Interview Bot / Backend Overview"

## 7. Helm chart

`helm/ai-interview-bot/` — production-ready chart.

```bash
helm lint helm/ai-interview-bot
helm template aibot helm/ai-interview-bot       # dry render
helm upgrade --install aibot helm/ai-interview-bot \
    --namespace ai-interview-bot --create-namespace \
    --set secrets.GEMINI_API_KEY=$GEMINI_API_KEY \
    --set global.imageRegistry=ghcr.io/yourorg \
    --set ingress.host=aibot.example.com
```

Highlights:
- Templated backend + frontend with separate enable flags
- HPA, PVCs, ServiceMonitor (Prometheus Operator)
- Pod-level + container-level security contexts
- `values.yaml` covers replicas, resources, autoscaling, ingress, TLS, secrets

## 8. Terraform — AWS infrastructure (`terraform/`)

Provisions a production-grade EKS environment:
- VPC across 3 AZs (public + private subnets, single NAT for cost)
- EKS 1.30 with managed node group (t3.medium × 2-6, autoscaling)
- ECR repos for backend + frontend with image scanning + lifecycle policy (keep last 20)
- Cluster add-ons via Helm: ingress-nginx (LoadBalancer), cert-manager, metrics-server
- IRSA enabled, EBS CSI driver for PVCs

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
make tf-init
make tf-plan
make tf-apply

# After apply:
aws eks update-kubeconfig --region us-east-1 --name ai-interview-bot-prod-eks
make helm-install
```

State: configure remote backend (S3 + DynamoDB) by uncommenting the `backend "s3"` block in `versions.tf` before first `init`.

## 9. End-to-end flow

```
Developer push → GitHub Actions (lint/build/scan)
              ↓
            GHCR (or ECR)
              ↓
       helm upgrade --install
              ↓
     EKS (HPA + ingress-nginx + cert-manager)
              ↓
      Prometheus → Grafana / Alertmanager
```

## 10. Useful commands

```bash
make help            # list everything
make build TAG=v1.0  # build images with explicit tag
make push  TAG=v1.0
make scan            # trivy scan local images
make k8s-rollout     # rolling restart
```
