# Kubernetes

```
k8s/
  base/                        # Shared manifests — do not deploy directly
    kustomization.yaml
    namespace.yaml
    app/
      configmap.yaml
      secret.yaml
      deployment.yaml
      service.yaml
      ingress.yaml
      hpa.yaml
      pdb.yaml
      network-policy.yaml
    jobs/
      migration.yaml
  overlays/
    dev/                       # 1 replica, lighter resources, debug logging
    staging/                   # 2 replicas, production-like topology
    prod/                      # 3 replicas, full resource envelope
```

## Deploying with Kustomize

```bash
# Preview what will be applied
kubectl kustomize k8s/overlays/prod

# Deploy (migration Job + all app resources)
kubectl apply -k k8s/overlays/prod

# Wait for the migration Job to complete before the Deployment is ready
kubectl wait --for=condition=complete job/fastapi-app-migration \
  -n fastapi-app --timeout=300s
```

Replace `prod` with `dev` or `staging` as needed.

### Pinning the image tag

Each overlay's `kustomization.yaml` contains an `images:` stanza that locks
both the Deployment and the migration Job to the same tag.  Override it in CI
before applying:

```bash
cd k8s/overlays/prod
kustomize edit set image your-registry/fastapi-large-app-template=v1.2.3
kubectl apply -k .
```

Or pass it inline (no file edit required):

```bash
kubectl apply -k k8s/overlays/prod \
  --kustomize-post-build-env IMAGE_TAG=v1.2.3
# Note: inline override requires kustomize ≥ 5.1 with the env transformer.
# The kustomize edit approach above is universally compatible.
```

### Teardown

```bash
kubectl delete namespace fastapi-app
```

## Secrets

`base/app/secret.yaml` contains `CHANGE_ME` placeholders.  **Never commit real
values.**  Supply them one of three ways:

**Imperative create (CI/CD):**

```bash
kubectl create secret generic fastapi-app-secret \
  --namespace fastapi-app \
  --from-literal=POSTGRES_PASSWORD="..." \
  --from-literal=REDIS_PASSWORD="..." \
  --from-literal=JWT_SECRET_KEY="..."
```

**Production:** use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
or [External Secrets Operator](https://external-secrets.io/) to store encrypted
secrets in git and have the operator inject them at apply time.

## Ingress & TLS

`base/app/ingress.yaml` ships with nginx-ingress annotations by default.
For Traefik, comment the nginx block and uncomment the Traefik annotations in
that file.  Certificate issuance is handled by [cert-manager](https://cert-manager.io/)
— install a `ClusterIssuer` named `letsencrypt-prod` before applying.

Each overlay's `configmap.yaml` patch overrides `ALLOWED_HOSTS` and
`CORS_ORIGINS` to match the environment's hostname.

## Architecture notes

**1 worker per pod** — FastAPI is async; the event loop handles concurrency on
a single Gunicorn worker.  Multiple workers would multiply memory and DB
connections with no latency benefit.  HPA adds pods when CPU exceeds 70 %.

**HPA scale-down stabilisation** — `behavior.scaleDown.stabilizationWindowSeconds:
300` prevents flapping by waiting 5 minutes after the last scale event before
removing pods.

**Migration Job** — `backoffLimit: 3` retries on transient failures;
`activeDeadlineSeconds: 300` surfaces stuck migrations instead of hanging
forever.  For Helm, annotate the Job with `"helm.sh/hook": pre-upgrade,pre-install`.
For Argo CD, set `argocd.argoproj.io/sync-wave: "-1"` so it runs before the
Deployment sync wave.

**PgBouncer (optional)** — with many pods each holding a SQLAlchemy connection
pool, open connections to Postgres multiply quickly.  Add a PgBouncer
Deployment as a sidecar or separate service to multiplex connections across
pods.

**Redis HA (optional)** — the template assumes a single Redis instance.  For
production consider [Redis Sentinel](https://redis.io/docs/management/sentinel/)
or a managed service (ElastiCache, Cloud Memorystore) with automatic failover.

## Per-environment summary

| Environment | replicas | HPA min/max | Resources (req/limit)        |
|-------------|----------|-------------|------------------------------|
| dev         | 1        | 1 / 3       | 50m–250m CPU · 128–256Mi RAM |
| staging     | 2        | 2 / 5       | 100m–500m CPU · 256–512Mi RAM |
| prod        | 3        | 3 / 10      | 200m–1000m CPU · 512Mi–1Gi RAM |
