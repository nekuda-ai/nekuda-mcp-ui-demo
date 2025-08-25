/**
 * Shared Configuration for Frontend (TypeScript)
 * Product metadata that matches the backend configuration
 */

export interface ProductMetadata {
  icon: string
  color: string
}

export interface CategoryMetadata {
  name: string
  description: string
  icon: string
  color: string
}

// Product metadata mapping (mirrors backend config)
export const PRODUCT_METADATA: Record<string, ProductMetadata> = {
  'headphones-1': { icon: '🎧', color: '#3b82f6' },
  'smartphone-1': { icon: '📱', color: '#6366f1' },
  'laptop-1': { icon: '💻', color: '#8b5cf6' },
  'tshirt-1': { icon: '👕', color: '#10b981' },
  'shoes-1': { icon: '👟', color: '#f59e0b' },
  'backpack-1': { icon: '🎒', color: '#ef4444' }
}

// Category metadata  
export const CATEGORY_METADATA: Record<string, CategoryMetadata> = {
  electronics: {
    name: "Electronics",
    description: "Latest gadgets and electronic devices",
    icon: "🔌",
    color: "#3b82f6"
  },
  fashion: {
    name: "Fashion", 
    description: "Clothing, shoes, and accessories",
    icon: "👕",
    color: "#10b981"
  }
}

// Environment configuration
export const ENV_CONFIG = {
  development: {
    mediaBaseUrl: "http://localhost:3003/media/products", // MCP server serves media
    mcpServerPort: 3003,
    backendPort: 8001, // Backend actually runs on 8001
    frontendPort: 5173 // Vite dev server default port
  },
  production: {
    mediaBaseUrl: import.meta.env?.VITE_MEDIA_BASE_URL || "http://localhost:3003/media/products",
    mcpServerPort: parseInt(import.meta.env?.VITE_MCP_SERVER_PORT || "3003"),
    backendPort: parseInt(import.meta.env?.VITE_BACKEND_PORT || "8001"), // Updated default
    frontendPort: parseInt(import.meta.env?.VITE_FRONTEND_PORT || "4173") // Preview port for production
  }
}

// Get current environment config
export function getEnvConfig() {
  const env = import.meta.env?.MODE === 'production' ? 'production' : 'development'
  return ENV_CONFIG[env]
}

// Helper functions
export function getProductMetadata(productId: string): ProductMetadata {
  return PRODUCT_METADATA[productId] || { icon: '📦', color: '#3b82f6' }
}

export function getAllProductMetadata(): Record<string, ProductMetadata> {
  return PRODUCT_METADATA
}