/**
 * API client for Trading Journal backend.
 * 
 * Handles authentication, request/response interceptors, and error handling.
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

// Get API URL by detecting from current host at runtime
// This ensures it works whether accessed via localhost or IP address
const getApiUrl = (): string => {
  const host = window.location.hostname
  const protocol = window.location.protocol
  
  // Always use port 8102 for backend (changed from 8100)
  // This dynamically adapts to whatever hostname is being used
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
  timeout: 60000, // 60 seconds (price data fetching can take longer)
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
      
      // Create a more descriptive error message
      let errorMessage = error.message
      if (data?.detail) {
        errorMessage = data.detail
      } else {
        switch (status) {
          case 401:
            errorMessage = 'Unauthorized - check API key'
            break
          case 403:
            errorMessage = 'Forbidden - invalid API key or insufficient permissions'
            break
          case 404:
            errorMessage = 'Resource not found'
            break
          case 422:
            errorMessage = `Validation error: ${data.detail || 'Invalid request'}`
            break
          case 500:
            errorMessage = 'Server error'
            break
          default:
            errorMessage = data.detail || error.message
        }
      }
      
      // Create a new error with the descriptive message
      const enhancedError = new Error(errorMessage)
      ;(enhancedError as any).response = error.response
      ;(enhancedError as any).status = status
      
      console.error(`API error (${status}):`, errorMessage)
      return Promise.reject(enhancedError)
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

