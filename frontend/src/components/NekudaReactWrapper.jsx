import React from 'react';
import { NekudaWalletProvider, NekudaPaymentForm, useNekudaWallet } from '@nekuda/react-nekuda-js';

const NEKUDA_PUBLIC_KEY = 'ak_mCL7GZh_ou1m1LDaU7jQkXrc5ohbsuaU8gBlu4Rzk1A';

// Simple payment form component following Nekuda docs exactly
const NekudaPaymentFormComponent = ({ onSuccess, onError, userId }) => {
  console.log('[NekudaReactWrapper] PaymentForm component rendered for user:', userId);

  const handlePaymentSave = async (formData) => {
    console.log('[NekudaReactWrapper] Payment saved via coordinator:', formData);
    
    // Extract token ID from coordinator response (as per docs)
    const tokenId = formData.id || formData.cardTokenId;
    
    if (tokenId) {
      console.log('[NekudaReactWrapper] Card token received:', tokenId);
      onSuccess?.(formData);
    } else {
      const error = 'Payment submission failed';
      console.error('[NekudaReactWrapper] Error:', error);
      onError?.(error);
    }
  };

  return (
    <div style={{
      background: 'transparent',
      minHeight: '200px',
      color: 'white'
    }}>
      <NekudaPaymentForm onSave={handlePaymentSave}>
        <button 
          type="submit" 
          style={{
            marginTop: '16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            width: '100%'
          }}
        >
          Save Payment Details
        </button>
      </NekudaPaymentForm>
    </div>
  );
};

// Provider wrapper component
const NekudaProviderWrapper = ({ children, userId, onPaymentSuccess, onPaymentError }) => {
  console.log('[NekudaReactWrapper] Provider initialized with user:', userId);
  
  return (
    <NekudaWalletProvider 
      publicKey={NEKUDA_PUBLIC_KEY}
      userId={userId}
      onSuccess={(result) => {
        console.log('[NekudaReactWrapper] Nekuda operation successful:', result);
        onPaymentSuccess?.(result);
      }}
      onError={(error) => {
        console.error('[NekudaReactWrapper] Nekuda error:', error);
        onPaymentError?.(error);
      }}
    >
      {children}
    </NekudaWalletProvider>
  );
};

export { NekudaProviderWrapper, NekudaPaymentFormComponent };
export default NekudaProviderWrapper;