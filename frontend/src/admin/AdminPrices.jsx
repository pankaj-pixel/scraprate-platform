import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Check, Database, Edit3, LoaderCircle, RefreshCw, Save, ShieldAlert } from 'lucide-react';
import { adminPriceApi } from '../services/api';
import './admin-prices.css';

const today = new Date().toLocaleDateString('en-CA');
const emptyForm = {
  date: today, city: '', material: '', grade: '', low_price: '', average_price: '',
  high_price: '', unit: 'kg', source: '', confidence_score: '0.7500', is_demo: true,
};
const emptyFilters = { city: '', material: '', date: '', is_demo: '' };
const money = (value) => Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function AdminPrices() {
  const [options, setOptions] = useState({ cities: [], materials: [], sources: [] });
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [filters, setFilters] = useState(emptyFilters);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const selectedMaterial = useMemo(
    () => options.materials.find((item) => item.slug === form.material),
    [options.materials, form.material],
  );

  const loadEntries = useCallback(async (activeFilters = filters) => {
    setLoading(true); setError('');
    try { setEntries(await adminPriceApi.list({ ...activeFilters, limit: 100 })); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [filters]);

  useEffect(() => {
    let active = true;
    Promise.all([adminPriceApi.options(), adminPriceApi.list({ limit: 100 })])
      .then(([optionData, priceData]) => {
        if (!active) return;
        setOptions(optionData); setEntries(priceData);
        setForm((current) => ({
          ...current,
          city: optionData.cities[0]?.slug || '',
          material: optionData.materials[0]?.slug || '',
          unit: optionData.materials[0]?.unit || 'kg',
          source: optionData.sources[0]?.slug || '',
        }));
      })
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const updateForm = (event) => {
    const { name, value } = event.target;
    if (name === 'material') {
      const material = options.materials.find((item) => item.slug === value);
      setForm((current) => ({ ...current, material: value, grade: '', unit: material?.unit || 'kg' }));
      return;
    }
    setForm((current) => ({ ...current, [name]: value }));
  };

  const resetForm = () => {
    setEditingId(null);
    setForm({
      ...emptyForm,
      city: options.cities[0]?.slug || '',
      material: options.materials[0]?.slug || '',
      unit: options.materials[0]?.unit || 'kg',
      source: options.sources[0]?.slug || '',
    });
  };

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError(''); setNotice('');
    const payload = {
      ...form,
      grade: form.grade || null,
      source_type: options.sources.find((item) => item.slug === form.source)?.source_type || null,
    };
    try {
      const saved = editingId
        ? await adminPriceApi.replace(editingId, payload)
        : await adminPriceApi.create(payload);
      const successMessage = `${saved.is_demo ? 'DEMO' : 'REAL'} price ${editingId ? 'updated' : 'created'} successfully.`;
      resetForm();
      setNotice(successMessage);
      await loadEntries(filters);
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  };

  const edit = (entry) => {
    setEditingId(entry.id); setError(''); setNotice('');
    setForm({
      date: entry.date, city: entry.city_slug, material: entry.material_slug,
      grade: entry.grade_slug || '', low_price: entry.low_price, average_price: entry.average_price,
      high_price: entry.high_price, unit: entry.unit, source: entry.source_slug,
      confidence_score: entry.confidence_score, is_demo: entry.is_demo,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const applyFilters = (event) => { event.preventDefault(); loadEntries(filters); };

  return <div className="admin-page">
    <header className="admin-header"><div className="admin-shell admin-header-inner">
      <a href="/" className="admin-brand"><span>♻</span><div><strong>ScrapRate</strong><small>INTERNAL PRICE ADMIN</small></div></a>
      <div className="admin-nav-actions"><a href="/admin/analytics" className="admin-back">Site analytics</a><a href="/admin/data-sources" className="admin-back">Data sources</a><a href="/admin/price-submissions" className="admin-back">Review submissions</a><a href="/admin/import-prices" className="admin-back">Import CSV</a><a href="/" className="admin-back"><ArrowLeft size={17}/> Public homepage</a></div>
    </div></header>

    <main className="admin-shell admin-main">
      <section className="admin-intro"><div><span className="admin-eyebrow">PRICE OPERATIONS</span><h1>Daily price management</h1><p>Add and explicitly edit database-backed scrap price observations.</p></div><div className="security-note"><ShieldAlert size={19}/><span><strong>Internal development tool</strong>Authentication must be added before production.</span></div></section>

      {error && <div className="admin-alert error" role="alert">{error}</div>}
      {notice && <div className="admin-alert success" role="status"><Check size={17}/>{notice}</div>}

      <section className="admin-card entry-card">
        <div className="admin-section-heading"><div><span>{editingId ? 'EDIT ENTRY' : 'ADD PRICE'}</span><h2>{editingId ? `Update price #${editingId}` : 'Record a daily price'}</h2></div>{editingId && <button type="button" className="text-button" onClick={resetForm}>Cancel edit</button>}</div>
        <form onSubmit={submit} className="price-form">
          <label>Date<input required type="date" name="date" value={form.date} onChange={updateForm}/></label>
          <label>City<select required name="city" value={form.city} onChange={updateForm}>{options.cities.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
          <label>Material<select required name="material" value={form.material} onChange={updateForm}>{options.materials.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
          <label>Grade<select name="grade" value={form.grade} onChange={updateForm}><option value="">Base / no grade</option>{(selectedMaterial?.grades || []).map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
          <label>Low ₹<input required min="0" step="0.01" inputMode="decimal" name="low_price" value={form.low_price} onChange={updateForm}/></label>
          <label>Average ₹<input required min="0" step="0.01" inputMode="decimal" name="average_price" value={form.average_price} onChange={updateForm}/></label>
          <label>High ₹<input required min="0" step="0.01" inputMode="decimal" name="high_price" value={form.high_price} onChange={updateForm}/></label>
          <label>Unit<input required name="unit" value={form.unit} onChange={updateForm}/></label>
          <label className="wide-field">Price source<select required name="source" value={form.source} onChange={updateForm}>{options.sources.map((item) => <option key={item.slug} value={item.slug}>{item.name} · {item.source_type}</option>)}</select></label>
          <label>Confidence (0–1)<input required type="number" min="0" max="1" step="0.0001" name="confidence_score" value={form.confidence_score} onChange={updateForm}/></label>
          <fieldset className="data-status"><legend>Data status</legend><button type="button" className={form.is_demo ? 'active demo' : ''} onClick={() => setForm((current) => ({ ...current, is_demo: true }))}>DEMO<span>Indicative/test data</span></button><button type="button" className={!form.is_demo ? 'active real' : ''} onClick={() => setForm((current) => ({ ...current, is_demo: false }))}>REAL<span>Manually verified observation</span></button></fieldset>
          <div className="form-actions"><p>{form.is_demo ? 'This record will be clearly identified as demo data.' : 'Confirm this observation is genuinely sourced before saving as REAL.'}</p><button className="primary-admin-button" disabled={saving || !options.sources.length}>{saving ? <LoaderCircle className="spin" size={18}/> : <Save size={18}/>} {editingId ? 'Save explicit update' : 'Add price record'}</button></div>
        </form>
      </section>

      <section className="admin-card recent-card">
        <div className="admin-section-heading"><div><span>DATABASE RECORDS</span><h2>Recent price entries</h2></div><button className="icon-button" type="button" onClick={() => loadEntries(filters)} aria-label="Refresh entries"><RefreshCw size={18}/></button></div>
        <form className="admin-filters" onSubmit={applyFilters}>
          <label>City<select value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })}><option value="">All cities</option>{options.cities.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
          <label>Material<select value={filters.material} onChange={(e) => setFilters({ ...filters, material: e.target.value })}><option value="">All materials</option>{options.materials.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
          <label>Date<input type="date" value={filters.date} onChange={(e) => setFilters({ ...filters, date: e.target.value })}/></label>
          <label>Status<select value={filters.is_demo} onChange={(e) => setFilters({ ...filters, is_demo: e.target.value })}><option value="">Demo + real</option><option value="true">DEMO only</option><option value="false">REAL only</option></select></label>
          <button className="filter-button">Apply filters</button>
        </form>
        {loading ? <div className="admin-loading"><LoaderCircle className="spin"/><span>Loading price records…</span></div> : entries.length === 0 ? <div className="admin-empty"><Database size={24}/><strong>No matching price entries</strong><span>Adjust the filters or add a new observation.</span></div> : <div className="admin-table-wrap"><table><thead><tr><th>Date</th><th>Material</th><th>City</th><th>Low</th><th>Average</th><th>High</th><th>Source</th><th>Status</th><th><span className="sr-only">Action</span></th></tr></thead><tbody>{entries.map((entry) => <tr key={entry.id}><td>{entry.date}</td><td><strong>{entry.material}</strong>{entry.grade && <small>{entry.grade}</small>}</td><td>{entry.city}</td><td>₹{money(entry.low_price)}</td><td className="average-cell">₹{money(entry.average_price)}<small>/{entry.unit}</small></td><td>₹{money(entry.high_price)}</td><td><span>{entry.source}</span><small>{entry.source_type}</small></td><td><span className={`status-badge ${entry.is_demo ? 'demo' : 'real'}`}>{entry.is_demo ? 'DEMO' : 'REAL'}</span></td><td><button className="edit-button" onClick={() => edit(entry)} aria-label={`Edit ${entry.material} price from ${entry.date}`}><Edit3 size={16}/> Edit</button></td></tr>)}</tbody></table></div>}
      </section>
    </main>
  </div>;
}

export default AdminPrices;
