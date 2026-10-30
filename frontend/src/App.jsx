import { useEffect, useState } from 'react'
import Plot from './Plot.jsx'

const get = (u) => fetch(u).then((r) => r.json())
const inr = (n) => '₹' + Math.round(n).toLocaleString('en-IN')
const badge = { 'Stockout risk': 'bg-red-100 text-red-700', Overstock: 'bg-amber-100 text-amber-700', Healthy: 'bg-emerald-100 text-emerald-700' }
const CATS = ['Produce', 'Bakery', 'Dairy', 'Beverages', 'Snacks', 'Household']

const Card = ({ title, children, className = '' }) => (
  <section className={`rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200 ${className}`}>
    {title && <h2 className="mb-2 font-semibold">{title}</h2>}{children}
  </section>
)
const Kpi = ({ label, value, tone = '' }) => (
  <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
    <div className={`text-2xl font-semibold ${tone}`}>{value}</div><div className="text-sm text-slate-500">{label}</div>
  </div>
)

function Dashboard() {
  const [sum, setSum] = useState(null), [inv, setInv] = useState([]), [met, setMet] = useState(null), [recs, setRecs] = useState([])
  const [pid, setPid] = useState(1), [fc, setFc] = useState(null)
  const [sc, setSc] = useState({ promo_category: '', footfall_pct: 0 }), [res, setRes] = useState(null)
  useEffect(() => { get('/api/summary').then(setSum); get('/api/inventory').then(setInv); get('/api/model/metrics').then(setMet); get('/api/recommendations').then(setRecs) }, [])
  useEffect(() => { get(`/api/forecast/${pid}`).then(setFc) }, [pid])
  const run = () => fetch('/api/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ promo_category: sc.promo_category || null, footfall_pct: +sc.footfall_pct, days: 7 }) }).then((r) => r.json()).then(setRes)
  useEffect(run, [])
  if (!sum) return <p className="p-6">Loading data from the backend…</p>
  const k = sum.kpis, d = res ? res.scenario.revenue - res.base.revenue : 0
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Kpi label="Revenue (last 30 days)" value={inr(k.revenue_30d)} /><Kpi label="Units sold (30 days)" value={k.units_30d.toLocaleString('en-IN')} />
        <Kpi label="Forecast revenue (next 7 days)" value={inr(k.forecast_revenue_7d)} /><Kpi label="Stockout risks" value={k.at_risk} tone="text-red-600" />
        <Kpi label="Overstocked items" value={k.overstock} tone="text-amber-600" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Daily sales by category (last 60 days)">
          <Plot data={Object.entries(sum.categories).map(([n, y]) => ({ x: sum.dates, y, name: n, type: 'bar' }))} layout={{ barmode: 'stack' }} />
        </Card>
        <Card title="Demand forecast (XGBoost)">
          <select className="mb-2 rounded border px-2 py-1 text-sm" value={pid} onChange={(e) => setPid(+e.target.value)}>
            {inv.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
          {fc && <Plot data={[{ x: fc.hist_dates, y: fc.hist, name: 'Actual units', mode: 'lines', line: { color: '#0E7C86' } },
            { x: [fc.hist_dates.at(-1), ...fc.fc_dates], y: [fc.hist.at(-1), ...fc.forecast], name: 'Forecast', mode: 'lines+markers', line: { color: '#D98E1F', dash: 'dot' } }]} />}
          {met && <p className="mt-1 text-xs text-slate-500">Test MAE {met.mae} units vs {met.baseline_mae} for a 7-day average baseline ({met.improvement_pct}% better).</p>}
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="What-if simulation" className="lg:col-span-1">
          <label className="block text-sm text-slate-500">Promotion on category
            <select className="mt-1 w-full rounded border px-2 py-1 text-slate-800" value={sc.promo_category} onChange={(e) => setSc({ ...sc, promo_category: e.target.value })}>
              <option value="">None</option>{CATS.map((c) => <option key={c}>{c}</option>)}</select></label>
          <label className="mt-3 block text-sm text-slate-500">Footfall change: {sc.footfall_pct}%
            <input type="range" min="-30" max="50" value={sc.footfall_pct} className="w-full" onChange={(e) => setSc({ ...sc, footfall_pct: e.target.value })} /></label>
          <button onClick={run} className="mt-3 rounded bg-teal-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800">Run simulation</button>
          {res && <dl className="mt-3 space-y-1 text-sm">
            <div className="flex justify-between"><dt>Baseline revenue (7 days)</dt><dd>{inr(res.base.revenue)}</dd></div>
            <div className="flex justify-between"><dt>Scenario revenue (7 days)</dt><dd>{inr(res.scenario.revenue)}</dd></div>
            <div className={`flex justify-between font-semibold ${d >= 0 ? 'text-emerald-700' : 'text-red-600'}`}><dt>Change</dt><dd>{d >= 0 ? '+' : ''}{inr(d)}</dd></div>
            <div className="flex justify-between"><dt>Sales lost to empty shelves</dt><dd>{inr(res.scenario.lost)}</dd></div></dl>}
        </Card>
        <Card title="Smart recommendations" className="lg:col-span-2">
          <ul className="space-y-2 text-sm">{recs.map((r, i) => (
            <li key={i} className="flex gap-2"><span className={`h-fit rounded px-1.5 py-0.5 text-xs ${r.priority === 'High' ? 'bg-red-100 text-red-700' : r.priority === 'Medium' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>{r.priority}</span>{r.text}</li>))}</ul>
        </Card>
      </div>
      <Card title="Inventory status and 7-day forecast">
        <div className="overflow-x-auto"><table className="w-full text-left text-sm">
          <thead className="text-slate-500"><tr>{['Product', 'Category', 'Stock', 'Forecast units', 'Days of cover', 'Reorder qty', 'Status'].map((h) => <th key={h} className="py-1 pr-4 font-medium">{h}</th>)}</tr></thead>
          <tbody>{inv.map((p) => (<tr key={p.id} className="border-t border-slate-100">
            <td className="py-1.5 pr-4">{p.name}</td><td className="pr-4">{p.category}</td><td className="pr-4">{p.stock}</td><td className="pr-4">{p.forecast_units}</td>
            <td className="pr-4">{p.days_cover}</td><td className="pr-4">{p.reorder_qty}</td><td><span className={`rounded px-2 py-0.5 text-xs ${badge[p.status]}`}>{p.status}</span></td></tr>))}</tbody></table></div>
      </Card>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('dash')
  const T = ({ id, children }) => <button onClick={() => setTab(id)} className={`rounded-full px-4 py-1.5 text-sm ${tab === id ? 'bg-teal-700 text-white' : 'bg-white text-slate-700 ring-1 ring-slate-200'}`}>{children}</button>
  return (
    <main className="mx-auto max-w-6xl p-4">
      <header className="mb-4"><h1 className="text-2xl font-semibold">RetailTwin AI</h1>
        <p className="text-sm text-slate-500">AI-powered digital twin: predict demand, simulate decisions, optimize inventory.</p>
        <div className="mt-3 flex gap-2"><T id="dash">Analytics dashboard</T><T id="twin">Live store twin</T></div></header>
      {tab === 'dash' ? <Dashboard /> : <iframe src="/store-twin.html" title="Live store twin" className="h-[1150px] w-full rounded-xl bg-white ring-1 ring-slate-200 md:h-[900px]" />}
    </main>
  )
}
