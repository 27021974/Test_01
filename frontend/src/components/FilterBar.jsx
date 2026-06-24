import { useState } from 'react'

const KMU_EMPLOYEES = 50
const KMU_REVENUE = 10000000

export default function FilterBar({ initialFilters, onApply, sources }) {
  const [filters, setFilters] = useState(initialFilters)

  const set = (k, v) => setFilters(prev => ({ ...prev, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onApply(filters)
  }

  const handleReset = () => {
    const reset = { insolvency: '', max_employees: '', max_revenue: '', source: '', q: '' }
    setFilters(reset)
    onApply(reset)
  }

  const applyKMU = () => {
    const kmu = { ...filters, max_employees: KMU_EMPLOYEES, max_revenue: KMU_REVENUE }
    setFilters(kmu)
    onApply(kmu)
  }

  return (
    <form className="filter-bar" onSubmit={handleSubmit}>
      <div className="filter-group">
        <label>Suche (Titel)</label>
        <input
          type="text"
          placeholder="z.B. Insolvenz…"
          value={filters.q}
          onChange={e => set('q', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Nur Insolvenz</label>
        <select value={filters.insolvency} onChange={e => set('insolvency', e.target.value)}>
          <option value="">Alle</option>
          <option value="true">Ja (Score ≥ 0.5)</option>
          <option value="false">Nein</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Max. Mitarbeiter</label>
        <input
          type="number"
          min={1}
          placeholder="z.B. 50"
          value={filters.max_employees}
          onChange={e => set('max_employees', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Max. Umsatz (EUR)</label>
        <input
          type="number"
          min={0}
          placeholder="z.B. 10000000"
          value={filters.max_revenue}
          onChange={e => set('max_revenue', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Quelle</label>
        <select value={filters.source} onChange={e => set('source', e.target.value)}>
          <option value="">Alle</option>
          {sources.map(s => (
            <option key={s.id} value={s.name}>{s.name}</option>
          ))}
        </select>
      </div>

      <button type="submit" className="btn btn-primary">Filtern</button>
      <button
        type="button"
        className="btn btn-secondary"
        onClick={applyKMU}
        title="Setzt KMU-Filter: ≤50 Mitarbeiter, <10 Mio EUR Umsatz"
      >
        KMU-Filter
      </button>
      <button type="button" className="btn btn-secondary" onClick={handleReset}>Zurücksetzen</button>
    </form>
  )
}
