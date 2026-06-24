import { useState, useEffect } from 'react'
import { fetchSources } from '../api.js'
import Badge from '../components/Badge.jsx'

export default function Sources() {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSources()
      .then(setSources)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Lädt…</div>
  if (error) return <div className="error-msg">{error}</div>

  return (
    <div>
      <h1 className="page-title">Datenquellen</h1>
      <div className="source-list">
        {sources.length === 0 && (
          <p className="text-muted">Keine Quellen konfiguriert. Starte den Backend-Server und triggere einmal einen Fetch.</p>
        )}
        {sources.map(s => (
          <div key={s.id} className="card" style={{ padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span className="source-name" style={{ fontWeight: 700 }}>{s.name}</span>
                <div className="source-meta mt-1">
                  <a href={s.base_url} target="_blank" rel="noopener noreferrer">{s.base_url}</a>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {s.enabled
                  ? <Badge variant="green">Aktiv</Badge>
                  : <Badge variant="gray">Deaktiviert</Badge>
                }
                <ModeBadge mode={s.mode} />
                <StatusBadge status={s.last_fetch_status} />
              </div>
            </div>

            {s.mode === 'degraded' && (
              <div className="degraded-banner mt-2">
                ⚠️ <strong>Eingeschränkter Modus:</strong> Kein automatisierter Datenabruf möglich.
              </div>
            )}

            {s.legal_note && (
              <div className="source-legal mt-2">
                ⚖️ <strong>Rechtlicher Hinweis:</strong> {s.legal_note}
              </div>
            )}

            <div className="mt-2" style={{ fontSize: '.8rem', color: '#718096' }}>
              {s.last_fetch_at
                ? <>Letzter Abruf: {new Date(s.last_fetch_at).toLocaleString('de-DE')}</>
                : 'Noch kein Abruf durchgeführt.'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ModeBadge({ mode }) {
  if (mode === 'degraded') return <Badge variant="yellow">Degraded</Badge>
  if (mode === 'rss') return <Badge variant="blue">RSS</Badge>
  return <Badge variant="green">{mode}</Badge>
}

function StatusBadge({ status }) {
  if (!status) return null
  if (status === 'ok') return <Badge variant="green">OK</Badge>
  if (status === 'error') return <Badge variant="red">Fehler</Badge>
  if (status === 'skipped') return <Badge variant="gray">Übersprungen</Badge>
  return <Badge variant="gray">{status}</Badge>
}
