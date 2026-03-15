import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import DayView from './pages/DayView';
import Admin from './pages/Admin';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/day-view" element={<DayView />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
