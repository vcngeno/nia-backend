import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const isConversationRequest = config.url?.includes('/conversation/');
  const token = isConversationRequest
    ? localStorage.getItem('childToken') || localStorage.getItem('token')
    : localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (localStorage.getItem('childToken')) {
        localStorage.removeItem('childToken');
        localStorage.removeItem('currentChild');
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    return Promise.reject(error);
  },
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
};

// Children API
export const childrenAPI = {
  create: (data) => api.post('/children/', data),
  getAll: () => api.get('/children/'),
  login: (data) => api.post('/children/login', data),
};

// Conversation API
export const conversationAPI = {
  sendMessage: (data) => api.post('/conversation/message', data),
  getFolders: (childId) => api.get(`/conversation/folders/${childId}`),
  getConversations: (childId, folder) =>
    api.get(`/conversation/conversations/${childId}`, { params: { folder } }),
  getMessages: (conversationId) => api.get(`/conversation/messages/${conversationId}`),
};

export default api;
