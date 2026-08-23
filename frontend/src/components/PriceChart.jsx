import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export default function PriceChart({ data, compact = false, unit = 'kg' }) {
  return (
    <div className={compact ? 'chart chart--compact' : 'chart'}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 0, left: compact ? -28 : -10, bottom: 0 }}>
          {!compact && <XAxis dataKey="date" tickFormatter={(v) => new Date(`${v}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })} tickLine={false} axisLine={false} minTickGap={25} />}
          {!compact && <YAxis domain={['dataMin - 5', 'dataMax + 5']} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${Math.round(v)}`} />}
          <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #dfe7e1', boxShadow: '0 10px 30px rgba(16,39,29,.12)', fontSize: 12 }} formatter={(v) => [`₹${Number(v).toLocaleString('en-IN')}/${unit}`, 'Indicative price']} labelFormatter={(v) => new Date(`${v}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} />
          <Area type="monotone" dataKey="price" stroke="currentColor" fill="currentColor" fillOpacity={0.08} strokeWidth={compact ? 2 : 2.4} isAnimationActive />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
