/**
 * Mock WebSocket class for testing real-time progress updates
 */
export class MockWebSocket {
  url: string
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  readyState: number = 0

  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  constructor(url: string) {
    this.url = url
    this.readyState = MockWebSocket.CONNECTING

    // Simulate connection opening asynchronously
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSING
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED
      if (this.onclose) {
        this.onclose(new CloseEvent('close'))
      }
    }, 0)
  }

  /**
   * Helper method to simulate receiving a message from the server
   */
  simulateMessage(data: any) {
    if (this.readyState !== MockWebSocket.OPEN) {
      return
    }

    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(data),
          })
        )
      }
    }, 0)
  }

  /**
   * Helper method to simulate a WebSocket error
   */
  simulateError(error: Event = new Event('error')) {
    setTimeout(() => {
      if (this.onerror) {
        this.onerror(error)
      }
    }, 0)
  }

  /**
   * Helper method to simulate connection close
   */
  simulateClose() {
    this.close()
  }
}

// Store instances for test access
export const mockWebSocketInstances: MockWebSocket[] = []

/**
 * Setup global WebSocket mock
 * Note: Use vi.stubGlobal in tests instead of calling this directly
 */
export function createWebSocketMockClass() {
  return class extends MockWebSocket {
    constructor(url: string) {
      super(url)
      mockWebSocketInstances.push(this)
    }
  }
}

/**
 * Setup global WebSocket mock
 * This should be called with vi.stubGlobal in beforeEach
 */
export function setupWebSocketMock() {
  mockWebSocketInstances.length = 0
}

/**
 * Get the most recent WebSocket instance
 */
export function getLatestWebSocket(): MockWebSocket | undefined {
  return mockWebSocketInstances[mockWebSocketInstances.length - 1]
}

/**
 * Cleanup WebSocket mock
 */
export function cleanupWebSocketMock() {
  mockWebSocketInstances.length = 0
}
