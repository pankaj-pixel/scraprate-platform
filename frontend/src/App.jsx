import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, BarChart3, Bell, Calculator, CalendarDays, CheckCircle2, ChevronDown, ChevronRight, CircleDollarSign, Factory, HandCoins, ImagePlus, MapPin, Menu, PackageCheck, Recycle, RefreshCw, Search, ShieldCheck, SlidersHorizontal, Sparkles, TrendingDown, TrendingUp, Truck, Users, X } from 'lucide-react';
import MaterialCard from './components/MaterialCard';
import ConfidenceBadge from './components/ConfidenceBadge';
import PriceChart from './components/PriceChart';
import { api } from './services/api';
import { trackEvent } from './analytics';
import { PublicFooter } from './public/StaticPage';
import './styles.css';

const CITIES = ['Delhi', 'Gurgaon', 'Noida', 'Faridabad', 'Ghaziabad'];
const CATEGORIES = ['All', 'Metals', 'Paper', 'Plastic', 'E-Waste', 'Batteries', 'Appliances', 'Other Recyclables'];
const CATEGORY_DETAILS = [
  ['Metals', 'Metals', Factory, 'Copper, brass, aluminium, iron and steel', 'sage'],
  ['Paper', 'Paper', PackageCheck, 'Newspaper, cardboard and clean paper waste', 'sand'],
  ['Plastic', 'Plastic', Recycle, 'PET bottles and sorted recyclable plastic', 'blue'],
  ['E-Waste', 'E-Waste', Sparkles, 'Electronics, wiring and recyclable components', 'violet'],
];
const STEPS = [
  [BarChart3, 'Check today’s price', 'Explore published indicative rates for supported scrap materials in your city.'],
  [TrendingUp, 'Review stored trends', 'Compare the latest observation with actual historical records when available.'],
  [Calculator, 'Calculate scrap value', 'Add your material and weight to see an indicative local market range.'],
  [ShieldCheck, 'Verify the source', 'Review freshness, attribution and methodology before making a decision.'],
];
const PRICE_FACTORS = [
  ['Material type', 'Copper, aluminium, iron, paper and plastic each follow different recycling markets.'],
  ['Grade and quality', 'Clean, sorted material generally differs in value from mixed or contaminated scrap.'],
  ['Quantity', 'Larger, consistent volumes may attract different collection and buying economics.'],
  ['Location', 'Transport distance, local availability and pickup costs can affect a city’s offered rate.'],
  ['Market demand', 'Industrial demand and broader commodity conditions influence buyer appetite.'],
  ['Buyer requirements', 'Every buyer may assess acceptable grades, preparation and minimum quantities differently.'],
];
const FAQS = [
  ['How are ScrapRate prices calculated?', 'The current indicative rate combines active source observations using source trust, median pricing and a weighted average. Real observations take priority over demo observations for each material, city and date.'],
  ['Are these guaranteed selling prices?', 'No. Every displayed rate and calculator result is indicative. A final offer can change after the buyer checks material grade, quality, quantity, contamination, location and pickup requirements.'],
  ['Why do scrap prices change?', 'Scrap values can move with material demand, recyclable commodity markets, available local supply, transport costs and individual buyer requirements.'],
  ['Do prices differ by city?', 'Yes. Local demand, availability and logistics can affect rates. ScrapRate currently demonstrates city-adjusted pricing for Delhi, Gurgaon, Noida, Faridabad and Ghaziabad.'],
  ['How often are prices updated?', 'Prices update when a new daily source observation is recorded. The last-updated time and DEMO or REAL status are shown with each material.'],
  ['Can I sell scrap through ScrapRate?', 'Not yet. Listings and buyer offers are upcoming product features. ScrapRate currently helps users explore indicative prices and calculate an estimated scrap value.'],
];
const money = (value) => Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
const dateTimeLabel = (value) => value ? new Date(value).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'Unavailable';
const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

export default function App() {
  const [city, setCity] = useState('Delhi');
  const [materials, setMaterials] = useState([]);
  const [histories, setHistories] = useState({});
  const [overview, setOverview] = useState(null);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [sortBy, setSortBy] = useState('name');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [calcSlug, setCalcSlug] = useState('');
  const [weight, setWeight] = useState(10);
  const [requestKey, setRequestKey] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setSelected(null);
    api.overview(city).then((summary) => {
      if (!active) return;
      const rows = summary.materials.map((item) => ({
        ...item,
        name: item.material,
        price: item.indicative_price,
        previous_price: item.previous_indicative_price,
        change_pct: item.change_percent,
      }));
      const realRows = rows.filter((item) => item.data_type === 'real');
      setMaterials(realRows);
      setHistories(Object.fromEntries(realRows.map((item) => [item.slug, item.history || []])));
      setOverview(summary);
      setCalcSlug((value) => realRows.some((item) => item.slug === value) ? value : realRows[0]?.slug || '');
    }).catch(() => active && setError('Market data is temporarily unavailable. Please check that the ScrapRate API is running.')).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [city, requestKey]);

  const filtered = useMemo(() => materials.filter((item) => {
    const query = search.toLowerCase().trim();
    return (category === 'All' || item.category === category) && (!query || item.name.toLowerCase().includes(query) || item.icon.toLowerCase().includes(query) || item.description.toLowerCase().includes(query));
  }).sort((a, b) => {
    if (sortBy === 'price-desc') return b.indicative_price - a.indicative_price;
    if (sortBy === 'price-asc') return a.indicative_price - b.indicative_price;
    if (sortBy === 'gainers') return b.change_pct - a.change_pct || b.change - a.change;
    if (sortBy === 'losers') return a.change_pct - b.change_pct || a.change - b.change;
    return a.name.localeCompare(b.name);
  }), [materials, category, search, sortBy]);
  const ranked = useMemo(() => [...materials].sort((a, b) => b.indicative_price - a.indicative_price), [materials]);
  const gainers = useMemo(() => materials.filter((item) => item.change > 0).sort((a, b) => b.change_pct - a.change_pct).slice(0, 3), [materials]);
  const losers = useMemo(() => materials.filter((item) => item.change < 0).sort((a, b) => a.change_pct - b.change_pct).slice(0, 3), [materials]);
  const calcMaterial = materials.find((item) => item.slug === calcSlug) || materials[0];
  const parsedWeight = Number(weight);
  const weightIsValid = weight !== '' && Number.isFinite(parsedWeight) && parsedWeight > 0;
  const safeWeight = weightIsValid ? parsedWeight : 0;
  const top = materials[0];
  const hasDemoData = materials.some((item) => item.data_type === 'demo');
  const allDemoData = materials.length > 0 && materials.every((item) => item.data_type === 'demo');
  const marketModeLabel = materials.length ? 'Published source data' : 'No published rates';
  const chooseCategory = (value) => { setCategory(value); setSearch(''); scrollTo('prices'); };

  return <div className="app-shell">
    <header className="nav-wrap"><nav className="nav container" aria-label="Main navigation">
      <a className="brand" href="#top"><span className="brand-mark"><Recycle size={22}/></span><span className="brand-copy"><strong>ScrapRate</strong><small>Market intelligence</small></span></a>
      <div className="nav-links"><a href="#prices">Prices</a><a href="#market">Market</a><a href="#how">How it works</a></div>
      <button className="btn btn-dark" onClick={() => scrollTo('calculator')}>Scrap value calculator <ArrowRight size={16}/></button>
      <button className="mobile-menu-button" aria-label="Toggle navigation" aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen((open) => !open)}>{menuOpen ? <X size={20}/> : <Menu size={20}/>}</button>
    </nav><div className={`mobile-navigation ${menuOpen ? 'open' : ''}`} id="mobile-navigation"><a href="#prices" onClick={() => setMenuOpen(false)}>Prices</a><a href="#market" onClick={() => setMenuOpen(false)}>Market</a><a href="#calculator" onClick={() => setMenuOpen(false)}>Calculator</a><a href="#how" onClick={() => setMenuOpen(false)}>How it works</a><a href="#sell" onClick={() => setMenuOpen(false)}>Sell scrap</a></div></header>

    <main id="top">
      <section className="hero container">
        <div className="hero-copy"><div className="hero-badge"><span className="live-dot"/> Published indicative rates · Delhi NCR</div><h1>Today’s <span>scrap prices</span> in Delhi NCR.</h1><p>Track published scrap buying rates, historical trends and recycling values.</p>
          <div className="hero-actions"><a className="btn btn-primary" href="/scrap-prices">View today’s prices <ArrowRight size={17}/></a><button className="btn btn-ghost" onClick={() => scrollTo('calculator')}><Calculator size={17}/> Scrap value calculator</button></div>
          <label className="hero-location"><span><MapPin size={17}/> Your market</span><select value={city} onChange={(e) => {setCity(e.target.value);trackEvent('city_changed',{city:e.target.value})}} aria-label="Select your market city">{CITIES.map((name) => <option key={name}>{name}</option>)}</select></label>
          <div className="trust-row"><span><ShieldCheck size={17}/> Transparent estimates</span><span><MapPin size={17}/> Local pricing</span><span><TrendingUp size={17}/> 30-day trends</span></div>
        </div>
        <div className="hero-panel"><div className="hero-panel-head"><div><span className="eyebrow">Market pulse</span><h2>{city} today</h2></div><span className={`status-chip status-chip--${overview?.data_type || 'demo'}`}><span className="status-dot"/> {marketModeLabel}</span></div><div className="pulse-labels"><span>Material</span><span>Indicative rate</span><span>Today</span></div>
          {materials.slice(0, 5).map((item) => <div className="ticker-row" key={item.slug}><span>{item.name}</span><strong>₹{money(item.indicative_price)}/{item.unit}</strong><em className={item.change_pct === null ? 'neutral' : item.change_pct >= 0 ? 'positive' : 'negative'}>{item.change_pct === null ? '—' : `${item.change_pct >= 0 ? '+' : ''}${item.change_pct.toFixed(2)}%`}</em></div>)}
          {loading && <div className="pulse-loading">Loading today’s market pulse…</div>}<div className="hero-chart">{top && <PriceChart data={histories[top.slug] || []}/>}</div><div className="chart-caption"><span>{top?.name || 'Market trend'} · stored 30-day history</span><span>Indicative ₹/{top?.unit || 'kg'}</span></div>
        </div>
      </section>

      <section className="market-strip" id="market"><div className="container stats-grid"><Stat label="Published materials" value={materials.length || '—'} note="REAL source observations only"/><Stat label="Coverage" value="Delhi NCR" note="City-specific availability"/><Stat label="Last updated" value={dateTimeLabel(overview?.updated_at)} note="Source publication time"/><Stat label="Method" value="Indicative" note="Transparent source calculation"/></div></section>

      <section className="prices-section container section" id="prices"><Heading eyebrow="Commodity dashboard" title="Today’s scrap prices" text="Indicative city-wise rates, daily movement and seven-day market trends." right={<CitySelect city={city} setCity={setCity}/>}/>{hasDemoData && <div className="demo-notice"><ShieldCheck size={17}/><span>{allDemoData ? 'Prices currently shown are development/demo market data and are not live verified scrap rates.' : 'Some materials currently use development/demo market data where verified real observations are unavailable.'}</span></div>}
        <div className="market-toolbar"><label className="searchbox"><Search size={18}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search material or symbol…" aria-label="Search materials"/>{search && <button className="search-clear" onClick={() => setSearch('')} aria-label="Clear search"><X size={15}/></button>}</label><label className="sort-select"><SlidersHorizontal size={16}/><span>Sort</span><select value={sortBy} onChange={(e) => setSortBy(e.target.value)} aria-label="Sort materials"><option value="name">Material name</option><option value="price-desc">Price: high to low</option><option value="price-asc">Price: low to high</option><option value="gainers">Biggest gainers</option><option value="losers">Biggest losers</option></select></label></div>
        <div className="filter-bar"><div className="chips" aria-label="Filter by category">{CATEGORIES.map((name) => <button key={name} className={category === name ? 'chip active' : 'chip'} onClick={() => setCategory(name)}>{name}<span>{name === 'All' ? materials.length : materials.filter((item) => item.category === name).length}</span></button>)}</div>{!loading && !error && <span className="result-count">Showing {filtered.length} of {materials.length} materials</span>}</div>
        {error && <State title="Unable to load market data" text={error} error action={<button className="btn retry-btn" onClick={() => setRequestKey((key) => key + 1)}><RefreshCw size={15}/> Try again</button>}/>} {!error && loading && <SkeletonGrid/>}{!error && !loading && !filtered.length && <State title={materials.length ? "No matching materials" : "No published prices for this city"} text={materials.length ? "Try another keyword, change the category, or clear your filters." : "Demo records are excluded from public launch sections. Choose a city with a published source observation."} action={materials.length ? <button className="btn reset-btn" onClick={() => { setSearch(''); setCategory('All'); }}>Clear filters</button> : null}/>} {!error && !loading && !!filtered.length && <div className="materials-grid market-card-grid">{filtered.map((item) => <MaterialCard key={item.slug} material={item} history={(histories[item.slug] || []).slice(-7)} onOpen={(value) => {trackEvent('material_viewed',{material_slug:value.slug});location.href=`/scrap-price/${value.slug}`}}/>)}</div>}
      </section>

      <section className="movers-section section"><div className="container"><Heading eyebrow="Market intelligence" title="Market movers" text={`Indicative daily performance and highest-value materials in ${city}.`} right={<span className="as-of">As of {dateTimeLabel(overview?.updated_at)} · {overview?.data_type || 'market'}</span>}/><div className="movers-grid"><MoverPanel title="Top gainers" icon={TrendingUp} rows={gainers} histories={histories} onOpen={setSelected} empty="No materials gained today"/><MoverPanel title="Top losers" icon={TrendingDown} rows={losers} histories={histories} onOpen={setSelected} empty="No materials declined today"/><MoverPanel title="Highest value materials" icon={CircleDollarSign} rows={ranked.slice(0, 3)} histories={histories} onOpen={setSelected}/></div></div></section>

      <section className="calculator-section container section" id="calculator"><div className="calculator-copy"><span className="eyebrow">Scrap value calculator</span><h2>Know your estimated value before you sell.</h2><p>Select your city and material, then enter the weight to calculate a value using the existing indicative ScrapRate API price.</p><div className="calculator-points"><span><CheckCircle2 size={17}/> Current city-adjusted rate</span><span><CheckCircle2 size={17}/> Expected low and high range</span><span><CheckCircle2 size={17}/> Instant calculation, no sign-up</span></div></div>
        <div className="calculator-card"><div className="calculator-card-head"><div><span className="eyebrow">Value estimate</span><h3>Calculate your scrap</h3></div><span className="calculator-status"><span/> Indicative {calcMaterial?.data_type || 'market'} data</span></div><div className="calculator-form"><label><span>City</span><div className="calculator-control"><MapPin size={16}/><select value={city} onChange={(e) => setCity(e.target.value)}>{CITIES.map((name) => <option key={name}>{name}</option>)}</select></div></label><label><span>Material</span><div className="calculator-control"><Recycle size={16}/><select value={calcSlug} onChange={(e) => setCalcSlug(e.target.value)}>{materials.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></div></label><label><span>Weight</span><div className={`calculator-control weight-input ${weight !== '' && !weightIsValid ? 'invalid' : ''}`}><input type="number" min="0.01" step="0.5" inputMode="decimal" value={weight} onChange={(e) => setWeight(e.target.value)} aria-invalid={weight !== '' && !weightIsValid}/><b>kg</b></div>{weight !== '' && !weightIsValid && <small className="field-error">Enter a weight greater than 0 kg.</small>}</label></div>
          <div className={`estimate-box ${!weightIsValid ? 'estimate-box--empty' : ''}`}><div className="rate-summary"><span><i>{calcMaterial?.icon || '—'}</i><span><small>{calcMaterial?.name || 'Select material'} in {city}</small><strong>Indicative rate: ₹{money(calcMaterial?.indicative_price)}/{calcMaterial?.unit || 'kg'}</strong></span></span><em>{calcMaterial?.data_type || 'market'} rate</em></div><div className="estimate-primary"><span>Indicative estimated value</span><strong>{weightIsValid ? `₹${money((calcMaterial?.indicative_price || 0) * safeWeight)}` : '—'}</strong><small>{weightIsValid ? `${money(safeWeight)} kg × ₹${money(calcMaterial?.indicative_price)}/${calcMaterial?.unit || 'kg'}` : 'Enter a valid weight to see your estimate'}</small></div><div className="estimate-range"><span><small>Expected market range</small><b>{weightIsValid ? `₹${money((calcMaterial?.low || 0) * safeWeight)} – ₹${money((calcMaterial?.high || 0) * safeWeight)}` : '—'}</b></span>{weightIsValid && <em>Low ₹{money(calcMaterial?.low)}/kg · High ₹{money(calcMaterial?.high)}/kg</em>}</div></div>
          <div className="calculator-actions"><button className="btn buyer-offers" disabled><Users size={16}/> Get Buyer Offers <span>Coming soon</span></button><p className="calculator-disclaimer"><ShieldCheck size={14}/><span>This is an indicative estimate. Actual buyer prices may vary by material quality, quantity, condition, pickup cost and physical inspection.</span></p></div></div>
      </section>

      <section className="categories-section section container"><Heading eyebrow="Browse faster" title="Popular scrap categories" text="Find the materials you handle most often."/><div className="category-grid">{CATEGORY_DETAILS.map(([name, filter, Icon, description, tone]) => <button className={`category-card ${tone}`} key={name} onClick={() => chooseCategory(filter)}><span className="category-icon"><Icon size={23}/></span><span><strong>{name}</strong><small>{description}</small></span><ChevronRight size={19}/></button>)}</div></section>

      <section className="price-guide section" aria-labelledby="price-factors-title"><div className="container price-guide-grid"><div className="price-guide-copy"><span className="eyebrow">Understanding kabadi rates</span><h2 id="price-factors-title">What affects scrap prices?</h2><p>There is no single universal kabadi rate today. A copper scrap price, aluminium scrap price or iron scrap rate reflects the material itself and the conditions of a particular sale. That is why ScrapRate presents an indicative range rather than one guaranteed selling price.</p><p>Our Delhi NCR directory also covers brass, cardboard and PET plastic scrap prices so you can compare common materials before speaking with a buyer.</p></div><div className="factor-grid">{PRICE_FACTORS.map(([title, text], index) => <article className="factor-card" key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{text}</p></div></article>)}</div></div></section>

      <section className="how-section section" id="how"><div className="container"><Heading eyebrow="Simple by design" title="How ScrapRate works" text="From price discovery to a better-informed sale." centered/><div className="steps-grid">{STEPS.map(([Icon, title, text], index) => <article className="step-card" key={title}><div className="step-top"><span className="step-icon"><Icon size={22}/></span><b>0{index + 1}</b></div><h3>{title}</h3><p>{text}</p></article>)}</div><p className="roadmap-note"><Sparkles size={16}/> Selling and buyer offers are roadmap features; displayed prices remain indicative estimates.</p></div></section>

      <section className="faq-section container section" aria-labelledby="faq-title"><div className="faq-heading"><span className="eyebrow">Helpful answers</span><h2 id="faq-title">Scrap price FAQs</h2><p>What to know before using an indicative scrap rate or value estimate.</p></div><div className="faq-list">{FAQS.map(([question, answer]) => <details key={question}><summary><span>{question}</span><ChevronDown size={17}/></summary><p>{answer}</p></details>)}</div></section>

      <section className="marketplace-preview container" id="sell"><div className="marketplace-intro"><div><span className="eyebrow eyebrow-light">Marketplace preview</span><h2>Turn your scrap into the <span>best available offer.</span></h2><p>ScrapRate is evolving from price discovery into a trusted place for sellers and local buyers to connect. Here’s what is coming next.</p></div><span className="preview-badge"><Sparkles size={14}/> Product preview</span></div><div className="marketplace-paths"><MarketplacePath role="For sellers" title="List scrap in a few clear steps" icon={Recycle} steps={[[PackageCheck, 'Post material'], [BarChart3, 'Add quantity'], [ImagePlus, 'Upload photos'], [MapPin, 'Set location']]}/><div className="marketplace-divider"><ArrowRight size={18}/></div><MarketplacePath role="For buyers" title="Find relevant local supply" icon={Users} steps={[[Search, 'Discover scrap'], [HandCoins, 'Make an offer'], [Truck, 'Arrange pickup']]}/></div><div className="marketplace-actions"><button className="btn btn-light" disabled>Sell Scrap <span>Coming soon</span></button><button className="btn btn-outline-light" disabled>Find Buyers <span>Coming soon</span></button><p><ShieldCheck size={14}/> No listings, payments or buyer accounts are active yet.</p></div></section>
    </main>

    <footer className="footer"><div className="container footer-grid"><div className="footer-brand"><a className="brand" href="#top"><span className="brand-mark"><Recycle size={20}/></span><span className="brand-copy"><strong>ScrapRate</strong><small>Market intelligence</small></span></a><p>Clearer scrap price discovery for households, businesses and recyclers across Delhi NCR.</p></div><FooterLinks title="Product" links={[["Today’s prices", '#prices'], ['Market movers', '#market'], ['Scrap calculator', '#calculator'], ['How it works', '#how']]}/><FooterLinks title="Popular materials" links={[['Copper', '#prices'], ['Aluminium', '#prices'], ['Iron / MS', '#prices'], ['Cardboard', '#prices']]}/><FooterLinks title="Popular cities" links={CITIES.slice(0, 4).map((name) => [name, '#prices'])}/></div><div className="container footer-bottom"><span>© {new Date().getFullYear()} ScrapRate</span><div><a href="#legal">Privacy</a><a href="#legal">Terms</a><a href="#legal">Data policy</a></div></div><div className="container price-disclaimer" id="legal"><ShieldCheck size={16}/><p><strong>Price disclaimer:</strong> Prices are calculated indicative rates, not guaranteed buying prices. {hasDemoData && 'DEMO-labelled materials are development data and are not live verified rates. '}Final rates depend on material grade, quality, quantity, location, pickup costs and buyer evaluation.</p></div></footer>
    <PublicFooter/>
    {selected && <MaterialModal material={selected} city={city} history={histories[selected.slug] || []} onClose={() => setSelected(null)}/>} 
  </div>;
}

function Heading({ eyebrow, title, text, right, centered }) { return <div className={`section-heading ${centered ? 'centered' : ''}`}><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{text}</p></div>{right}</div>; }
function Stat({ label, value, note }) { return <div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>; }
function State({ title, text, error, action }) { return <div className={`state-card ${error ? 'error-state' : ''}`} role={error ? 'alert' : 'status'}><strong>{title}</strong><span>{text}</span>{action}</div>; }
function CitySelect({ city, setCity }) { return <label className="city-select"><MapPin size={16}/><select value={city} onChange={(e) => setCity(e.target.value)} aria-label="Select price city">{CITIES.map((name) => <option key={name}>{name}</option>)}</select></label>; }
function SkeletonGrid() { return <div className="materials-grid market-card-grid" aria-label="Loading scrap prices" aria-live="polite" aria-busy="true">{Array.from({ length: 6 }, (_, index) => <div className="material-skeleton" aria-hidden="true" key={index}><div className="skeleton-row"><i/><b/></div><span/><strong/><em/><div/><small/></div>)}</div>; }
function MoverPanel({ title, icon: Icon, rows, histories, onOpen, empty }) { return <article className="mover-panel"><div className="panel-title"><span><Icon size={18}/></span><h3>{title}</h3></div><div className="mover-list">{rows.length ? rows.map((item) => { const hasChange = item.change !== null && item.change_pct !== null; const direction = !hasChange ? 'neutral' : item.change > 0 ? 'positive' : item.change < 0 ? 'negative' : 'neutral'; return <button className="mover-row mover-row-button" key={item.slug} onClick={() => onOpen(item)} aria-label={`Open ${item.name} price details`}><div className="mover-material"><span className="mover-symbol">{item.icon}</span><span><strong>{item.name}</strong><small>₹{money(item.indicative_price)}/{item.unit}</small></span></div><div className={`mover-change ${direction}`}><strong>{hasChange ? `${item.change > 0 ? '+' : item.change < 0 ? '−' : ''}₹${money(Math.abs(item.change))}` : '—'}</strong><small>{hasChange ? `${item.change_pct > 0 ? '+' : item.change_pct < 0 ? '−' : ''}${Math.abs(item.change_pct).toFixed(2)}%` : 'No prior rate'}</small></div><div className={`mover-spark ${direction}`}><PriceChart data={(histories[item.slug] || []).slice(-7)} compact/></div><ChevronRight size={15}/></button>; }) : <div className="mover-empty"><span><Icon size={16}/></span><p>{empty || 'No movement available'}</p><small>Available rates can be unchanged or move in one direction.</small></div>}</div></article>; }
function FooterLinks({ title, links }) { return <div className="footer-links"><strong>{title}</strong>{links.map(([label, href]) => <a href={href} key={label}>{label}</a>)}</div>; }
function MarketplacePath({ role, title, icon: Icon, steps }) { return <article className="marketplace-path"><header><span><Icon size={20}/></span><div><small>{role}</small><h3>{title}</h3></div></header><div className="marketplace-steps">{steps.map(([StepIcon, label], index) => <div key={label}><span><StepIcon size={15}/></span><strong>{label}</strong>{index < steps.length - 1 && <ChevronRight size={13}/>}</div>)}</div></article>; }
function MaterialModal({ material, city, history, onClose }) {
  const [period, setPeriod] = useState(30);
  const closeRef = useRef(null);
  useEffect(() => { const previousFocus = document.activeElement; const previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; closeRef.current?.focus(); const key = (event) => { if (event.key === 'Escape') onClose(); if (event.key === 'Tab') { const dialog = closeRef.current?.closest('[role="dialog"]'); const focusable = [...(dialog?.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])') || [])]; const first = focusable[0]; const last = focusable.at(-1); if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); } } }; window.addEventListener('keydown', key); return () => { window.removeEventListener('keydown', key); document.body.style.overflow = previousOverflow; previousFocus?.focus?.(); }; }, [onClose]);
  const periodData = history.slice(-period);
  const prices = periodData.map((point) => point.price);
  const periodHigh = prices.length ? Math.max(...prices) : material.indicative_price;
  const periodLow = prices.length ? Math.min(...prices) : material.indicative_price;
  const periodChange = periodData.length > 1 ? periodData.at(-1).price - periodData[0].price : 0;
  const hasDailyChange = material.change !== null && material.change_pct !== null;
  const dailyDirection = !hasDailyChange ? 'neutral' : material.change > 0 ? 'positive' : material.change < 0 ? 'negative' : 'neutral';
  const periodDirection = periodChange > 0 ? 'positive' : periodChange < 0 ? 'negative' : 'neutral';
  const updatedLabel = dateTimeLabel(material.last_updated);

  return <div className="modal-backdrop detail-backdrop" onClick={onClose}><div className="modal material-detail" role="dialog" aria-modal="true" aria-labelledby="modal-title" onClick={(e) => e.stopPropagation()}>
    <button className="modal-close" ref={closeRef} onClick={onClose} aria-label="Close details"><X/></button>
    <header className="detail-header"><div className="modal-title"><div className="material-icon material-photo large"><span>{material.icon}</span><img src={material.image_reference || `/materials/${material.slug}.png`} alt="" onError={(e) => { e.currentTarget.style.display = 'none'; }}/></div><div><span className="eyebrow">{material.category} · {material.icon}</span><h2 id="modal-title">{material.name}</h2><span className="detail-location"><MapPin size={13}/> {city}</span></div></div><div className="detail-updated"><CalendarDays size={14}/><span>Last updated<strong>{updatedLabel}</strong></span></div></header>
    <div className="detail-market-meta"><ConfidenceBadge level={material.confidence}/><span className={`data-type-badge ${material.data_type}`}>{material.data_type.toUpperCase()}</span><span>{material.source_count} active source{material.source_count === 1 ? '' : 's'}</span></div>
    <section className="detail-quote"><div><span>Current indicative price</span><strong>₹{money(material.indicative_price)}<small>/{material.unit}</small></strong></div><div className={`quote-change ${dailyDirection}`}><span>Daily change</span><strong>{hasDailyChange ? `${material.change > 0 ? '+' : material.change < 0 ? '−' : ''}₹${money(Math.abs(material.change))}` : '—'}</strong><em>{hasDailyChange ? `${material.change_pct > 0 ? '+' : material.change_pct < 0 ? '−' : ''}${Math.abs(material.change_pct).toFixed(2)}%` : 'No prior rate'}</em></div><div><span>Market low / high</span><strong className="range-value">₹{money(material.low)} <i>—</i> ₹{money(material.high)}</strong></div></section>
    <section className="detail-chart-section"><div className="detail-chart-head"><div><span className="eyebrow">Historical price</span><h3>{period} day movement</h3></div><div className="period-tabs" role="group" aria-label="Chart period"><button className={period === 7 ? 'active' : ''} aria-pressed={period === 7} onClick={() => setPeriod(7)}>7D</button><button className={period === 30 ? 'active' : ''} aria-pressed={period === 30} onClick={() => setPeriod(30)}>30D</button></div></div><div className="modal-chart"><PriceChart data={periodData} unit={material.unit}/></div></section>
    <section className="period-stats"><div><span>Current indicative</span><strong>₹{money(material.indicative_price)}</strong></div><div><span>{period}D stored high</span><strong>₹{money(periodHigh)}</strong></div><div><span>{period}D stored low</span><strong>₹{money(periodLow)}</strong></div><div><span>{period}D stored change</span><strong className={periodDirection}>{periodChange > 0 ? '+' : periodChange < 0 ? '−' : ''}₹{money(Math.abs(periodChange))}</strong></div></section>
    <section className="detail-description"><div><span className="eyebrow">About this material</span><p>{material.description}</p></div><div className="modal-notice"><ShieldCheck size={16}/><span>{material.data_type === 'demo' ? 'Development/demo indicative rate—not a live verified quote.' : material.source_names?.includes('Urban Scrap') ? 'Source data includes Urban Scrap published buying rates. These are dealer rates, not an official Delhi market price.' : 'Calculated from active real source observations.'}</span></div></section>
    <button className="btn btn-primary detail-cta" onClick={() => { onClose(); scrollTo('calculator'); }}>Calculate Scrap Value <ArrowRight size={17}/></button>
  </div></div>;
}
