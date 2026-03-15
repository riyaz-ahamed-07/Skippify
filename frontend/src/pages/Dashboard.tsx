import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { studentApi } from '../lib/api';
import { LayoutDashboard, Calendar as CalendarIcon, LogOut, AlertTriangle, MoreHorizontal, ChevronDown, ChevronUp, Calculator, Plus, Minus } from 'lucide-react';
import { DashboardSkeleton } from '../components/Skeleton';

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSubject, setExpandedSubject] = useState<string | null>(null);
  const userId = localStorage.getItem('skippify_user_id');

  useEffect(() => {
    if (!userId) {
      navigate('/onboarding');
      return;
    }
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await studentApi.getDashboard(parseInt(userId!));
      setData(res.data);
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 404) {
        localStorage.removeItem('skippify_user_id');
        navigate('/onboarding');
      } else {
        alert('Failed to fetch dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  const updateAttendance = async (component: 'subject' | 'mentor', offering_id: number | null, action: 'increment' | 'decrement') => {
    try {
      await studentApi.updateAttendance({
        user_id: parseInt(userId!),
        offering_id: offering_id || undefined,
        component,
        action,
        hours: component === 'mentor' ? 1 : 1 // Each click is 1 hour
      });
      fetchData(); // Refresh to show new numbers
    } catch (err) {
      console.error(err);
      alert('Failed to update attendance');
    }
  };

  if (loading) return (
    <div className="dashboard-page">
      <DashboardSkeleton />
    </div>
  );
  if (!data) return null;

  return (
    <div className="dashboard-page">
      <div className="nav-header">
        <div className="logo" onClick={() => navigate('/')}>
          SKIPPIFY
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="brutal-btn brutal-btn-primary" onClick={() => navigate('/day-view')}>
            <CalendarIcon size={18} /> Day View
          </button>
          <button className="brutal-btn" style={{ background: 'white' }} onClick={() => { localStorage.clear(); navigate('/'); }}>
            <LogOut size={18} />
          </button>
        </div>
      </div>

      <header style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Welcome back. Here is your strategic summary.</p>
      </header>

      <div className="overall-gauge brutal-card glass" style={{ marginBottom: '3rem' }}>
        <div className="badge badge-mid" style={{ marginBottom: '1rem' }}>Overall Weighted Attendance</div>
        <div className="gauge-value text-gradient">{data.current_overall_pct}%</div>
        <div style={{ display: 'flex', gap: '2rem', marginTop: '1.5rem', fontWeight: 600 }}>
          <div style={{ color: 'var(--text-secondary)' }}>Target: <span style={{ color: 'white' }}>{data.target_pct}%</span></div>
          <div style={{ color: 'var(--text-secondary)' }}>Projected: <span style={{ color: 'var(--accent-cyan)' }}>{data.projected_overall_pct}%</span></div>
        </div>
      </div>

      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <LayoutDashboard /> Subjects
      </h2>

      <div className="dashboard-grid">
        {data.subjects.map((s: any) => (
          <div key={s.subject_code} className={`brutal-card ${s.at_risk ? 'at-risk' : ''}`} style={{ 
            position: 'relative',
            borderLeftColor: s.at_risk ? 'var(--accent-pink)' : 'var(--accent-lime)',
            borderLeftWidth: '8px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontWeight: 900, fontSize: '1.25rem' }}>{s.subject_code}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{s.subject_name}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                <div className={`badge ${s.current_pct >= 80 ? 'badge-high' : s.current_pct >= 75 ? 'badge-mid' : 'badge-low'}`}>
                  {s.current_pct}%
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="brutal-btn" style={{ padding: '2px', minWidth: '24px', height: '24px', boxShadow: 'none' }} onClick={() => updateAttendance('subject', s.offering_id, 'decrement')}>
                        <Minus size={12} />
                    </button>
                    <button className="brutal-btn" style={{ padding: '2px', minWidth: '24px', height: '24px', boxShadow: 'none' }} onClick={() => updateAttendance('subject', s.offering_id , 'increment')}>
                        <Plus size={12} />
                    </button>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <div className="form-label" style={{ marginBottom: '1rem' }}>Projections</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="brutal-card" style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Must Attend</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--accent-purple)' }}>{s.must_attend}</div>
                </div>
                <div className="brutal-card" style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                   <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>Can Skip</div>
                   <div style={{ fontSize: '1.5rem', fontWeight: 900, color: s.can_skip > 0 ? 'var(--accent-lime)' : 'var(--accent-pink)' }}>{s.can_skip}</div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <div style={{ color: 'var(--text-muted)' }}>Projected End-of-Term</div>
              <div style={{ fontWeight: 800, color: 'var(--accent-cyan)' }}>{s.projected_pct}%</div>
            </div>

            {s.at_risk && (
              <div style={{ 
                marginTop: '1rem', padding: '0.5rem', background: 'rgba(241, 91, 181, 0.1)', 
                color: 'var(--accent-pink)', fontSize: '0.75rem', fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: '0.5rem'
              }}>
                <AlertTriangle size={14} /> NO SAFE SKIPS LEFT
              </div>
            )}

            <button 
              className="brutal-btn" 
              style={{ 
                width: '100%', marginTop: '1rem', padding: '0.5rem', fontSize: '0.75rem', 
                background: expandedSubject === s.subject_code ? 'var(--bg-primary)' : 'white' 
              }}
              onClick={() => setExpandedSubject(expandedSubject === s.subject_code ? null : s.subject_code)}
            >
              {expandedSubject === s.subject_code ? <><ChevronUp size={14} /> Hide Details</> : <><ChevronDown size={14} /> Strategic Breakdown</>}
            </button>

            {expandedSubject === s.subject_code && (
              <div style={{ 
                marginTop: '1rem', padding: '1rem', background: 'var(--bg-primary)', 
                border: '1px dashed var(--border-color)', animation: 'fadeIn 0.3s ease-out' 
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-purple)' }}>
                  <Calculator size={14} />
                  <span style={{ fontWeight: 800, fontSize: '0.75rem', textTransform: 'uppercase' }}>Show Your Work</span>
                </div>
                
                <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Current Hours:</span>
                    <span style={{ fontWeight: 700 }}>{s.current_attended} / {s.current_total}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Remaining Classes:</span>
                    <span style={{ fontWeight: 700 }}>{s.future_classes}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Remaining Hours:</span>
                    <span style={{ fontWeight: 700 }}>{s.remaining_hours}</span>
                  </div>
                  <div style={{ borderBottom: '1px solid var(--border-glass)', margin: '0.25rem 0' }}></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Target Total:</span>
                    <span style={{ fontWeight: 700 }}>{s.final_total_hours} hrs</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Target ({data.target_pct}%):</span>
                    <span style={{ fontWeight: 800, color: 'var(--accent-cyan)' }}>{s.required_attended_hours} hrs</span>
                  </div>
                  <div style={{ borderBottom: '1px solid var(--border-glass)', margin: '0.25rem 0' }}></div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span style={{ fontWeight: 700 }}>Extra Needed:</span>
                    <span style={{ fontWeight: 900, color: 'var(--accent-purple)' }}>{s.extra_hours_needed} hrs</span>
                  </div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '0.5rem' }}>
                    *Calculated by counting teaching days until term end, excluding Sundays and holidays.*
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="brutal-card glass" style={{ marginTop: '4rem', display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
          <MoreHorizontal size={32} color="var(--accent-purple)" />
        </div>
        <div style={{ flex: 1 }}>
          <h4>Extra Components</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Mentor: {data.mentor_attended}/{data.mentor_total} hrs | Program: {data.program_attended}/{data.program_total} hrs
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 800, marginBottom: '0.25rem' }}>MENTOR</div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button className="brutal-btn" style={{ padding: '4px', minWidth: '32px', height: '32px' }} onClick={() => updateAttendance('mentor', null, 'decrement')}>
                        <Minus size={14} />
                    </button>
                    <button className="brutal-btn" style={{ padding: '4px', minWidth: '32px', height: '32px' }} onClick={() => updateAttendance('mentor', null, 'increment')}>
                        <Plus size={14} />
                    </button>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
