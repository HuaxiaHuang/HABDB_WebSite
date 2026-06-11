# HABDB-Web-v2 Build Notes

v2 was scaffolded as a formal NAR-ready engineering project:

- FastAPI backend
- PostgreSQL schema
- Redis/RQ worker
- Real DIAMOND job path using existing `HABs_Func_db.dmnd`
- BLASTN/Kraken2 18SrRNA workflow prepared with configurable indexes
- React + Vite frontend preserving v1 visual language
- Docker Compose and Makefile commands
- Explicit import command; no automatic large resource scan on ordinary `docker compose up`

The v1 `HABDB-Web` directory is kept as backup and raw resources are mounted read-only.
