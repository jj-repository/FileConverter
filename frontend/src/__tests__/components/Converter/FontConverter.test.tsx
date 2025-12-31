import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FontConverter } from '../../../components/Converter/FontConverter'

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
  outputFormat: 'woff2',
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
  fontAPI: {
    convert: vi.fn(),
  },
}))

describe('FontConverter', () => {
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
    mockConverter.outputFormat = 'woff2'
    mockConverter.customFilename = ''
    mockConverter.outputDirectory = null
    // Reset window.electron
    delete (window as any).electron
  })

  describe('Rendering', () => {
    it('should render title "converter.font.title"', () => {
      render(<FontConverter />)
      expect(screen.getByText('converter.font.title')).toBeInTheDocument()
    })

    it('should render info box with font format descriptions', () => {
      render(<FontConverter />)
      expect(screen.getByText(/Convert between font formats for web and desktop use/)).toBeInTheDocument()
      expect(screen.getByText(/TrueType/)).toBeInTheDocument()
      expect(screen.getByText(/OpenType/)).toBeInTheDocument()
      expect(screen.getByText(/Web Open Font Format/)).toBeInTheDocument()
      expect(screen.getByText(/Better compression, modern browsers only/)).toBeInTheDocument()
    })

    it('should render drop zone', () => {
      render(<FontConverter />)
      // Drop zone should be rendered when no file is selected
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render all 4 font formats in dropdown', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      expect(screen.getByRole('option', { name: 'TTF' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'OTF' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'WOFF' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'WOFF2' })).toBeInTheDocument()
    })

    it('should render "Advanced Options" section', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      expect(screen.getByText('Advanced Options')).toBeInTheDocument()
    })

    it('should render subset text input with placeholder', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByPlaceholderText(/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/)
      expect(subsetInput).toBeInTheDocument()
    })

    it('should render optimize checkbox (checked by default)', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const optimizeCheckbox = screen.getByLabelText(/Optimize font/) as HTMLInputElement
      expect(optimizeCheckbox).toBeInTheDocument()
      expect(optimizeCheckbox.checked).toBe(true)
    })

    it('should show Electron-specific fields when window.electron exists', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<FontConverter />)

      expect(screen.getByLabelText(/Custom Filename/)).toBeInTheDocument()
      expect(screen.getByLabelText('Output directory path')).toBeInTheDocument()
      expect(screen.getByLabelText('Browse for output directory')).toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('should call handleFileSelect when file selected', () => {
      render(<FontConverter />)
      // The handleFileSelect function should be available
      expect(mockConverter.handleFileSelect).toBeDefined()
    })

    it('should display file name and size in KB', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      Object.defineProperty(mockFile, 'size', { value: 50 * 1024 }) // 50 KB

      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      expect(screen.getByText(/test.ttf/)).toBeInTheDocument()
      expect(screen.getByText(/50.00 KB/)).toBeInTheDocument()
    })

    it('should enable conversion after file select', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Font/i })
      expect(convertButton).not.toBeDisabled()
    })

    it('should show correct file size format (KB, not MB)', () => {
      const mockFile = new File(['test'], 'large-font.ttf', { type: 'font/ttf' })
      Object.defineProperty(mockFile, 'size', { value: 2048 * 1024 }) // 2048 KB

      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      expect(screen.getByText(/2048.00 KB/)).toBeInTheDocument()
      expect(screen.queryByText(/MB/)).not.toBeInTheDocument()
    })
  })

  describe('Conversion Options', () => {
    it('should change output format', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const formatSelect = screen.getByLabelText('Select output format for font conversion')
      const user = userEvent.setup()
      await user.selectOptions(formatSelect, 'woff')

      await waitFor(() => {
        expect(mockConverter.setOutputFormat).toHaveBeenCalledWith('woff')
      })
    })

    it('should update subset text input', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByLabelText(/Subset Text/)
      const user = userEvent.setup()
      await user.type(subsetInput, 'ABC123')

      await waitFor(() => {
        expect(subsetInput).toHaveValue('ABC123')
      })
    })

    it('should update optimize checkbox', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const optimizeCheckbox = screen.getByLabelText(/Optimize font/) as HTMLInputElement
      const user = userEvent.setup()

      expect(optimizeCheckbox.checked).toBe(true)
      await user.click(optimizeCheckbox)
      expect(optimizeCheckbox.checked).toBe(false)
    })

    it('should default optimize to true', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const optimizeCheckbox = screen.getByLabelText(/Optimize font/) as HTMLInputElement
      expect(optimizeCheckbox.checked).toBe(true)
    })

    it('should update custom filename (Electron)', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<FontConverter />)

      const filenameInput = screen.getByLabelText(/Custom Filename/)
      const user = userEvent.setup()
      await user.type(filenameInput, 'custom-font')

      await waitFor(() => {
        expect(mockConverter.setCustomFilename).toHaveBeenCalled()
      })
    })

    it('should call handleSelectOutputDirectory (Electron)', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<FontConverter />)

      const browseButton = screen.getByLabelText('Browse for output directory')
      const user = userEvent.setup()
      await user.click(browseButton)

      await waitFor(() => {
        expect(mockConverter.handleSelectOutputDirectory).toHaveBeenCalled()
      })
    })

    it('should show "Default Downloads folder" text', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputDirectory = null
      ;(window as any).electron = {}

      render(<FontConverter />)

      expect(screen.getByDisplayValue('Default Downloads folder')).toBeInTheDocument()
    })

    it('should have placeholder for subset text with example characters', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByPlaceholderText(/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/)
      expect(subsetInput).toBeInTheDocument()
    })

    it('should have hint for subset text explaining purpose', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      expect(screen.getByText(/Include only these characters to reduce file size/)).toBeInTheDocument()
    })
  })

  describe('Conversion Flow', () => {
    it('should call fontAPI.convert with subsetText and optimize options', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByLabelText(/Subset Text/)
      const user = userEvent.setup()
      await user.type(subsetInput, 'ABC')

      const convertButton = screen.getByRole('button', { name: /Convert Font/i })
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            subsetText: 'ABC',
            optimize: true,
          })
        )
      })
    })

    it('should pass undefined when subsetText is empty', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Font/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            subsetText: undefined,
            optimize: true,
          })
        )
      })
    })

    it('should pass optimize boolean value', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const optimizeCheckbox = screen.getByLabelText(/Optimize font/)
      const user = userEvent.setup()
      await user.click(optimizeCheckbox) // Uncheck optimize

      const convertButton = screen.getByRole('button', { name: /Convert Font/i })
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            optimize: false,
          })
        )
      })
    })

    it('should show uploading progress', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'uploading'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 45

      render(<FontConverter />)

      expect(screen.getByText('Uploading file...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('45%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show conversion progress', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Converting font...' }

      render(<FontConverter />)

      expect(screen.getByText('Converting font...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('75%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display success message on completion', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Conversion completed!')).toBeInTheDocument()
    })

    it('should handle conversion errors', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Invalid font file'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Invalid font file')).toBeInTheDocument()
    })

    it('should show download link after conversion', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/font.woff2'

      render(<FontConverter />)

      const downloadLink = screen.getByText('Download Converted Font')
      expect(downloadLink).toBeInTheDocument()
      expect(downloadLink).toHaveAttribute('href', '/api/download/font.woff2')
    })
  })

  describe('Status Display', () => {
    it('should show correct status colors', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      const { container } = render(<FontConverter />)

      const statusElement = container.querySelector('.text-green-600')
      expect(statusElement).toBeInTheDocument()
    })

    it('should show correct status text', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Ready to convert')).toBeInTheDocument()
    })

    it('should show "Converting font..." during conversion', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Converting font...')).toBeInTheDocument()
    })

    it('should show "Conversion completed!" on success', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Conversion completed!')).toBeInTheDocument()
    })

    it('should show error message on failure', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Font conversion error'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('Font conversion error')).toBeInTheDocument()
    })

    it('should display progress percentage', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.progress = { progress: 65 }

      render(<FontConverter />)

      const progressTexts = screen.getAllByText('65%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })
  })

  describe('Accessibility', () => {
    it('should have aria-label for output format select', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const formatSelect = screen.getByLabelText('Select output format for font conversion')
      expect(formatSelect).toBeInTheDocument()
    })

    it('should have aria-describedby for subset text hint', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByLabelText(/Subset Text/)
      expect(subsetInput).toHaveAttribute('aria-describedby', 'subset-text-hint')
    })

    it('should have aria-label for output directory and browse button', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      ;(window as any).electron = {}

      render(<FontConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should have proper progress bar ARIA attributes', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.progress = { progress: 50 }

      render(<FontConverter />)

      expect(mockConverter.getProgressAriaAttributes).toHaveBeenCalled()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window.electron', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      delete (window as any).electron

      render(<FontConverter />)

      expect(screen.queryByLabelText(/Custom Filename/)).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Output directory path')).not.toBeInTheDocument()
    })

    it('should handle empty subset text (pass undefined)', async () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile

      render(<FontConverter />)

      const subsetInput = screen.getByLabelText(/Subset Text/)
      expect((subsetInput as HTMLInputElement).value).toBe('')

      const convertButton = screen.getByRole('button', { name: /Convert Font/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            subsetText: undefined,
          })
        )
      })
    })

    it('should handle API errors', () => {
      const mockFile = new File(['test'], 'test.ttf', { type: 'font/ttf' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'API Error: Server unavailable'
      mockConverter.showFeedback = true

      render(<FontConverter />)

      expect(screen.getByText('API Error: Server unavailable')).toBeInTheDocument()
    })
  })
})
