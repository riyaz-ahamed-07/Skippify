import { useNavigate } from 'react-router-dom';
import { Calendar, ShieldCheck, Zap } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing-page" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
      <div className="nav-header">
        <div className="logo">
          SKIPPIFY
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="brutal-btn brutal-btn-secondary" onClick={() => navigate('/admin')}>
            Admin
          </button>
        </div>
      </div>

      <header style={{ marginBottom: '5rem' }}>
        <h1 style={{ fontSize: '4.5rem', marginBottom: '1.5rem' }}>
          TRACK ATTENDANCE.<br />
          <span className="text-gradient">PLAN YOUR SKIPS.</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.25rem', maxWidth: '700px', margin: '0 auto 3rem', fontWeight: 500 }}>
          Skippify helps engineering students manage their safe bunks while staying above target attendance. 
          No ERP logins. Just pure deterministic planning.
        </p>
        <button 
          className="brutal-btn brutal-btn-primary" 
          style={{ padding: '1.5rem 3rem', fontSize: '1.25rem' }}
          onClick={() => navigate('/onboarding')}
        >
          Get Started Now
        </button>
      </header>

      <div className="dashboard-grid" style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div className="brutal-card">
          <Zap size={40} color="var(--accent-lime)" style={{ marginBottom: '1rem' }} />
          <h3>Smart Projections</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Know exactly how many classes you can skip in each subject and still hit 80%.</p>
        </div>
        <div className="brutal-card">
          <Calendar size={40} color="var(--accent-purple)" style={{ marginBottom: '1rem' }} />
          <h3>Calendar Sync</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Integrates with your college's academic calendar (holidays, CIA, events).</p>
        </div>
        <div className="brutal-card">
          <ShieldCheck size={40} color="var(--accent-cyan)" style={{ marginBottom: '1rem' }} />
          <h3>Private & Safe</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>No credentials collected. Your data, your planning, your peace of mind.</p>
        </div>
      </div>

      <footer style={{ marginTop: '8rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        <p>© 2026 Skippify for Engineering Students. Built with precision.</p>
      </footer>
    </div>
  );
}
