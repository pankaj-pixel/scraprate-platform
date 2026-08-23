import { ArrowDownRight, ArrowRight, ArrowUpRight, Clock3, Minus } from 'lucide-react';
import PriceChart from './PriceChart';

const money = (value) => Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

export default function MaterialCard({ material, history, onOpen }) {
  const hasChange = material.change !== null && material.change_pct !== null;
  const direction = !hasChange ? 'flat' : material.change > 0 ? 'up' : material.change < 0 ? 'down' : 'flat';
  const DirectionIcon = direction === 'up' ? ArrowUpRight : direction === 'down' ? ArrowDownRight : Minus;
  const dateLabel = material.last_updated ? new Date(material.last_updated).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }) : 'Unavailable';
  return (
    <button className={`material-card market-card market-card--${direction}`} onClick={() => onOpen(material)} aria-label={`Open ${material.name} price details`}>
      <div className="material-card__top">
        <div className="material-identity"><div className="material-icon material-photo">
          <span>{material.icon}</span>
          <img
            src={material.image_reference || `/materials/${material.slug}.png`}
            alt={`${material.name} scrap`}
            loading="lazy"
            decoding="async"
            onError={(event) => { event.currentTarget.style.display = 'none'; }}
          />
        </div><div><span className="material-symbol">{material.icon}</span><span className="eyebrow">{material.category}</span></div></div>
        <div className={`change-pill ${direction}`}><DirectionIcon size={14}/>{hasChange ? `${direction === 'up' ? '+' : direction === 'down' ? '−' : ''}${Math.abs(material.change_pct).toFixed(2)}%` : 'No prior rate'}</div>
      </div>
      <div className="material-name-row"><h3>{material.name}</h3><ArrowRight size={17}/></div>
      <div className="price-line">
        <strong>₹{money(material.indicative_price)}</strong>
        <span>/ {material.unit}</span>
      </div>
      <div className={`daily-change ${direction}`}><span>Daily change</span><b>{hasChange ? `${direction === 'up' ? '+' : direction === 'down' ? '−' : ''}₹${money(Math.abs(material.change))}` : '—'}</b><em>{hasChange ? `${direction === 'up' ? '+' : direction === 'down' ? '−' : ''}${Math.abs(material.change_pct).toFixed(2)}%` : 'No comparison'}</em></div>
      <div className="card-market-meta"><span className={`data-type-badge ${material.data_type}`}>{material.data_type === 'real' ? 'Published rate' : 'Demo data'}</span></div>
      <div className="trend-head"><span>7-day stored trend</span><small>₹/{material.unit}</small></div><PriceChart data={history || []} compact />
      <div className="range-row"><span>Market range</span><b>₹{money(material.low)} – ₹{money(material.high)}</b></div>
      <div className="card-updated"><Clock3 size={12}/><span>{material.freshness_label || `Updated ${dateLabel}`}</span></div>
      <span className="card-detail-link">View price details <ArrowRight size={14}/></span>
    </button>
  );
}
