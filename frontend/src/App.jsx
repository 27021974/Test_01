import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import EventDetail from './pages/EventDetail.jsx'
import MarketInsights from './pages/MarketInsights.jsx'
import Sources from './pages/Sources.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="navbar">
          <span className="navbar-brand">📊 Marktbeobachtung</span>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/market">Market Insights</NavLink>
          <NavLink to="/sources">Quellen</NavLink>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/market" element={<MarketInsights />} />
            <Route path="/events/:id" element={<EventDetail />} />
            <Route path="/sources" element={<Sources />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
