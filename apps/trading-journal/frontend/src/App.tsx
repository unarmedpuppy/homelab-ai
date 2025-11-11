import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Calendar from './pages/Calendar'
import DailyJournal from './pages/DailyJournal'
import TradeEntry from './pages/TradeEntry'
import Charts from './pages/Charts'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/daily/:date?" element={<DailyJournal />} />
        <Route path="/trade-entry" element={<TradeEntry />} />
        <Route path="/charts/:ticker?" element={<Charts />} />
        <Route path="/charts/trade/:tradeId" element={<Charts />} />
      </Routes>
    </Layout>
  )
}

export default App

