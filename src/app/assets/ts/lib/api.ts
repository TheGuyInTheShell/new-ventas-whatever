import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE = '/api/v1';

/**
 * Centralized Axios instance for API requests.
 */
export const api: AxiosInstance = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor if needed (e.g., for auth tokens)
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // You can add logic here (like adding headers from localStorage)
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor for global error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
    }
);
