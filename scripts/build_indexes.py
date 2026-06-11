from __future__ import annotations
import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    args = p.parse_args()
    src = args.source
    print("Checking HABDB sequence indexes...")
    diamond_db = src / "HABs_Func_db.dmnd"
    print(f"DIAMOND DB: {diamond_db} -> {'OK' if diamond_db.exists() else 'MISSING'}")
    fasta = src / "HABDB-AS" / "HABDB-AS-18SrRNA" / "HABs_18S_sequences.fasta"
    print(f"18SrRNA FASTA: {fasta} -> {'OK' if fasta.exists() else 'MISSING'}")
    if shutil.which("makeblastdb") and fasta.exists():
        out = Path("/indexes/18SrRNA/habdb_18SrRNA")
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"Building BLAST 18SrRNA index at {out}")
        subprocess.run(["makeblastdb", "-in", str(fasta), "-dbtype", "nucl", "-out", str(out)], check=False)
    else:
        print("BLAST index not built: makeblastdb or FASTA missing.")
    kraken = src / "HABDB-AS" / "HABDB-AS-18SrRNA" / "HABs_Final_Kraken2_db.tar.gz"
    print(f"Kraken2 archive: {kraken} -> {'OK' if kraken.exists() else 'MISSING'}")
    print("If Kraken2 archive is present, extract it to ./indexes/kraken2_18SrRNA before running kraken2 jobs.")


if __name__ == "__main__":
    main()
