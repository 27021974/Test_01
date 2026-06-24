/**
 * Thin API client – proxied via Vite dev server to http://localhost:8000
 */
const BASE = import.meta.env.VITE_API_URL || ''

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

export function fetchStats() {
  return apiFetch('/api/stats')
}

export function fetchEvents(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') qs.set(k, v)
  })
  const q = qs.toString()
  return apiFetch(`/api/events${q ? '?' + q : ''}`)
}

export function fetchEvent(id) {
  return apiFetch(`/api/events/${id}`)
}

export function fetchSources() {
  return apiFetch('/api/sources')
}

export function triggerFetch(token) {
  return apiFetch('/api/jobs/fetch', {
    method: 'POST',
    headers: { 'X-Api-Token': token },
  })
}
