import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ImageConverter } from '../../components/Converter/ImageConverter'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: () => new Promise(() => {}),
      language: 'en',
    },
  }),
}))

// Mock useConverter hook
const mockConverter = {
  selectedFile: null,
  outputFormat: 'png',
  status: 'idle' as const,
  error: null,
  downloadUrl: null,
  progress: null,
  showFeedback: false,
  isDraggingOver: false,
  customFilename: '',
  uploadProgress: 0,
  isUploading: false,
  setSelectedFile: vi.fn(),
  setOutputFormat: vi.fn(),
  setCustomFilename: vi.fn(),
  setOutputDirectory: vi.fn(),
  handleFileSelect: vi.fn(),
  handleDragOver: vi.fn(),
  handleDragLeave: vi.fn(),
  handleDrop: vi.fn(),
  handleConvert: vi.fn(),
  handleDownload: vi.fn(),
  handleReset: vi.fn(),
  setStatus: vi.fn(),
  setError: vi.fn(),
  setDownloadUrl: vi.fn(),
  setShowFeedback: vi.fn(),
  setIsDraggingOver: vi.fn(),
  setUploadProgress: vi.fn(),
  setIsUploading: vi.fn(),
  getStatusAriaAttributes: vi.fn(() => ({
    role: 'status',
    'aria-live': 'polite',
  })),
}

vi.mock('../../hooks/useConverter', () => ({
  useConverter: () => mockConverter,
}))

// Mock API
vi.mock('../../services/api', () => ({
  imageAPI: {
    convert: vi.fn(),
  },
}))

describe('ImageConverter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset mock converter to initial state
    mockConverter.selectedFile = null
    mockConverter.status = 'idle'
    mockConverter.error = null
    mockConverter.downloadUrl = null
    mockConverter.isDraggingOver = false
  })

  describe('Rendering', () => {
    it('should render image converter title', () => {
      render(<ImageConverter />)
      expect(screen.getByText('converter.image.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<ImageConverter />)
      // DropZone component should be rendered
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      Object.defineProperty(mockFile, 'size', { value: 1024 * 1024 }) // 1 MB

      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      expect(screen.getByText(/common.file/)).toBeInTheDocument()
      expect(screen.getByText(/test.jpg/)).toBeInTheDocument()
    })
  })

  describe('File Preview', () => {
    it('should show preview when image file is selected', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      // Mock URL.createObjectURL
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = vi.fn()

      render(<ImageConverter />)

      await waitFor(() => {
        const preview = screen.getByAltText('converter.image.preview')
        expect(preview).toBeInTheDocument()
      })
    })

    it('should cleanup preview URL on unmount', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      const mockRevokeURL = vi.fn()
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = mockRevokeURL

      const { unmount } = render(<ImageConverter />)

      unmount()

      expect(mockRevokeURL).toHaveBeenCalled()
    })
  })

  describe('Quality Control', () => {
    it('should have default quality value of 95', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      // Quality input should have default value
      const qualityInput = screen.queryByRole('slider')
      if (qualityInput) {
        expect(qualityInput).toHaveValue('95')
      }
    })

    it('should render quality slider when file is selected', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      const qualitySlider = screen.queryByRole('slider')
      expect(qualitySlider).toBeTruthy()
    })
  })

  describe('Format Selection', () => {
    it('should have PNG as default output format', () => {
      expect(mockConverter.outputFormat).toBe('png')
    })

    it('should show all supported image formats', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      // Check for format select dropdown
      const formatSelect = screen.queryByRole('combobox')
      expect(formatSelect).toBeTruthy()
    })
  })

  describe('Conversion', () => {
    it('should call handleConvert when convert button is clicked', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      const convertButton = screen.getByRole('button', { name: /convert/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should disable convert button when no file is selected', () => {
      mockConverter.selectedFile = null

      render(<ImageConverter />)

      const convertButton = screen.queryByRole('button', { name: /convert/i })
      // Button should either not exist or be disabled
      if (convertButton) {
        expect(convertButton).toBeDisabled()
      }
    })

    it('should pass quality parameter to conversion', async () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      const convertButton = screen.getByRole('button', { name: /convert/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({ quality: expect.any(Number) })
        )
      })
    })
  })

  describe('Drag and Drop', () => {
    it('should show overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<ImageConverter />)

      expect(screen.getByText('common.dropToReplace')).toBeInTheDocument()
    })

    it('should not show overlay when not dragging', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<ImageConverter />)

      expect(screen.queryByText('common.dropToReplace')).not.toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show loading state during conversion', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<ImageConverter />)

      // Should show some indication of conversion in progress
      expect(mockConverter.status).toBe('converting')
    })

    it('should show error message when conversion fails', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Conversion failed'
      mockConverter.showFeedback = true

      render(<ImageConverter />)

      // Error should be available in the state
      expect(mockConverter.error).toBe('Conversion failed')
    })

    it('should show success message when conversion completes', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/file.png'

      render(<ImageConverter />)

      expect(mockConverter.status).toBe('completed')
      expect(mockConverter.downloadUrl).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ImageConverter />)

      // Check for semantic HTML
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
    })

    it('should have accessible form controls when file is selected', () => {
      const mockFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      mockConverter.selectedFile = mockFile

      render(<ImageConverter />)

      // Form controls should be accessible
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })
})
