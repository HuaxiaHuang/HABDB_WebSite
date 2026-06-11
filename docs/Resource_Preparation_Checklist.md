# HABDB-Web-v2 Resource Preparation Checklist

This checklist records which search resources are ready for the v2 Docker Compose workflow.

## Naming Rule

All UI labels, API labels, documentation, and reports should use `18SrRNA`, not the shorter `18S`.

## Functional Gene DIAMOND

| Resource | Expected path in container | Status |
|---|---|---|
| DIAMOND database | `/dataresource/HABs_Func_db.dmnd` | Available from v1 resources |
| ID to gene map | `/dataresource/HABs_FuncDB_id2genemap.txt` | Available from v1 resources |
| Full functional DB | `/dataresource/HABs_FuncDB_Full.database` | Available from v1 resources |

DIAMOND jobs are implemented as real executable jobs in the worker.

## 18SrRNA BLAST

| Resource | Expected path | Status |
|---|---|---|
| 18SrRNA FASTA | `/dataresource/HABDB-AS/HABDB-AS-18SrRNA/HABs_18S_sequences.fasta` | Available |
| BLAST index prefix | `/indexes/18SrRNA/habdb_18SrRNA` | Build with `make build-indexes` |

The API and worker workflow are complete. Once `makeblastdb` creates `.nin/.nhr/.nsq` files, BLASTN jobs can run.

## 18SrRNA Kraken2

| Resource | Expected path | Status |
|---|---|---|
| Kraken2 archive | `/dataresource/HABDB-AS/HABDB-AS-18SrRNA/HABs_Final_Kraken2_db.tar.gz` | Available |
| Extracted Kraken2 DB | `/indexes/kraken2_18SrRNA` | Extract archive manually or in deployment script |

The API and worker workflow are complete. Once the archive is extracted to the expected directory, Kraken2 jobs can run.
