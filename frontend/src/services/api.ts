import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const api = axios.create({
  baseURL: '/', // Adjust if your API is on a different host
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor to add the access token to every request
api.interceptors.request.use(config => {
  const authStore = useAuthStore();
  const token = authStore.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response error interceptor to handle expired tokens
api.interceptors.response.use(
  response => response, // Simply return successful responses
  async error => {
    const originalRequest = error.config;
    const authStore = useAuthStore();

    // Check if the error is 401 and it's not a retry request
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Mark it as a retry

      try {
        console.log('Access token expired. Attempting to refresh...');
        const { data } = await axios.post('/api/token/refresh');
        
        // Set the new token in the store
        authStore.setToken(data.access_token);
        
        // Update the authorization header of the original request
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Unable to refresh token. Logging out.', refreshError);
        authStore.logout(); // If refresh fails, logout the user
        return Promise.reject(refreshError);
      }
    }

    // For other errors, just reject the promise
    return Promise.reject(error);
  }
);

export default api;
