// Frontend types for the MCP E-commerce demo

// MCP-UI resource format (remote-dom only)
export interface UIResource {
  type: 'resource'
  resource: {
    uri: string // e.g., ui://component/id
    mimeType: 'application/vnd.mcp.ui.remote-dom+javascript'
    text: string // Remote-dom React component script
    blob?: string // Base64-encoded remote-dom script (if needed)
  }
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  uiResource?: UIResource // MCP-UI resource if present
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  message: ChatMessage
  session_id: string
  is_mcp_response: boolean
}

export interface MCPActionRequest {
  action_type: string
  tool_name: string
  params: Record<string, unknown>
  session_id?: string
}

export interface UIActionResult {
  type: 'tool' | 'intent' | 'prompt' | 'notify' | 'link'
  payload: {
    toolName?: string
    params?: Record<string, unknown>
    intent?: string
    prompt?: string
    message?: string
    url?: string
  }
  messageId?: string
}

// Cart types
export interface CartItem {
  id: string
  productId: string
  variantId: string
  name: string
  variant: string
  price: number
  quantity: number
  imageUrl: string
  icon?: string
  color?: string
}

export interface CartState {
  items: CartItem[]
  total: number
  isOpen: boolean
  itemCount: number
}