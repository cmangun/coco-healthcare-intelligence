# CoCo Azure Deployment Guide

## Overview

This guide covers deploying CoCo to Azure Kubernetes Service (AKS) with HIPAA-compliant configuration. Azure is the recommended cloud provider for healthcare workloads due to its comprehensive compliance certifications and healthcare-specific services.

## Prerequisites

- Azure subscription with Owner or Contributor role
- Azure CLI installed and authenticated
- kubectl installed
- Helm 3.x installed
- Docker installed (for building images)

## Architecture on Azure

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              Azure Region                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │  Azure Front    │                                                       │
│   │     Door        │  ◄── WAF, DDoS Protection                            │
│   └────────┬────────┘                                                       │
│            │                                                                │
│   ┌────────▼────────────────────────────────────────────────────────────┐  │
│   │                    Virtual Network (10.0.0.0/16)                     │  │
│   │                                                                      │  │
│   │   ┌──────────────────────────────────────────────────────────────┐  │  │
│   │   │              AKS Cluster (System Node Pool)                   │  │  │
│   │   │                                                               │  │  │
│   │   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │  │  │
│   │   │   │CoCo API │  │CoCo API │  │CoCo API │  │ Ingress │        │  │  │
│   │   │   │  Pod 1  │  │  Pod 2  │  │  Pod 3  │  │Controller│        │  │  │
│   │   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘        │  │  │
│   │   │                                                               │  │  │
│   │   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │  │  │
│   │   │   │Prometheus│  │ Grafana │  │ MLflow  │  │  Feast  │        │  │  │
│   │   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘        │  │  │
│   │   │                                                               │  │  │
│   │   └──────────────────────────────────────────────────────────────┘  │  │
│   │                                                                      │  │
│   │   ┌──────────────────────────────────────────────────────────────┐  │  │
│   │   │                   Data Subnet (10.0.2.0/24)                   │  │  │
│   │   │                                                               │  │  │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │  │
│   │   │   │Azure DB for │  │   Azure     │  │   Azure     │          │  │  │
│   │   │   │ PostgreSQL  │  │   Redis     │  │  Storage    │          │  │  │
│   │   │   │ (Flexible)  │  │   Cache     │  │  (Blob)     │          │  │  │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘          │  │  │
│   │   │                                                               │  │  │
│   │   └──────────────────────────────────────────────────────────────┘  │  │
│   │                                                                      │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│   │    Azure ML     │  │ Azure Cognitive │  │    Azure        │           │
│   │   Workspace     │  │    Search       │  │    Monitor      │           │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐                                 │
│   │   Key Vault     │  │  Azure Policy   │  ◄── HIPAA Compliance          │
│   └─────────────────┘  └─────────────────┘                                 │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

## Step 1: Azure Resource Group and Network

```bash
# Set variables
export RESOURCE_GROUP="coco-healthcare-rg"
export LOCATION="eastus"
export VNET_NAME="coco-vnet"
export AKS_SUBNET="coco-aks-subnet"
export DATA_SUBNET="coco-data-subnet"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags "Environment=Production" "Application=CoCo" "Compliance=HIPAA"

# Create virtual network
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --address-prefix 10.0.0.0/16 \
  --subnet-name $AKS_SUBNET \
  --subnet-prefix 10.0.1.0/24

# Create data subnet
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $DATA_SUBNET \
  --address-prefix 10.0.2.0/24 \
  --service-endpoints Microsoft.Storage Microsoft.Sql Microsoft.KeyVault
```

## Step 2: AKS Cluster with HIPAA Configuration

```bash
# Get subnet ID
AKS_SUBNET_ID=$(az network vnet subnet show \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name $AKS_SUBNET \
  --query id -o tsv)

# Create AKS cluster with HIPAA-compliant settings
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name coco-aks \
  --location $LOCATION \
  --kubernetes-version 1.28 \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --network-plugin azure \
  --vnet-subnet-id $AKS_SUBNET_ID \
  --docker-bridge-address 172.17.0.1/16 \
  --dns-service-ip 10.0.0.10 \
  --service-cidr 10.0.0.0/16 \
  --enable-managed-identity \
  --enable-azure-rbac \
  --enable-defender \
  --enable-private-cluster \
  --enable-encryption-at-host \
  --enable-azure-policy \
  --generate-ssh-keys \
  --tags "Compliance=HIPAA" "Application=CoCo"

# Get credentials
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name coco-aks
```

## Step 3: Azure Database for PostgreSQL

```bash
# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name coco-postgres \
  --location $LOCATION \
  --admin-user cocoadmin \
  --admin-password $(openssl rand -base64 32) \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15 \
  --high-availability ZoneRedundant \
  --vnet $VNET_NAME \
  --subnet $DATA_SUBNET \
  --private-dns-zone coco-postgres.private.postgres.database.azure.com

# Create databases
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name coco-postgres \
  --database-name coco

az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name coco-postgres \
  --database-name mlflow
```

## Step 4: Azure Cache for Redis

```bash
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name coco-redis \
  --location $LOCATION \
  --sku Premium \
  --vm-size P1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2 \
  --subnet-id $(az network vnet subnet show \
    --resource-group $RESOURCE_GROUP \
    --vnet-name $VNET_NAME \
    --name $DATA_SUBNET \
    --query id -o tsv)
```

## Step 5: Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name coco-keyvault \
  --location $LOCATION \
  --enable-rbac-authorization true \
  --enable-purge-protection true \
  --retention-days 90

# Store secrets
az keyvault secret set \
  --vault-name coco-keyvault \
  --name postgres-connection-string \
  --value "postgresql://cocoadmin:PASSWORD@coco-postgres.postgres.database.azure.com:5432/coco?sslmode=require"

az keyvault secret set \
  --vault-name coco-keyvault \
  --name openai-api-key \
  --value "YOUR_OPENAI_API_KEY"
```

## Step 6: Azure Cognitive Search (for RAG)

```bash
az search service create \
  --resource-group $RESOURCE_GROUP \
  --name coco-search \
  --location $LOCATION \
  --sku standard \
  --partition-count 1 \
  --replica-count 2
```

## Step 7: Azure ML Workspace

```bash
# Create Azure ML workspace
az ml workspace create \
  --resource-group $RESOURCE_GROUP \
  --name coco-ml-workspace \
  --location $LOCATION \
  --storage-account coco-storage \
  --key-vault coco-keyvault

# Register model endpoint
az ml online-endpoint create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name coco-ml-workspace \
  --name readmission-endpoint \
  --auth-mode key
```

## Step 8: Deploy CoCo to AKS

### Build and Push Container Image

```bash
# Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name cocoacr \
  --sku Premium \
  --admin-enabled false

# Attach ACR to AKS
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name coco-aks \
  --attach-acr cocoacr

# Build and push image
az acr build \
  --registry cocoacr \
  --image coco-api:v1.0.0 \
  --file Dockerfile .
```

### Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coco-api
  namespace: coco
  labels:
    app: coco-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: coco-api
  template:
    metadata:
      labels:
        app: coco-api
    spec:
      serviceAccountName: coco-sa
      containers:
      - name: coco-api
        image: cocoacr.azurecr.io/coco-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: coco-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: coco-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: coco-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: coco-api
  namespace: coco
spec:
  selector:
    app: coco-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: coco-ingress
  namespace: coco
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - coco-api.yourdomain.com
    secretName: coco-tls
  rules:
  - host: coco-api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: coco-api
            port:
              number: 80
```

### Deploy to AKS

```bash
# Create namespace
kubectl create namespace coco

# Apply secrets from Key Vault (using CSI driver)
kubectl apply -f k8s/secrets-provider.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Verify deployment
kubectl get pods -n coco
kubectl get services -n coco
```

## Step 9: Azure Monitor and Alerts

```bash
# Enable Container Insights
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name coco-aks \
  --addons monitoring

# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name coco-logs

# Create alert for high error rate
az monitor metrics alert create \
  --resource-group $RESOURCE_GROUP \
  --name coco-error-alert \
  --scopes "/subscriptions/YOUR_SUB/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerService/managedClusters/coco-aks" \
  --condition "avg requests/failed > 10" \
  --description "CoCo API error rate exceeds threshold"
```

## Step 10: HIPAA Compliance Verification

```bash
# Apply Azure Policy for HIPAA
az policy assignment create \
  --name 'HIPAA-HITRUST-CoCo' \
  --display-name 'HIPAA HITRUST for CoCo' \
  --scope "/subscriptions/YOUR_SUB/resourceGroups/$RESOURCE_GROUP" \
  --policy-set-definition 'a169a624-5599-4385-a696-c8d643089fab'

# Verify compliance status
az policy state list \
  --resource-group $RESOURCE_GROUP \
  --query "[?complianceState=='NonCompliant']"
```

## Maintenance

### Backup Strategy

```bash
# Enable automated backups for PostgreSQL
az postgres flexible-server update \
  --resource-group $RESOURCE_GROUP \
  --name coco-postgres \
  --backup-retention 35

# Create manual backup
az postgres flexible-server backup create \
  --resource-group $RESOURCE_GROUP \
  --server-name coco-postgres \
  --backup-name manual-backup-$(date +%Y%m%d)
```

### Scaling

```bash
# Scale AKS nodes
az aks scale \
  --resource-group $RESOURCE_GROUP \
  --name coco-aks \
  --node-count 5

# Scale deployment
kubectl scale deployment coco-api --replicas=5 -n coco
```

## Cost Estimation

| Service | SKU | Monthly Cost (Est.) |
|---------|-----|---------------------|
| AKS (3 nodes) | Standard_D4s_v3 | $438 |
| PostgreSQL | Standard_D2s_v3 | $196 |
| Redis | Premium P1 | $219 |
| Cognitive Search | Standard | $250 |
| Azure ML | Pay-as-you-go | ~$100 |
| Storage | Hot tier | ~$50 |
| **Total** | | **~$1,253/month** |

*Costs vary by region and usage. Enable cost management alerts.*
