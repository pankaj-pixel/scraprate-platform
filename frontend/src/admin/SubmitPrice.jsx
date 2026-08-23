import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, LoaderCircle, ShieldAlert } from 'lucide-react';
import { submissionApi } from '../services/api';
import './admin-prices.css';
import './price-submissions.css';

const initial = { source: '', city: '', material: '', grade: '', date: new Date().toISOString().slice(0, 10), low: '', average: '', high: '', unit: 'kg' };
export default function SubmitPrice() {
  const [options, setOptions] = useState({ sources: [], cities: [], materials: [] }); const [form, setForm] = useState(initial);
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState(''); const [error, setError] = useState('');
  useEffect(() => { submissionApi.options().then(setOptions).catch(e => setError(e.message)); }, []);
  const material = useMemo(() => options.materials.find(x => x.slug === form.material), [options, form.material]);
  const change = e => { const { name, value } = e.target; setForm(old => ({ ...old, [name]: value, ...(name === 'material' ? { grade: '', unit: options.materials.find(x => x.slug === value)?.unit || 'kg' } : {}) })); };
  const submit = async e => { e.preventDefault(); setBusy(true); setError(''); setMessage(''); try { const row = await submissionApi.create(form); setMessage(`Submission #${row.id} is pending admin review.`); setForm(initial); } catch (err) { setError(err.message); } finally { setBusy(false); } };
  return <div className="admin-page"><header className="admin-header"><div className="admin-shell"><a className="admin-brand" href="/">ScrapRate <small>MARKET INTELLIGENCE</small></a><a className="admin-back" href="/"><ArrowLeft size={17}/> Homepage</a></div></header><main className="admin-main admin-shell narrow-admin">
    <section className="admin-intro"><div><span className="admin-eyebrow">DEVELOPMENT SUBMISSION</span><h1>Submit a daily scrap rate</h1><p>Price submissions are reviewed before they affect ScrapRate market prices.</p></div><div className="security-note"><ShieldAlert size={19}/><span><strong>Development only</strong>Authenticated source ownership must be required before production.</span></div></section>
    <section className="entry-card"><form className="price-form" onSubmit={submit}>
      <label>Dealer or recycler source<select name="source" required value={form.source} onChange={change}><option value="">Select source</option>{options.sources.map(x => <option key={x.slug} value={x.slug}>{x.name} · {x.source_type}</option>)}</select></label>
      <label>City<select name="city" required value={form.city} onChange={change}><option value="">Select city</option>{options.cities.map(x => <option key={x.slug} value={x.slug}>{x.name}</option>)}</select></label>
      <label>Material<select name="material" required value={form.material} onChange={change}><option value="">Select material</option>{options.materials.map(x => <option key={x.slug} value={x.slug}>{x.name}</option>)}</select></label>
      <label>Grade<select name="grade" value={form.grade} onChange={change}><option value="">Base / unspecified</option>{material?.grades.map(x => <option key={x.slug} value={x.slug}>{x.name}</option>)}</select></label>
      <label>Date<input type="date" name="date" required value={form.date} onChange={change}/></label>
      {['low','average','high'].map(name => <label key={name}>{name[0].toUpperCase()+name.slice(1)} ₹/{form.unit}<input type="number" name={name} min="0.01" step="0.01" required value={form[name]} onChange={change}/></label>)}
      <div className="form-actions wide-field"><p>Submitting creates an audit record—not a public price observation.</p><button className="primary-admin-button" disabled={busy || !options.sources.length}>{busy && <LoaderCircle className="spin" size={18}/>} Submit for review</button></div>
    </form>{error && <div className="import-message error">{error}</div>}{message && <div className="import-message success"><CheckCircle2 size={18}/>{message}</div>}{!options.sources.length && !error && <div className="admin-empty">No active dealer or recycler sources are available.</div>}</section>
  </main></div>;
}
