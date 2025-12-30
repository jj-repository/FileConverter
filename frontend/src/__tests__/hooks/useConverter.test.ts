import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useConverter } from '../../hooks/useConverter'

// Mock useWebSocket hook
vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    progress: null,
    isConnected: false,
  })),
}))

// Mock fetch
global.fetch = vi.fn()

describe('useConverter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(result.current.selectedFile).toBeNull()
      expect(result.current.outputFormat).toBe('png')
      expect(result.current.status).toBe('idle')
      expect(result.current.error).toBeNull()
      expect(result.current.downloadUrl).toBeNull()
    })

    it('should initialize with custom output format', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'webp' })
      )

      expect(result.current.outputFormat).toBe('webp')
    })
  })

  describe('File Selection', () => {
    it('should have handleFileSelect function', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(typeof result.current.handleFileSelect).toBe('function')
    })

    it('should handle file selection', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })

      // Call handleFileSelect
      act(() => {
        result.current.handleFileSelect(mockFile)
      })

      // File should be updated
      expect(result.current.selectedFile).toBeTruthy()
    })
  })

  describe('Format Selection', () => {
    it('should have setOutputFormat function', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(typeof result.current.setOutputFormat).toBe('function')
    })
  })

  describe('Custom Filename', () => {
    it('should have setCustomFilename function', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(typeof result.current.setCustomFilename).toBe('function')
    })
  })

  describe('Drag and Drop', () => {
    it('should have drag and drop handlers', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(typeof result.current.handleDragOver).toBe('function')
      expect(typeof result.current.handleDragLeave).toBe('function')
      expect(typeof result.current.handleDrop).toBe('function')
    })
  })

  describe('Status Management', () => {
    it('should have status field', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(result.current.status).toBeDefined()
      expect(result.current.status).toBe('idle')
    })
  })

  describe('Error Handling', () => {
    it('should have error field', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(result.current.error).toBeNull()
    })
  })

  describe('Upload Progress', () => {
    it('should have upload progress fields', () => {
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      expect(result.current.uploadProgress).toBeDefined()
      expect(result.current.isUploading).toBeDefined()
    })
  })

  describe('Callback Handlers', () => {
    it('should accept onConversionComplete callback', () => {
      const onConversionComplete = vi.fn()

      const { result } = renderHook(() =>
        useConverter({
          defaultOutputFormat: 'png',
          onConversionComplete,
        })
      )

      // Hook should initialize successfully with callback
      expect(result.current.outputFormat).toBe('png')
    })
  })

  describe('Cleanup', () => {
    it('should handle unmount without errors', () => {
      const { unmount } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png' })
      )

      // Unmount should not throw errors
      expect(() => unmount()).not.toThrow()
    })
  })
})
