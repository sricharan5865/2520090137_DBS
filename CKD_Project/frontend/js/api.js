// ====================================================================
// SMART CKD FRONTEND - API CLIENT & AUTHENTICATION HELPER
// ====================================================================

const API_BASE = (typeof window !== 'undefined' && window.API_BASE) ? window.API_BASE : '/api';

const API = {
  getToken() {
    return localStorage.getItem('ckd_token');
  },

  getUser() {
    const userStr = localStorage.getItem('ckd_user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setAuth(token, user) {
    localStorage.setItem('ckd_token', token);
    localStorage.setItem('ckd_user', JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem('ckd_token');
    localStorage.removeItem('ckd_user');
    window.location.href = '/login.html';
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};
    
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401) {
        this.clearAuth();
        throw new Error('Session expired. Please log in again.');
      }

      const data = await response.json();
      if (!response.ok) {
        let msg = 'An error occurred during request processing';
        if (typeof data.detail === 'string') {
          msg = data.detail;
        } else if (Array.isArray(data.detail)) {
          msg = data.detail.map(d => {
            const loc = d.loc ? d.loc.filter(l => l !== 'body').join(' ') : '';
            return `${loc ? loc + ': ' : ''}${d.msg}`;
          }).join(', ');
        } else if (data.detail && typeof data.detail === 'object') {
          msg = JSON.stringify(data.detail);
        }
        throw new Error(msg);
      }

      return data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  login(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  },

  registerPatient(patientData) {
    return this.request('/auth/register/patient', {
      method: 'POST',
      body: JSON.stringify(patientData)
    });
  },

  getProfile() {
    return this.request('/auth/me');
  },

  // Patients
  getPatientOverview() {
    return this.request('/patients/me/dashboard-overview');
  },

  submitAssessment(formData) {
    return this.request('/patients/me/assessment', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
  },

  getMyLabReports() {
    return this.request('/patients/me/lab-reports');
  },

  getMyPredictions() {
    return this.request('/patients/me/predictions');
  },

  // Appointments
  getAppointments(statusFilter = null) {
    const q = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : '';
    return this.request(`/appointments${q}`);
  },

  bookAppointment(appData) {
    return this.request('/appointments', {
      method: 'POST',
      body: JSON.stringify(appData)
    });
  },

  updateAppointmentStatus(id, statusData) {
    return this.request(`/appointments/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify(statusData)
    });
  },

  // Laboratory
  getLabTests(statusFilter = null, patientId = null) {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    if (patientId) params.append('patient_id', patientId);
    return this.request(`/laboratory/tests?${params.toString()}`);
  },

  enterLabResults(testId, resultsData) {
    return this.request(`/laboratory/tests/${testId}/results`, {
      method: 'POST',
      body: JSON.stringify(resultsData)
    });
  },

  uploadLabReportFile(testId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/laboratory/tests/${testId}/upload-report`, {
      method: 'POST',
      body: formData
    });
  },

  verifyLabTest(testId) {
    return this.request(`/laboratory/tests/${testId}/verify`, {
      method: 'PUT'
    });
  },

  // Doctor Portal & Directory
  getDoctors() {
    return this.request('/doctors/list');
  },

  getDoctorOverview() {
    return this.request('/doctors/dashboard-overview');
  },

  searchPatients(q = '') {
    return this.request(`/doctors/patients/search?q=${encodeURIComponent(q)}`);
  },

  getPatient360(patientId) {
    return this.request(`/doctors/patients/${patientId}/360`);
  },

  addClinicalNotes(noteData) {
    return this.request('/doctors/clinical-notes', {
      method: 'POST',
      body: JSON.stringify(noteData)
    });
  },

  // Predictions
  runPrediction(predData) {
    return this.request('/predictions/run', {
      method: 'POST',
      body: JSON.stringify(predData)
    });
  },

  getPredictionHistory(patientId) {
    return this.request(`/predictions/history/${patientId}`);
  },

  getModelInfo() {
    return this.request('/predictions/model-info');
  },

  // Admin
  getAdminOverview() {
    return this.request('/admin/overview');
  },

  getUsers(roleFilter = null) {
    const q = roleFilter ? `?role_filter=${encodeURIComponent(roleFilter)}` : '';
    return this.request(`/admin/users${q}`);
  },

  createDoctor(docData) {
    return this.request('/admin/doctors', {
      method: 'POST',
      body: JSON.stringify(docData)
    });
  },

  createStaff(staffData) {
    return this.request('/admin/staff', {
      method: 'POST',
      body: JSON.stringify(staffData)
    });
  },

  toggleUserStatus(userId, isActive) {
    return this.request(`/admin/users/${userId}/status?is_active=${isActive}`, {
      method: 'PUT'
    });
  },

  getAuditLogs(limit = 50) {
    return this.request(`/admin/audit-logs?limit=${limit}`);
  },

  executeDemoQuery(sqlQuery) {
    return this.request('/admin/execute-query', {
      method: 'POST',
      body: JSON.stringify({ query: sqlQuery })
    });
  },

  // Notifications
  getNotifications() {
    return this.request('/notifications');
  },

  markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: 'PUT'
    });
  },

  markAllNotificationsRead() {
    return this.request('/notifications/read-all', {
      method: 'PUT'
    });
  }
};

// UI Notifications (Toasts)
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle');
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// RBAC Guard helper for Pages
function checkAuthRole(expectedRole) {
  const user = API.getUser();
  const token = API.getToken();
  if (!token || !user) {
    window.location.href = '/login.html';
    return false;
  }
  if (expectedRole && user.role !== expectedRole) {
    // Redirect to matching role portal
    if (user.role === 'ADMIN') window.location.href = '/admin/index.html';
    else if (user.role === 'DOCTOR') window.location.href = '/doctor/index.html';
    else if (user.role === 'STAFF') window.location.href = '/staff/index.html';
    else if (user.role === 'PATIENT') window.location.href = '/patient/index.html';
    else window.location.href = '/login.html';
    return false;
  }
  return true;
}
