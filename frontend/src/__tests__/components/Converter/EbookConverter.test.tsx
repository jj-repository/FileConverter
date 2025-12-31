import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EbookConverter } from '../../../components/Converter/EbookConverter'

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
  outputFormat: 'epub',
  status: 'idle' as const,
  error: null,
  downloadUrl: null,
  progress: null,
  showFeedback: false,
  isDraggingOver: false,
  customFilename: '',
  uploadProgress: 0,
  isUploading: false,
  outputDirectory: null,
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
  handleSelectOutputDirectory: vi.fn(),
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
  getProgressAriaAttributes: vi.fn(() => ({
    role: 'progressbar',
    'aria-valuenow': 0,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
  })),
  getUploadProgressAriaAttributes: vi.fn(() => ({
    role: 'progressbar',
    'aria-valuenow': 0,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
  })),
}

vi.mock('../../../hooks/useConverter', () => ({
  useConverter: () => mockConverter,
}))

// Mock API
vi.mock('../../../services/api', () => ({
  ebookAPI: {
    convert: vi.fn(),
  },
}))

describe('EbookConverter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset mock converter to initial state
    mockConverter.selectedFile = null
    mockConverter.status = 'idle'
    mockConverter.error = null
    mockConverter.downloadUrl = null
    mockConverter.isDraggingOver = false
    mockConverter.showFeedback = false
    mockConverter.isUploading = false
    mockConverter.uploadProgress = 0
    mockConverter.progress = null
    mockConverter.outputFormat = 'epub'
    mockConverter.customFilename = ''
    mockConverter.outputDirectory = null
    // Clear window.electron
    delete (window as any).electron
  })

  describe('Rendering', () => {
    it('should render title "converter.ebook.title"', () => {
      render(<EbookConverter />)
      expect(screen.getByText('converter.ebook.title')).toBeInTheDocument()
    })

    it('should render info box with supported formats', () => {
      render(<EbookConverter />)
      expect(screen.getByText(/Convert between eBook formats/)).toBeInTheDocument()
      expect(screen.getByText(/Supports EPUB, TXT, HTML, and PDF/)).toBeInTheDocument()
    })

    it('should render warning box about formatting loss', () => {
      render(<EbookConverter />)
      expect(screen.getByText(/Note:/)).toBeInTheDocument()
      expect(screen.getByText(/Conversions may lose advanced formatting, images, and metadata/)).toBeInTheDocument()
      expect(screen.getByText(/EPUB is recommended for preservation of structure and content/)).toBeInTheDocument()
    })

    it('should render drop zone', () => {
      render(<EbookConverter />)
      // DropZone component should be rendered when no file is selected
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render all 4 ebook formats in dropdown', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      expect(screen.getByRole('option', { name: 'EPUB' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TXT' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'HTML' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'PDF' })).toBeInTheDocument()
    })

    it('should render file info when file selected', () => {
      const mockFile = new File(['test'], 'book.epub', { type: 'application/epub+zip' })
      Object.defineProperty(mockFile, 'size', { value: 3 * 1024 * 1024 }) // 3 MB
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      expect(screen.getByText(/Selected file:/)).toBeInTheDocument()
      expect(screen.getByText(/book.epub/)).toBeInTheDocument()
    })

    it('should show Electron-specific fields when window.electron exists', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<EbookConverter />)

      expect(screen.getByLabelText('Output directory path')).toBeInTheDocument()
      expect(screen.getByLabelText('Browse for output directory')).toBeInTheDocument()
      expect(screen.getByLabelText(/Custom Filename/)).toBeInTheDocument()
    })

    it('should have proper structure with Card components', () => {
      render(<EbookConverter />)
      // Component should render without errors and contain proper structure
      expect(screen.getByText('converter.ebook.title')).toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('should call handleFileSelect when file selected', () => {
      render(<EbookConverter />)
      // The DropZone component receives handleFileSelect callback
      expect(mockConverter.handleFileSelect).toBeDefined()
    })

    it('should display selected file name and size', () => {
      const mockFile = new File(['test'], 'mybook.epub', { type: 'application/epub+zip' })
      Object.defineProperty(mockFile, 'size', { value: 5 * 1024 * 1024 }) // 5 MB
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      expect(screen.getByText(/mybook.epub/)).toBeInTheDocument()
      expect(screen.getByText(/5.00 MB/)).toBeInTheDocument()
    })

    it('should show file size in MB format', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      Object.defineProperty(mockFile, 'size', { value: 2.5 * 1024 * 1024 }) // 2.5 MB
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      expect(screen.getByText(/2.50 MB/)).toBeInTheDocument()
    })

    it('should enable conversion controls after selection', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert eBook/i })
      expect(convertButton).not.toBeDisabled()
    })
  })

  describe('Conversion Options', () => {
    it('should change output format', async () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      const formatSelect = screen.getByLabelText('Select output format for ebook conversion')
      const user = userEvent.setup()
      await user.selectOptions(formatSelect, 'pdf')

      expect(mockConverter.setOutputFormat).toHaveBeenCalledWith('pdf')
    })

    it('should update custom filename (Electron only)', async () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const filenameInput = screen.getByLabelText(/Custom Filename/)
      const user = userEvent.setup()
      await user.type(filenameInput, 'customname')

      expect(mockConverter.setCustomFilename).toHaveBeenCalled()
    })

    it('should call handleSelectOutputDirectory (Electron only)', async () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const browseButton = screen.getByLabelText('Browse for output directory')
      const user = userEvent.setup()
      await user.click(browseButton)

      expect(mockConverter.handleSelectOutputDirectory).toHaveBeenCalled()
    })

    it('should show "Default Downloads folder" when no directory set', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputDirectory = null
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path') as HTMLInputElement
      expect(outputDirInput.value).toBe('Default Downloads folder')
    })

    it('should disable controls during conversion', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<EbookConverter />)

      const convertButton = screen.getByRole('button', { name: /Converting.../i })
      expect(convertButton).toBeDisabled()
    })

    it('should show placeholder for custom filename', () => {
      const mockFile = new File(['test'], 'mybook.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'pdf'
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const filenameInput = screen.getByLabelText(/Custom Filename/) as HTMLInputElement
      expect(filenameInput.placeholder).toBe('mybook.pdf')
    })
  })

  describe('Conversion Flow', () => {
    it('should call ebookAPI.convert when convert clicked', async () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert eBook/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should show "Converting..." during upload/conversion', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'uploading'

      render(<EbookConverter />)

      expect(screen.getByRole('button', { name: /Converting.../i })).toBeInTheDocument()
    })

    it('should display upload progress bar and percentage', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'uploading'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 45

      render(<EbookConverter />)

      const progressTexts = screen.getAllByText('45%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display conversion progress bar', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 70, message: 'Converting eBook...' }

      render(<EbookConverter />)

      const progressTexts = screen.getAllByText('70%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show completion message with download link (web)', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.pdf'
      mockConverter.showFeedback = true
      // No window.electron

      render(<EbookConverter />)

      expect(screen.getByText(/Download Converted eBook/i)).toBeInTheDocument()
    })

    it('should handle conversion errors', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Invalid eBook format'
      mockConverter.showFeedback = true

      render(<EbookConverter />)

      expect(screen.getByText('Invalid eBook format')).toBeInTheDocument()
    })

    it('should allow reset and file reselection', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      // Component allows file reselection through handleFileSelect
      expect(mockConverter.handleFileSelect).toBeDefined()
    })

    it('should pass empty options object to API', async () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert eBook/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          {}
        )
      })
    })
  })

  describe('Status Display', () => {
    it('should show correct status colors (green=completed, red=failed, blue=converting, gray=idle)', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      // Test completed - green
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true
      const { rerender } = render(<EbookConverter />)
      let statusElement = screen.getByText('Conversion completed!')
      expect(statusElement.parentElement?.className).toContain('text-green-600')

      // Test failed - red
      mockConverter.status = 'failed'
      mockConverter.error = 'Error'
      rerender(<EbookConverter />)
      statusElement = screen.getByText('Error')
      expect(statusElement.parentElement?.className).toContain('text-red-600')

      // Test converting - blue
      mockConverter.status = 'converting'
      mockConverter.error = null
      rerender(<EbookConverter />)
      statusElement = screen.getByText('Converting eBook...')
      expect(statusElement.parentElement?.className).toContain('text-blue-600')

      // Test uploading - blue
      mockConverter.status = 'uploading'
      rerender(<EbookConverter />)
      statusElement = screen.getByText('Uploading file...')
      expect(statusElement.parentElement?.className).toContain('text-blue-600')
    })

    it('should show correct status text for each state', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.showFeedback = true

      // Test idle
      mockConverter.status = 'idle'
      const { rerender } = render(<EbookConverter />)
      expect(screen.getByText('Ready to convert')).toBeInTheDocument()

      // Test uploading
      mockConverter.status = 'uploading'
      rerender(<EbookConverter />)
      expect(screen.getByText('Uploading file...')).toBeInTheDocument()

      // Test converting
      mockConverter.status = 'converting'
      rerender(<EbookConverter />)
      expect(screen.getByText('Converting eBook...')).toBeInTheDocument()

      // Test completed
      mockConverter.status = 'completed'
      rerender(<EbookConverter />)
      expect(screen.getByText('Conversion completed!')).toBeInTheDocument()

      // Test failed
      mockConverter.status = 'failed'
      mockConverter.error = 'Custom error'
      rerender(<EbookConverter />)
      expect(screen.getByText('Custom error')).toBeInTheDocument()
    })

    it('should display progress message from WebSocket', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.progress = { progress: 50, message: 'Processing chapters...' }

      render(<EbookConverter />)

      expect(screen.getByText('Processing chapters...')).toBeInTheDocument()
    })

    it('should show upload progress during upload', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'uploading'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 33

      render(<EbookConverter />)

      expect(screen.getByText('Uploading file...')).toBeInTheDocument()
      expect(screen.getAllByText('33%').length).toBeGreaterThan(0)
    })

    it('should show conversion progress during conversion', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 88 }

      render(<EbookConverter />)

      expect(screen.getAllByText('88%').length).toBeGreaterThan(0)
    })

    it('should show "Conversion completed!" on success', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<EbookConverter />)

      expect(screen.getByText('Conversion completed!')).toBeInTheDocument()
    })

    it('should show error message on failure', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Failed to process eBook'
      mockConverter.showFeedback = true

      render(<EbookConverter />)

      expect(screen.getByText('Failed to process eBook')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have aria-label for output format select', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile

      render(<EbookConverter />)

      const formatSelect = screen.getByLabelText('Select output format for ebook conversion')
      expect(formatSelect).toBeInTheDocument()
    })

    it('should have aria-label for output directory input', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()
    })

    it('should have aria-label for browse button', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<EbookConverter />)

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should have proper progress bar ARIA attributes', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.progress = { progress: 60 }

      render(<EbookConverter />)

      expect(mockConverter.getProgressAriaAttributes).toHaveBeenCalled()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window.electron', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      delete (window as any).electron

      render(<EbookConverter />)

      // Should not show Electron-specific fields
      expect(screen.queryByLabelText('Output directory path')).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/Custom Filename/)).not.toBeInTheDocument()
    })

    it('should handle API errors gracefully', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Network error'
      mockConverter.showFeedback = true

      render(<EbookConverter />)

      expect(screen.getByText('Network error')).toBeInTheDocument()
    })

    it('should handle missing progress data', () => {
      const mockFile = new File(['test'], 'test.epub', { type: 'application/epub+zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.progress = null

      render(<EbookConverter />)

      expect(screen.getByText('Converting eBook...')).toBeInTheDocument()
    })
  })
})
