import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DocumentConverter } from '../../components/Converter/DocumentConverter'

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
  selectedFile: null as File | null,
  outputFormat: 'pdf',
  status: 'idle' as 'idle' | 'uploading' | 'converting' | 'completed' | 'failed' | 'error',
  error: null as string | null,
  downloadUrl: null as string | null,
  progress: null as any,
  showFeedback: false,
  isDraggingOver: false,
  customFilename: '',
  uploadProgress: 0,
  isUploading: false,
  outputDirectory: null as string | null,
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

vi.mock('../../hooks/useConverter', () => ({
  useConverter: () => mockConverter,
}))

// Mock API
vi.mock('../../services/api', () => ({
  documentAPI: {
    convert: vi.fn(),
  },
}))

describe('DocumentConverter', () => {
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
    mockConverter.outputFormat = 'pdf'
  })

  describe('Rendering', () => {
    it('should render document converter title', () => {
      render(<DocumentConverter />)
      expect(screen.getByText('converter.document.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<DocumentConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      Object.defineProperty(mockFile, 'size', { value: 2 * 1024 * 1024 }) // 2 MB

      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      expect(screen.getByText(/common.file/)).toBeInTheDocument()
      expect(screen.getByText(/test.docx/)).toBeInTheDocument()
      expect(screen.getByText(/2.00 MB/)).toBeInTheDocument()
    })

    it('should format file size correctly for KB', () => {
      const mockFile = new File(['test'], 'small.txt', { type: 'text/plain' })
      Object.defineProperty(mockFile, 'size', { value: 128 * 1024 }) // 128 KB

      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      expect(screen.getByText(/128.00 KB/)).toBeInTheDocument()
    })
  })

  describe('Format Selection', () => {
    it('should have PDF as default output format', () => {
      expect(mockConverter.outputFormat).toBe('pdf')
    })

    it('should show all supported document formats', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const formatSelect = screen.getByLabelText('Select output format for document conversion')
      expect(formatSelect).toBeInTheDocument()

      // Check for formats with their descriptions
      expect(screen.getByRole('option', { name: /PDF Document/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Microsoft Word/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Markdown/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /HTML Webpage/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Plain Text/ })).toBeInTheDocument()
    })

    it('should disable format select during conversion', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DocumentConverter />)

      const formatSelect = screen.getByLabelText('Select output format for document conversion')
      expect(formatSelect).toBeDisabled()
    })

    it('should show format descriptions correctly', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      expect(screen.getByRole('option', { name: 'Plain Text' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'PDF Document' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Microsoft Word' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Markdown' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'HTML Webpage' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Rich Text Format' })).toBeInTheDocument()
    })
  })

  describe('Preserve Formatting Checkbox', () => {
    it('should render preserve formatting checkbox', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.preserveFormatting')
      expect(checkbox).toBeInTheDocument()
    })

    it('should have preserve formatting checked by default', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.preserveFormatting') as HTMLInputElement
      expect(checkbox.checked).toBe(true)
    })

    it('should allow toggling preserve formatting', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.preserveFormatting') as HTMLInputElement
      const user = userEvent.setup()

      expect(checkbox.checked).toBe(true)
      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })

    it('should disable preserve formatting during conversion', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.preserveFormatting')
      expect(checkbox).toBeDisabled()
    })
  })

  describe('Table of Contents Checkbox', () => {
    it('should render table of contents checkbox', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).toBeInTheDocument()
    })

    it('should have table of contents unchecked by default', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents') as HTMLInputElement
      expect(checkbox.checked).toBe(false)
    })

    it('should allow toggling table of contents for PDF format', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'pdf'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents') as HTMLInputElement
      const user = userEvent.setup()

      expect(checkbox.checked).toBe(false)
      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)
    })

    it('should enable TOC for PDF format', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'pdf'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).not.toBeDisabled()
    })

    it('should enable TOC for HTML format', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'html'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).not.toBeDisabled()
    })

    it('should enable TOC for DOCX format', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'docx'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).not.toBeDisabled()
    })

    it('should disable TOC for TXT format', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'txt'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).toBeDisabled()
    })

    it('should disable TOC for MD format', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'md'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).toBeDisabled()
    })

    it('should disable TOC during conversion', () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.outputFormat = 'pdf'

      render(<DocumentConverter />)

      const checkbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(checkbox).toBeDisabled()
    })
  })

  describe('Custom Filename', () => {
    it('should render custom filename input', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeInTheDocument()
    })

    it('should disable custom filename during conversion', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DocumentConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeDisabled()
    })
  })

  describe('Output Directory (Electron)', () => {
    it('should show output directory controls in Electron environment', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should disable output directory controls during conversion', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DocumentConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeDisabled()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeDisabled()
    })
  })

  describe('Conversion', () => {
    it('should call handleConvert when convert button is clicked', async () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const convertButton = screen.getByRole('button', { name: /convertDocument/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should pass preserveFormatting and toc to conversion', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'pdf'

      render(<DocumentConverter />)

      // Toggle preserve formatting off
      const preserveCheckbox = screen.getByLabelText('converter.document.preserveFormatting')
      await userEvent.click(preserveCheckbox)

      // Enable TOC
      const tocCheckbox = screen.getByLabelText('converter.document.tableOfContents')
      await userEvent.click(tocCheckbox)

      const convertButton = screen.getByRole('button', { name: /convertDocument/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            preserveFormatting: false,
            toc: true,
          })
        )
      })
    })

    it('should pass default values when checkboxes unchecked', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const convertButton = screen.getByRole('button', { name: /convertDocument/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            preserveFormatting: true,
            toc: false,
          })
        )
      })
    })
  })

  describe('Drag and Drop', () => {
    it('should show overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<DocumentConverter />)

      expect(screen.getByText('common.dropToReplace')).toBeInTheDocument()
    })

    it('should not show overlay when not dragging', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<DocumentConverter />)

      expect(screen.queryByText('common.dropToReplace')).not.toBeInTheDocument()
    })
  })

  describe('Upload Progress', () => {
    it('should show upload progress during upload', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 60

      render(<DocumentConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('60%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should not show upload progress when not uploading', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false

      render(<DocumentConverter />)

      expect(screen.queryByText('common.uploadingFile')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Progress', () => {
    it('should show conversion progress during conversion', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 80, message: 'Converting document...' }

      render(<DocumentConverter />)

      expect(screen.getByText('Converting document...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('80%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show processing message when no progress message', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 50 }

      render(<DocumentConverter />)

      expect(screen.getByText('common.processing')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show error message when conversion fails', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Conversion failed: Invalid document'
      mockConverter.showFeedback = true

      render(<DocumentConverter />)

      expect(mockConverter.error).toBe('Conversion failed: Invalid document')
    })

    it('should show success message when conversion completes', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.pdf'
      mockConverter.showFeedback = true

      render(<DocumentConverter />)

      expect(screen.getByText('messages.conversionSuccess')).toBeInTheDocument()
    })
  })

  describe('Button States', () => {
    it('should show convert and reset buttons when idle', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<DocumentConverter />)

      expect(screen.getByRole('button', { name: /convertDocument/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('should show disabled button when converting', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DocumentConverter />)

      // When converting, the convert and reset buttons should not be available
      expect(screen.queryByRole('button', { name: /convertDocument/i })).not.toBeInTheDocument()
      expect(mockConverter.status).toBe('converting')
    })

    it('should show download and convert another buttons when completed', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.pdf'

      render(<DocumentConverter />)

      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /convertAnother/i })).toBeInTheDocument()
    })

    it('should show convert and reset buttons when failed', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed'

      render(<DocumentConverter />)

      expect(screen.getByRole('button', { name: /convertDocument/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<DocumentConverter />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
    })

    it('should have accessible form controls when file is selected', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const formatSelect = screen.getByLabelText('Select output format for document conversion')
      expect(formatSelect).toBeInTheDocument()

      const preserveCheckbox = screen.getByLabelText('converter.document.preserveFormatting')
      expect(preserveCheckbox).toBeInTheDocument()

      const tocCheckbox = screen.getByLabelText('converter.document.tableOfContents')
      expect(tocCheckbox).toBeInTheDocument()
    })

    it('should have describedby for custom filename input', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()
    })

    it('should have describedby for output directory input', () => {
      const mockFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      mockConverter.selectedFile = mockFile

      render(<DocumentConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toHaveAttribute('aria-describedby', 'output-directory-hint')
      expect(screen.getByText('common.outputDirectoryHint')).toBeInTheDocument()
    })
  })
})
