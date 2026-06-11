COMPOSE=docker compose

.PHONY: bootstrap import-data reset-db build-indexes verify-release up down logs

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

bootstrap:
	$(COMPOSE) up -d db redis
	$(COMPOSE) build backend worker
	$(COMPOSE) run --rm backend python scripts/import_data.py --source /dataresource --reset
	$(COMPOSE) up -d backend worker frontend

import-data:
	$(COMPOSE) run --rm backend python scripts/import_data.py --source /dataresource

reset-db:
	$(COMPOSE) run --rm backend python scripts/import_data.py --source /dataresource --reset

build-indexes:
	$(COMPOSE) run --rm worker python scripts/build_indexes.py --source /dataresource

verify-release:
	$(COMPOSE) run --rm backend python scripts/verify_release.py --source /dataresource
