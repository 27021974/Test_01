import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchMarketInsights } from '../api.js'
import Badge from '../components/Badge.jsx'

export default function MarketInsights() {
  const [days, setDays] = useState(180)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchMarketInsights(days)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [days])

  return (
    <div>
      <div className="page-header-row">
        <div>
          <h1 className="page-title" style={{ marginBottom: '.25rem' }}>Market Insights</h1>
          <p className="text-muted" style={{ marginTop: 0 }}>
            Aggregierte Signale aus deutschen Insolvenzbekanntmachungen für Markt- und Risikoanalyse.
          </p>
        </div>
        <div className="filter-group">
          <label>Zeitraum</label>
          <select value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={30}>30 Tage</option>
            <option value={90}>90 Tage</option>
            <option value={180}>180 Tage</option>
            <option value={365}>12 Monate</option>
          </select>
        </div>
      </div>

      {loading && <div className="loading">Lädt…</div>}
      {error && <div className="error-msg">{error}</div>}

      {data && !loading && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card insolvency">
              <div className="label">Insolvenz-Signale</div>
              <div className="value">{data.total_insolvency_events}</div>
            </div>
            <div className="kpi-card new">
              <div className="label">Unvollständige Datensätze</div>
              <div className="value">{data.data_incomplete_events}</div>
            </div>
            <div className="kpi-card">
              <div className="label">Top-Region</div>
              <div className="value compact">{data.by_bundesland[0]?.label || '—'}</div>
            </div>
            <div className="kpi-card">
              <div className="label">Top-Branche</div>
              <div className="value compact">{data.by_industry[0]?.label || '—'}</div>
            </div>
          </div>

          <div className="insights-grid">
            <BucketCard title="Nach Bundesland" items={data.by_bundesland} />
            <BucketCard title="Nach Branche" items={data.by_industry} />
            <BucketCard title="Nach Verfahrensart" items={data.by_procedure_type} />
            <BucketCard title="Top Insolvenzgerichte" items={data.by_court} />
          </div>

          <div className="card mt-3">
            <div className="card-header">Monatlicher Trend</div>
            <div className="trend-row">
              {data.monthly_trend.length === 0 && <span className="text-muted">Keine Trenddaten vorhanden.</span>}
              {data.monthly_trend.map(point => (
                <div key={point.period} className="trend-item">
                  <div
                    className="trend-bar"
                    style={{ height: `${Math.max(8, point.count * 12)}px` }}
                    title={`${point.period}: ${point.count}`}
                  />
                  <div className="trend-label">{point.period.slice(5)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card mt-3">
            <div className="card-header">Neueste Insolvenz-Signale</div>
            {data.latest_events.length === 0 ? (
              <div className="loading">Keine Ereignisse gefunden.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Titel</th>
                    <th>Region</th>
                    <th>Verfahren</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data.latest_events.map(event => (
                    <tr key={event.id}>
                      <td><Link to={`/events/${event.id}`}>{event.company_name || event.title}</Link></td>
                      <td>{event.company?.bundesland || <span className="text-muted">—</span>}</td>
                      <td>{event.procedure_type || <span className="text-muted">—</span>}</td>
                      <td><Badge variant="red">{Math.round(event.insolvency_score * 100)}%</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function BucketCard({ title, items }) {
  const max = Math.max(...items.map(item => item.count), 1)
  return (
    <div className="card bucket-card">
      <div className="card-header">{title}</div>
      <div className="bucket-list">
        {items.length === 0 && <span className="text-muted">Keine Daten.</span>}
        {items.map(item => (
          <div key={item.label} className="bucket-row">
            <div className="bucket-label">{item.label}</div>
            <div className="bucket-track">
              <div className="bucket-fill" style={{ width: `${(item.count / max) * 100}%` }} />
            </div>
            <div className="bucket-count">{item.count}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
