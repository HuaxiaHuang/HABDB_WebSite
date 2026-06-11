from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Species(Base):
    __tablename__ = "species"
    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    taxid: Mapped[str] = mapped_column(String(64), default="")
    domain: Mapped[str] = mapped_column(String(120), default="")
    kingdom: Mapped[str] = mapped_column(String(120), default="")
    phylum: Mapped[str] = mapped_column(String(120), default="", index=True)
    class_name: Mapped[str] = mapped_column("class", String(120), default="", index=True)
    order: Mapped[str] = mapped_column(String(120), default="")
    family: Mapped[str] = mapped_column(String(120), default="")
    genus: Mapped[str] = mapped_column(String(120), default="", index=True)
    toxic_status: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    toxin_class: Mapped[str] = mapped_column(String(64), default="unknown", index=True)
    representative_18srrna: Mapped[str] = mapped_column(String(128), default="")
    sequence_status: Mapped[str] = mapped_column(String(128), default="")
    extended_18srrna_count: Mapped[int] = mapped_column(Integer, default=0)
    genome_count: Mapped[int] = mapped_column(Integer, default=0)
    cds_count: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(Text, default="")


class MarkerSequence(Base):
    __tablename__ = "marker_sequence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[str | None] = mapped_column(ForeignKey("species.id"), nullable=True, index=True)
    species_name: Mapped[str] = mapped_column(String(255), index=True)
    marker_type: Mapped[str] = mapped_column(String(64), default="18SrRNA")
    accession: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    length_bp: Mapped[int] = mapped_column(Integer, default=0)
    sequence: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("marker_type", "accession", name="uq_marker_type_accession"),)


class Genome(Base):
    __tablename__ = "genome"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_id: Mapped[str | None] = mapped_column(ForeignKey("species.id"), nullable=True, index=True)
    genome: Mapped[str] = mapped_column(String(255), index=True)
    strain: Mapped[str] = mapped_column(String(255), default="")
    assembly_accession: Mapped[str] = mapped_column(String(128), default="", index=True)
    assembly_level: Mapped[str] = mapped_column(String(128), default="")
    gc_percent: Mapped[str] = mapped_column(String(64), default="")
    scaffold_n50: Mapped[str] = mapped_column(String(64), default="")
    contig_n50: Mapped[str] = mapped_column(String(64), default="")


class GeneFamily(Base):
    __tablename__ = "gene_family"
    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    module: Mapped[str] = mapped_column(String(128), index=True)
    gene_family: Mapped[str] = mapped_column(String(255), index=True)
    annotation: Mapped[str] = mapped_column(Text, default="")
    seed_count: Mapped[int] = mapped_column(Integer, default=0)
    full_count: Mapped[int] = mapped_column(Integer, default=0)
    source_files: Mapped[str] = mapped_column(Text, default="")


class FunctionalSequence(Base):
    __tablename__ = "functional_sequence"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    gene_family_id: Mapped[str | None] = mapped_column(ForeignKey("gene_family.id"), nullable=True, index=True)
    module: Mapped[str] = mapped_column(String(128), index=True)
    gene_family: Mapped[str] = mapped_column(String(255), index=True)
    accession: Mapped[str] = mapped_column(String(255), default="", index=True)
    annotation: Mapped[str] = mapped_column(Text, default="")
    source_database: Mapped[str] = mapped_column(String(255), default="")
    evidence: Mapped[str] = mapped_column(String(128), default="")
    database_layer: Mapped[str] = mapped_column(String(64), default="seed")
    sequence_length: Mapped[int] = mapped_column(Integer, default=0)
    sequence: Mapped[str] = mapped_column(Text, default="")


class DownloadFile(Base):
    __tablename__ = "download_file"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    relative_path: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(128), index=True)
    format: Mapped[str] = mapped_column(String(64), default="")
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum_sha256: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class Statistic(Base):
    __tablename__ = "statistic"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class ReleaseManifest(Base):
    __tablename__ = "release_manifest"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    release: Mapped[str] = mapped_column(String(128), index=True)
    manifest_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SearchJob(Base):
    __tablename__ = "search_job"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    query_name: Mapped[str] = mapped_column(String(255), default="")
    query_sequence: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    result_path: Mapped[str] = mapped_column(Text, default="")
    result_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
