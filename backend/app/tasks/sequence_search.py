from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import SearchJob


def _clean_sequence(raw: str) -> tuple[str, str]:
    name = "query"
    for line in raw.splitlines():
        if line.startswith(">"):
            name = line[1:].strip().split()[0] or "query"
            break
    seq = re.sub(r"^>.*$", "", raw, flags=re.M)
    seq = re.sub(r"[^A-Za-z*.-]", "", seq).upper()
    return name, seq


def _write_fasta(path: Path, name: str, seq: str) -> None:
    path.write_text(f">{name}\n{seq}\n", encoding="utf-8")


def _update(db: Session, job: SearchJob, status: str, message: str = "", hits=None, result_path: str = ""):
    job.status = status
    job.message = message
    job.updated_at = datetime.utcnow()
    if hits is not None:
        job.result_json = json.dumps(hits, ensure_ascii=False)
    if result_path:
        job.result_path = result_path
    db.add(job)
    db.commit()


def run_sequence_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(SearchJob, job_id)
        if not job:
            return
        _update(db, job, "running", "Job started")
        name, seq = _clean_sequence(job.query_sequence)
        job_dir = settings.habdb_job_dir / job.id
        job_dir.mkdir(parents=True, exist_ok=True)
        query_fa = job_dir / "query.fasta"
        result_tsv = job_dir / "result.tsv"
        _write_fasta(query_fa, name, seq)

        mode = (job.mode or "auto").lower()
        if mode in {"auto", "diamond", "functional"}:
            _run_diamond(db, job, query_fa, result_tsv)
        elif mode in {"blast", "blastn", "18srrna"}:
            _run_blastn(db, job, query_fa, result_tsv)
        elif mode == "kraken2":
            _run_kraken2(db, job, query_fa, result_tsv)
        else:
            _update(db, job, "failed", f"Unsupported mode: {job.mode}")
    except Exception as exc:
        job = db.get(SearchJob, job_id)
        if job:
            _update(db, job, "failed", str(exc))
    finally:
        db.close()


def _run_diamond(db: Session, job: SearchJob, query_fa: Path, result_tsv: Path) -> None:
    if not shutil.which(settings.diamond_bin):
        _update(db, job, "failed", f"DIAMOND binary not found: {settings.diamond_bin}")
        return
    if not Path(settings.diamond_db).exists():
        _update(db, job, "failed", f"DIAMOND database not found: {settings.diamond_db}")
        return
    cmd = [
        settings.diamond_bin, "blastx",
        "--db", str(settings.diamond_db),
        "--query", str(query_fa),
        "--out", str(result_tsv),
        "--outfmt", "6", "qseqid", "sseqid", "pident", "length", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore",
        "--max-target-seqs", "25",
        "--threads", "2",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        _update(db, job, "failed", proc.stderr[-2000:])
        return
    hits = _parse_blast6(result_tsv, "DIAMOND blastx")
    job.engine = "DIAMOND blastx"
    _update(db, job, "completed", f"{len(hits)} DIAMOND hits", hits, str(result_tsv))


def _run_blastn(db: Session, job: SearchJob, query_fa: Path, result_tsv: Path) -> None:
    db_prefix = Path(settings.blast_18srrna_db)
    expected = [db_prefix.with_suffix(s) for s in [".nin", ".nhr", ".nsq"]]
    if not shutil.which(settings.blastn_bin):
        _update(db, job, "failed", f"BLASTN binary not found: {settings.blastn_bin}")
        return
    if not any(p.exists() for p in expected):
        _update(db, job, "waiting_for_index", f"18SrRNA BLAST index missing at {db_prefix}. Run make build-indexes after preparing FASTA.")
        return
    cmd = [settings.blastn_bin, "-db", str(db_prefix), "-query", str(query_fa), "-out", str(result_tsv), "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore", "-max_target_seqs", "25"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        _update(db, job, "failed", proc.stderr[-2000:])
        return
    hits = _parse_blast6(result_tsv, "BLASTN 18SrRNA")
    job.engine = "BLASTN 18SrRNA"
    _update(db, job, "completed", f"{len(hits)} BLASTN hits", hits, str(result_tsv))


def _run_kraken2(db: Session, job: SearchJob, query_fa: Path, result_tsv: Path) -> None:
    if not shutil.which(settings.kraken2_bin):
        _update(db, job, "failed", f"Kraken2 binary not found: {settings.kraken2_bin}")
        return
    if not Path(settings.kraken2_db).exists():
        _update(db, job, "waiting_for_index", f"Kraken2 18SrRNA DB missing at {settings.kraken2_db}")
        return
    cmd = [settings.kraken2_bin, "--db", str(settings.kraken2_db), "--output", str(result_tsv), str(query_fa)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        _update(db, job, "failed", proc.stderr[-2000:])
        return
    hits = [{"raw": line} for line in result_tsv.read_text(encoding="utf-8", errors="replace").splitlines()[:25]]
    job.engine = "Kraken2 18SrRNA"
    _update(db, job, "completed", f"{len(hits)} Kraken2 rows", hits, str(result_tsv))


def _parse_blast6(path: Path, engine: str) -> list[dict]:
    cols = ["qseqid", "sseqid", "pident", "length", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore"]
    hits = []
    if not path.exists():
        return hits
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:100]:
        parts = line.split("\t")
        row = dict(zip(cols, parts))
        row["engine"] = engine
        hits.append(row)
    return hits
