from __future__ import annotations
import argparse
import json
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--api", default="http://backend:8000")
    args = parser.parse_args()
    checks = {}
    for endpoint in ["/api/health", "/api/summary", "/api/species?limit=1", "/api/genes?limit=1", "/api/downloads?limit=1"]:
        try:
            with urllib.request.urlopen(args.api + endpoint, timeout=10) as r:
                checks[endpoint] = r.status
        except Exception as exc:
            checks[endpoint] = str(exc)
    required = [
        args.source / "HABs_Func_db.dmnd",
        args.source / "HABs_FuncDB_id2genemap.txt",
        args.source / "HABDB-AS" / "HABDB-AS-18SrRNA" / "HABs_18S_sequences.fasta",
    ]
    files = {str(p): p.exists() for p in required}
    print(json.dumps({"api": checks, "files": files, "marker_naming": "18SrRNA"}, indent=2))


if __name__ == "__main__":
    main()
