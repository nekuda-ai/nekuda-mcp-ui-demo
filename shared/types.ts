// Shared types for the MCP E-commerce demo

export interface Product {
  id: string;
  name: string;
  description: string;
  basePrice: number;
  category: 'electronics' | 'fashion';
  imageUrl: string;
  variants: ProductVariant[];
  tags: string[];
}

export interface ProductVariant {
  id: string;
  name: string;
  type: 'color' | 'size' | 'configuration';
  value: string;
  priceModifier: number; // +/- amount from base price
  imageUrl?: string;
  inStock: boolean;
}

export interface CartItem {
  productId: string;
  variantId: string;
  quantity: number;
  addedAt: Date;
}

export interface Cart {
  id: string;
  items: CartItem[];
  total: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  uiResource?: any; // MCP-UI resource if present
}

export interface MCPAction {
  type: 'tool' | 'prompt' | 'notify';
  payload: {
    toolName?: string;
    params?: Record<string, unknown>;
    prompt?: string;
    message?: string;
  };
}