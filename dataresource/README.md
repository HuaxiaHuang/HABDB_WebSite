# dataresource

Place HABDB raw resource files here when deploying without the sibling `../HABDB-Web/dataresource` directory.

This directory is intentionally committed as an empty placeholder. Large data files are ignored by Git.

Expected key files include:

- `HABDB-List.xlsx`
- `HABDB-AS-18SrRNA-plus.xlsx`
- `HABDB-AS-Genomeinfo.xlsx`
- `HABDB-FG-STX-SeedSequence.xlsx`
- `HABDB-FG-DA-SeedSequence.xlsx`
- `HABDB-FG-Bioluminescence-SeedSequence.xlsx`
- `HABs_FuncDB_Full.database`
- `HABs_FuncDB_id2genemap.txt`
- `HABs_Func_db.dmnd`
- `HABDB-AS/HABDB-AS-18SrRNA/HABs_18S_sequences.fasta`
- `HABDB-AS/HABDB-AS-18SrRNA/HABs_Final_Kraken2_db.tar.gz`

User-facing documentation should call the marker `18SrRNA`; historical file paths may still contain `18S`.
