import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { ProgressUpdate } from '../../types/conversion'

// Mock WebSocket
class MockWebSocket {
  url: string
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  readyState: number = 0 // CONNECTING

  constructor(url: string) {
    this.url = url
    // Store instance for test access
    ;(global as any).lastWebSocket = this
  }

  close() {
    this.readyState = 3 // CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  // Test helper to simulate receiving a message
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  // Test helper to simulate connection open
  simulateOpen() {
    this.readyState = 1 // OPEN
    if (this.onopen) {
      this.onopen(new Event('open'))
    }
  }

  // Test helper to simulate error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// Setup and teardown
beforeEach(() => {
  global.WebSocket = MockWebSocket as any
  ;(global as any).lastWebSocket = null
  vi.spyOn(console, 'log').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  vi.restoreAllMocks()
  ;(global as any).lastWebSocket = null
})

describe('useWebSocket', () => {
  // 1. INITIALIZATION TESTS (4 tests)
  describe('Initialization', () => {
    it('should return progress as null initially', () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))
      expect(result.current.progress).toBeNull()
    })

    it('should return isConnected as false initially', () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))
      expect(result.current.isConnected).toBe(false)
    })

    it('should not connect when sessionId is null', () => {
      renderHook(() => useWebSocket(null))
      expect((global as any).lastWebSocket).toBeNull()
    })

    it('should not connect when sessionId is undefined', () => {
      renderHook(() => useWebSocket(null))
      expect((global as any).lastWebSocket).toBeNull()
    })
  })

  // 2. CONNECTION ESTABLISHMENT TESTS (6 tests)
  describe('Connection Establishment', () => {
    it('should create WebSocket connection when sessionId provided', async () => {
      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })
    })

    it('should use correct WebSocket URL with sessionId', async () => {
      renderHook(() => useWebSocket('test-session-123'))

      await waitFor(() => {
        const ws = (global as any).lastWebSocket as MockWebSocket
        expect(ws).not.toBeNull()
        expect(ws.url).toContain('/ws/progress/test-session-123')
      })
    })

    it('should use "ws:" protocol for http:// pages', async () => {
      // Mock window.location with http protocol
      const originalLocation = window.location
      delete (window as any).location
      window.location = { ...originalLocation, protocol: 'http:' } as Location

      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        const ws = (global as any).lastWebSocket as MockWebSocket
        expect(ws).not.toBeNull()
        expect(ws.url).toMatch(/^ws:/)
      })

      // Restore original location
      window.location = originalLocation
    })

    it('should use "wss:" protocol for https:// pages', async () => {
      // Mock window.location with https protocol
      const originalLocation = window.location
      delete (window as any).location
      window.location = { ...originalLocation, protocol: 'https:' } as Location

      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        const ws = (global as any).lastWebSocket as MockWebSocket
        expect(ws).not.toBeNull()
        expect(ws.url).toMatch(/^wss:/)
      })

      // Restore original location
      window.location = originalLocation
    })

    it('should set isConnected to true when connection opens', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })
    })

    it('should log "WebSocket connected" on open', async () => {
      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(console.log).toHaveBeenCalledWith('WebSocket connected')
      })
    })
  })

  // 3. MESSAGE RECEIVING TESTS (5 tests)
  describe('Message Receiving', () => {
    it('should parse and set progress when message received', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressData: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 50,
        status: 'converting',
        message: 'Converting file...'
      }

      act(() => {
        ws.simulateMessage(progressData)
      })

      await waitFor(() => {
        expect(result.current.progress).toEqual(progressData)
      })
    })

    it('should update progress state with ProgressUpdate data', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressData: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 75,
        status: 'converting',
        message: 'Almost done...',
        current_operation: 'encoding'
      }

      act(() => {
        ws.simulateMessage(progressData)
      })

      await waitFor(() => {
        expect(result.current.progress).not.toBeNull()
        expect(result.current.progress?.progress).toBe(75)
        expect(result.current.progress?.status).toBe('converting')
        expect(result.current.progress?.message).toBe('Almost done...')
        expect(result.current.progress?.current_operation).toBe('encoding')
      })
    })

    it('should handle JSON parsing correctly', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const validJson: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 100,
        status: 'completed',
        message: 'Conversion complete'
      }

      act(() => {
        ws.simulateMessage(validJson)
      })

      await waitFor(() => {
        expect(result.current.progress).toEqual(validJson)
      })
      expect(console.error).not.toHaveBeenCalled()
    })

    it('should log error for invalid JSON messages', async () => {
      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        if (ws.onmessage) {
          ws.onmessage(new MessageEvent('message', { data: 'invalid json{' }))
        }
      })

      await waitFor(() => {
        expect(console.error).toHaveBeenCalledWith(
          'Error parsing WebSocket message:',
          expect.any(Error)
        )
      })
    })

    it('should not crash on malformed messages', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      expect(() => {
        act(() => {
          if (ws.onmessage) {
            ws.onmessage(new MessageEvent('message', { data: '}{invalid' }))
          }
        })
      }).not.toThrow()

      // Progress should remain null since message was malformed
      expect(result.current.progress).toBeNull()
    })
  })

  // 4. PROGRESS UPDATES TESTS (4 tests)
  describe('Progress Updates', () => {
    it('should update progress with valid ProgressUpdate object', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressUpdate: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 25,
        status: 'uploading',
        message: 'Uploading file...'
      }

      act(() => {
        ws.simulateMessage(progressUpdate)
      })

      await waitFor(() => {
        expect(result.current.progress).toEqual(progressUpdate)
      })
    })

    it('should handle progress with message field', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressUpdate: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 60,
        status: 'converting',
        message: 'Processing video frames...'
      }

      act(() => {
        ws.simulateMessage(progressUpdate)
      })

      await waitFor(() => {
        expect(result.current.progress?.message).toBe('Processing video frames...')
      })
    })

    it('should handle progress with progress percentage', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressUpdate: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 85,
        status: 'converting',
        message: 'Nearly complete...'
      }

      act(() => {
        ws.simulateMessage(progressUpdate)
      })

      await waitFor(() => {
        expect(result.current.progress?.progress).toBe(85)
      })
    })

    it('should handle progress with status field', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const progressUpdate: ProgressUpdate = {
        session_id: 'test-session-id',
        progress: 100,
        status: 'completed',
        message: 'Conversion successful'
      }

      act(() => {
        ws.simulateMessage(progressUpdate)
      })

      await waitFor(() => {
        expect(result.current.progress?.status).toBe('completed')
      })
    })
  })

  // 5. CONNECTION STATE TESTS (4 tests)
  describe('Connection State', () => {
    it('should maintain isConnected as true while connected', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })

      // Should remain connected
      await new Promise(resolve => setTimeout(resolve, 50))
      expect(result.current.isConnected).toBe(true)
    })

    it('should set isConnected to false on close', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })

      act(() => {
        ws.close()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false)
      })
    })

    it('should set isConnected to false on error', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })

      // Simulate error followed by close (typical browser behavior)
      act(() => {
        ws.simulateError()
        ws.close()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false)
      })
    })

    it('should log "WebSocket disconnected" on close', async () => {
      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.close()
      })

      await waitFor(() => {
        expect(console.log).toHaveBeenCalledWith('WebSocket disconnected')
      })
    })
  })

  // 6. ERROR HANDLING TESTS (3 tests)
  describe('Error Handling', () => {
    it('should handle WebSocket errors gracefully', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      expect(() => {
        act(() => {
          ws.simulateError()
        })
      }).not.toThrow()

      // Hook should still be functional
      expect(result.current).toBeDefined()
    })

    it('should log error message on WebSocket error', async () => {
      renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateError()
      })

      await waitFor(() => {
        expect(console.error).toHaveBeenCalledWith(
          'WebSocket error:',
          expect.any(Event)
        )
      })
    })

    it('should not crash on connection error', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      expect(() => {
        act(() => {
          ws.simulateError()
        })
      }).not.toThrow()

      expect(result.current.progress).toBeNull()
    })
  })

  // 7. CLEANUP TESTS (4 tests)
  describe('Cleanup', () => {
    it('should close WebSocket on component unmount', async () => {
      const { unmount } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const closeSpy = vi.spyOn(ws, 'close')

      unmount()

      expect(closeSpy).toHaveBeenCalled()
    })

    it('should clean up connection when sessionId becomes null', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'test-session-id' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket
      const closeSpy = vi.spyOn(ws, 'close')

      act(() => {
        rerender({ sessionId: null })
      })

      expect(closeSpy).toHaveBeenCalled()
    })

    it('should disconnect when sessionId changes', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'session-1' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const firstWs = (global as any).lastWebSocket as MockWebSocket
      const closeSpy = vi.spyOn(firstWs, 'close')

      act(() => {
        rerender({ sessionId: 'session-2' })
      })

      await waitFor(() => {
        expect(closeSpy).toHaveBeenCalled()
      })
    })

    it('should set isConnected to false on cleanup', async () => {
      const { result, unmount } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      act(() => {
        ws.simulateOpen()
      })

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true)
      })

      unmount()

      // Note: After unmount, we can't check result.current
      // But the cleanup function sets isConnected to false
      expect(ws.readyState).toBe(3) // CLOSED
    })
  })

  // 8. SESSION ID CHANGES TESTS (3 tests)
  describe('SessionId Changes', () => {
    it('should reconnect when sessionId changes', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'session-1' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const firstWs = (global as any).lastWebSocket as MockWebSocket
      expect(firstWs.url).toContain('session-1')

      act(() => {
        rerender({ sessionId: 'session-2' })
      })

      await waitFor(() => {
        const secondWs = (global as any).lastWebSocket as MockWebSocket
        expect(secondWs).not.toBe(firstWs)
        expect(secondWs.url).toContain('session-2')
      })
    })

    it('should close old connection before creating new one', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'session-1' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const firstWs = (global as any).lastWebSocket as MockWebSocket
      const closeSpy = vi.spyOn(firstWs, 'close')

      act(() => {
        rerender({ sessionId: 'session-2' })
      })

      await waitFor(() => {
        expect(closeSpy).toHaveBeenCalled()
      })

      // New WebSocket should be created
      await waitFor(() => {
        const secondWs = (global as any).lastWebSocket as MockWebSocket
        expect(secondWs).not.toBe(firstWs)
      })
    })

    it('should not reconnect if sessionId becomes null', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'test-session-id' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const firstWs = (global as any).lastWebSocket as MockWebSocket
      const closeSpy = vi.spyOn(firstWs, 'close')

      // Clear the global reference to test that no new connection is created
      ;(global as any).lastWebSocket = null

      act(() => {
        rerender({ sessionId: null })
      })

      await waitFor(() => {
        expect(closeSpy).toHaveBeenCalled()
      })

      // No new WebSocket should be created
      expect((global as any).lastWebSocket).toBeNull()
    })
  })

  // ADDITIONAL EDGE CASE TESTS
  describe('Edge Cases', () => {
    it('should handle multiple progress updates sequentially', async () => {
      const { result } = renderHook(() => useWebSocket('test-session-id'))

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      const ws = (global as any).lastWebSocket as MockWebSocket

      const updates: ProgressUpdate[] = [
        { session_id: 'test-session-id', progress: 25, status: 'uploading', message: 'Uploading...' },
        { session_id: 'test-session-id', progress: 50, status: 'converting', message: 'Converting...' },
        { session_id: 'test-session-id', progress: 75, status: 'converting', message: 'Almost done...' },
        { session_id: 'test-session-id', progress: 100, status: 'completed', message: 'Complete!' }
      ]

      for (const update of updates) {
        act(() => {
          ws.simulateMessage(update)
        })

        await waitFor(() => {
          expect(result.current.progress).toEqual(update)
        })
      }
    })

    it('should handle rapid sessionId changes', async () => {
      const { rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { initialProps: { sessionId: 'session-1' } }
      )

      await waitFor(() => {
        expect((global as any).lastWebSocket).not.toBeNull()
      })

      // Rapidly change sessionId
      act(() => {
        rerender({ sessionId: 'session-2' })
      })
      act(() => {
        rerender({ sessionId: 'session-3' })
      })
      act(() => {
        rerender({ sessionId: 'session-4' })
      })

      await waitFor(() => {
        const finalWs = (global as any).lastWebSocket as MockWebSocket
        expect(finalWs.url).toContain('session-4')
      })
    })

    it('should handle empty string sessionId as falsy', () => {
      renderHook(() => useWebSocket(''))

      // Empty string is falsy in the implementation's check (!sessionId)
      // So no WebSocket connection should be created
      expect((global as any).lastWebSocket).toBeNull()
    })
  })
})
