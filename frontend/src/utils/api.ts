// API utilities for communicating with the backend
import type { ChatRequest, ChatResponse, MCPActionRequest } from '@/types'

const getAPIBaseURL = () => {
  const envURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'
  // If it's just a hostname, add https://
  if (!envURL.startsWith('http://') && !envURL.startsWith('https://')) {
    return `https://${envURL}`
  }
  return envURL
}

const API_BASE_URL = getAPIBaseURL()

const getMCPServerBaseURL = () => {
  const envURL = import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:3003'
  // If it's just a hostname, add https://
  if (!envURL.startsWith('http://') && !envURL.startsWith('https://')) {
    return `https://${envURL}`
  }
  return envURL
}

const MCP_SERVER_URL = getMCPServerBaseURL()

class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI<T>(baseUrl: string, endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${baseUrl}${endpoint}`
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.text()
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      
      try {
        const parsedError = JSON.parse(errorData)
        errorMessage = parsedError.detail || parsedError.message || errorMessage
      } catch {
        // If error response is not JSON, use the text as is
        if (errorData) {
          errorMessage = errorData
        }
      }
      
      throw new APIError(errorMessage, response.status)
    }

    const data = await response.json()
    return data
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError('Unable to connect to the server. Please ensure the backend is running.')
    }
    
    throw new APIError('An unexpected error occurred while communicating with the server.')
  }
}

// Note: Removed serverApi - all API calls should go through chatApi (backend)

export const chatApi = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>(API_BASE_URL, '/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async mcpAction(request: MCPActionRequest): Promise<any> {
    return fetchAPI<any>(API_BASE_URL, '/mcp-action', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  async createCartSession(): Promise<{ session_id: string }> {
    return fetchAPI<{ session_id: string }>(API_BASE_URL, '/sessions', {
      method: 'POST',
    });
  },

  async getHealth(): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>(API_BASE_URL, '/health')
  }
}