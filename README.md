# HABDB WebSite v2

HABDB-Web-v2 is a formal, deployable engineering version of the **HABDB: Harmful Algal Bloom Database** website, targeting NAR Database Issue readiness.

It upgrades the earlier static/local prototype into a containerized database website with:

- **FastAPI** backend API
- **PostgreSQL** relational database
- **Redis + RQ** asynchronous job queue
- **React + Vite** frontend
- **Docker Compose** deployment
- Explicit data import and release verification commands
- Real DIAMOND job workflow using existing HABDB functional gene resources
- Prepared BLASTN / Kraken2 workflow for `18SrRNA` search once indexes are available

> Naming rule: all user-facing labels and documentation use **18SrRNA**. Historical raw file names may still contain `18S` because they are original resource paths.

---

## 1. Repository Layout

```text
HABDB-Web-v2/
  backend/
    app/
      main.py                  # FastAPI app and API routes
      models.py                # SQLAlchemy PostgreSQL schema
      config.py                # Environment-driven settings
      database.py              # DB engine/session
      tasks/sequence_search.py # DIAMOND / BLASTN / Kraken2 worker jobs
    data/
  frontend/
    src/App.jsx                # React UI
    src/styles.css             # v1-consistent visual style
    Dockerfile
    package.json
  scripts/
    import_data.py             # Explicit HABDB resource import
    build_indexes.py           # Check/build DIAMOND/BLAST/Kraken2 indexes
    verify_release.py          # Release/API/resource verification
  docker/postgres/init.sql
  docs/
    Resource_Preparation_Checklist.md
  Log/
    Run guide and implementation reports
  docker-compose.yml
  Makefile
  .env.example
```

---

## 2. Important Data Policy

The raw HABDB resources are **not committed to GitHub**.

The expected local resource directory is:

```text
../HABDB-Web/dataresource
```

Docker Compose mounts it read-only into containers as:

```text
/dataresource
```

This avoids committing large resources such as:

- `.dmnd`
- FASTA/FNA/GBFF files
- Kraken2 archives
- genome archives
- large release bundles

If your resource directory is elsewhere, update the volume path in `docker-compose.yml` and `HABDB_DATARESOURCE` in `.env`.

This repository also includes an empty `dataresource/` placeholder. For standalone deployment, you may copy the real HABDB resource files into that directory and change the Docker Compose volume from `../HABDB-Web/dataresource:/dataresource:ro` to `./dataresource:/dataresource:ro`.

---

## 3. Requirements

Install:

- Docker Desktop
- Docker Compose, included with modern Docker Desktop
- Optional: `make`

If `make` is unavailable on Windows, use the equivalent `docker compose ...` commands shown below.

---

## 4. First-Time Setup

Open PowerShell in the project directory:

```powershell
cd "I:\论文\赤潮\文章\数据库文章\openclaw\codex\NAR\WebSite\HABDB-Web-v2"
```

Create local environment config:

```powershell
copy .env.example .env
```

Start PostgreSQL and Redis:

```powershell
docker compose up -d db redis
```

Build backend and worker images:

```powershell
docker compose build backend worker
```

Import HABDB resources into PostgreSQL:

```powershell
docker compose run --rm backend python scripts/import_data.py --source /dataresource --reset
```

Start all services:

```powershell
docker compose up -d backend worker frontend
```

Open:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- OpenAPI docs: <http://localhost:8000/docs>

---

## 5. Make Commands

If `make` is available:

```powershell
make bootstrap
```

Equivalent to:

1. Start database and Redis
2. Build backend and worker
3. Import data
4. Start backend, worker, and frontend

Other commands:

```powershell
make import-data      # Explicit import without ordinary startup
make reset-db         # Reset and rebuild database
make build-indexes    # Check/build DIAMOND, BLASTN 18SrRNA and Kraken2 resources
make verify-release   # Verify API, resource availability and release consistency
make logs             # Follow service logs
make down             # Stop services
```

---

## 6. Service URLs

| Service | URL |
|---|---|
| Frontend | <http://localhost:5173> |
| FastAPI backend | <http://localhost:8000> |
| OpenAPI docs | <http://localhost:8000/docs> |
| Health check | <http://localhost:8000/api/health> |
| Summary | <http://localhost:8000/api/summary> |

---

## 7. API Overview

Core endpoints:

```text
GET  /api/health
GET  /api/summary
GET  /api/species?q=&limit=&offset=
GET  /api/species/{species_id}
GET  /api/genes?q=&module=&limit=&offset=
GET  /api/downloads?q=&limit=&offset=
GET  /api/downloads/{file_id}/file
GET  /api/search?q=
POST /api/jobs/sequence
GET  /api/jobs/{job_id}
GET  /api/jobs/{job_id}/download
```

Sequence job example:

```bash
curl -X POST http://localhost:8000/api/jobs/sequence \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"diamond\",\"query_name\":\"test\",\"sequence\":\">q\nACCTGGTTGATCCTGCCAGTAGTCATATGCTTGTCTCAAAGATTAAGCCATGCATGTCTAAGTATAA\"}"
```

---

## 8. Sequence Search Workflow

The v2 workflow is not a UI mock. It uses real job objects:

```text
Frontend FASTA input
  -> FastAPI creates search_job
  -> Redis/RQ queues job
  -> Worker runs DIAMOND / BLASTN / Kraken2
  -> Result TSV is written to backend/data/jobs
  -> API returns job status and result table
  -> Frontend displays hits and download link
```

### DIAMOND

DIAMOND is the first real integrated search path.

Expected database:

```text
/dataresource/HABs_Func_db.dmnd
```

Related resources:

```text
/dataresource/HABs_FuncDB_id2genemap.txt
/dataresource/HABs_FuncDB_Full.database
```

### BLASTN 18SrRNA

Workflow and API are implemented. The BLAST database prefix is:

```text
/indexes/18SrRNA/habdb_18SrRNA
```

Build/check indexes with:

```powershell
make build-indexes
```

or:

```powershell
docker compose run --rm worker python scripts/build_indexes.py --source /dataresource
```

### Kraken2 18SrRNA

Workflow and API are implemented. Expected extracted database:

```text
/indexes/kraken2_18SrRNA
```

If the Kraken2 database is missing, jobs return `waiting_for_index` with the missing path instead of fake results.

---

## 9. Database Import Design

Ordinary startup does **not** scan large resources.

Use explicit import:

```powershell
make import-data
```

or:

```powershell
docker compose run --rm backend python scripts/import_data.py --source /dataresource
```

Reset and rebuild:

```powershell
make reset-db
```

The importer:

- Creates/updates PostgreSQL schema
- Reads Excel metadata and sequence metadata
- Generates stable HABDB IDs
- Imports species, marker sequence, genome, gene family, functional sequence and download file tables
- Generates statistics cache
- Generates release manifest
- Checks checksums
- Avoids accidental duplicate import unless `--reset` is used

---

## 10. Troubleshooting

Check running services:

```powershell
docker compose ps
```

Read logs:

```powershell
docker compose logs backend --tail=100
docker compose logs worker --tail=100
docker compose logs frontend --tail=100
```

Common issues:

| Problem | Likely cause | Fix |
|---|---|---|
| `docker` not found | Docker Desktop not installed/running | Install/start Docker Desktop |
| Frontend not opening | frontend service failed | Check `docker compose logs frontend` |
| Backend not opening | db not ready or backend failed | Check `docker compose logs backend` |
| Import failed | resource mount path incorrect | Verify `../HABDB-Web/dataresource:/dataresource:ro` |
| DIAMOND job failed | `.dmnd` missing or DIAMOND unavailable | Check `/dataresource/HABs_Func_db.dmnd` and worker logs |
| BLASTN job waiting | 18SrRNA BLAST index missing | Run `make build-indexes` |
| Kraken2 job waiting | Kraken2 DB not extracted | Extract DB to `indexes/kraken2_18SrRNA` |

---

## 11. NAR-Readiness Notes

This v2 engineering version supports:

- Browseable species and taxonomy data
- 18SrRNA marker naming and workflow
- Functional gene browser
- Downloads with checksums
- API documentation
- Sequence search job workflow
- Explicit data import and verification
- Dockerized deployment

For a public NAR submission deployment, add:

- Stable HTTPS domain
- Nginx reverse proxy
- Large-file download proxy or object storage
- Database backup
- Monitoring
- Citation / DOI / License / Contact pages
- Release archive and checksum manifest

---

## 12. License

Add the final project license before public publication. Recommended options for database resources include CC BY 4.0 or CC BY-NC 4.0 depending on the intended reuse policy.
