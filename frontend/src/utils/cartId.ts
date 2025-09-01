const CART_ID_KEY = 'mcp_cart_id';

export const getCartId = (): string | null => {
  return localStorage.getItem(CART_ID_KEY);
};

export const setCartId = (cartId: string): void => {
  localStorage.setItem(CART_ID_KEY, cartId);
};

export const clearCartId = (): void => {
  localStorage.removeItem(CART_ID_KEY);
};
