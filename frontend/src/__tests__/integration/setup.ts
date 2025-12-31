import { afterAll, afterEach, beforeAll } from 'vitest'
import { setupServer } from 'msw/node'
import { handlers } from './mocks/handlers'

/**
 * Integration test setup with MSW (Mock Service Worker)
 * This setup intercepts HTTP requests and provides mock responses
 */
export const server = setupServer(...handlers)

// Start server before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn', // Warn about unhandled requests
  })
})

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers()
})

// Cleanup after all tests
afterAll(() => {
  server.close()
})
