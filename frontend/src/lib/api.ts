import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

// Admin API
export const adminApi = {
  uploadCalendar: (formData: FormData) => api.post('/api/admin/calendar/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  listCalendars: () => api.get('/api/admin/calendars'),
  activateCalendar: (id: number) => api.post(`/api/admin/calendar/${id}/activate`),
  uploadEnrolment: (formData: FormData, year?: number, branch?: string, semester?: number) => {
    let url = '/api/admin/enrolment/upload';
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    if (branch) params.append('branch', branch);
    if (semester) params.append('semester', semester.toString());
    if (params.toString()) url += `?${params.toString()}`;
    return api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadEnrolmentText: (data: { text: string; year?: number; branch?: string; semester?: number }) => 
    api.post('/api/admin/enrolment/text', data),
  listSubjects: (params: any) => api.get('/api/admin/subjects', { params }),
};

// Student API
export const studentApi = {
  getConfig: (params?: any) => api.get('/api/config', { params }),
  setupUser: (data: any) => api.post('/api/user/setup', data),
  getDashboard: (userId: number) => api.get(`/api/dashboard/${userId}`),
  getDayView: (userId: number, date?: string) => api.get(`/api/day-view/${userId}`, { params: { view_date: date } }),
  updateAttendance: (data: { user_id: number; offering_id?: number; component?: string; action: 'attend' | 'skip' | 'increment' | 'decrement'; hours?: number }) => 
    api.post('/api/attendance/update', data),
};
