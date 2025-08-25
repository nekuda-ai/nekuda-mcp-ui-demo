/**
 * Centralized error handling utilities for MCP E-commerce Demo Frontend
 * Provides consistent error types, logging, and response formatting
 */

export enum ErrorCode {
  // General errors
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  NETWORK_ERROR = 'NETWORK_ERROR',
  
  // Business logic errors
  CART_ERROR = 'CART_ERROR',
  PRODUCT_ERROR = 'PRODUCT_ERROR',
  CHECKOUT_ERROR = 'CHECKOUT_ERROR',
  SESSION_ERROR = 'SESSION_ERROR',
  
  // External service errors
  API_ERROR = 'API_ERROR',
  MCP_ERROR = 'MCP_ERROR',
  NEKUDA_ERROR = 'NEKUDA_ERROR',
  
  // UI errors
  RENDER_ERROR = 'RENDER_ERROR',
  COMPONENT_ERROR = 'COMPONENT_ERROR',
}

export interface ErrorContext {
  userId?: string
  sessionId?: string
  requestId?: string
  operation?: string
  component?: string
  url?: string
  additionalData?: Record<string, any>
}

export class AppError extends Error {
  public readonly errorCode: ErrorCode
  public readonly context: ErrorContext
  public readonly cause?: Error
  public readonly userMessage: string
  public readonly timestamp: Date

  constructor(
    message: string,
    errorCode: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    context: ErrorContext = {},
    cause?: Error,
    userMessage?: string
  ) {
    super(message)
    this.name = 'AppError'
    this.errorCode = errorCode
    this.context = context
    this.cause = cause
    this.userMessage = userMessage || this.getDefaultUserMessage()
    this.timestamp = new Date()
  }

  private getDefaultUserMessage(): string {
    const userMessages: Record<ErrorCode, string> = {
      [ErrorCode.VALIDATION_ERROR]: 'Invalid input provided. Please check your data and try again.',
      [ErrorCode.NOT_FOUND]: 'The requested resource was not found.',
      [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please wait and try again.',
      [ErrorCode.NETWORK_ERROR]: 'Network connection issue. Please check your connection and try again.',
      [ErrorCode.CART_ERROR]: 'There was an issue with your cart. Please try again.',
      [ErrorCode.PRODUCT_ERROR]: 'Product information is temporarily unavailable.',
      [ErrorCode.CHECKOUT_ERROR]: 'Checkout failed. Please review your information and try again.',
      [ErrorCode.SESSION_ERROR]: 'Your session has expired. Please refresh the page.',
      [ErrorCode.API_ERROR]: 'Service is temporarily unavailable. Please try again.',
      [ErrorCode.MCP_ERROR]: 'Communication error. Please try again.',
      [ErrorCode.NEKUDA_ERROR]: 'Payment service is temporarily unavailable. Please try again.',
      [ErrorCode.RENDER_ERROR]: 'Display error occurred. Please refresh the page.',
      [ErrorCode.COMPONENT_ERROR]: 'Component error occurred. Please try again.',
      [ErrorCode.UNKNOWN_ERROR]: 'An unexpected error occurred. Please try again.',
      [ErrorCode.AUTHENTICATION_ERROR]: 'Authentication failed. Please log in again.',
      [ErrorCode.AUTHORIZATION_ERROR]: 'You do not have permission to perform this action.',
    }
    return userMessages[this.errorCode] || userMessages[ErrorCode.UNKNOWN_ERROR]
  }

  toJSON(): Record<string, any> {
    return {
      errorCode: this.errorCode,
      message: this.message,
      userMessage: this.userMessage,
      timestamp: this.timestamp.toISOString(),
      context: this.context,
      cause: this.cause?.message,
    }
  }
}

export class ValidationError extends AppError {
  constructor(message: string, context: ErrorContext = {}, cause?: Error) {
    super(message, ErrorCode.VALIDATION_ERROR, context, cause)
  }
}

export class NetworkError extends AppError {
  constructor(message: string, context: ErrorContext = {}, cause?: Error) {
    super(message, ErrorCode.NETWORK_ERROR, context, cause)
  }
}

export class CartError extends AppError {
  constructor(message: string, context: ErrorContext = {}, cause?: Error) {
    super(message, ErrorCode.CART_ERROR, context, cause)
  }
}

export class CheckoutError extends AppError {
  constructor(message: string, context: ErrorContext = {}, cause?: Error) {
    super(message, ErrorCode.CHECKOUT_ERROR, context, cause)
  }
}

export class APIError extends AppError {
  public readonly status?: number

  constructor(message: string, status?: number, context: ErrorContext = {}, cause?: Error) {
    super(message, ErrorCode.API_ERROR, context, cause)
    this.status = status
  }
}

// Logging levels
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

// Structured logger interface
export interface Logger {
  debug(message: string, context?: Record<string, any>): void
  info(message: string, context?: Record<string, any>): void
  warn(message: string, context?: Record<string, any>): void
  error(message: string, context?: Record<string, any>): void
}

class ConsoleLogger implements Logger {
  constructor(private component: string, private level: LogLevel = LogLevel.INFO) {}

  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
    return levels.indexOf(level) >= levels.indexOf(this.level)
  }

  private formatMessage(level: LogLevel, message: string, context?: Record<string, any>): void {
    if (!this.shouldLog(level)) return

    const timestamp = new Date().toISOString()
    const prefix = `${timestamp} | ${level.toUpperCase().padEnd(5)} | ${this.component.padEnd(15)} |`
    
    if (context && Object.keys(context).length > 0) {
      console[level](`${prefix} ${message}`, context)
    } else {
      console[level](`${prefix} ${message}`)
    }
  }

  debug(message: string, context?: Record<string, any>): void {
    this.formatMessage(LogLevel.DEBUG, message, context)
  }

  info(message: string, context?: Record<string, any>): void {
    this.formatMessage(LogLevel.INFO, message, context)
  }

  warn(message: string, context?: Record<string, any>): void {
    this.formatMessage(LogLevel.WARN, message, context)
  }

  error(message: string, context?: Record<string, any>): void {
    this.formatMessage(LogLevel.ERROR, message, context)
  }
}

// Logger factory
export function createLogger(component: string, level: LogLevel = LogLevel.INFO): Logger {
  return new ConsoleLogger(component, level)
}

// Error logging utility
export function logError(logger: Logger, error: Error | AppError, context?: ErrorContext): void {
  if (error instanceof AppError) {
    logger.error(`[${error.errorCode}] ${error.message}`, {
      context: error.context,
      cause: error.cause?.message,
      userMessage: error.userMessage,
      ...context,
    })
  } else {
    logger.error(`Unexpected error: ${error.message}`, {
      name: error.name,
      stack: error.stack,
      ...context,
    })
  }
}

// Error recovery utility
export async function handleErrorRecovery<T>(
  operation: () => Promise<T>,
  operationName: string,
  fallbackAction?: () => Promise<T>,
  logger?: Logger
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (logger) {
      const context: ErrorContext = { operation: operationName }
      logError(logger, error as Error, context)
    }

    if (fallbackAction) {
      try {
        logger?.info(`Attempting fallback for ${operationName}`)
        return await fallbackAction()
      } catch (fallbackError) {
        logger?.error(`Fallback action failed for ${operationName}`, {
          fallbackError: (fallbackError as Error).message,
        })
        throw error // Re-throw original error
      }
    }

    throw error
  }
}

// Retry utility with exponential backoff
export async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number
    baseDelay?: number
    maxDelay?: number
    operationName?: string
    logger?: Logger
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    operationName = 'operation',
    logger,
  } = options

  let lastError: Error

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        logger?.info(`Retry attempt ${attempt} for ${operationName}`)
      }
      return await operation()
    } catch (error) {
      lastError = error as Error
      
      if (attempt === maxRetries) {
        logger?.error(`All retry attempts failed for ${operationName}`, {
          attempts: attempt + 1,
          finalError: lastError.message,
        })
        throw lastError
      }

      const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay)
      logger?.warn(`${operationName} failed, retrying in ${delay}ms`, {
        attempt: attempt + 1,
        error: lastError.message,
      })
      
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError!
}

// Error boundary helper for Vue components
export function createErrorHandler(component: string, logger?: Logger) {
  return (error: Error, info: string) => {
    const appError = new AppError(
      error.message,
      ErrorCode.COMPONENT_ERROR,
      { component, additionalData: { info } },
      error
    )
    
    if (logger) {
      logError(logger, appError)
    } else {
      console.error(`[${component}] Component Error:`, error, info)
    }
  }
}

// Notification helper for user-facing errors
export interface NotificationOptions {
  type: 'error' | 'warning' | 'info' | 'success'
  title?: string
  message: string
  duration?: number
  action?: {
    label: string
    handler: () => void
  }
}

export function createErrorNotification(error: Error | AppError): NotificationOptions {
  if (error instanceof AppError) {
    return {
      type: 'error',
      title: 'Error',
      message: error.userMessage,
      duration: 5000,
    }
  } else {
    return {
      type: 'error',
      title: 'Unexpected Error',
      message: 'An unexpected error occurred. Please try again.',
      duration: 5000,
    }
  }
}
