import { useState, useEffect } from 'react';
import { adminApi } from '../lib/api';
import { Upload, FileText, Calendar, CheckCircle, Settings } from 'lucide-react';

export default function Admin() {
  const [calendars, setCalendars] = useState<any[]>([]);
  const [calFile, setCalFile] = useState<File | null>(null);
  const [enrolFile, setEnrolFile] = useState<File | null>(null);
  const [enrolText, setEnrolText] = useState('');
  const [inputType, setInputType] = useState<'file' | 'text'>('file');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Enrolment filters
  const [filters, setFilters] = useState({ year: 3, branch: 'AI&DS', semester: 6 });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const res = await adminApi.listCalendars();
    setCalendars(res.data);
  };

  const handleCalUpload = async () => {
    if (!calFile) return;
    try {
      setLoading(true);
      const fd = new FormData();
      fd.append('file', calFile);
      const res = await adminApi.uploadCalendar(fd);
      setMessage(`Calendar saved ID: ${res.data.id}. Please activate.`);
      fetchData();
    } catch (err) {
      console.error(err);
      setMessage('Failed to upload calendar');
    } finally {
      setLoading(false);
    }
  };

  const handleEnrolUpload = async () => {
    if (inputType === 'file' && !enrolFile) return;
    if (inputType === 'text' && !enrolText) return;

    try {
      setLoading(true);
      if (inputType === 'file') {
        const fd = new FormData();
        fd.append('file', enrolFile!);
        const res = await adminApi.uploadEnrolment(fd, filters.year, filters.branch, filters.semester);
        setMessage(res.data.message);
      } else {
        const res = await adminApi.uploadEnrolmentText({
          text: enrolText,
          year: filters.year,
          branch: filters.branch,
          semester: filters.semester
        });
        setMessage(res.data.message);
        setEnrolText('');
      }
    } catch (err) {
      console.error(err);
      setMessage('Failed to upload enrolment');
    } finally {
      setLoading(false);
    }
  };

  const activateCal = async (id: number) => {
    const res = await adminApi.activateCalendar(id);
    setMessage(res.data.message);
    fetchData();
  };

  return (
    <div className="admin-page">
      <div className="nav-header">
        <div className="logo">SKIPPIFY ADMIN</div>
        <button className="brutal-btn" style={{ background: 'var(--bg-secondary)' }} onClick={() => window.location.href = '/'}>
          Site View
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
        <section>
          <h2 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Calendar /> Activity Calendars
          </h2>
          
          <div className="brutal-card glass" style={{ marginBottom: '2rem' }}>
            <label className="form-label">Upload PDF</label>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <input type="file" className="form-input" style={{ padding: '0.4rem' }} onChange={e => setCalFile(e.target.files?.[0] || null)} />
              <button 
                className="brutal-btn brutal-btn-primary" 
                onClick={handleCalUpload} 
                disabled={loading || !calFile}
              >
                <Upload size={16} /> {loading ? '...' : 'Upload'}
              </button>
            </div>
          </div>

          <div className="calendar-list">
            {calendars.map(c => (
              <div key={c.id} className="brutal-card" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 800 }}>{c.term}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{c.academic_year} | {c.start_date} to {c.last_working_date}</div>
                </div>
                {c.is_active ? (
                  <span className="badge badge-high"><CheckCircle size={12} /> Active</span>
                ) : (
                  <button className="brutal-btn brutal-btn-secondary" style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem' }} onClick={() => activateCal(c.id)}>
                    Activate
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText /> Enrolments (Timetable)
          </h2>

          <div className="brutal-card glass">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
               <div className="form-group" style={{ marginBottom: 0 }}>
                 <label className="form-label">Year</label>
                 <input type="number" className="form-input" value={filters.year} onChange={e => setFilters({...filters, year: parseInt(e.target.value)})} />
               </div>
               <div className="form-group" style={{ marginBottom: 0 }}>
                 <label className="form-label">Branch</label>
                 <input className="form-input" value={filters.branch} onChange={e => setFilters({...filters, branch: e.target.value})} />
               </div>
               <div className="form-group" style={{ marginBottom: 0 }}>
                 <label className="form-label">Sem</label>
                 <input type="number" className="form-input" value={filters.semester} onChange={e => setFilters({...filters, semester: parseInt(e.target.value)})} />
               </div>
            </div>
            
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
              <button 
                className={`brutal-btn ${inputType === 'file' ? 'brutal-btn-primary' : ''}`}
                style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                onClick={() => setInputType('file')}
              >
                File Upload
              </button>
              <button 
                className={`brutal-btn ${inputType === 'text' ? 'brutal-btn-primary' : ''}`}
                style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                onClick={() => setInputType('text')}
              >
                Paste Text
              </button>
            </div>
            
            <label className="form-label">{inputType === 'file' ? 'Upload PDF' : 'Paste Enrolment Text'}</label>
            {inputType === 'file' ? (
              <div style={{ display: 'flex', gap: '1rem' }}>
                <input type="file" className="form-input" style={{ padding: '0.4rem' }} onChange={e => setEnrolFile(e.target.files?.[0] || null)} />
                <button 
                  className="brutal-btn brutal-btn-primary" 
                  onClick={handleEnrolUpload} 
                  disabled={loading || !enrolFile}
                >
                  <Upload size={16} /> {loading ? '...' : 'Upload'}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <textarea 
                  className="form-input" 
                  style={{ minHeight: '150px', resize: 'vertical' }} 
                  placeholder="Paste subject list or timetable text here..."
                  value={enrolText}
                  onChange={e => setEnrolText(e.target.value)}
                />
                <button 
                  className="brutal-btn brutal-btn-primary" 
                  onClick={handleEnrolUpload} 
                  disabled={loading || !enrolText}
                >
                  <Upload size={16} /> {loading ? '...' : 'Process Text'}
                </button>
              </div>
            )}
          </div>

          <div style={{ marginTop: '2rem', padding: '1.5rem', border: '2px dashed var(--border-glass)', textAlign: 'center', color: 'var(--text-muted)' }}>
             <Settings size={32} style={{ marginBottom: '1rem', opacity: 0.5 }} />
             <p>Parsed subjects will appear in the student onboarding flow after upload.</p>
          </div>
        </section>
      </div>

      {message && (
        <div className="badge badge-mid" style={{ position: 'fixed', bottom: '2rem', right: '2rem', padding: '1rem 2rem', fontSize: '1rem' }}>
          {message}
        </div>
      )}
    </div>
  );
}
