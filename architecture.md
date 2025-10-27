# Architecture — WICS-3

This document describes the architecture, components, and recommended operational practices for WICS-3 (Warehouse Inventory Control System).

Overview
- WICS-3 is a Django-based web application backed by MySQL. The repository contains a primary app/package named `WICS` and supporting apps `userprofiles` and `cMenu`. Heavy domain logic is implemented in a series of processing modules (procs_*.py) and a set of SQL view definitions (WICS/dbVIEWS.sql).

Goals
- Keep web requests fast and responsive by moving heavy processing into background workers.
- Use SQL views to optimize complex/aggregated queries and keep critical lookups in the DB where they are fastest.
- Maintain data correctness and auditability: persist raw input and processed results.
- Make the system horizontally scalable for the worker layer and read-scalable for query-heavy workloads.

High-level components
- Web application (Django)
  - Hosts server-rendered UI (templates) and light-weight JSON endpoints.
  - Responsible for authentication, authorization, form handling, and enqueueing work.
  - Recommended stack: Python 3.10+, Django 4.x.
- Background workers
  - Execute heavy processing (parsing, normalization, enrichment, rule evaluation) implemented in procs_*.py.
  - Recommended: Celery workers with Redis or RabbitMQ as broker; django-rq or Django-Q are valid simpler alternatives.
  - Tasks: import CSV rows, apply business rules, generate alerts, update aggregated tables, send notifications.
- Database (MySQL)
  - Primary persistent store for raw and processed records.
  - Use mysqlclient or PyMySQL adapter via Django DATABASES settings.
  - SQL views are defined in WICS/dbVIEWS.sql and should be maintained alongside schema migrations.
- Static assets and front-end
  - Django templates with vanilla JavaScript and jQuery for DOM interactions and AJAX calls.
  - Static files served by Django in development; in production, serve via CDN or web server (nginx).

Data flow
1. Ingest
   - Web UI or API receives events or CSV files.
   - Django validates/norms input and stores raw records or enqueues tasks.
2. Process
   - Worker picks up tasks and runs domain logic from procs_*.py.
   - Processing may enrich records (lookups, math expressions via mathematical_expressions_parser), detect anomalies and create alerts.
   - Workers persist processed records and create or update aggregates.
3. Present
   - Web UI and AJAX endpoints query MySQL (optionally through SQL views) to render dashboards, lists, and detail pages.
4. Notify
   - When rules trigger, worker tasks create alert objects and dispatch notifications (email, webhook, etc.).

Schema, views and performance
- The repository intentionally uses SQL views (WICS/dbVIEWS.sql) to optimize expensive joins and aggregations. Treat those views as part of the schema and update them when underlying tables change.
- Indexing: ensure commonly-filtered columns (dates, foreign keys, status flags, material identifiers) have appropriate indexes. Reindex after bulk loads if necessary.
- Read replicas: consider adding MySQL read replicas for heavy read dashboards. Route long-running analytical queries to replicas.
- Migrations: use Django migrations for schema changes but coordinate view updates (dbVIEWS.sql) in migrations or a deployment step.

Background processing guidance
- Idempotency: design tasks to be idempotent (use unique keys or upserts) so retries do not duplicate work.
- Batching: process large CSV imports in batches to limit memory and DB transaction sizes.
- Concurrency: tune worker concurrency to avoid overloading MySQL; use connection pooling.
- Monitoring: export worker metrics (task durations, success/failure rates) to a central monitoring system.

Deployment recommendations
- Containerization
  - Build container images for web and worker processes (same image, different entrypoints).
  - Example services for local dev via docker-compose: web, worker, redis (or rabbitmq), mysql, adminer (optional).
- Example docker-compose (snippet)

```yaml
version: '3.8'
services:
  db:
    image: mysql:8
    environment:
      MYSQL_DATABASE: wics3
      MYSQL_USER: wics_user
      MYSQL_PASSWORD: s3cr3t
      MYSQL_ROOT_PASSWORD: rootpw
    volumes:
      - db_data:/var/lib/mysql
    ports:
      - 3306:3306
  redis:
    image: redis:7
  web:
    build: .
    command: gunicorn project.wsgi:application --bind 0.0.0.0:8000
    ports:
      - 8000:8000
    environment:
      - DATABASE_URL=mysql://wics_user:s3cr3t@db:3306/wics3
    depends_on:
      - db
      - redis
  worker:
    build: .
    command: celery -A WICS worker -l info
    depends_on:
      - db
      - redis
volumes:
  db_data:
```

- Secrets: do not store secrets in image or repo; use environment variables or a secrets manager.
- Static assets: in production, collectstatic and serve with nginx or via a CDN.

Observability & operations
- Logging: centralize logs (web + worker) to a log store (ELK/EFK, Datadog, CloudWatch).
- Metrics: export Prometheus metrics for request rates, DB query times, worker queue lengths, and task durations.
- Tracing: add distributed tracing (OpenTelemetry) for long-running flows that traverse web and worker components.
- Backups: schedule regular MySQL backups (logical or physical), test restores, and back up critical SQL views definitions.

Security
- Use HTTPS for all external traffic; terminate TLS at the load balancer or reverse proxy.
- Use Django's security settings (SECURE_SSL_REDIRECT, CSRF_COOKIE_SECURE, SESSION_COOKIE_SECURE, etc.).
- Limit DB privileges for the application user; use a separate read-only user for analytics if possible.
- Keep dependencies up to date and scan for vulnerabilities.

Operational checklist for releases
- Run django migrations.
- Re-apply or update SQL views (WICS/dbVIEWS.sql) after schema changes.
- Run database migrations in off-peak windows if they will lock tables.
- Warm up read replicas (if any) and verify indexes.
- Run smoke tests against staging before promoting to production.

Where to look in the repository
- WICS/ — main app: models.py, views.py, urls.py, procs_*.py, templates/
- WICS/dbVIEWS.sql — SQL view definitions used by the app
- mathematical_expressions_parser/ — expression evaluation used by rules
- userprofiles/ and cMenu/ — supporting apps

Open items / suggestions
- Add architecture diagrams (sequence and deployment diagrams) to docs/ or architecture.md if you want visual aids.
- Add a docker-compose.yml and an example .env to simplify local onboarding.
- Document the most important SQL views (purpose and indexed columns) in a views.md.

---

Generated on 2025-10-27 by GitHub Copilot for curtindolph-calvin-10.
