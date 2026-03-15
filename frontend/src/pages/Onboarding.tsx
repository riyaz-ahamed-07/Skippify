import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { studentApi } from '../lib/api';
import { ChevronRight, ChevronLeft, CheckCircle } from 'lucide-react';
import { Skeleton } from '../components/Skeleton';

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [calendars, setCalendars] = useState<any[]>([]);
  const [availableSubjects, setAvailableSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    target_pct: 80,
    calendar_id: 0,
    subjects: [] as any[],
    mentor_attended: 0,
    mentor_total: 0,
    program_attended: 0,
    program_total: 0,
    // Keep internal fields for compatibility but don't show to user
    year: 1,
    branch: 'GEN',
    section: 'A',
    semester: 1
  });

  useEffect(() => {
    const userId = localStorage.getItem('skippify_user_id');
    if (userId) {
      navigate('/dashboard');
    }
  }, [navigate]);

  useEffect(() => {
    if (step === 2) {
      setLoading(true);
      studentApi.getConfig() // No filters needed now
        .then(res => {
          setCalendars(res.data.calendars);
          setAvailableSubjects(res.data.subjects);
          if (res.data.calendars.length > 0 && !formData.calendar_id) {
            setFormData(prev => ({ ...prev, calendar_id: res.data.calendars[0].id }));
          }
        })
        .finally(() => setLoading(false));
    }
  }, [step]);

  const handleNext = () => setStep(s => s + 1);
  const handleBack = () => setStep(s => s - 1);

  const toggleSubject = (subj: any) => {
    const isSelected = formData.subjects.find(s => s.offering_id === subj.offerings[0]?.id);
    if (isSelected) {
      setFormData(prev => ({
        ...prev,
        subjects: prev.subjects.filter(s => s.offering_id !== subj.offerings[0]?.id)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        subjects: [...prev.subjects, { 
          offering_id: subj.offerings[0]?.id, 
          code: subj.code, 
          name: subj.name,
          attended_hours: 0, 
          total_hours: 0 
        }]
      }));
    }
  };

  const updateSubjHours = (oid: number, field: string, val: number) => {
    setFormData(prev => ({
      ...prev,
      subjects: prev.subjects.map(s => s.offering_id === oid ? { ...s, [field]: val } : s)
    }));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const res = await studentApi.setupUser(formData);
      localStorage.setItem('skippify_user_id', res.data.user_id.toString());
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert('Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-wizard">
      <div className="logo" style={{ justifyContent: 'center', marginBottom: '3rem' }}>
        SKIPPIFY
      </div>

      <div className="step-indicator">
        {[1, 2, 3, 4].map(s => (
          <div key={s} className={`step-dot ${s <= step ? 'active' : ''}`} />
        ))}
      </div>

      <div className="brutal-card glass">
        {step === 1 && (
          <div className="step-content">
            <h2 style={{ marginBottom: '1.5rem' }}>Tell us about yourself</h2>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input 
                className="form-input" 
                value={formData.name} 
                onChange={e => setFormData({ ...formData, name: e.target.value })} 
                placeholder="Enter your name"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Target Percentage (%)</label>
              <input 
                type="number" 
                className="form-input" 
                value={formData.target_pct} 
                onChange={e => setFormData({ ...formData, target_pct: parseFloat(e.target.value) || 0 })} 
              />
              <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                We'll use this to calculate how many classes you can safely skip.
              </p>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="step-content">
            <h2 style={{ marginBottom: '1.5rem' }}>Select Calendar & Subjects</h2>
            <div className="form-group">
              <label className="form-label">Academic Calendar</label>
              {loading ? <Skeleton height="2.5rem" /> : (
                <select 
                  className="form-input form-select" 
                  value={formData.calendar_id} 
                  onChange={e => setFormData({ ...formData, calendar_id: parseInt(e.target.value) })}
                >
                  {calendars.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.academic_year} - {c.term}
                    </option>
                  ))}
                  {calendars.length === 0 && <option>No active calendars</option>}
                </select>
              )}
            </div>
            
            <label className="form-label">Enrolled Subjects</label>
            <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '1rem' }}>
              {loading ? (
                [1, 2, 3, 4].map(i => <Skeleton key={i} height="3.5rem" style={{ marginBottom: '0.5rem' }} />)
              ) : (
                availableSubjects.map(s => {
                const isSelected = formData.subjects.find(sub => sub.offering_id === s.offerings[0]?.id);
                return (
                  <div 
                    key={s.id} 
                    className="brutal-card" 
                    style={{ 
                      padding: '0.75rem', 
                      marginBottom: '0.5rem', 
                      cursor: 'pointer',
                      borderColor: isSelected ? 'var(--accent-lime)' : 'var(--border-color)',
                      background: isSelected ? 'rgba(193, 255, 0, 0.05)' : 'transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem'
                    }}
                    onClick={() => toggleSubject(s)}
                  >
                    <div style={{ 
                      width: '20px', height: '20px', border: '1px solid var(--border-color)', 
                      background: isSelected ? 'var(--accent-lime)' : 'transparent' 
                    }} />
                    <div>
                      <div style={{ fontWeight: 800 }}>{s.code}</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{s.name}</div>
                    </div>
                  </div>
                );
              })
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="step-content">
            <h2 style={{ marginBottom: '1.5rem' }}>Current Attendance</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Enter your current total and attended hours from MyCamu.
            </p>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {formData.subjects.map(s => (
                <div key={s.offering_id} className="brutal-card" style={{ marginBottom: '1rem' }}>
                  <div style={{ fontWeight: 800, marginBottom: '0.75rem' }}>{s.code} - {s.name}</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">Attended Hrs</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={s.attended_hours} 
                        onChange={e => updateSubjHours(s.offering_id, 'attended_hours', parseFloat(e.target.value) || 0)} 
                      />
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label">Total Hrs</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={s.total_hours} 
                        onChange={e => updateSubjHours(s.offering_id, 'total_hours', parseFloat(e.target.value) || 0)} 
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="step-content">
            <h2 style={{ marginBottom: '1.5rem' }}>Other Components</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Final step! Add any extra hours that count toward your weighted overall.
            </p>
            <div className="brutal-card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: 800, marginBottom: '0.75rem' }}>Mentor Meetings</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Attended</label>
                  <input type="number" className="form-input" value={formData.mentor_attended} onChange={e => setFormData({...formData, mentor_attended: parseFloat(e.target.value) || 0})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Total</label>
                  <input type="number" className="form-input" value={formData.mentor_total} onChange={e => setFormData({...formData, mentor_total: parseFloat(e.target.value) || 0})} />
                </div>
              </div>
            </div>
            <div className="brutal-card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: 800, marginBottom: '0.75rem' }}>Program/Events</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Attended</label>
                  <input type="number" className="form-input" value={formData.program_attended} onChange={e => setFormData({...formData, program_attended: parseFloat(e.target.value) || 0})} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Total</label>
                  <input type="number" className="form-input" value={formData.program_total} onChange={e => setFormData({...formData, program_total: parseFloat(e.target.value) || 0})} />
                </div>
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem', gap: '1rem' }}>
          {step > 1 && (
            <button className="brutal-btn" style={{ background: 'var(--bg-secondary)', flex: 1 }} onClick={handleBack}>
              <ChevronLeft /> Back
            </button>
          )}
          {step < 4 ? (
            <button 
              className="brutal-btn brutal-btn-primary" 
              style={{ flex: 1, marginLeft: step === 1 ? 'auto' : 0 }} 
              onClick={handleNext}
              disabled={step === 1 && !formData.name}
            >
              Next <ChevronRight />
            </button>
          ) : (
            <button className="brutal-btn brutal-btn-primary" style={{ flex: 1 }} onClick={handleSubmit} disabled={loading}>
              {loading ? 'Processing...' : (
                <><CheckCircle /> Finish Setup</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
