# Kubernetes

```
k8s/
  namespace.yaml
  app/
    configmap.yaml
    secret.yaml
    deployment.yaml
    service.yaml
    hpa.yaml
    pdb.yaml
  jobs/
    migration.yaml
```

## Apply Order

The migration Job must complete before the Deployment starts, as the app checks DB connectivity on startup.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/app/configmap.yaml
kubectl apply -f k8s/app/secret.yaml
kubectl apply -f k8s/jobs/migration.yaml
kubectl wait --for=condition=complete job/fastapi-app-migration -n fastapi-app --timeout=120s
kubectl apply -f k8s/app/deployment.yaml
kubectl apply -f k8s/app/service.yaml
kubectl apply -f k8s/app/hpa.yaml
kubectl apply -f k8s/app/pdb.yaml
```

Teardown:

```bash
kubectl delete namespace fastapi-app
```

## Secrets

`secret.yaml` contains `CHANGE_ME` placeholders. Replace before applying.

**Edit directly (dev only — never commit real values):**

```bash
kubectl apply -f k8s/app/secret.yaml
```

**Imperative create (CI/CD):**

```bash
kubectl create secret generic fastapi-app-secret \
  --namespace fastapi-app \
  --from-literal=POSTGRES_PASSWORD="..." \
  --from-literal=REDIS_PASSWORD="..." \
  --from-literal=JWT_SECRET_KEY="..." \
  --from-literal=JWT_REFRESH_SECRET_KEY="..." \
  --from-literal=DATABASE_URL="postgresql+asyncpg://postgres:...@postgres:5432/mydb" \
  --from-literal=REDIS_URL="redis://:...@redis:6379/0"
```

**Production:** use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) or [External Secrets Operator](https://external-secrets.io/).

## 1 Worker Per Pod

FastAPI is async — the event loop handles concurrency on a single worker. Multiple workers would multiply memory and DB connections with no latency benefit. HPA adds pods when CPU exceeds 70%.

`--graceful-timeout 45` is less than `terminationGracePeriodSeconds: 60` so in-flight requests finish before the pod is force-killed.

## Overriding Resources Per Environment

Use a Kustomize patch or Helm values to override without editing base manifests.

```yaml
# Example: k8s/overlays/prod/deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: fastapi-app
spec:
  template:
    spec:
      containers:
        - name: fastapi-app
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
```

| Environment | minReplicas | maxReplicas | targetCPU |
|-------------|-------------|-------------|-----------|
| dev         | 1           | 3           | 80%       |
| staging     | 2           | 5           | 70%       |
| production  | 2           | 10          | 70%       |
