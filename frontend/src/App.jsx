import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import EventDetail from './pages/EventDetail.jsx'
import Sources from './pages/Sources.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="navbar">
          <span className="navbar-brand">📊 Marktbeobachtung</span>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/sources">Quellen</NavLink>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/events/:id" element={<EventDetail />} />
            <Route path="/sources" element={<Sources />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
