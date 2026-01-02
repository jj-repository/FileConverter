import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioConverter } from '../../components/Converter/AudioConverter'

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
  outputFormat: 'mp3',
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
  audioAPI: {
    convert: vi.fn(),
  },
}))

describe('AudioConverter', () => {
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
    mockConverter.outputFormat = 'mp3'
  })

  describe('Rendering', () => {
    it('should render audio converter title', () => {
      render(<AudioConverter />)
      expect(screen.getByText('converter.audio.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<AudioConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      Object.defineProperty(mockFile, 'size', { value: 3 * 1024 * 1024 }) // 3 MB

      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      expect(screen.getByText(/common.file/)).toBeInTheDocument()
      expect(screen.getByText(/test.mp3/)).toBeInTheDocument()
      expect(screen.getByText(/3.00 MB/)).toBeInTheDocument()
    })

    it('should format file size correctly for KB', () => {
      const mockFile = new File(['test'], 'small.wav', { type: 'audio/wav' })
      Object.defineProperty(mockFile, 'size', { value: 256 * 1024 }) // 256 KB

      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      expect(screen.getByText(/256.00 KB/)).toBeInTheDocument()
    })
  })

  describe('Format Selection', () => {
    it('should have MP3 as default output format', () => {
      expect(mockConverter.outputFormat).toBe('mp3')
    })

    it('should show all supported audio formats', () => {
      const mockFile = new File(['test'], 'test.wav', { type: 'audio/wav' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const formatSelect = screen.getByLabelText('Select output format for audio conversion')
      expect(formatSelect).toBeInTheDocument()

      // Check for some common formats
      expect(screen.getByRole('option', { name: 'MP3' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'WAV' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'FLAC' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'AAC' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'OGG' })).toBeInTheDocument()
    })

    it('should disable format select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const formatSelect = screen.getByLabelText('Select output format for audio conversion')
      expect(formatSelect).toBeDisabled()
    })
  })

  describe('Bitrate Selection', () => {
    it('should show bitrate options', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      expect(bitrateSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /64 kbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /128 kbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /192 kbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /256 kbps/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /320 kbps/ })).toBeInTheDocument()
    })

    it('should have 192k as default bitrate', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate') as HTMLSelectElement
      expect(bitrateSelect.value).toBe('192k')
    })

    it('should allow changing bitrate', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      const user = userEvent.setup()

      await user.selectOptions(bitrateSelect, '320k')

      expect(bitrateSelect).toHaveValue('320k')
    })

    it('should disable bitrate select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      expect(bitrateSelect).toBeDisabled()
    })

    it('should disable bitrate for lossless formats (FLAC)', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'flac'

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      expect(bitrateSelect).toBeDisabled()
    })

    it('should disable bitrate for lossless formats (WAV)', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'wav'

      render(<AudioConverter />)

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      expect(bitrateSelect).toBeDisabled()
    })
  })

  describe('Sample Rate Selection', () => {
    it('should show sample rate options', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const sampleRateSelect = screen.getByLabelText('Select audio sample rate')
      expect(sampleRateSelect).toBeInTheDocument()

      // Check for specific sample rate options (Original appears in multiple selects)
      expect(screen.getByRole('option', { name: /22.05 kHz/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /44.1 kHz/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /48 kHz/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /96 kHz/ })).toBeInTheDocument()
    })

    it('should have Original as default sample rate', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const sampleRateSelect = screen.getByLabelText('Select audio sample rate') as HTMLSelectElement
      expect(sampleRateSelect.value).toBe('')
    })

    it('should allow changing sample rate', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const sampleRateSelect = screen.getByLabelText('Select audio sample rate')
      const user = userEvent.setup()

      await user.selectOptions(sampleRateSelect, '44100')

      expect(sampleRateSelect).toHaveValue('44100')
    })

    it('should disable sample rate select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const sampleRateSelect = screen.getByLabelText('Select audio sample rate')
      expect(sampleRateSelect).toBeDisabled()
    })
  })

  describe('Channels Selection', () => {
    it('should show channel options', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const channelsSelect = screen.getByLabelText('Select audio channels')
      expect(channelsSelect).toBeInTheDocument()

      const options = screen.getAllByRole('option')
      const channelOptions = options.filter(opt =>
        ['Original', 'Mono', 'Stereo'].includes(opt.textContent || '')
      )
      expect(channelOptions.length).toBeGreaterThanOrEqual(3)
    })

    it('should have Original as default channels', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const channelsSelect = screen.getByLabelText('Select audio channels') as HTMLSelectElement
      expect(channelsSelect.value).toBe('')
    })

    it('should allow changing channels', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const channelsSelect = screen.getByLabelText('Select audio channels')
      const user = userEvent.setup()

      await user.selectOptions(channelsSelect, '2')

      expect(channelsSelect).toHaveValue('2')
    })

    it('should disable channels select during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const channelsSelect = screen.getByLabelText('Select audio channels')
      expect(channelsSelect).toBeDisabled()
    })
  })

  describe('Custom Filename', () => {
    it('should render custom filename input', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeInTheDocument()
    })

    it('should disable custom filename during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeDisabled()
    })
  })

  describe('Output Directory (Electron)', () => {
    it('should show output directory controls in Electron environment', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should disable output directory controls during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeDisabled()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeDisabled()
    })
  })

  describe('Conversion', () => {
    it('should call handleConvert when convert button is clicked', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const convertButton = screen.getByRole('button', { name: /convertAudio/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should pass bitrate, sample rate, and channels to conversion', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      // Change bitrate
      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      await userEvent.selectOptions(bitrateSelect, '320k')

      // Change sample rate
      const sampleRateSelect = screen.getByLabelText('Select audio sample rate')
      await userEvent.selectOptions(sampleRateSelect, '44100')

      // Change channels
      const channelsSelect = screen.getByLabelText('Select audio channels')
      await userEvent.selectOptions(channelsSelect, '2')

      const convertButton = screen.getByRole('button', { name: /convertAudio/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            bitrate: '320k',
            sampleRate: 44100,
            channels: 2,
          })
        )
      })
    })

    it('should not include sample rate when set to original', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const convertButton = screen.getByRole('button', { name: /convertAudio/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        const callArgs = mockConverter.handleConvert.mock.calls[0][1]
        expect(callArgs.sampleRate).toBeUndefined()
      })
    })

    it('should not include channels when set to original', async () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const convertButton = screen.getByRole('button', { name: /convertAudio/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        const callArgs = mockConverter.handleConvert.mock.calls[0][1]
        expect(callArgs.channels).toBeUndefined()
      })
    })
  })

  describe('Drag and Drop', () => {
    it('should show overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<AudioConverter />)

      expect(screen.getByText('common.dropToReplace')).toBeInTheDocument()
    })

    it('should not show overlay when not dragging', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<AudioConverter />)

      expect(screen.queryByText('common.dropToReplace')).not.toBeInTheDocument()
    })
  })

  describe('Upload Progress', () => {
    it('should show upload progress during upload', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 50

      render(<AudioConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('50%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should not show upload progress when not uploading', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false

      render(<AudioConverter />)

      expect(screen.queryByText('common.uploadingFile')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Progress', () => {
    it('should show conversion progress during conversion', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Converting audio...' }

      render(<AudioConverter />)

      expect(screen.getByText('Converting audio...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('75%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show processing message when no progress message', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 40 }

      render(<AudioConverter />)

      expect(screen.getByText('common.processing')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show error message when conversion fails', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Conversion failed: Unsupported format'
      mockConverter.showFeedback = true

      render(<AudioConverter />)

      expect(mockConverter.error).toBe('Conversion failed: Unsupported format')
    })

    it('should show success message when conversion completes', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.mp3'
      mockConverter.showFeedback = true

      render(<AudioConverter />)

      expect(screen.getByText('messages.conversionSuccess')).toBeInTheDocument()
    })
  })

  describe('Button States', () => {
    it('should show convert and reset buttons when idle', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<AudioConverter />)

      expect(screen.getByRole('button', { name: /convertAudio/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('should show disabled button when converting', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<AudioConverter />)

      // When converting, the convert and reset buttons should not be available
      expect(screen.queryByRole('button', { name: /convertAudio/i })).not.toBeInTheDocument()
      expect(mockConverter.status).toBe('converting')
    })

    it('should show download and convert another buttons when completed', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.mp3'

      render(<AudioConverter />)

      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /convertAnother/i })).toBeInTheDocument()
    })

    it('should show convert and reset buttons when failed', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed'

      render(<AudioConverter />)

      expect(screen.getByRole('button', { name: /convertAudio/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<AudioConverter />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
    })

    it('should have accessible form controls when file is selected', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const formatSelect = screen.getByLabelText('Select output format for audio conversion')
      expect(formatSelect).toBeInTheDocument()

      const bitrateSelect = screen.getByLabelText('Select audio bitrate')
      expect(bitrateSelect).toBeInTheDocument()

      const sampleRateSelect = screen.getByLabelText('Select audio sample rate')
      expect(sampleRateSelect).toBeInTheDocument()

      const channelsSelect = screen.getByLabelText('Select audio channels')
      expect(channelsSelect).toBeInTheDocument()
    })

    it('should have describedby for custom filename input', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()
    })

    it('should have describedby for output directory input', () => {
      const mockFile = new File(['test'], 'test.mp3', { type: 'audio/mp3' })
      mockConverter.selectedFile = mockFile

      render(<AudioConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toHaveAttribute('aria-describedby', 'output-directory-hint')
      expect(screen.getByText('common.outputDirectoryHint')).toBeInTheDocument()
    })
  })
})
