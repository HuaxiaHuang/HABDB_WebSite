import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Database, Download, FlaskConical, Search, Play, RefreshCw } from 'lucide-react';
import './styles.css';

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function getJSON(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function Stat({ label, value }) {
  return <div className="stat"><strong>{Number(value || 0).toLocaleString()}</strong><span>{label}</span></div>;
}

function App() {
  const [summary, setSummary] = useState({});
  const [species, setSpecies] = useState([]);
  const [genes, setGenes] = useState([]);
  const [downloads, setDownloads] = useState([]);
  const [q, setQ] = useState('');
  const [sequence, setSequence] = useState('>example_18SrRNA_query\nACCTGGTTGATCCTGCCAGTAGTCATATGCTTGTCTCAAAGATTAAGCCATGCATGTCTAAGTATAA');
  const [mode, setMode] = useState('diamond');
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      getJSON('/api/summary'),
      getJSON('/api/species?limit=100'),
      getJSON('/api/genes?limit=100'),
      getJSON('/api/downloads?limit=100')
    ]).then(([s, sp, g, d]) => {
      setSummary(s); setSpecies(sp.items || []); setGenes(g.items || []); setDownloads(d.items || []);
    });
  }, []);

  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return;
    const timer = setInterval(async () => setJob(await getJSON(`/api/jobs/${job.id}`)), 2000);
    return () => clearInterval(timer);
  }, [job]);

  const filteredSpecies = useMemo(() => species.filter(s => `${s.name} ${s.phylum} ${s.genus} ${s.representative_18srrna}`.toLowerCase().includes(q.toLowerCase())), [species, q]);
  const filteredGenes = useMemo(() => genes.filter(g => `${g.module} ${g.gene_family} ${g.annotation}`.toLowerCase().includes(q.toLowerCase())), [genes, q]);

  async function submitJob() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/jobs/sequence`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sequence, mode, query_name: 'web_query' }) });
      setJob(await res.json());
    } finally {
      setLoading(false);
    }
  }

  return <div>
    <header className="site-header">
      <a className="brand" href="#home"><span className="brand-mark">H</span><span><strong>HABDB v2</strong><small>NAR-ready database engineering build</small></span></a>
      <nav><a href="#species">Species</a><a href="#genes">Functional Genes</a><a href="#tools">Tools</a><a href="#downloads">Downloads</a><a href={`${API}/docs`}>OpenAPI</a></nav>
    </header>

    <main>
      <section id="home" className="hero section-band">
        <div className="hero-copy">
          <p className="eyebrow">PostgreSQL · FastAPI · React · Docker Compose</p>
          <h1>HABDB: Harmful Algal Bloom Database</h1>
          <p className="lead">Curated taxonomic, 18SrRNA marker, genome, CDS and HAB-related functional gene references for aquatic metagenomics.</p>
          <div className="hero-actions"><a className="button primary" href="#tools"><Play size={16}/> Run sequence search</a><a className="button" href="#downloads"><Download size={16}/> Download release</a></div>
        </div>
        <div className="graphical-abstract"><div className="flow-node cyan">HAB taxa</div><div className="flow-link"></div><div className="flow-node green">18SrRNA / genomes / CDS</div><div className="flow-link"></div><div className="flow-node amber">DIAMOND / BLAST / Kraken2</div><div className="flow-link"></div><div className="flow-node violet">Metagenomic annotation</div></div>
      </section>

      <section className="stats-row">
        <Stat label="Species" value={summary.species_count}/>
        <Stat label="18SrRNA markers" value={summary.marker_18srrna_count}/>
        <Stat label="Genome assemblies" value={summary.genome_assemblies}/>
        <Stat label="Gene families" value={summary.gene_family_count}/>
        <Stat label="Seed FG sequences" value={summary.functional_sequence_seed_count}/>
        <Stat label="Downloads" value={summary.download_file_count}/>
      </section>

      <section className="section-grid">
        <div className="panel wide panel-head">
          <div><p className="eyebrow">Global filter</p><h2>Browse HABDB v2</h2></div>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Alexandrium, sxtA, 18SrRNA accession, DIAMOND" />
        </div>
      </section>

      <section id="species" className="section-grid">
        <div className="panel wide"><p className="eyebrow">Species Browser</p><h2>Species and 18SrRNA marker coverage</h2><Table rows={filteredSpecies} cols={['id','name','phylum','class','genus','toxic_status','representative_18srrna','extended_18srrna_count','genome_count','cds_count']} /></div>
      </section>

      <section id="genes" className="section-grid">
        <div className="panel wide"><p className="eyebrow">Functional Genes</p><h2>HAB-related gene families</h2><Table rows={filteredGenes} cols={['module','gene_family','annotation','seed_count','full_count','source_files']} /></div>
      </section>

      <section id="tools" className="section-grid">
        <div className="panel wide">
          <div className="panel-head"><div><p className="eyebrow">Sequence Search</p><h2>Real job workflow</h2></div><select value={mode} onChange={e => setMode(e.target.value)}><option value="diamond">DIAMOND functional genes</option><option value="18SrRNA">BLASTN 18SrRNA</option><option value="kraken2">Kraken2 18SrRNA</option><option value="auto">Auto</option></select></div>
          <textarea value={sequence} onChange={e => setSequence(e.target.value)} />
          <div className="tool-actions"><button className="button primary" onClick={submitJob} disabled={loading}><FlaskConical size={16}/> Submit job</button>{job && <button className="button" onClick={async()=>setJob(await getJSON(`/api/jobs/${job.id}`))}><RefreshCw size={16}/> Refresh</button>}</div>
          {job && <div className="result-item"><strong>Job {job.id}</strong><p>Status: {job.status} · Engine: {job.engine || '-'} · {job.message}</p>{job.result_download_url && <a className="button" href={`${API}${job.result_download_url}`}>Download result TSV</a>}<pre className="json-output">{JSON.stringify(job.hits || [], null, 2)}</pre></div>}
        </div>
      </section>

      <section id="downloads" className="section-grid">
        <div className="panel wide"><p className="eyebrow">Downloads</p><h2>Release assets and checksums</h2><Table rows={downloads.map(d => ({...d, download: `${API}${d.download_url}`}))} cols={['name','category','format','size_bytes','checksum_sha256','download']} linkCol="download" /></div>
      </section>
    </main>
    <footer><span>HABDB v2</span><span>18SrRNA naming normalized</span><span>FastAPI + PostgreSQL + Docker Compose</span></footer>
  </div>;
}

function Table({ rows, cols, linkCol }) {
  return <div className="table-wrap"><table><thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((r,i) => <tr key={i}>{cols.map(c => <td key={c}>{c === linkCol ? <a className="button" href={r[c]}>Open</a> : String(r[c] ?? '')}</td>)}</tr>)}</tbody></table></div>;
}

createRoot(document.getElementById('root')).render(<App />);
