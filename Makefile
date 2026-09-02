# AI Interview Bot — DevOps Makefile
# Usage: make <target>

SHELL := /bin/bash
COMPOSE_DEV  := docker compose
COMPOSE_PROD := docker compose -f docker-compose.prod.yml --env-file .env
K8S_DIR      := k8s
NAMESPACE    := ai-interview-bot

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------- Local dev (compose) ----------
.PHONY: up
up: ## Start dev stack (build if needed)
	$(COMPOSE_DEV) up --build -d

.PHONY: down
down: ## Stop dev stack
	$(COMPOSE_DEV) down

.PHONY: logs
logs: ## Tail dev logs
	$(COMPOSE_DEV) logs -f --tail=100

.PHONY: ps
ps: ## List dev containers
	$(COMPOSE_DEV) ps

.PHONY: rebuild
rebuild: ## Rebuild dev images without cache
	$(COMPOSE_DEV) build --no-cache

.PHONY: shell-backend
shell-backend: ## Shell into backend
	$(COMPOSE_DEV) exec backend /bin/bash

.PHONY: shell-frontend
shell-frontend: ## Shell into frontend
	$(COMPOSE_DEV) exec frontend /bin/sh

# ---------- Production (compose + nginx) ----------
.PHONY: prod-up
prod-up: ## Start prod stack
	$(COMPOSE_PROD) up -d --build

.PHONY: prod-down
prod-down: ## Stop prod stack
	$(COMPOSE_PROD) down

.PHONY: prod-logs
prod-logs: ## Tail prod logs
	$(COMPOSE_PROD) logs -f --tail=100

# ---------- Image build & push ----------
REGISTRY ?= ghcr.io/dhaneshpachipulusu
TAG      ?= $(shell git rev-parse --short HEAD)

.PHONY: build
build: ## Build both images locally
	docker build -t $(REGISTRY)/ai-interview-bot-backend:$(TAG)  -f Dockerfile .
	docker build -t $(REGISTRY)/ai-interview-bot-frontend:$(TAG) -f ai-frontend/Dockerfile ai-frontend

.PHONY: push
push: ## Push both images
	docker push $(REGISTRY)/ai-interview-bot-backend:$(TAG)
	docker push $(REGISTRY)/ai-interview-bot-frontend:$(TAG)

# ---------- Kubernetes ----------
.PHONY: k8s-apply
k8s-apply: ## Apply all manifests via kustomize
	kubectl apply -k $(K8S_DIR)

.PHONY: k8s-delete
k8s-delete: ## Delete the namespace (DANGEROUS)
	kubectl delete namespace $(NAMESPACE)

.PHONY: k8s-status
k8s-status: ## Show pods, svc, ingress
	kubectl -n $(NAMESPACE) get pods,svc,ingress,hpa

.PHONY: k8s-logs
k8s-logs: ## Tail backend logs
	kubectl -n $(NAMESPACE) logs -f deploy/backend

.PHONY: k8s-rollout
k8s-rollout: ## Rolling restart of both deployments
	kubectl -n $(NAMESPACE) rollout restart deploy/backend deploy/frontend

# ---------- Quality ----------
.PHONY: scan
scan: ## Trivy scan local images
	trivy image $(REGISTRY)/ai-interview-bot-backend:$(TAG)
	trivy image $(REGISTRY)/ai-interview-bot-frontend:$(TAG)

.PHONY: lint-compose
lint-compose: ## Validate compose files
	$(COMPOSE_DEV)  config -q
	$(COMPOSE_PROD) config -q

# ---------- Monitoring ----------
.PHONY: monitoring-up
monitoring-up: ## Start Prometheus + Grafana + node/cAdvisor
	$(COMPOSE_PROD) -f monitoring/docker-compose.monitoring.yml up -d

.PHONY: monitoring-down
monitoring-down: ## Stop monitoring stack
	$(COMPOSE_PROD) -f monitoring/docker-compose.monitoring.yml down

# ---------- Helm ----------
HELM_RELEASE ?= aibot
HELM_NS      ?= ai-interview-bot

.PHONY: helm-lint
helm-lint: ## Lint the Helm chart
	helm lint helm/ai-interview-bot

.PHONY: helm-template
helm-template: ## Render manifests for review
	helm template $(HELM_RELEASE) helm/ai-interview-bot

.PHONY: helm-install
helm-install: ## Install/upgrade chart
	helm upgrade --install $(HELM_RELEASE) helm/ai-interview-bot \
	  --namespace $(HELM_NS) --create-namespace \
	  --set secrets.GEMINI_API_KEY=$$GEMINI_API_KEY

.PHONY: helm-uninstall
helm-uninstall: ## Uninstall release
	helm uninstall $(HELM_RELEASE) --namespace $(HELM_NS)

# ---------- Terraform ----------
TF_DIR := terraform

.PHONY: tf-init
tf-init: ## terraform init
	cd $(TF_DIR) && terraform init

.PHONY: tf-plan
tf-plan: ## terraform plan
	cd $(TF_DIR) && terraform plan -out=tfplan

.PHONY: tf-apply
tf-apply: ## terraform apply (uses saved plan)
	cd $(TF_DIR) && terraform apply tfplan

.PHONY: tf-destroy
tf-destroy: ## terraform destroy
	cd $(TF_DIR) && terraform destroy

.PHONY: tf-fmt
tf-fmt: ## terraform fmt
	cd $(TF_DIR) && terraform fmt -recursive

.PHONY: tf-validate
tf-validate: ## terraform validate
	cd $(TF_DIR) && terraform validate
