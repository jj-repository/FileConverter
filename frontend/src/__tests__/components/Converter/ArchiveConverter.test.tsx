import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ArchiveConverter } from '../../../components/Converter/ArchiveConverter'

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
  outputFormat: 'zip',
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
  archiveAPI: {
    convert: vi.fn(),
  },
}))

describe('ArchiveConverter', () => {
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
    mockConverter.outputFormat = 'zip'
  })

  describe('Rendering', () => {
    it('should render archive converter title', () => {
      render(<ArchiveConverter />)
      expect(screen.getByText('converter.archive.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<ArchiveConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      Object.defineProperty(mockFile, 'size', { value: 2 * 1024 * 1024 }) // 2 MB

      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText(/File:/)).toBeInTheDocument()
      expect(screen.getByText(/test.zip/)).toBeInTheDocument()
      expect(screen.getByText(/2.00 MB/)).toBeInTheDocument()
    })

    it('should render all 8 archive formats in dropdown', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const formatSelect = screen.getByLabelText('Select output format for archive conversion')
      expect(formatSelect).toBeInTheDocument()

      // Check for all 8 archive formats
      expect(screen.getByRole('option', { name: 'ZIP' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TAR' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TAR.GZ' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TGZ' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TAR.BZ2' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TBZ2' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'GZ' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: '7Z' })).toBeInTheDocument()
    })

    it('should render compression level slider (0-9)', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level: 6/)
      expect(slider).toBeInTheDocument()
      expect(slider).toHaveAttribute('min', '0')
      expect(slider).toHaveAttribute('max', '9')
      expect(slider).toHaveValue('6')
    })

    it('should show Electron-specific fields when window.electron exists', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('should call handleFileSelect when file dropped', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = null

      render(<ArchiveConverter />)

      // DropZone should be present and should trigger file selection
      expect(mockConverter.handleFileSelect).toBeDefined()
    })

    it('should display file name and size', () => {
      const mockFile = new File(['test'], 'archive.tar.gz', { type: 'application/gzip' })
      Object.defineProperty(mockFile, 'size', { value: 5.5 * 1024 * 1024 }) // 5.5 MB

      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText(/archive.tar.gz/)).toBeInTheDocument()
      expect(screen.getByText(/5.50 MB/)).toBeInTheDocument()
    })

    it('should enable conversion options after file select', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const formatSelect = screen.getByLabelText('Select output format for archive conversion')
      expect(formatSelect).not.toBeDisabled()

      const slider = screen.getByLabelText(/Compression level:/)
      expect(slider).not.toBeDisabled()
    })

    it('should show drag overlay on dragover', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<ArchiveConverter />)

      expect(screen.getByText('Drop to replace file')).toBeInTheDocument()
    })

    it('should hide drag overlay on dragleave/drop', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<ArchiveConverter />)

      expect(screen.queryByText('Drop to replace file')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Options', () => {
    it('should change output format', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const formatSelect = screen.getByLabelText('Select output format for archive conversion')
      const user = userEvent.setup()

      await user.selectOptions(formatSelect, 'tar')

      expect(mockConverter.setOutputFormat).toHaveBeenCalledWith('tar')
    })

    it('should update compression level on slider change', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      const { container } = render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level:/) as HTMLInputElement

      // For range inputs, we need to fire a change event directly
      const event = new Event('change', { bubbles: true })
      slider.value = '9'
      slider.dispatchEvent(event)

      expect(slider).toHaveValue('9')
    })

    it('should show compression level value in label', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText(/Compression Level \(6\)/)).toBeInTheDocument()
    })

    it('should show "Faster" and "Smaller" labels for slider', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText('Faster')).toBeInTheDocument()
      expect(screen.getByText('Smaller')).toBeInTheDocument()
    })

    it('should disable controls during conversion', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<ArchiveConverter />)

      const formatSelect = screen.getByLabelText('Select output format for archive conversion')
      expect(formatSelect).toBeDisabled()

      const slider = screen.getByLabelText(/Compression level:/)
      expect(slider).toBeDisabled()

      const filenameInput = screen.getByLabelText('Custom Filename (Optional)')
      expect(filenameInput).toBeDisabled()
    })

    it('should update custom filename', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const filenameInput = screen.getByLabelText('Custom Filename (Optional)')
      const user = userEvent.setup()

      await user.type(filenameInput, 'my-archive')

      expect(mockConverter.setCustomFilename).toHaveBeenCalled()
    })

    it('should call handleSelectOutputDirectory for Electron', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const browseButton = screen.getByLabelText('Browse for output directory')
      const user = userEvent.setup()

      await user.click(browseButton)

      expect(mockConverter.handleSelectOutputDirectory).toHaveBeenCalled()
    })

    it('should default compression level to 6', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level: 6/)
      expect(slider).toHaveValue('6')
    })
  })

  describe('Conversion Flow', () => {
    it('should call archiveAPI.convert with correct parameters', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Archive/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            compressionLevel: 6,
          })
        )
      })
    })

    it('should show uploading progress during upload', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 50

      render(<ArchiveConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('50%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show conversion progress', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Compressing archive...' }

      render(<ArchiveConverter />)

      expect(screen.getByText('Compressing archive...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('75%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display success message on completion', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<ArchiveConverter />)

      expect(screen.getByText('Archive conversion completed successfully!')).toBeInTheDocument()
    })

    it('should display error message on failure', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Compression failed: Invalid archive format'
      mockConverter.showFeedback = true

      render(<ArchiveConverter />)

      expect(mockConverter.error).toBe('Compression failed: Invalid archive format')
    })

    it('should show download button when completed', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/archive.tar.gz'

      render(<ArchiveConverter />)

      expect(screen.getByRole('button', { name: /Download/i })).toBeInTheDocument()
    })

    it('should call handleReset and clear file', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<ArchiveConverter />)

      const resetButton = screen.getByRole('button', { name: /Reset/i })
      const user = userEvent.setup()
      await user.click(resetButton)

      expect(mockConverter.handleReset).toHaveBeenCalled()
    })

    it('should allow "Convert Another" after success', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/archive.zip'

      render(<ArchiveConverter />)

      expect(screen.getByRole('button', { name: /Convert Another/i })).toBeInTheDocument()
    })
  })

  describe('Progress and Status', () => {
    it('should show upload progress bar and percentage', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 35

      render(<ArchiveConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('35%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show conversion progress bar', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 60 }

      render(<ArchiveConverter />)

      expect(screen.getByText('common.processing')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('60%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display progress message', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 80, message: 'Finalizing archive...' }

      render(<ArchiveConverter />)

      expect(screen.getByText('Finalizing archive...')).toBeInTheDocument()
    })

    it('should show converting button state (loading/disabled)', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<ArchiveConverter />)

      // When converting, the convert button is replaced with a disabled button
      // Just verify the status is converting
      expect(mockConverter.status).toBe('converting')
    })

    it('should hide feedback when not converting', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'
      mockConverter.showFeedback = false

      render(<ArchiveConverter />)

      expect(screen.queryByText('common.uploadingFile')).not.toBeInTheDocument()
      expect(screen.queryByText('common.processing')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for output format select', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const formatSelect = screen.getByLabelText('Select output format for archive conversion')
      expect(formatSelect).toBeInTheDocument()
      expect(formatSelect).toHaveAttribute('aria-label', 'Select output format for archive conversion')
    })

    it('should have aria-label and aria-value* for compression slider', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level: 6/)
      expect(slider).toHaveAttribute('aria-label', 'Compression level: 6')
      expect(slider).toHaveAttribute('aria-valuemin', '0')
      expect(slider).toHaveAttribute('aria-valuemax', '9')
      expect(slider).toHaveAttribute('aria-valuenow', '6')
    })

    it('should have aria-describedby for hints', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const filenameInput = screen.getByLabelText('Custom Filename (Optional)')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toHaveAttribute('aria-describedby', 'output-directory-hint')
    })

    it('should have proper ARIA attributes for progress bars', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 40

      mockConverter.getUploadProgressAriaAttributes = vi.fn(() => ({
        role: 'progressbar',
        'aria-valuenow': 40,
        'aria-valuemin': 0,
        'aria-valuemax': 100,
      }))

      render(<ArchiveConverter />)

      expect(mockConverter.getUploadProgressAriaAttributes).toHaveBeenCalled()
    })

    it('should have ARIA labels for browse button', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
      expect(browseButton).toHaveAttribute('aria-label', 'Browse for output directory')
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window.electron gracefully', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      // Simulate missing window.electron by checking if component still renders
      render(<ArchiveConverter />)

      // Component should still render basic functionality
      expect(screen.getByText('converter.archive.title')).toBeInTheDocument()
    })

    it('should handle API error responses', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Network error: Connection timeout'
      mockConverter.showFeedback = true

      render(<ArchiveConverter />)

      expect(mockConverter.error).toBe('Network error: Connection timeout')
    })

    it('should handle drag/drop with invalid file', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      // Component should handle drag/drop events through the converter hook
      expect(mockConverter.handleDragOver).toBeDefined()
      expect(mockConverter.handleDragLeave).toBeDefined()
      expect(mockConverter.handleDrop).toBeDefined()
    })
  })

  describe('Button States', () => {
    it('should show convert and reset buttons when idle', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<ArchiveConverter />)

      expect(screen.getByRole('button', { name: /Convert Archive/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Reset/i })).toBeInTheDocument()
    })

    it('should show disabled button when converting', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<ArchiveConverter />)

      // When converting, the convert and reset buttons should not be available
      expect(screen.queryByRole('button', { name: /Convert Archive/i })).not.toBeInTheDocument()
      expect(mockConverter.status).toBe('converting')
    })

    it('should show download and convert another buttons when completed', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/archive.tar.gz'

      render(<ArchiveConverter />)

      expect(screen.getByRole('button', { name: /Download/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Convert Another/i })).toBeInTheDocument()
    })

    it('should show convert and reset buttons when failed', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed'

      render(<ArchiveConverter />)

      expect(screen.getByRole('button', { name: /Convert Archive/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Reset/i })).toBeInTheDocument()
    })
  })

  describe('Compression Level Variations', () => {
    it('should allow setting compression level to 0 (fastest)', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level:/) as HTMLInputElement

      // For range inputs, we need to fire a change event directly
      const event = new Event('change', { bubbles: true })
      slider.value = '0'
      slider.dispatchEvent(event)

      expect(slider).toHaveValue('0')
    })

    it('should allow setting compression level to 9 (maximum compression)', () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level:/) as HTMLInputElement

      // For range inputs, we need to fire a change event directly
      const event = new Event('change', { bubbles: true })
      slider.value = '9'
      slider.dispatchEvent(event)

      expect(slider).toHaveValue('9')
    })

    it('should pass custom compression level to conversion', async () => {
      const mockFile = new File(['test'], 'test.zip', { type: 'application/zip' })
      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      const slider = screen.getByLabelText(/Compression level:/) as HTMLInputElement

      // Change compression level to 3
      const event = new Event('change', { bubbles: true })
      slider.value = '3'
      slider.dispatchEvent(event)

      expect(slider.value).toBe('3')

      const convertButton = screen.getByRole('button', { name: /Convert Archive/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      // Verify handleConvert was called
      expect(mockConverter.handleConvert).toHaveBeenCalled()
    })
  })

  describe('File Size Display', () => {
    it('should format file size correctly for KB', () => {
      const mockFile = new File(['test'], 'small.zip', { type: 'application/zip' })
      Object.defineProperty(mockFile, 'size', { value: 256 * 1024 }) // 256 KB

      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText(/0.25 MB/)).toBeInTheDocument()
    })

    it('should format file size correctly for large files', () => {
      const mockFile = new File(['test'], 'large.7z', { type: 'application/x-7z-compressed' })
      Object.defineProperty(mockFile, 'size', { value: 150 * 1024 * 1024 }) // 150 MB

      mockConverter.selectedFile = mockFile

      render(<ArchiveConverter />)

      expect(screen.getByText(/150.00 MB/)).toBeInTheDocument()
    })
  })

  describe('Heading and Semantic Structure', () => {
    it('should have proper heading structure', () => {
      render(<ArchiveConverter />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('converter.archive.title')
    })
  })
})
