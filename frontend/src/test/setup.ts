// @ts-nocheck
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn((key: string) => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
global.localStorage = localStorageMock as any

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock window.electron (for Electron API)
global.window.electron = {
  ipcRenderer: {
    send: vi.fn(),
    on: vi.fn(),
    once: vi.fn(),
    removeListener: vi.fn(),
    invoke: vi.fn(),
  },
  isElectron: true,
}

// Mock file reader
global.FileReader = class MockFileReader {
  result: string | ArrayBuffer | null = null
  error: Error | null = null
  onload: ((event: ProgressEvent) => void) | null = null
  onerror: ((event: ProgressEvent) => void) | null = null
  onabort: ((event: ProgressEvent) => void) | null = null

  readAsDataURL() {
    setTimeout(() => {
      this.result = 'data:image/png;base64,mock'
      if (this.onload) {
        this.onload({ target: this } as any)
      }
    }, 0)
  }

  readAsText() {
    setTimeout(() => {
      this.result = 'mock text'
      if (this.onload) {
        this.onload({ target: this } as any)
      }
    }, 0)
  }

  readAsArrayBuffer() {
    setTimeout(() => {
      this.result = new ArrayBuffer(8)
      if (this.onload) {
        this.onload({ target: this } as any)
      }
    }, 0)
  }

  abort() {}
}
