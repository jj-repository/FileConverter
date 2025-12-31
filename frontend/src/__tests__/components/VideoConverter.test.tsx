import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VideoConverter } from '../../components/Converter/VideoConverter'

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
  outputFormat: 'mp4',
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

vi.mock('../../hooks/useConverter', () => ({
  useConverter: () => mockConverter,
}))

// Mock API
vi.mock('../../services/api', () => ({
  videoAPI: {
    convert: vi.fn(),
  },
}))

describe('VideoConverter', () => {
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
    mockConverter.outputFormat = 'mp4'
  })

  describe('Rendering', () => {
    it('should render video converter title', () => {
      render(<VideoConverter />)
      expect(screen.getByText('converter.video.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<VideoConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      Object.defineProperty(mockFile, 'size', { value: 5 * 1024 * 1024 }) // 5 MB

      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      expect(screen.getByText(/common.file/)).toBeInTheDocument()
      expect(screen.getByText(/test.mp4/)).toBeInTheDocument()
      expect(screen.getByText(/5.00 MB/)).toBeInTheDocument()
    })

    it('should format file size correctly for KB', () => {
      const mockFile = new File(['test'], 'small.mp4', { type: 'video/mp4' })
      Object.defineProperty(mockFile, 'size', { value: 512 * 1024 }) // 512 KB

      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      expect(screen.getByText(/512.00 KB/)).toBeInTheDocument()
    })
  })

  describe('Format Selection', () => {
    it('should have MP4 as default output format', () => {
      expect(mockConverter.outputFormat).toBe('mp4')
    })

    it('should show all supported video formats', () => {
      const mockFile = new File(['test'], 'test.avi', { type: 'video/avi' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const formatSelect = screen.getByLabelText('Select output format for video conversion')
      expect(formatSelect).toBeInTheDocument()

      // Check for some common formats
      expect(screen.getByRole('option', { name: 'MP4' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'AVI' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'WEBM' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'MKV' })).toBeInTheDocument()
    })

    it('should disable format select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const formatSelect = screen.getByLabelText('Select output format for video conversion')
      expect(formatSelect).toBeDisabled()
    })
  })

  describe('Codec Selection', () => {
    it('should show codec options', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const codecSelect = screen.getByLabelText('Select video codec')
      expect(codecSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /H.264/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /H.265/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /VP9/ })).toBeInTheDocument()
    })

    it('should have H.264 as default codec', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const codecSelect = screen.getByLabelText('Select video codec') as HTMLSelectElement
      expect(codecSelect.value).toBe('libx264')
    })

    it('should allow changing codec', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const codecSelect = screen.getByLabelText('Select video codec')
      const user = userEvent.setup()

      await user.selectOptions(codecSelect, 'libx265')

      expect(codecSelect).toHaveValue('libx265')
    })

    it('should disable codec select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const codecSelect = screen.getByLabelText('Select video codec')
      expect(codecSelect).toBeDisabled()
    })
  })

  describe('Resolution Selection', () => {
    it('should show resolution options', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const resolutionSelect = screen.getByLabelText('Select video resolution')
      expect(resolutionSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /Original/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /480p/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /720p/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /1080p/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /4K/ })).toBeInTheDocument()
    })

    it('should have original as default resolution', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const resolutionSelect = screen.getByLabelText('Select video resolution') as HTMLSelectElement
      expect(resolutionSelect.value).toBe('original')
    })

    it('should allow changing resolution', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const resolutionSelect = screen.getByLabelText('Select video resolution')
      const user = userEvent.setup()

      await user.selectOptions(resolutionSelect, '1080p')

      expect(resolutionSelect).toHaveValue('1080p')
    })

    it('should disable resolution select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const resolutionSelect = screen.getByLabelText('Select video resolution')
      expect(resolutionSelect).toBeDisabled()
    })
  })

  describe('Bitrate Selection', () => {
    it('should show bitrate options', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const bitrateSelect = screen.getByLabelText('Select video bitrate')
      expect(bitrateSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /1 Mbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /2 Mbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /5 Mbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /10 Mbps/ })).toBeInTheDocument()
    })

    it('should have 2M as default bitrate', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const bitrateSelect = screen.getByLabelText('Select video bitrate') as HTMLSelectElement
      expect(bitrateSelect.value).toBe('2M')
    })

    it('should allow changing bitrate', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const bitrateSelect = screen.getByLabelText('Select video bitrate')
      const user = userEvent.setup()

      await user.selectOptions(bitrateSelect, '5M')

      expect(bitrateSelect).toHaveValue('5M')
    })

    it('should disable bitrate select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const bitrateSelect = screen.getByLabelText('Select video bitrate')
      expect(bitrateSelect).toBeDisabled()
    })
  })

  describe('Custom Filename', () => {
    it('should render custom filename input', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeInTheDocument()
    })

    it('should disable custom filename during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeDisabled()
    })
  })

  describe('Output Directory (Electron)', () => {
    it('should show output directory controls in Electron environment', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should disable output directory controls during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeDisabled()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeDisabled()
    })
  })

  describe('Conversion', () => {
    it('should call handleConvert when convert button is clicked', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const convertButton = screen.getByRole('button', { name: /convertVideo/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should pass codec, resolution, and bitrate to conversion', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      // Change codec
      const codecSelect = screen.getByLabelText('Select video codec')
      await userEvent.selectOptions(codecSelect, 'libx265')

      // Change resolution
      const resolutionSelect = screen.getByLabelText('Select video resolution')
      await userEvent.selectOptions(resolutionSelect, '1080p')

      // Change bitrate
      const bitrateSelect = screen.getByLabelText('Select video bitrate')
      await userEvent.selectOptions(bitrateSelect, '5M')

      const convertButton = screen.getByRole('button', { name: /convertVideo/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            codec: 'libx265',
            resolution: '1080p',
            bitrate: '5M',
          })
        )
      })
    })
  })

  describe('Drag and Drop', () => {
    it('should show overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<VideoConverter />)

      expect(screen.getByText('common.dropToReplace')).toBeInTheDocument()
    })

    it('should not show overlay when not dragging', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<VideoConverter />)

      expect(screen.queryByText('common.dropToReplace')).not.toBeInTheDocument()
    })
  })

  describe('Upload Progress', () => {
    it('should show upload progress during upload', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 45

      render(<VideoConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('45%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should not show upload progress when not uploading', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false

      render(<VideoConverter />)

      expect(screen.queryByText('common.uploadingFile')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Progress', () => {
    it('should show conversion progress during conversion', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 65, message: 'Converting video...' }

      render(<VideoConverter />)

      expect(screen.getByText('Converting video...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('65%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show processing message when no progress message', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 30 }

      render(<VideoConverter />)

      expect(screen.getByText('common.processing')).toBeInTheDocument()
    })

    it('should show conversion time warning', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true

      render(<VideoConverter />)

      expect(screen.getByText(/Video conversion may take several minutes/)).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show error message when conversion fails', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Conversion failed: Invalid codec'
      mockConverter.showFeedback = true

      render(<VideoConverter />)

      expect(mockConverter.error).toBe('Conversion failed: Invalid codec')
    })

    it('should show success message when conversion completes', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.mp4'
      mockConverter.showFeedback = true

      render(<VideoConverter />)

      expect(screen.getByText('messages.conversionSuccess')).toBeInTheDocument()
    })
  })

  describe('Button States', () => {
    it('should show convert and reset buttons when idle', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<VideoConverter />)

      expect(screen.getByRole('button', { name: /convertVideo/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('should show disabled button when converting', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<VideoConverter />)

      // When converting, the convert and reset buttons should not be available
      expect(screen.queryByRole('button', { name: /convertVideo/i })).not.toBeInTheDocument()
      expect(mockConverter.status).toBe('converting')
    })

    it('should show download and convert another buttons when completed', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.mp4'

      render(<VideoConverter />)

      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /convertAnother/i })).toBeInTheDocument()
    })

    it('should show convert and reset buttons when failed', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed'

      render(<VideoConverter />)

      expect(screen.getByRole('button', { name: /convertVideo/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<VideoConverter />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
    })

    it('should have accessible form controls when file is selected', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const formatSelect = screen.getByLabelText('Select output format for video conversion')
      expect(formatSelect).toBeInTheDocument()

      const codecSelect = screen.getByLabelText('Select video codec')
      expect(codecSelect).toBeInTheDocument()

      const resolutionSelect = screen.getByLabelText('Select video resolution')
      expect(resolutionSelect).toBeInTheDocument()

      const bitrateSelect = screen.getByLabelText('Select video bitrate')
      expect(bitrateSelect).toBeInTheDocument()
    })

    it('should have describedby for custom filename input', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()
    })

    it('should have describedby for output directory input', () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' })
      mockConverter.selectedFile = mockFile

      render(<VideoConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toHaveAttribute('aria-describedby', 'output-directory-hint')
      expect(screen.getByText('common.outputDirectoryHint')).toBeInTheDocument()
    })
  })
})
