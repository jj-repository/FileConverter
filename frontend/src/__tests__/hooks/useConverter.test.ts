import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useConverter } from '../../hooks/useConverter'

vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    progress: null,
    isConnected: false,
    reconnectAttempt: 0,
    reconnect: vi.fn(),
  })),
}))

global.fetch = vi.fn()

const mockFile = new File(['content'], 'test.jpg', { type: 'image/jpeg' })

const makeAPI = (overrides = {}) => ({
  convert: vi.fn().mockResolvedValue({
    session_id: 'sess-123',
    status: 'completed',
    download_url: '/api/image/download/out.png',
  }),
  ...overrides,
})

describe('useConverter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('initializes with correct defaults', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      expect(result.current.selectedFile).toBeNull()
      expect(result.current.outputFormat).toBe('png')
      expect(result.current.status).toBe('idle')
      expect(result.current.error).toBeNull()
      expect(result.current.downloadUrl).toBeNull()
      expect(result.current.uploadProgress).toBe(0)
      expect(result.current.isUploading).toBe(false)
    })

    it('respects defaultOutputFormat', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'webp' }))
      expect(result.current.outputFormat).toBe('webp')
    })
  })

  describe('File selection', () => {
    it('sets selectedFile and resets state on handleFileSelect', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      expect(result.current.selectedFile).toBe(mockFile)
      expect(result.current.status).toBe('idle')
      expect(result.current.error).toBeNull()
      expect(result.current.downloadUrl).toBeNull()
    })
  })

  describe('Format and filename', () => {
    it('setOutputFormat updates outputFormat', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.setOutputFormat('gif') })
      expect(result.current.outputFormat).toBe('gif')
    })

    it('setCustomFilename updates customFilename', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.setCustomFilename('my-output') })
      expect(result.current.customFilename).toBe('my-output')
    })
  })

  describe('Drag and drop', () => {
    it('setIsDraggingOver on handleDragOver, cleared on handleDragLeave', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      const makeEv = () => ({ preventDefault: vi.fn(), stopPropagation: vi.fn() }) as unknown as React.DragEvent
      act(() => { result.current.handleDragOver(makeEv()) })
      expect(result.current.isDraggingOver).toBe(true)
      act(() => { result.current.handleDragLeave(makeEv()) })
      expect(result.current.isDraggingOver).toBe(false)
    })

    it('handleDrop selects the first dropped file', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      const ev = {
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        dataTransfer: { files: [mockFile] },
      } as unknown as React.DragEvent
      act(() => { result.current.handleDrop(ev) })
      expect(result.current.selectedFile).toBe(mockFile)
      expect(result.current.isDraggingOver).toBe(false)
    })
  })

  describe('handleConvert — success', () => {
    it('transitions idle → converting → completed, sets downloadUrl', async () => {
      const api = makeAPI()
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })

      await act(async () => { await result.current.handleConvert(api, {}) })

      expect(api.convert).toHaveBeenCalledOnce()
      expect(api.convert).toHaveBeenCalledWith(mockFile, expect.objectContaining({ outputFormat: 'png' }))
      expect(result.current.status).toBe('completed')
      expect(result.current.downloadUrl).toBe('/api/image/download/out.png')
      expect(result.current.error).toBeNull()
    })

    it('calls onConversionComplete callback with download URL', async () => {
      const onConversionComplete = vi.fn()
      const api = makeAPI()
      const { result } = renderHook(() =>
        useConverter({ defaultOutputFormat: 'png', onConversionComplete })
      )
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, {}) })
      expect(onConversionComplete).toHaveBeenCalledWith('/api/image/download/out.png')
    })

    it('passes extra options to converter API', async () => {
      const api = makeAPI()
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, { quality: 90 }) })
      expect(api.convert).toHaveBeenCalledWith(mockFile, expect.objectContaining({ quality: 90 }))
    })
  })

  describe('handleConvert — failure', () => {
    it('sets status to failed and records error on API rejection', async () => {
      const api = makeAPI({
        convert: vi.fn().mockRejectedValue(new Error('Network error')),
      })
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, {}) })
      expect(result.current.status).toBe('failed')
      expect(result.current.error).not.toBeNull()
    })

    it('sets status to failed when API returns status=failed', async () => {
      const api = makeAPI({
        convert: vi.fn().mockResolvedValue({
          session_id: 'sess-456',
          status: 'failed',
          error: 'Unsupported format',
        }),
      })
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, {}) })
      expect(result.current.status).toBe('failed')
      expect(result.current.error).not.toBeNull()
    })

    it('does nothing when no file is selected', async () => {
      const api = makeAPI()
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      await act(async () => { await result.current.handleConvert(api, {}) })
      expect(api.convert).not.toHaveBeenCalled()
      expect(result.current.status).toBe('idle')
    })
  })

  describe('handleReset', () => {
    it('clears all state back to idle after a conversion', async () => {
      const api = makeAPI()
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, {}) })
      expect(result.current.status).toBe('completed')

      act(() => { result.current.handleReset() })
      expect(result.current.selectedFile).toBeNull()
      expect(result.current.status).toBe('idle')
      expect(result.current.downloadUrl).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })

  describe('Accessibility helpers', () => {
    it('getProgressAriaAttributes returns progressbar role', () => {
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      const attrs = result.current.getProgressAriaAttributes()
      expect(attrs.role).toBe('progressbar')
      expect(attrs['aria-valuemin']).toBe(0)
      expect(attrs['aria-valuemax']).toBe(100)
    })

    it('getStatusAriaAttributes returns alert role for failed status', async () => {
      const api = makeAPI({ convert: vi.fn().mockRejectedValue(new Error('fail')) })
      const { result } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      act(() => { result.current.handleFileSelect(mockFile) })
      await act(async () => { await result.current.handleConvert(api, {}) })
      const attrs = result.current.getStatusAriaAttributes()
      expect(attrs.role).toBe('alert')
    })
  })

  describe('Cleanup', () => {
    it('unmounts without errors', () => {
      const { unmount } = renderHook(() => useConverter({ defaultOutputFormat: 'png' }))
      expect(() => unmount()).not.toThrow()
    })
  })
})
