from __future__ import annotations

import json
import uuid
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from redis import Redis
from rq import Queue
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from . import models, schemas
from .services.search import search_species, search_genes
from .tasks.sequence_search import run_sequence_job


Base.metadata.create_all(bind=engine)

app = FastAPI(title="HABDB v2 API", version="2.0-dev")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def asdict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


@app.get("/api/health")
def health():
    return {"status": "ok", "release": settings.habdb_release}


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    stats = {s.key: s.value for s in db.query(models.Statistic).all()}
    if not stats:
        stats = {
            "species_count": str(db.query(models.Species).count()),
            "gene_family_count": str(db.query(models.GeneFamily).count()),
            "download_file_count": str(db.query(models.DownloadFile).count()),
        }
    stats["release"] = settings.habdb_release
    stats["marker_label"] = "18SrRNA"
    return stats


@app.get("/api/species")
def species(q: str = "", limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    page = search_species(db, q, limit, offset)
    page["items"] = [asdict(x) for x in page["items"]]
    return page


@app.get("/api/species/{species_id}")
def species_detail(species_id: str, db: Session = Depends(get_db)):
    item = db.get(models.Species, species_id)
    if not item:
        raise HTTPException(404, "species not found")
    data = asdict(item)
    data["markers"] = [asdict(x) for x in db.query(models.MarkerSequence).filter(models.MarkerSequence.species_id == species_id).limit(200).all()]
    data["genomes"] = [asdict(x) for x in db.query(models.Genome).filter(models.Genome.species_id == species_id).all()]
    return data


@app.get("/api/genes")
def genes(q: str = "", module: str = "", limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    page = search_genes(db, q, module, limit, offset)
    page["items"] = [asdict(x) for x in page["items"]]
    return page


@app.get("/api/downloads")
def downloads(q: str = "", limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    query = db.query(models.DownloadFile)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.DownloadFile.name.ilike(like), models.DownloadFile.category.ilike(like), models.DownloadFile.description.ilike(like)))
    total = query.count()
    items = query.order_by(models.DownloadFile.category, models.DownloadFile.name).offset(offset).limit(min(limit, 500)).all()
    return {"total": total, "limit": limit, "offset": offset, "items": [asdict(x) | {"download_url": f"/api/downloads/{x.id}/file"} for x in items]}


@app.get("/api/downloads/{file_id}/file")
def download_file(file_id: str, db: Session = Depends(get_db)):
    item = db.get(models.DownloadFile, file_id)
    if not item:
        raise HTTPException(404, "download file not found")
    target = (settings.habdb_dataresource / item.relative_path).resolve()
    root = settings.habdb_dataresource.resolve()
    try:
        target.relative_to(root)
    except Exception:
        raise HTTPException(400, "invalid path")
    if not target.exists():
        raise HTTPException(404, "file missing on server")
    return FileResponse(target, filename=item.name)


@app.get("/api/search")
def search(q: str, db: Session = Depends(get_db)):
    species_items = search_species(db, q, 10, 0)["items"]
    gene_items = search_genes(db, q, "", 10, 0)["items"]
    downloads_q = db.query(models.DownloadFile).filter(models.DownloadFile.name.ilike(f"%{q}%")).limit(10).all()
    return {
        "query": q,
        "results": [{"type": "species", "item": asdict(x)} for x in species_items]
        + [{"type": "gene_family", "item": asdict(x)} for x in gene_items]
        + [{"type": "download", "item": asdict(x)} for x in downloads_q],
    }


@app.post("/api/jobs/sequence", response_model=schemas.JobOut)
def create_sequence_job(payload: schemas.SequenceJobCreate, db: Session = Depends(get_db)):
    job_id = uuid.uuid4().hex
    job = models.SearchJob(id=job_id, mode=payload.mode, status="queued", query_name=payload.query_name, query_sequence=payload.sequence)
    db.add(job)
    db.commit()
    queue = Queue("habdb-jobs", connection=Redis.from_url(settings.redis_url))
    queue.enqueue(run_sequence_job, job_id, job_timeout=3600)
    return schemas.JobOut(id=job.id, mode=job.mode, status=job.status, engine=job.engine, message=job.message, hits=[])


@app.get("/api/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(models.SearchJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    hits = json.loads(job.result_json or "[]")
    url = f"/api/jobs/{job.id}/download" if job.result_path else None
    return schemas.JobOut(id=job.id, mode=job.mode, status=job.status, engine=job.engine, message=job.message, result_download_url=url, hits=hits)


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(models.SearchJob, job_id)
    if not job or not job.result_path:
        raise HTTPException(404, "job result not found")
    path = Path(job.result_path)
    if not path.exists():
        raise HTTPException(404, "result file missing")
    return FileResponse(path, filename=f"{job.id}_result.tsv")
