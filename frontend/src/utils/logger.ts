type LogLevel = 'error' | 'warn' | 'info' | 'debug'

interface Logger {
  error: (message: string, ...args: any[]) => void
  warn: (message: string, ...args: any[]) => void  
  info: (message: string, ...args: any[]) => void
  debug: (message: string, ...args: any[]) => void
}

class DebugLogger implements Logger {
  private isDevelopment: boolean
  private isDebugEnabled: boolean

  constructor() {
    this.isDevelopment = import.meta.env.MODE === 'development'
    this.isDebugEnabled = import.meta.env.VITE_DEBUG === 'true' // Only when explicitly enabled
  }

  private shouldLog(level: LogLevel): boolean {
    // Always show errors and warnings
    if (level === 'error' || level === 'warn') return true
    
    // Show info in development or when debug is enabled
    if (level === 'info') return this.isDevelopment || this.isDebugEnabled
    
    // Show debug only when explicitly enabled
    if (level === 'debug') return this.isDebugEnabled
    
    return false
  }

  private log(level: LogLevel, message: string, ...args: any[]): void {
    if (!this.shouldLog(level)) return

    const timestamp = new Date().toISOString().split('T')[1].split('.')[0]
    const prefix = `[${timestamp}] ${level.toUpperCase()}`

    switch (level) {
      case 'error':
        console.error(prefix, message, ...args)
        break
      case 'warn':
        console.warn(prefix, message, ...args)
        break
      case 'info':
        console.info(prefix, message, ...args)
        break
      case 'debug':
        console.log(prefix, message, ...args)
        break
    }
  }

  error(message: string, ...args: any[]): void {
    this.log('error', message, ...args)
  }

  warn(message: string, ...args: any[]): void {
    this.log('warn', message, ...args)
  }

  info(message: string, ...args: any[]): void {
    this.log('info', message, ...args)
  }

  debug(message: string, ...args: any[]): void {
    this.log('debug', message, ...args)
  }
}

// Create singleton logger instance
export const logger = new DebugLogger()

// Export for backwards compatibility if needed
export default logger