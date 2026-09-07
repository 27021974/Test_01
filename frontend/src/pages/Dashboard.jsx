import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { fetchStats, fetchEvents, triggerFetch } from '../api.js'
import FilterBar from '../components/FilterBar.jsx'
import ScoreBar from '../components/ScoreBar.jsx'
import Badge from '../components/Badge.jsx'

const DEFAULT_FILTERS = {
  insolvency: '',
  max_employees: '',
  max_revenue: '',
  source: '',
  bundesland: '',
  industry: '',
  procedure_type: '',
  q: '',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [events, setEvents] = useState([])
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fetchLoading, setFetchLoading] = useState(false)
  const [fetchMsg, setFetchMsg] = useState(null)

  const loadData = useCallback(async (currentFilters) => {
    setLoading(true)
    setError(null)
    try {
      const [statsData, eventsData] = await Promise.all([
        fetchStats(),
        fetchEvents(currentFilters),
      ])
      setStats(statsData)
      setEvents(eventsData)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData(filters)
  }, []) // eslint-disable-line

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters)
    loadData(newFilters)
  }

  const handleManualFetch = async () => {
    const token = window.prompt('API-Token eingeben:')
    if (!token) return
    setFetchLoading(true)
    setFetchMsg(null)
    try {
      const res = await triggerFetch(token)
      setFetchMsg(`✅ Fetch abgeschlossen: ${JSON.stringify(res.summary)}`)
      loadData(filters)
    } catch (e) {
      setFetchMsg(`❌ Fehler: ${e.message}`)
    } finally {
      setFetchLoading(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>Insolvenz-Monitor</h1>
        <button
          className="btn btn-secondary"
          onClick={handleManualFetch}
          disabled={fetchLoading}
        >
          {fetchLoading ? 'Lädt…' : '🔄 Manuell abrufen'}
        </button>
      </div>

      {fetchMsg && <div className={fetchMsg.startsWith('✅') ? 'degraded-banner' : 'error-msg'} style={{ marginBottom: '1rem' }}>{fetchMsg}</div>}

      {/* KPI Tiles */}
      {stats && (
        <div className="kpi-grid">
          <div className="kpi-card new">
            <div className="label">Neue Treffer (24h)</div>
            <div className="value">{stats.new_events_24h}</div>
          </div>
          <div className="kpi-card new">
            <div className="label">Neue Treffer (7 Tage)</div>
            <div className="value">{stats.new_events_7d}</div>
          </div>
          <div className="kpi-card insolvency">
            <div className="label">Insolvenzen (24h)</div>
            <div className="value">{stats.insolvency_events_24h}</div>
          </div>
          <div className="kpi-card insolvency">
            <div className="label">Insolvenzen (7 Tage)</div>
            <div className="value">{stats.insolvency_events_7d}</div>
          </div>
        </div>
      )}

      {/* Degraded source notice */}
      {stats?.sources?.filter(s => s.mode === 'degraded').map(s => (
        <div key={s.id} className="degraded-banner">
          ⚠️ <strong>{s.name}</strong> ist im eingeschränkten Modus (degraded): {s.legal_note}
        </div>
      ))}

      {/* Filter Bar */}
      <FilterBar
        initialFilters={filters}
        onApply={handleApplyFilters}
        sources={stats?.sources || []}
      />

      {/* Events Table */}
      <div className="card">
        <div className="card-header">
          <span>Ereignisse {events.length > 0 && `(${events.length})`}</span>
          {loading && <span className="text-muted">Lädt…</span>}
        </div>
        {error && <div className="error-msg" style={{ margin: '1rem' }}>{error}</div>}
        {!loading && events.length === 0 && !error && (
          <div className="loading">Keine Ereignisse gefunden.</div>
        )}
        {events.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Titel</th>
                <th>Quelle</th>
                <th>Datum</th>
                <th>Region</th>
                <th>Branche</th>
                <th>Verfahren</th>
                <th>Score</th>
                <th>Typ</th>
                <th>Vollständigkeit</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {events.map(ev => (
                <tr key={ev.id}>
                  <td>
                    <Link to={`/events/${ev.id}`} className="truncate" style={{ display: 'block' }}>
                      {ev.title}
                    </Link>
                  </td>
                  <td><Badge variant="blue">{ev.source_name || '—'}</Badge></td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {ev.published_at
                      ? new Date(ev.published_at).toLocaleDateString('de-DE')
                      : <span className="text-muted">—</span>}
                  </td>
                  <td>{ev.company?.bundesland || ev.company_bundesland || <span className="text-muted">—</span>}</td>
                  <td>{ev.company?.industry || <span className="text-muted">—</span>}</td>
                  <td>{ev.procedure_type || <span className="text-muted">—</span>}</td>
                  <td>
                    <ScoreBar score={ev.insolvency_score} />
                  </td>
                  <td>
                    <EventTypeBadge type={ev.event_type} score={ev.insolvency_score} />
                  </td>
                  <td>
                    {ev.data_incomplete
                      ? <Badge variant="yellow">⚠ Unvollständig</Badge>
                      : <Badge variant="green">Vollständig</Badge>
                    }
                  </td>
                  <td>
                    {ev.url
                      ? <a href={ev.url} target="_blank" rel="noopener noreferrer">↗</a>
                      : <span className="text-muted">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function EventTypeBadge({ type, score }) {
  if (score >= 0.5) return <Badge variant="red">Insolvenz</Badge>
  if (type === 'insolvency') return <Badge variant="orange">Insolvenz-Hinweis</Badge>
  return <Badge variant="gray">{type}</Badge>
}
