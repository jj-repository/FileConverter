import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getFriendlyErrorMessage, getErrorMessage } from '../../utils/errorMessages'

// Mock i18n
vi.mock('../../i18n', () => ({
  default: {
    t: (key: string) => key,
  },
}))

describe('errorMessages', () => {
  describe('getFriendlyErrorMessage', () => {
    it('should return unknown error for empty string', () => {
      const result = getFriendlyErrorMessage('')
      expect(result).toBe('errors.unknown')
    })

    it('should return unknown error for null/undefined', () => {
      const result = getFriendlyErrorMessage(null as any)
      expect(result).toBe('errors.unknown')
    })

    describe('FFmpeg and conversion errors', () => {
      it('should detect FFmpeg errors', () => {
        expect(getFriendlyErrorMessage('FFmpeg failed to encode')).toBe('errors.conversionFailed')
        expect(getFriendlyErrorMessage('ffmpeg: error while processing')).toBe('errors.conversionFailed')
      })

      it('should detect codec errors', () => {
        expect(getFriendlyErrorMessage('Codec not supported')).toBe('errors.conversionFailed')
        expect(getFriendlyErrorMessage('encoding failed')).toBe('errors.conversionFailed')
        expect(getFriendlyErrorMessage('decoding error')).toBe('errors.conversionFailed')
      })

      it('should detect corrupted file errors', () => {
        expect(getFriendlyErrorMessage('File is corrupted')).toBe('errors.conversionFailed')
        expect(getFriendlyErrorMessage('Invalid stream detected')).toBe('errors.conversionFailed')
      })
    })

    describe('File not found errors', () => {
      it('should detect file not found errors', () => {
        expect(getFriendlyErrorMessage('File not found')).toBe('errors.fileNotFound')
        expect(getFriendlyErrorMessage('No such file or directory')).toBe('errors.fileNotFound')
        expect(getFriendlyErrorMessage('ENOENT: file does not exist')).toBe('errors.fileNotFound')
      })
    })

    describe('Timeout errors', () => {
      it('should detect timeout errors', () => {
        expect(getFriendlyErrorMessage('Request timeout')).toBe('errors.timeout')
        expect(getFriendlyErrorMessage('Operation timed out')).toBe('errors.timeout')
        expect(getFriendlyErrorMessage('Deadline exceeded')).toBe('errors.timeout')
        expect(getFriendlyErrorMessage('Process took too long')).toBe('errors.timeout')
      })
    })

    describe('Format errors', () => {
      it('should detect unsupported format errors', () => {
        expect(getFriendlyErrorMessage('Format not supported')).toBe('errors.formatError')
        expect(getFriendlyErrorMessage('Unsupported format: xyz')).toBe('errors.formatError')
        expect(getFriendlyErrorMessage('Invalid format specified')).toBe('errors.formatError')
        expect(getFriendlyErrorMessage('Unknown format type')).toBe('errors.formatError')
      })
    })

    describe('Network errors', () => {
      it('should detect network connection errors', () => {
        expect(getFriendlyErrorMessage('Network error occurred')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('Connection refused')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('ECONNREFUSED')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('ECONNRESET')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('ETIMEDOUT')).toBe('errors.networkError')
      })

      it('should detect fetch errors', () => {
        expect(getFriendlyErrorMessage('Fetch failed')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('Failed to fetch resource')).toBe('errors.networkError')
      })
    })

    describe('File size errors', () => {
      it('should detect file too large errors', () => {
        expect(getFriendlyErrorMessage('File too large')).toBe('errors.fileTooLarge')
        expect(getFriendlyErrorMessage('File size exceeds maximum')).toBe('errors.fileTooLarge')
        expect(getFriendlyErrorMessage('File is too big')).toBe('errors.fileTooLarge')
        expect(getFriendlyErrorMessage('Payload too large')).toBe('errors.fileTooLarge')
        expect(getFriendlyErrorMessage('HTTP 413 error')).toBe('errors.fileTooLarge')
      })
    })

    describe('Permission errors', () => {
      it('should detect permission denied errors', () => {
        expect(getFriendlyErrorMessage('Permission denied')).toBe('errors.permissionDenied')
        expect(getFriendlyErrorMessage('Access denied to file')).toBe('errors.permissionDenied')
        expect(getFriendlyErrorMessage('EACCES')).toBe('errors.permissionDenied')
        expect(getFriendlyErrorMessage('Unauthorized access')).toBe('errors.permissionDenied')
        expect(getFriendlyErrorMessage('Forbidden operation')).toBe('errors.permissionDenied')
      })
    })

    describe('Disk space errors', () => {
      it('should detect disk space errors', () => {
        expect(getFriendlyErrorMessage('No space left on device')).toBe('errors.diskSpace')
        expect(getFriendlyErrorMessage('Disk full error')).toBe('errors.diskSpace')
        expect(getFriendlyErrorMessage('ENOSPC')).toBe('errors.diskSpace')
        expect(getFriendlyErrorMessage('Out of space')).toBe('errors.diskSpace')
      })
    })

    describe('Server errors', () => {
      it('should detect internal server errors', () => {
        expect(getFriendlyErrorMessage('HTTP 500 error')).toBe('errors.serverError')
        expect(getFriendlyErrorMessage('Internal server error occurred')).toBe('errors.serverError')
        expect(getFriendlyErrorMessage('Server error while processing')).toBe('errors.serverError')
      })
    })

    describe('Case insensitivity', () => {
      it('should handle uppercase errors', () => {
        expect(getFriendlyErrorMessage('FFMPEG FAILED')).toBe('errors.conversionFailed')
        expect(getFriendlyErrorMessage('FILE NOT FOUND')).toBe('errors.fileNotFound')
        expect(getFriendlyErrorMessage('TIMEOUT ERROR')).toBe('errors.timeout')
      })

      it('should handle mixed case errors', () => {
        expect(getFriendlyErrorMessage('Network Error Occurred')).toBe('errors.networkError')
        expect(getFriendlyErrorMessage('Format Not Supported')).toBe('errors.formatError')
      })
    })

    describe('Unknown errors', () => {
      it('should return unknown error for unrecognized messages', () => {
        expect(getFriendlyErrorMessage('Some random error')).toBe('errors.unknown')
        expect(getFriendlyErrorMessage('xyz123 error code')).toBe('errors.unknown')
        expect(getFriendlyErrorMessage('Unexpected failure')).toBe('errors.unknown')
      })
    })
  })

  describe('getErrorMessage', () => {
    it('should call getFriendlyErrorMessage and return result', () => {
      const result = getErrorMessage('FFmpeg failed')
      expect(result).toBe('errors.conversionFailed')
    })

    it('should return unknown error for unrecognized messages', () => {
      const result = getErrorMessage('Some unknown error')
      expect(result).toBe('errors.unknown')
    })

    it('should handle network errors', () => {
      const result = getErrorMessage('Network connection failed')
      expect(result).toBe('errors.networkError')
    })

    it('should handle file size errors', () => {
      const result = getErrorMessage('File too large for upload')
      expect(result).toBe('errors.fileTooLarge')
    })
  })
})
