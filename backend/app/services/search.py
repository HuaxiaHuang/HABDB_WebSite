from sqlalchemy import or_
from sqlalchemy.orm import Session
from .. import models


def paginate(query, limit: int = 50, offset: int = 0):
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    total = query.count()
    return {"total": total, "limit": limit, "offset": offset, "items": query.offset(offset).limit(limit).all()}


def search_species(db: Session, q: str = "", limit: int = 50, offset: int = 0):
    query = db.query(models.Species)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Species.name.ilike(like), models.Species.genus.ilike(like), models.Species.phylum.ilike(like), models.Species.representative_18srrna.ilike(like)))
    return paginate(query.order_by(models.Species.name), limit, offset)


def search_genes(db: Session, q: str = "", module: str = "", limit: int = 50, offset: int = 0):
    query = db.query(models.GeneFamily)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.GeneFamily.gene_family.ilike(like), models.GeneFamily.annotation.ilike(like), models.GeneFamily.module.ilike(like)))
    if module:
        query = query.filter(models.GeneFamily.module.ilike(f"%{module}%"))
    return paginate(query.order_by(models.GeneFamily.module, models.GeneFamily.gene_family), limit, offset)
