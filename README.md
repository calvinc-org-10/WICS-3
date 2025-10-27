# WICS-3

Short description
- WICS-3 is a Django-based web application that ingests, processes, and displays event data. It uses Python/Django for the backend, MySQL for persistent storage, and vanilla JavaScript with jQuery for client-side interactions embedded in Django-generated HTML templates.

System overview
- Purpose: WICS-3 provides a pipeline to accept events (API or batch import), run domain-specific processing rules, persist raw and processed records in MySQL, and offer a web UI and REST endpoints for querying and visualizing results.
- Primary users: operators, analysts, and integrators who need a lightweight dashboard and API for event monitoring and alerts.
- Key capabilities:
  - Data ingestion: HTTP endpoints and CSV import for batch uploads.
  - Processing pipeline: Django background tasks (Celery recommended) perform parsing, normalization, enrichment, and rule evaluation.
  - Storage: MySQL stores raw and processed records; Django ORM models are used for persistence.
  - Access layer: Django REST Framework (optional) exposes API endpoints; server-rendered templates provide the UI.
  - Alerts & notifications: rules-based alerting via email or webhooks; Celery tasks dispatch notifications.
  - Front-end: Django templates with JavaScript/jQuery for interactivity (tables, AJAX calls, form handling).

How it works (high-level data flow)
1. Client posts events to API endpoints or uploads CSV via the web UI.
2. Django validates inputs and enqueues processing tasks (Celery/RQ or Django management commands).
3. Workers process events (parse, normalize, enrich) and save raw + processed records to MySQL.
4. The web UI queries the database and displays KPIs, lists, and charts; AJAX endpoints support live updates.
5. When rules trigger, alerts are created and notifications are sent via configured channels.

Architecture (concrete for this repo)
- Backend: Python 3.10+ and Django 4.x (adjust versions as needed).
- Database: MySQL 8.x (configure settings.DATABASES accordingly).
- Task queue: Celery with Redis/RabbitMQ (recommended) or Django-RQ for simpler setups.
- API: Django REST Framework for JSON endpoints (optional but recommended).
- Front-end: Django templates, jQuery for AJAX and DOM manipulation, optionally Chart.js for charts.
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
celery -A project_name worker -l info
```
- Alternatively use Django-Q, django-rq, or management commands depending on the repo.

Front-end (JavaScript/jQuery)
- Place custom JS under static/ and include via template tags. Use AJAX endpoints to fetch data without full page reloads.

Testing
- Run Django's test suite:
```bash
python manage.py test
```
- Or run pytest if the project uses pytest-django:
```bash
pytest
```

Project structure
- README.md — this file
- requirements.txt — Python dependencies
- manage.py — Django management
- project_name/ — Django project settings and urls
- app/ — Django apps (models, views, templates, static)
- static/ — static assets including JavaScript/jQuery
- templates/ — Django templates
- tests/ — test modules

Contributing
- Fork the repo and open a branch with a descriptive name (e.g., feature/add-export).
- Run tests locally and include passing test results with your PR.
- Follow existing code style and include migrations for model changes.

License
- Add a LICENSE file or update this section with the chosen license (e.g., MIT).

Contact
- Maintainer: curtindolph-calvin-10 (GitHub: @curtindolph-calvin-10)
- For questions or issues, open a GitHub Issue in this repository.

Notes / TODO
- Replace project_name and app placeholders with the actual Django project and app names in the repo.
- Add example .env, requirements.txt, and a docker-compose.yml for local development.