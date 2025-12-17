# WICS-3

Short description
- WICS-3 (Warehouse Inventory Control System) is a Django-based web application that ingests, processes, and displays event and operational data for inventory and counting workflows. It uses Python/Django for the backend, MySQL for persistent storage, and vanilla JavaScript with jQuery for client-side interactions embedded in Django-generated HTML templates.

Background & original README notes
- WICS = Warehouse Inventory Control System
- WICS3 is a major rewrite of the original WICS. Goals carried from the original README:
  - Users are not tied to an organization. The org they are in will be the default, but they can switch organizations without logging out and back in.
  - Optimize queries and construct/use SQL views where appropriate to improve performance (see WICS/dbVIEWS.sql).
  - Other goals as outlined in the WICS3 project roadmap.
- WICS uses Semantic Versioning (https://semver.org/).

System overview
- Purpose: WICS-3 provides a pipeline to accept events (API or batch import), run domain-specific processing rules, persist raw and processed records in MySQL, and offer a web UI and REST endpoints for querying and visualizing results.
- Primary users: operators, analysts, and integrators who need a lightweight dashboard and API for inventory monitoring and alerts.
- Core domain objects / tables (from original README and code):
  - Materials
  - Count Schedule
  - Actual Counts
  - SAP table

Key capabilities
- Data ingestion: HTTP endpoints and CSV import for batch uploads.
- Processing pipeline: Django background tasks (Celery recommended) perform parsing, normalization, enrichment, and rule evaluation.
- Storage: MySQL stores raw and processed records; Django ORM models are used for persistence. This repo contains view definitions (WICS/dbVIEWS.sql) used to optimize key queries.
- Access layer: Django server-rendered templates for the UI, and optional Django REST Framework endpoints for programmatic access.
- Alerts & notifications: rules-based alerting via email or webhooks; worker tasks dispatch notifications.
- Front-end: Django templates with jQuery for interactivity (tables, AJAX calls, form handling).

What I inferred from the codebase that improves clarity
- The main functional app is a Django package named `WICS` (it includes models.py, views.py, urls.py and templates). Several large processing modules (e.g., procs_*.py) indicate heavy server-side processing/aggregation logic best offloaded to background workers.
- There are supporting apps for user handling and UI/menuing: `userprofiles` and `cMenu`.
- A mathematical expressions parser is included as a utility library (mathematical_expressions_parser), used for evaluating expressions in rules or calculations.
- dbVIEWS.sql is present and used to create SQL views — the project intentionally uses SQL views to optimize certain domain queries where raw ORM queries would be inefficient.
- Large procedural modules and SQL view usage imply indexing and query tuning are important for performance; consider documenting key views and indexed columns for DB admins.

How it works (high-level data flow)
1. Client posts events to API endpoints or uploads CSV via the web UI.
2. Django validates inputs and enqueues processing tasks (Celery/RQ or management commands).
3. Workers process events (parse, normalize, enrich) and save raw + processed records to MySQL.
4. The web UI queries the database and displays KPIs, lists, and charts; AJAX endpoints support live updates via jQuery.
5. When rules trigger, alerts are created and notifications are sent via configured channels.

Architecture (concrete for this repo)
- Backend: Python 3.10+ and Django 4.x (adjust versions as needed).
- Django project/app layout found in this repo:
  - Main Django package/app: `WICS` (contains models.py, views.py, urls.py, templates/)
  - Additional apps: `userprofiles`, `cMenu`
  - Supporting modules/folders: `django_support`, `mathematical_expressions_parser`, `initdata`
- Database: MySQL 8.x (configure settings.DATABASES accordingly).
- Query performance: The repository includes SQL view definitions (WICS/dbVIEWS.sql) to optimize frequently-run or complex queries — maintain these views and reindex as schema evolves.
- Task queue: Celery with Redis/RabbitMQ (recommended) or Django-RQ for simpler setups; large processing modules suggest asynchronous work is desirable.
- API: Django REST Framework for JSON endpoints (optional but recommended).
- Front-end: Django templates + jQuery for AJAX and DOM manipulation; consider Chart.js for charts.
- Deployment: containerize with Docker and orchestrate with Docker Compose or Kubernetes for production.

Getting started
Prerequisites
- Git
- Python 3.10+ (or project-specific version)
- pip
- MySQL 8+ server running
- Node/npm only if you add front-end build tooling (optional)

Clone and checkout
```bash
git clone https://github.com/calvinc-org-10/WICS-3.git
cd WICS-3
git checkout add-readme
```

Setup (development)
```bash
# create a virtual environment
python -m venv .venv
source .venv/bin/activate

# install Python dependencies
pip install -r requirements.txt

# configure your local settings (example: copy env or settings file)
cp example.env .env
# edit .env or settings/local.py to point DATABASE_URL or DATABASES to your MySQL server

# run migrations
python manage.py migrate

# create a superuser for admin access
python manage.py createsuperuser

# collect static files (for production or when DEBUG=False)
python manage.py collectstatic --noinput

# run the development server
python manage.py runserver
```

Database notes
- Configure DATABASES in settings.py to use mysqlclient or PyMySQL. Example (using mysqlclient):

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wics3',
        'USER': 'wics_user',
        'PASSWORD': 's3cr3t',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

- Ensure the MySQL user has appropriate privileges and that utf8mb4 is used for character set.

Running background workers
- Celery example:
```bash
celery -A WICS worker -l info
```
- Alternatively use Django-Q, django-rq, or management commands depending on the repo.

Front-end (JavaScript/jQuery)
- Place custom JS under the repository's static/ directories (static files are typically found under app static/ folders). Include scripts via template tags:
```django
{% load static %}
<script src="{% static 'your_app/js/yourfile.js' %}"></script>
```
- Use jQuery-backed AJAX endpoints in views to support partial updates and interactive tables.

Testing
- Run Django's test suite:
```bash
python manage.py test
```
- Or run pytest if the project uses pytest-django:
```bash
pytest
```

Project structure (based on repository contents)
- README.md — this file
- WICS/ — main Django app/project (models.py, views.py, urls.py, templates/, procs_*.py, dbVIEWS.sql)
- userprofiles/ — user profile app
- cMenu/ — menu or UI-related app
- templates/ — top-level templates directory used by Django
- static/ — static assets (JS, CSS, images)
- initdata/ — initial data / fixtures
- django_support/ — supporting code and utilities
- mathematical_expressions_parser/ — domain-specific parser library
- requirements.txt — Python dependencies (add if missing)
- devnotes-log.txt — development notes and changelog

Contributing
- Fork the repo and open a branch with a descriptive name (e.g., `feature/add-export`).
- Run tests locally and include passing test results with your PR.
- Follow existing code style and include migrations for model changes.
- Document any schema changes that require updating WICS/dbVIEWS.sql.

License
- Add a LICENSE file or update this section with the chosen license (e.g., MIT).

Contact
- Maintainer: curtindolph-calvin-10 (GitHub: @curtindolph-calvin-10)
- For questions or issues, open a GitHub Issue in this repository.

Notes / TODO
- Replace project_name and app placeholders (if present elsewhere) with the actual Django project and app names used in the repo (`WICS`, `userprofiles`, `cMenu`).
- Add example .env, requirements.txt (if missing), and a docker-compose.yml for local development (MySQL + Redis/RabbitMQ + web worker).
- Add documentation for the most important SQL views (explain what they optimize and their indexed columns).
- Consider adding a small diagram or architecture.md showing data flow and where procs_*.py modules run (web / worker).