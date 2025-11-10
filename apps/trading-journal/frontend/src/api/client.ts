/**
 * API client for Trading Journal backend.
 * 
 * Handles authentication, request/response interceptors, and error handling.
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

// Get API URL from environment variable or detect from current host
// Vite env vars are build-time, so we need a runtime fallback
const getApiUrl = (): string => {
  // If VITE_API_URL is set at build time, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // Otherwise, detect from current window location
  // If accessing via IP, use same IP for API
  // If accessing via localhost, use localhost
  const host = window.location.hostname
  const protocol = window.location.protocol
  
  // Use port 8102 for backend (changed from 8100)
  return `${protocol}//${host}:8102/api`
}

const API_URL = getApiUrl()
const API_KEY = import.meta.env.VITE_API_KEY || ''

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Request interceptor - add API key to all requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (API_KEY && config.headers) {
      config.headers['X-API-Key'] = API_KEY
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data as { detail?: string }
      
      switch (status) {
        case 401:
          console.error('Unauthorized - check API key')
          break
        case 403:
          console.error('Forbidden - insufficient permissions')
          break
        case 404:
          console.error('Resource not found')
          break
        case 422:
          console.error('Validation error:', data.detail)
          break
        case 500:
          console.error('Server error')
          break
        default:
          console.error('API error:', data.detail || error.message)
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error - backend may be unavailable')
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

