import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchEvent } from '../api.js'
import ScoreBar from '../components/ScoreBar.jsx'
import Badge from '../components/Badge.jsx'

export default function EventDetail() {
  const { id } = useParams()
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchEvent(id)
      .then(setEvent)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading">Lädt…</div>
  if (error) return <div className="error-msg">{error}</div>
  if (!event) return null

  return (
    <div>
      <div className="mb-2">
        <Link to="/">← Zurück zur Übersicht</Link>
      </div>
      <h1 className="page-title">{event.title}</h1>

      <div className="detail-grid">
        {/* Main */}
        <div>
          <div className="card" style={{ padding: '1.25rem' }}>
            <DetailField label="Quelle">
              <Badge variant="blue">{event.source_name || '—'}</Badge>
            </DetailField>
            <DetailField label="Ereignistyp">
              {event.insolvency_score >= 0.5
                ? <Badge variant="red">Insolvenz</Badge>
                : <Badge variant="gray">{event.event_type}</Badge>
              }
            </DetailField>
            <DetailField label="Insolvenz-Score">
              <ScoreBar score={event.insolvency_score} showValue />
            </DetailField>
            <DetailField label="Datenvollständigkeit">
              {event.data_incomplete
                ? <Badge variant="yellow">⚠ Unvollständig – KMU-Kennzahlen fehlen</Badge>
                : <Badge variant="green">Vollständig</Badge>
              }
            </DetailField>
            <DetailField label="Veröffentlicht">
              {event.published_at
                ? new Date(event.published_at).toLocaleString('de-DE')
                : '—'}
            </DetailField>
            <DetailField label="Erfasst am">
              {new Date(event.fetched_at).toLocaleString('de-DE')}
            </DetailField>
            {event.url && (
              <DetailField label="Quell-URL">
                <a href={event.url} target="_blank" rel="noopener noreferrer">{event.url}</a>
              </DetailField>
            )}
            {event.raw_excerpt && (
              <DetailField label="Auszug">
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '.8rem', color: '#4a5568', background: '#f7fafc', padding: '.75rem', borderRadius: '6px', margin: 0 }}>
                  {event.raw_excerpt}
                </pre>
              </DetailField>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div>
          <div className="card" style={{ padding: '1.25rem' }}>
            <h3 style={{ margin: '0 0 .75rem', fontSize: '.9rem' }}>Unternehmen</h3>
            {event.company ? (
              <>
                <DetailField label="Name">{event.company.name}</DetailField>
                {event.company.registry_id && (
                  <DetailField label="Handelsregister-Nr.">{event.company.registry_id}</DetailField>
                )}
                {event.company.location && (
                  <DetailField label="Ort">{event.company.location}</DetailField>
                )}
                {event.company.employees != null ? (
                  <DetailField label="Mitarbeiter">{event.company.employees}</DetailField>
                ) : (
                  <DetailField label="Mitarbeiter"><span className="text-muted">unbekannt</span></DetailField>
                )}
                {event.company.revenue_eur != null ? (
                  <DetailField label="Jahresumsatz">
                    {new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(event.company.revenue_eur)}
                  </DetailField>
                ) : (
                  <DetailField label="Jahresumsatz"><span className="text-muted">unbekannt</span></DetailField>
                )}
              </>
            ) : (
              <p className="text-muted">Kein Unternehmen zugeordnet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function DetailField({ label, children }) {
  return (
    <div className="detail-field">
      <div className="field-label">{label}</div>
      <div className="field-value">{children}</div>
    </div>
  )
}
