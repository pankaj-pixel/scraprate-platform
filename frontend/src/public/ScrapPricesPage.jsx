import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import MaterialCard from '../components/MaterialCard';
import { setSeo } from './seo';
import './public-pages.css';

export default function ScrapPricesPage() {
  const [data, setData] = useState(null); const [error, setError] = useState(''); const [search, setSearch] = useState('');
  useEffect(() => { const canonical = `${location.origin}/scrap-prices`; setSeo({ title: "Today's Scrap Prices in Delhi NCR | ScrapRate", description: 'Compare indicative scrap prices, market ranges and stored price trends for metals, paper, plastic, e-waste and more in Delhi NCR.', canonical, schema: { '@context':'https://schema.org','@type':'CollectionPage', name:"Today's Scrap Prices in Delhi NCR", url:canonical } }); api.overview('delhi').then(setData).catch(() => setError('Prices are temporarily unavailable. Please try again.')); }, []);
  const materials = useMemo(() => (data?.materials || []).filter(x => x.data_type === 'real' && x.material.toLowerCase().includes(search.toLowerCase())), [data, search]);
  return <><LaunchHeader/><main className="public-page"><section className="public-hero"><span>DELHI NCR PRICE DIRECTORY</span><h1>Today’s scrap prices</h1><p>Explore indicative local scrap rates from active sources. Buyer quotes can vary by grade, quantity, location and inspection.</p><input aria-label="Search materials" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search copper, iron, paper…"/></section>
    {error ? <div className="state-card error-state">{error}</div> : !data ? <div className="loading-grid"><div className="loader"/>Loading prices…</div> : materials.length ? <PriceGroup title="Published local buying rates" items={materials}/> : <div className="state-card"><strong>No published rates are available</strong><span>Demo records are excluded from this public price directory.</span></div>}
  </main></>;
}
function PriceGroup({title,items}) { return <section className="public-group"><h2>{title}</h2><div className="materials-grid">{items.map(item=><MaterialCard key={item.slug} material={{...item,name:item.material,icon:item.slug.slice(0,2).toUpperCase(),change_pct:item.change_percent}} history={item.history||[]} onOpen={()=>location.href=`/scrap-price/${item.slug}`}/>)}</div></section> }
export function LaunchHeader(){return <header className="launch-header"><a href="/" className="brand"><span className="brand-mark">♻</span><span className="brand-copy"><strong>ScrapRate</strong><small>Daily scrap prices. Clear trends. Better decisions.</small></span></a><nav aria-label="Public navigation"><a href="/scrap-prices">Prices</a><a href="/methodology">Methodology</a><a href="/about">About</a><a href="/#calculator">Calculator</a></nav></header>}
