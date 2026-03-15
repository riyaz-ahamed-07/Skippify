import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { studentApi } from '../lib/api';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

export default function DayView() {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date().toISOString().split('T')[0]);
  const userId = localStorage.getItem('skippify_user_id');

  useEffect(() => {
    if (!userId) { navigate('/onboarding'); return; }
    fetchDay(currentDate);
  }, [userId, currentDate]);

  const fetchDay = async (dateStr: string) => {
    try {
      setLoading(true);
      const res = await studentApi.getDayView(parseInt(userId!), dateStr);
      setData(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to fetch day schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (offeringId: number, action: 'attend' | 'skip', hours: number) => {
    try {
      await studentApi.updateAttendance({
        user_id: parseInt(userId!),
        offering_id: offeringId,
        action,
        hours
      });
      fetchDay(currentDate); // Refresh
    } catch (err) {
      console.error(err);
      alert('Failed to update attendance');
    }
  };

  const adjustDate = (days: number) => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + days);
    setCurrentDate(d.toISOString().split('T')[0]);
  };

  if (loading && !data) return <div style={{ padding: '4rem', textAlign: 'center' }}>Loading schedule...</div>;

  return (
    <div className="day-view-page">
      <div className="nav-header">
        <div className="logo" onClick={() => navigate('/')}>
          SKIPPIFY
        </div>
        <button className="brutal-btn" style={{ background: 'var(--bg-secondary)' }} onClick={() => navigate('/dashboard')}>
          <ChevronLeft size={18} /> Dashboard
        </button>
      </div>

      <header style={{ marginBottom: '3rem', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', marginBottom: '1rem' }}>
          <button className="brutal-btn" onClick={() => adjustDate(-1)}><ChevronLeft /></button>
          <h1 style={{ minWidth: '300px' }}>{new Date(currentDate).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</h1>
          <button className="brutal-btn" onClick={() => adjustDate(1)}><ChevronRight /></button>
        </div>
        <button className="brutal-btn brutal-btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }} onClick={() => setCurrentDate(new Date().toISOString().split('T')[0])}>
          Today
        </button>
      </header>

      {!data?.is_teaching_day ? (
        <div className="brutal-card glass" style={{ textAlign: 'center', padding: '5rem 2rem' }}>
          <CalendarIcon size={64} color="var(--text-muted)" style={{ marginBottom: '1.5rem' }} />
          <h3>No Classes Scheduled</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>Enjoy your holiday or exam break!</p>
        </div>
      ) : (
        <div className="classes-list" style={{ maxWidth: '800px', margin: '0 auto' }}>
          {data.classes.length === 0 ? (
             <div className="brutal-card glass" style={{ textAlign: 'center', padding: '3rem' }}>
               <p>No timetable slots for this weekday.</p>
             </div>
          ) : data.classes.map((c: any) => (
            <div key={`${c.offering_id}-${c.start_time}`} className="brutal-card glass" style={{ marginBottom: '1.5rem', display: 'grid', gridTemplateColumns: '120px 1fr auto', gap: '2rem', alignItems: 'center' }}>
              <div style={{ borderRight: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 800 }}>
                  <Clock size={16} color="var(--accent-cyan)" /> {c.start_time}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>to {c.end_time}</div>
              </div>

              <div>
                <div style={{ fontWeight: 900, fontSize: '1.4rem' }}>{c.subject_code}</div>
                <div style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{c.subject_name}</div>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', fontSize: '0.8rem' }}>
                   {c.duration_hours > 1 && <span className="badge badge-mid">{c.duration_hours} hrs</span>}
                   <span className={c.can_skip_this ? 'badge badge-high' : 'badge badge-low'}>
                     {c.can_skip_this ? `Safe to Skip (${c.remaining_skips} left)` : 'MUST ATTEND'}
                   </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <button 
                  className="brutal-btn brutal-btn-primary" 
                  style={{ width: '120px', fontSize: '0.75rem' }}
                  onClick={() => handleAction(c.offering_id, 'attend', c.duration_hours)}
                >
                  <CheckCircle size={16} /> Present
                </button>
                <button 
                  className="brutal-btn brutal-btn-danger" 
                  style={{ width: '120px', fontSize: '0.75rem' }}
                  onClick={() => handleAction(c.offering_id, 'skip', c.duration_hours)}
                >
                  <XCircle size={16} /> Absent
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {data?.is_teaching_day && data.classes.length > 0 && (
         <div style={{ textAlign: 'center', marginTop: '3rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
           <AlertCircle size={16} />
           <span>Actions will instantly update your end-of-term projections.</span>
         </div>
      )}
    </div>
  );
}
