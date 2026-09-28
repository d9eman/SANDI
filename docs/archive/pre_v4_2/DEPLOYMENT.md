# Deployment Guide

## Local team demo

Use `run_demo.bat`, `run_demo.sh`, or Docker Compose. Keep `SANDI_DEMO_MODE=true` and use fictional data.

## Shared web demo

The repository is container-ready. Deploy the Docker image to a platform that supports:

- HTTPS;
- persistent disk or a managed database;
- secret environment variables;
- health checks at `/health`;
- log access;
- backups.

Minimum environment variables:

```text
SANDI_SESSION_SECRET
SANDI_VAULT_KEY
SANDI_STAFF_USERNAME
SANDI_STAFF_PASSWORD
SANDI_PROVIDER_USERNAME
SANDI_PROVIDER_PASSWORD
SANDI_DATA_DIR
```

Generate a vault key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

For a public demo, set the platform to run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers
```

Mount persistent storage at the configured data directory. Without persistence, profiles and referrals disappear on restart.

## Production pilot architecture changes

Before real data:

1. PostgreSQL and schema migrations.
2. Private managed object storage, KMS, malware scanning, retention jobs.
3. Identity provider, individual accounts, MFA, roles/attributes, provider tenancy.
4. HTTPS-only secure cookies and trusted proxy/host configuration.
5. Central audit logging and monitoring.
6. Queue/worker for notifications, retries, imports, and document processing.
7. Secrets manager.
8. Rate limits, abuse controls, backup/restore, incident response.
9. Separate development/test/production environments.

## Reverse proxy

Terminate TLS at a trusted load balancer/reverse proxy. Set `https_only=True` for session cookies in `app/main.py`, configure trusted hosts, and do not expose the vault directory through Nginx or a static-file mount.

## Health check

`GET /health` returns:

```json
{"status":"ok","demo_mode":true}
```
