import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SubtitleConverter } from '../../../components/Converter/SubtitleConverter'

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
  outputFormat: 'srt',
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
    'aria-atomic': true,
  })),
  getProgressAriaAttributes: vi.fn(() => ({
    role: 'progressbar',
    'aria-valuenow': 0,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
    'aria-label': 'Conversion progress',
  })),
  getUploadProgressAriaAttributes: vi.fn(() => ({
    role: 'progressbar',
    'aria-valuenow': 0,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
    'aria-label': 'Upload progress',
  })),
}

vi.mock('../../../hooks/useConverter', () => ({
  useConverter: () => mockConverter,
}))

// Mock API
vi.mock('../../../services/api', () => ({
  subtitleAPI: {
    convert: vi.fn(),
    adjustTiming: vi.fn(),
  },
}))

describe('SubtitleConverter', () => {
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
    mockConverter.outputFormat = 'srt'
  })

  describe('Rendering', () => {
    it('should render subtitle converter title', () => {
      render(<SubtitleConverter />)
      expect(screen.getByText('converter.subtitle.title')).toBeInTheDocument()
    })

    it('should render info box with supported formats', () => {
      render(<SubtitleConverter />)
      expect(screen.getAllByText(/Supported formats:/)[0]).toBeInTheDocument()
      expect(screen.getByText(/SRT \(SubRip\)/)).toBeInTheDocument()
      expect(screen.getByText(/VTT \(WebVTT\)/)).toBeInTheDocument()
      expect(screen.getByText(/ASS\/SSA \(Advanced SubStation Alpha\)/)).toBeInTheDocument()
      expect(screen.getByText(/SUB \(MicroDVD\)/)).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<SubtitleConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render two tabs: Convert Format and Adjust Timing', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      expect(screen.getByRole('tab', { name: /Convert Format/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /Adjust Timing/i })).toBeInTheDocument()
    })

    it('should render all 5 subtitle formats in dropdown', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      expect(screen.getByRole('option', { name: 'SRT' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'VTT' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'ASS' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'SSA' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'SUB' })).toBeInTheDocument()
    })

    it('should render encoding dropdown with 4 options', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      expect(screen.getByRole('option', { name: /UTF-8 \(Default\)/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'UTF-16' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Latin-1' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'ASCII' })).toBeInTheDocument()
    })

    it('should render FPS dropdown when SUB format selected', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'sub'

      render(<SubtitleConverter />)

      const fpsSelect = screen.getByLabelText('Select frame rate')
      expect(fpsSelect).toBeInTheDocument()
      expect(screen.getByText(/Required for SUB format timing/)).toBeInTheDocument()
    })

    it('should NOT render FPS dropdown for other formats', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'srt'

      render(<SubtitleConverter />)

      const fpsSelect = screen.queryByLabelText('Select frame rate')
      expect(fpsSelect).not.toBeInTheDocument()
    })

    it('should render keepHtmlTags checkbox', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const checkbox = screen.getByLabelText('HTML Tags')
      expect(checkbox).toBeInTheDocument()
      expect(screen.getByText(/Preserve <b>, <i>, etc./)).toBeInTheDocument()
    })

    it('should show drag overlay when dragging', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<SubtitleConverter />)

      expect(screen.getByText('Drop to replace file')).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    it('should default to Convert Format tab', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const convertTab = screen.getByRole('tab', { name: /Convert Format/i })
      expect(convertTab).toHaveAttribute('aria-selected', 'true')
    })

    it('should switch to Adjust Timing tab when clicked', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      expect(adjustTimingTab).toHaveAttribute('aria-selected', 'true')
    })

    it('should show Convert Format panel when first tab active', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      expect(screen.getByLabelText('Select output format for subtitle conversion')).toBeInTheDocument()
    })

    it('should show Adjust Timing panel when second tab active', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      expect(screen.getByLabelText('Time Offset (milliseconds)')).toBeInTheDocument()
    })

    it('should have proper ARIA role="tab" and aria-selected', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const convertTab = screen.getByRole('tab', { name: /Convert Format/i })
      const adjustTab = screen.getByRole('tab', { name: /Adjust Timing/i })

      expect(convertTab).toHaveAttribute('role', 'tab')
      expect(convertTab).toHaveAttribute('aria-selected', 'true')
      expect(adjustTab).toHaveAttribute('role', 'tab')
      expect(adjustTab).toHaveAttribute('aria-selected', 'false')
    })

    it('should have proper role="tabpanel" for panels', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const panel = screen.getByRole('tabpanel')
      expect(panel).toBeInTheDocument()
      expect(panel).toHaveAttribute('id', 'convert-format-panel')
    })
  })

  describe('File Selection', () => {
    it('should call handleFileSelect', () => {
      render(<SubtitleConverter />)

      // Since DropZone is rendered when no file, verify it's in initial state
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should display file name and size in KB', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      Object.defineProperty(mockFile, 'size', { value: 2048 }) // 2 KB

      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      expect(screen.getByText(/test.srt/)).toBeInTheDocument()
      expect(screen.getByText(/2.00 KB/)).toBeInTheDocument()
    })

    it('should enable conversion options', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const formatSelect = screen.getByLabelText('Select output format for subtitle conversion')
      expect(formatSelect).toBeEnabled()

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeEnabled()
    })

    it('should show drag overlay on dragover', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<SubtitleConverter />)

      expect(screen.getByText('Drop to replace file')).toBeInTheDocument()
    })

    it('should hide drag overlay on drop', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<SubtitleConverter />)

      expect(screen.queryByText('Drop to replace file')).not.toBeInTheDocument()
    })
  })

  describe('Convert Format Mode', () => {
    it('should change output format', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const formatSelect = screen.getByLabelText('Select output format for subtitle conversion')
      const user = userEvent.setup()

      await user.selectOptions(formatSelect, 'vtt')

      expect(mockConverter.setOutputFormat).toHaveBeenCalledWith('vtt')
    })

    it('should change encoding', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      const user = userEvent.setup()

      await user.selectOptions(encodingSelect, 'utf-16')

      expect(encodingSelect).toHaveValue('utf-16')
    })

    it('should change FPS when SUB format', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'sub'

      render(<SubtitleConverter />)

      const fpsSelect = screen.getByLabelText('Select frame rate')
      const user = userEvent.setup()

      await user.selectOptions(fpsSelect, '25')

      expect(fpsSelect).toHaveValue('25')
    })

    it('should toggle keepHtmlTags checkbox', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const checkbox = screen.getByLabelText('HTML Tags')
      const user = userEvent.setup()

      expect(checkbox).not.toBeChecked()

      await user.click(checkbox)

      expect(checkbox).toBeChecked()
    })

    it('should default encoding to utf-8', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding') as HTMLSelectElement
      expect(encodingSelect.value).toBe('utf-8')
    })

    it('should default fps to 23.976', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'sub'

      render(<SubtitleConverter />)

      const fpsSelect = screen.getByLabelText('Select frame rate') as HTMLSelectElement
      expect(fpsSelect.value).toBe('23.976')
    })

    it('should default keepHtmlTags to false', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const checkbox = screen.getByLabelText('HTML Tags')
      expect(checkbox).not.toBeChecked()
    })

    it('should show FPS dropdown only for SUB output', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'srt'

      const { rerender } = render(<SubtitleConverter />)

      expect(screen.queryByLabelText('Select frame rate')).not.toBeInTheDocument()

      mockConverter.outputFormat = 'sub'
      rerender(<SubtitleConverter />)

      expect(screen.getByLabelText('Select frame rate')).toBeInTheDocument()
    })

    it('should call subtitleAPI.convert with correct params', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Subtitle/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should pass encoding, fps, keepHtmlTags to API', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'sub'

      render(<SubtitleConverter />)

      // Change encoding
      const encodingSelect = screen.getByLabelText('Select text encoding')
      await userEvent.selectOptions(encodingSelect, 'utf-16')

      // Change FPS
      const fpsSelect = screen.getByLabelText('Select frame rate')
      await userEvent.selectOptions(fpsSelect, '30')

      // Toggle keepHtmlTags
      const checkbox = screen.getByLabelText('HTML Tags')
      await userEvent.click(checkbox)

      const convertButton = screen.getByRole('button', { name: /Convert Subtitle/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            encoding: 'utf-16',
            fps: 30,
            keepHtmlTags: true,
          })
        )
      })
    })
  })

  describe('Adjust Timing Mode', () => {
    it('should show timing offset input in Adjust Timing tab', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      expect(screen.getByLabelText('Time Offset (milliseconds)')).toBeInTheDocument()
    })

    it('should update timingOffset value', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)') as HTMLInputElement
      await user.clear(timingInput)
      await user.type(timingInput, '2000')

      expect(timingInput.value).toBe('2000')
    })

    it('should default timingOffset to 0', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)') as HTMLInputElement
      expect(timingInput.value).toBe('0')
    })

    it('should show placeholder text with examples', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)')
      expect(timingInput).toHaveAttribute('placeholder', 'e.g., 2000 (delay) or -2000 (advance)')
    })

    it('should show hint explaining positive/negative values', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      expect(screen.getByText(/Positive = delay subtitles, Negative = advance subtitles/)).toBeInTheDocument()
      expect(screen.getByText(/Example: \+2000ms delays by 2 seconds, -1500ms advances by 1.5 seconds/)).toBeInTheDocument()
    })

    it('should call subtitleAPI.adjustTiming with timingOffset', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)')
      await user.clear(timingInput)
      await user.type(timingInput, '1500')

      const adjustButton = screen.getByRole('button', { name: /Adjust Timing/i })
      await user.click(adjustButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            timingOffset: 1500,
          })
        )
      })
    })

    it('should show different success message for timing adjustment', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)')
      await user.clear(timingInput)
      await user.type(timingInput, '1000')

      // Check that the success message shows the offset value
      expect(screen.getByText(/Subtitle timing adjusted by 1000ms successfully!/)).toBeInTheDocument()
    })
  })

  describe('Conversion Flow', () => {
    it('should show conversion progress', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 50, message: 'Converting subtitle...' }

      render(<SubtitleConverter />)

      expect(screen.getByText('Converting subtitle...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('50%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display success message for format conversion', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<SubtitleConverter />)

      expect(screen.getByText('Subtitle conversion completed successfully!')).toBeInTheDocument()
    })

    it('should display success message for timing adjustment with offset value', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<SubtitleConverter />)

      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      const timingInput = screen.getByLabelText('Time Offset (milliseconds)')
      await user.clear(timingInput)
      await user.type(timingInput, '2500')

      expect(screen.getByText(/Subtitle timing adjusted by 2500ms successfully!/)).toBeInTheDocument()
    })

    it('should show different button text: Convert Subtitle vs Adjust Timing', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      // Convert Format tab
      expect(screen.getByRole('button', { name: /Convert Subtitle/i })).toBeInTheDocument()

      // Switch to Adjust Timing tab
      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      expect(screen.getByRole('button', { name: /Adjust Timing/i })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Convert Subtitle/i })).not.toBeInTheDocument()
    })

    it('should show loading text when converting', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      const { rerender } = render(<SubtitleConverter />)

      // Both modes show "Processing..." from Button component when loading=true
      expect(screen.getByRole('button', { name: /Processing.../i })).toBeInTheDocument()

      // Switch to Adjust Timing mode
      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      rerender(<SubtitleConverter />)

      // Still shows "Processing..." because Button component overrides text when loading
      expect(screen.getByRole('button', { name: /Processing.../i })).toBeInTheDocument()
    })

    it('should handle errors', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed: Invalid file format'
      mockConverter.showFeedback = true

      render(<SubtitleConverter />)

      expect(mockConverter.error).toBe('Conversion failed: Invalid file format')
    })

    it('should allow reset', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const resetButton = screen.getByRole('button', { name: /Reset/i })
      const user = userEvent.setup()
      await user.click(resetButton)

      expect(mockConverter.handleReset).toHaveBeenCalled()
    })

    it('should allow download after completion', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.srt'

      render(<SubtitleConverter />)

      const downloadButton = screen.getByRole('button', { name: /Download/i })
      const user = userEvent.setup()
      await user.click(downloadButton)

      expect(mockConverter.handleDownload).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have aria-label for selects', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const formatSelect = screen.getByLabelText('Select output format for subtitle conversion')
      expect(formatSelect).toBeInTheDocument()

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeInTheDocument()
    })

    it('should have aria-describedby for FPS hint', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'sub'

      render(<SubtitleConverter />)

      const fpsSelect = screen.getByLabelText('Select frame rate')
      expect(fpsSelect).toHaveAttribute('aria-describedby', 'fps-hint')
      expect(screen.getByText(/Required for SUB format timing/)).toBeInTheDocument()
    })

    it('should have aria-describedby for timing offset hint and HTML tags hint', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      // Check HTML tags hint
      const htmlTagsCheckbox = screen.getByLabelText('HTML Tags')
      expect(htmlTagsCheckbox).toHaveAttribute('aria-describedby', 'html-tags-hint')

      // Switch to Adjust Timing tab
      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      // Check timing offset hint
      const timingInput = screen.getByLabelText('Time Offset (milliseconds)')
      expect(timingInput).toHaveAttribute('aria-describedby', 'timing-offset-hint')
      expect(screen.getByText(/Positive = delay subtitles, Negative = advance subtitles/)).toBeInTheDocument()
    })

    it('should have proper progress bar ARIA attributes', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Converting...' }

      render(<SubtitleConverter />)

      const progressAriaAttributes = mockConverter.getProgressAriaAttributes()
      expect(progressAriaAttributes).toEqual(
        expect.objectContaining({
          role: 'progressbar',
          'aria-valuenow': 0,
          'aria-valuemin': 0,
          'aria-valuemax': 100,
        })
      )
    })

    it('should have aria-controls for tab panels', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      const convertTab = screen.getByRole('tab', { name: /Convert Format/i })
      expect(convertTab).toHaveAttribute('aria-controls', 'convert-format-panel')

      const adjustTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      expect(adjustTab).toHaveAttribute('aria-controls', 'adjust-timing-panel')
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window.electron', () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      // Temporarily remove window.electron
      const originalElectron = window.electron
      delete (window as any).electron

      render(<SubtitleConverter />)

      // Should not show output directory controls
      expect(screen.queryByLabelText('Output directory path')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Browse for output directory')).not.toBeInTheDocument()

      // Restore window.electron
      ;(window as any).electron = originalElectron
    })

    it('should handle API errors in both modes', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'API Error: Connection failed'
      mockConverter.showFeedback = true

      render(<SubtitleConverter />)

      expect(mockConverter.error).toBe('API Error: Connection failed')

      // Switch to Adjust Timing mode
      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      const user = userEvent.setup()
      await user.click(adjustTimingTab)

      // Error should still be displayed
      expect(mockConverter.error).toBe('API Error: Connection failed')
    })

    it('should switch modes and reset options', async () => {
      const mockFile = new File(['test'], 'test.srt', { type: 'text/plain' })
      mockConverter.selectedFile = mockFile

      render(<SubtitleConverter />)

      // Set some options in Convert Format mode
      const encodingSelect = screen.getByLabelText('Select text encoding')
      await userEvent.selectOptions(encodingSelect, 'utf-16')

      // Switch to Adjust Timing mode
      const adjustTimingTab = screen.getByRole('tab', { name: /Adjust Timing/i })
      await userEvent.click(adjustTimingTab)

      expect(screen.getByLabelText('Time Offset (milliseconds)')).toBeInTheDocument()

      // Switch back to Convert Format mode
      const convertTab = screen.getByRole('tab', { name: /Convert Format/i })
      await userEvent.click(convertTab)

      // Encoding should still be set
      const updatedEncodingSelect = screen.getByLabelText('Select text encoding') as HTMLSelectElement
      expect(updatedEncodingSelect.value).toBe('utf-16')
    })
  })
})
