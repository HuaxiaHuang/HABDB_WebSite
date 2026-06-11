from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    habdb_release: str = "HABDB v2.0-dev"
    database_url: str = "postgresql+psycopg://habdb:habdb@localhost:5432/habdb"
    redis_url: str = "redis://localhost:6379/0"
    habdb_dataresource: Path = Path("../HABDB-Web/dataresource")
    habdb_job_dir: Path = Path("backend/data/jobs")
    diamond_bin: str = "diamond"
    diamond_db: Path = Path("../HABDB-Web/dataresource/HABs_Func_db.dmnd")
    blastn_bin: str = "blastn"
    blast_18srrna_db: Path = Path("indexes/18SrRNA/habdb_18SrRNA")
    kraken2_bin: str = "kraken2"
    kraken2_db: Path = Path("indexes/kraken2_18SrRNA")


settings = Settings()
