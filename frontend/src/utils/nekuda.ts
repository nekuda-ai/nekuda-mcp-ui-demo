// nekuda Wallet Integration Utilities
// This module provides Vue-compatible methods to interact with the Nekuda backend

import axios from 'axios'

// Configure axios to use the correct backend URL
const getAPIBaseURL = () => {
  const envURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'
  // If it's just a hostname, add https://
  if (!envURL.startsWith('http://') && !envURL.startsWith('https://')) {
    return `https://${envURL}`
  }
  return envURL
}

const API_BASE_URL = getAPIBaseURL()
axios.defaults.baseURL = API_BASE_URL

export interface NekudaPaymentData {
  token: string
  pan: string
  expiryMonth: string
  expiryYear: string
  cvv: string
}

export interface NekudaMandate {
  mandateId: string
  product: string
  amount: number
  currency: string
  userId: string
}

/**
 * Atomic checkout flow: Create mandate when user clicks checkout → get PAN
 * This represents the user's explicit intent to purchase
 */
export const atomicNekudaCheckout = async (
  userId: string,
  cartTotal: number,
  cartItems: any[],
  quoteSessionId?: string,
  quoteVersion?: number
): Promise<NekudaPaymentData & { mandate_id: string; checkout_context: string }> => {
  try {
    const response = await axios.post('/api/atomic-nekuda-checkout', {
      user_id: userId,
      cart_total: cartTotal,
      cart_items: cartItems,
      product_summary: `Cart Purchase (${cartItems.length} items)`,
      currency: 'USD',
      checkout_context: 'user_clicked_checkout_button',
      quote_session_id: quoteSessionId,
      quote_version: quoteVersion
    })
    
    return response.data
  } catch (error) {
    console.error('Failed to process atomic checkout:', error)
    throw new Error('Failed to process checkout with payment credentials')
  }
}


/**
 * Check if user has stored payment methods in Nekuda wallet
 */
export const hasStoredPaymentMethods = async (userId: string): Promise<boolean> => {
  try {
    console.log('DEBUG: Making API call to check wallet status for user:', userId)
    const url = `/api/nekuda-wallet-status?userId=${userId}`
    console.log('DEBUG: API URL:', url)
    
    const response = await axios.get(url)
    console.log('DEBUG: API response:', response.data)
    
    const hasPaymentMethods = response.data.hasPaymentMethods
    console.log('DEBUG: Extracted hasPaymentMethods:', hasPaymentMethods)
    
    return hasPaymentMethods
  } catch (error) {
    console.error('Failed to check wallet status:', error)
    console.error('Error details:', error.response?.data || error.message)
    return false
  }
}

/**
 * Initialize Nekuda payment collection (for adding new cards)
 * This would typically open the Nekuda payment form
 */
export const initializeNekudaPaymentCollection = async (userId: string) => {
  try {
    const response = await axios.post('/api/initialize-nekuda-collection', {
      userId,
      environment: 'sandbox' // Use sandbox for development
    })
    
    return response.data
  } catch (error) {
    console.error('Failed to initialize payment collection:', error)
    throw new Error('Failed to initialize payment collection')
  }
}

/**
 * Simplified mock implementation for development
 * This simulates the Nekuda payment flow until real integration is complete
 */
export const getMockNekudaPaymentData = (): Promise<NekudaPaymentData> => {
  return new Promise((resolve) => {
    // Simulate API delay
    setTimeout(() => {
      resolve({
        token: 'nt_test_' + Math.random().toString(36).substr(2, 9),
        pan: '4111111111111111', // Test card number
        expiryMonth: '12',
        expiryYear: '25',
        cvv: '123'
      })
    }, 1000)
  })
}

export default {
  hasStoredPaymentMethods,
  initializeNekudaPaymentCollection,
  getMockNekudaPaymentData
}