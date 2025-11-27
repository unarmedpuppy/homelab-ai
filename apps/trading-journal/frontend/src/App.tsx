import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ErrorBoundary from './components/common/ErrorBoundary'
import Dashboard from './pages/Dashboard'
import Calendar from './pages/Calendar'
import DailyJournal from './pages/DailyJournal'
import Playbooks from './pages/Playbooks'
import PlaybookDetails from './pages/PlaybookDetails'
import Analytics from './pages/Analytics'
import TradeEntry from './pages/TradeEntry'
import Charts from './pages/Charts'

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/daily/:date?" element={<DailyJournal />} />
            <Route path="/playbooks" element={<Playbooks />} />
            <Route path="/playbooks/:id" element={<PlaybookDetails />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/trade-entry" element={<TradeEntry />} />
            <Route path="/charts/:ticker?" element={<Charts />} />
            <Route path="/charts/trade/:tradeId" element={<Charts />} />
          </Routes>
        </ErrorBoundary>
      </Layout>
    </ErrorBoundary>
  )
}

export default App

