import React, { useEffect, useState } from 'react';
import { ArrowLeft, Check, LoaderCircle, X } from 'lucide-react';
import { submissionApi } from '../services/api';
import './admin-prices.css'; import './price-submissions.css';

const money = value => Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2 });
export default function AdminPriceSubmissions() {
  const [status, setStatus] = useState('pending'); const [rows, setRows] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = () => { setLoading(true); submissionApi.list({ status }).then(setRows).catch(e => setError(e.message)).finally(() => setLoading(false)); };
  useEffect(load, [status]);
  const review = async (row, action) => { if (action === 'approve' && !window.confirm(`Approve ${row.material} from ${row.source}? This creates a REAL observation.`)) return; const notes = window.prompt(`${action === 'reject' ? 'Rejection' : 'Review'} notes (optional):`) ?? null; if (notes === null) return; try { await submissionApi[action](row.id, notes || null); load(); } catch (e) { setError(e.message); } };
  return <div className="admin-page"><header className="admin-header"><div className="admin-shell"><a className="admin-brand" href="/">ScrapRate <small>MARKET INTELLIGENCE</small></a><div className="admin-nav-actions"><a className="admin-back" href="/admin/prices"><ArrowLeft size={17}/> Price admin</a><a className="admin-back" href="/submit-price">Submission form</a></div></div></header><main className="admin-main admin-shell">
    <section className="admin-intro"><div><span className="admin-eyebrow">SOURCE REVIEW QUEUE</span><h1>Price submissions</h1><p>Approve source-attributed rates into REAL observations or retain rejected submissions for audit.</p></div></section>
    <div className="submission-tabs" role="tablist">{['pending','approved','rejected'].map(x => <button role="tab" aria-selected={status === x} className={status === x ? 'active' : ''} onClick={() => setStatus(x)} key={x}>{x}</button>)}</div>
    <section className="recent-card">{error && <div className="import-message error">{error}</div>}{loading ? <div className="admin-loading"><LoaderCircle className="spin"/> Loading submissions…</div> : !rows.length ? <div className="admin-empty"><strong>No {status} submissions</strong></div> : <div className="admin-table-wrap"><table><thead><tr><th>Source</th><th>City / material</th><th>Date</th><th>Low</th><th>Average</th><th>High</th><th>Submitted</th><th>Status</th><th>Review</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td><strong>{row.source}</strong><small>{row.source_type}</small></td><td><strong>{row.material}</strong><small>{row.city}{row.grade ? ` · ${row.grade}` : ''}</small></td><td>{row.date}</td><td>₹{money(row.low)}</td><td>₹{money(row.average)}</td><td>₹{money(row.high)}</td><td>{new Date(row.submitted_at).toLocaleString()}</td><td><span className={`submission-status ${row.status}`}>{row.status}</span></td><td>{row.status === 'pending' && <div className="review-actions"><button onClick={() => review(row, 'approve')}><Check size={15}/>Approve</button><button className="reject" onClick={() => review(row, 'reject')}><X size={15}/>Reject</button></div>}</td></tr>)}</tbody></table></div>}</section>
  </main></div>;
}
