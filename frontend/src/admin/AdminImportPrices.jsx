import { useState } from 'react';
import { AlertTriangle, ArrowLeft, CheckCircle2, FileSearch, LoaderCircle, ShieldAlert, Upload } from 'lucide-react';
import { adminImportApi } from '../services/api';
import './admin-prices.css';
import './admin-import-prices.css';

const money = (value) => Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function IssueTable({ title, rows, tone = 'invalid' }) {
  if (!rows?.length) return null;
  return <section className={`import-results ${tone}`}><header><h3>{title}</h3><span>{rows.length}</span></header><div className="import-table-wrap"><table><thead><tr><th>Row</th><th>Date</th><th>Material</th><th>City</th><th>Source</th><th>Reason</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.row_number}-${index}`}><td>{row.row_number}</td><td>{row.raw.date || '—'}</td><td>{row.raw.material || '—'}</td><td>{row.raw.city || '—'}</td><td>{row.raw.source || '—'}</td><td>{row.errors.join('; ')}</td></tr>)}</tbody></table></div></section>;
}

export default function AdminImportPrices() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const previewFile = async (event) => {
    event.preventDefault();
    if (!file) return;
    setBusy(true); setError(''); setResult(null);
    try { setPreview(await adminImportApi.preview(file)); }
    catch (err) { setError(err.message); setPreview(null); }
    finally { setBusy(false); }
  };

  const commit = async () => {
    if (!preview?.valid_rows.length) return;
    setBusy(true); setError('');
    try { setResult(await adminImportApi.commit(preview.valid_rows)); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const chooseFile = (event) => {
    setFile(event.target.files?.[0] || null);
    setPreview(null); setResult(null); setError('');
  };

  return <div className="admin-page">
    <header className="admin-header"><div className="admin-shell admin-header-inner">
      <a href="/" className="admin-brand"><span>♻</span><div><strong>ScrapRate</strong><small>INTERNAL PRICE ADMIN</small></div></a>
      <div className="admin-nav-actions"><a href="/admin/prices" className="admin-back"><ArrowLeft size={17}/> Price entries</a><a href="/" className="admin-back">Public homepage</a></div>
    </div></header>

    <main className="admin-shell admin-main">
      <section className="admin-intro"><div><span className="admin-eyebrow">REAL PRICE INGESTION</span><h1>Import price observations</h1><p>Upload, validate, preview, and explicitly approve source-attributed CSV rows.</p></div><div className="security-note"><ShieldAlert size={19}/><span><strong>Internal development tool</strong>Imports are always REAL and require an existing active source.</span></div></section>

      {error && <div className="admin-alert error" role="alert"><AlertTriangle size={17}/>{error}</div>}
      {result && <div className="admin-alert success" role="status"><CheckCircle2 size={17}/>Import complete: {result.inserted_count} of {result.approved_count} approved rows inserted as REAL.</div>}

      <section className="admin-card import-upload-card">
        <div className="admin-section-heading"><div><span>STEP 1</span><h2>Upload CSV</h2></div></div>
        <form onSubmit={previewFile} className="import-upload-form">
          <label className="file-picker"><Upload size={25}/><span><strong>{file?.name || 'Choose a CSV price file'}</strong><small>UTF-8 CSV · maximum 2 MB and 1,000 rows</small></span><input type="file" accept=".csv,text/csv" onChange={chooseFile}/></label>
          <button className="primary-admin-button" disabled={!file || busy}>{busy ? <LoaderCircle className="spin" size={18}/> : <FileSearch size={18}/>} Preview import</button>
        </form>
        <p className="template-note">Required columns: date, city, material, grade, low_price, average_price, high_price, unit, source. The source must already exist and be active.</p>
      </section>

      {preview && <section className="admin-card import-preview-card">
        <div className="admin-section-heading"><div><span>STEP 2</span><h2>Review preview</h2></div><span className="preview-total">{preview.total_rows} parsed rows</span></div>
        <div className="import-summary"><div className="valid"><strong>{preview.valid_rows.length}</strong><span>Valid</span></div><div><strong>{preview.invalid_rows.length}</strong><span>Invalid</span></div><div><strong>{preview.duplicate_rows.length}</strong><span>Duplicates</span></div><div><strong>{preview.unknown_sources.length}</strong><span>Unknown sources</span></div></div>

        {!!preview.valid_rows.length && <section className="import-results valid"><header><h3>Approved candidates</h3><span>{preview.valid_rows.length}</span></header><div className="import-table-wrap"><table><thead><tr><th>Row</th><th>Date</th><th>Material</th><th>Grade</th><th>City</th><th>Low</th><th>Average</th><th>High</th><th>Source</th><th>Type</th></tr></thead><tbody>{preview.valid_rows.map((row) => <tr key={row.row_number}><td>{row.row_number}</td><td>{row.date}</td><td>{row.material}</td><td>{row.grade || 'Base'}</td><td>{row.city}</td><td>₹{money(row.low_price)}</td><td><strong>₹{money(row.average_price)}</strong></td><td>₹{money(row.high_price)}</td><td>{row.source}</td><td><span className="status-badge real">REAL</span></td></tr>)}</tbody></table></div></section>}
        <IssueTable title="Invalid rows" rows={preview.invalid_rows}/>
        <IssueTable title="Duplicate rows" rows={preview.duplicate_rows} tone="duplicate"/>

        <div className="unknown-summary"><span>Unknown cities: <strong>{preview.unknown_cities.length}</strong></span><span>Unknown materials: <strong>{preview.unknown_materials.length}</strong></span><span>Unknown grades: <strong>{preview.unknown_grades.length}</strong></span><span>Unknown sources: <strong>{preview.unknown_sources.length}</strong></span></div>
        <div className="import-commit"><div><strong>Only valid rows will be submitted.</strong><span>Commit revalidates sources and duplicates. Existing observations are never overwritten.</span></div><button className="primary-admin-button" disabled={!preview.valid_rows.length || busy || !!result} onClick={commit}>{busy ? <LoaderCircle className="spin" size={18}/> : <CheckCircle2 size={18}/>} Confirm REAL import</button></div>
      </section>}
    </main>
  </div>;
}
