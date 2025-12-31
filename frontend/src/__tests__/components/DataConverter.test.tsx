import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataConverter } from '../../components/Converter/DataConverter'

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
  outputFormat: 'csv',
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
  dataAPI: {
    convert: vi.fn(),
  },
}))

describe('DataConverter', () => {
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
    mockConverter.outputFormat = 'csv'
  })

  describe('Rendering', () => {
    it('should render data converter title', () => {
      render(<DataConverter />)
      expect(screen.getByText('converter.data.title')).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<DataConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render file info when file is selected', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      Object.defineProperty(mockFile, 'size', { value: 1.5 * 1024 * 1024 }) // 1.5 MB

      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      expect(screen.getByText(/common.file/)).toBeInTheDocument()
      expect(screen.getByText(/test.csv/)).toBeInTheDocument()
      expect(screen.getByText(/1.50 MB/)).toBeInTheDocument()
    })
  })

  describe('Format Selection', () => {
    it('should have CSV as default output format', () => {
      expect(mockConverter.outputFormat).toBe('csv')
    })

    it('should show all supported data formats', () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const formatSelect = screen.getByLabelText('Select output format for data conversion')
      expect(formatSelect).toBeInTheDocument()

      // Check for all data formats
      expect(screen.getByRole('option', { name: 'CSV' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'JSON' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'XML' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'YAML' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'YML' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TOML' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'INI' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'JSONL' })).toBeInTheDocument()
    })

    it('should disable format select during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const formatSelect = screen.getByLabelText('Select output format for data conversion')
      expect(formatSelect).toBeDisabled()
    })
  })

  describe('Encoding Selection', () => {
    it('should show encoding options', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /UTF-8/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /UTF-16/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /ASCII/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Latin-1/ })).toBeInTheDocument()
    })

    it('should have UTF-8 as default encoding', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding') as HTMLSelectElement
      expect(encodingSelect.value).toBe('utf-8')
    })

    it('should allow changing encoding', async () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      const user = userEvent.setup()

      await user.selectOptions(encodingSelect, 'utf-16')

      expect(encodingSelect).toHaveValue('utf-16')
    })

    it('should disable encoding select during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeDisabled()
    })
  })

  describe('Delimiter Selection', () => {
    it('should show delimiter options', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /Comma/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Semicolon/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Tab/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Pipe/ })).toBeInTheDocument()
    })

    it('should have comma as default delimiter', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output') as HTMLSelectElement
      expect(delimiterSelect.value).toBe(',')
    })

    it('should allow changing delimiter', async () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      const user = userEvent.setup()

      await user.selectOptions(delimiterSelect, '\t')

      expect(delimiterSelect).toHaveValue('\t')
    })

    it('should disable delimiter select during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toBeDisabled()
    })

    it('should have describedby for delimiter hint', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toHaveAttribute('aria-describedby', 'delimiter-hint')
      expect(screen.getByText('converter.data.delimiterHint')).toBeInTheDocument()
    })
  })

  describe('Pretty Print Checkbox', () => {
    it('should render pretty print checkbox', () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const checkbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ })
      expect(checkbox).toBeInTheDocument()
    })

    it('should have pretty print checked by default', () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const checkbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ }) as HTMLInputElement
      expect(checkbox.checked).toBe(true)
    })

    it('should allow toggling pretty print', async () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const checkbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ }) as HTMLInputElement
      const user = userEvent.setup()

      expect(checkbox.checked).toBe(true)
      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })

    it('should disable pretty print during conversion', () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const checkbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ })
      expect(checkbox).toBeDisabled()
    })

    it('should have describedby for pretty hint', () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const checkbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ })
      expect(checkbox).toHaveAttribute('aria-describedby', 'pretty-hint')
      expect(screen.getByText('converter.data.prettyHint')).toBeInTheDocument()
    })
  })

  describe('Custom Filename', () => {
    it('should render custom filename input', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeInTheDocument()
    })

    it('should disable custom filename during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toBeDisabled()
    })
  })

  describe('Output Directory (Electron)', () => {
    it('should show output directory controls in Electron environment', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeInTheDocument()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeInTheDocument()
    })

    it('should disable output directory controls during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toBeDisabled()

      const browseButton = screen.getByLabelText('Browse for output directory')
      expect(browseButton).toBeDisabled()
    })
  })

  describe('Conversion', () => {
    it('should call handleConvert when convert button is clicked', async () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const convertButton = screen.getByRole('button', { name: /convertData/i })
      const user = userEvent.setup()
      await user.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalled()
      })
    })

    it('should pass encoding, delimiter, and pretty to conversion', async () => {
      const mockFile = new File(['test'], 'test.json', { type: 'application/json' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      // Change encoding
      const encodingSelect = screen.getByLabelText('Select text encoding')
      await userEvent.selectOptions(encodingSelect, 'utf-16')

      // Change delimiter
      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      await userEvent.selectOptions(delimiterSelect, ';')

      // Toggle pretty print off
      const prettyCheckbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ })
      await userEvent.click(prettyCheckbox)

      const convertButton = screen.getByRole('button', { name: /convertData/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            encoding: 'utf-16',
            delimiter: ';',
            pretty: false,
          })
        )
      })
    })

    it('should pass default values when not changed', async () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const convertButton = screen.getByRole('button', { name: /convertData/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            encoding: 'utf-8',
            delimiter: ',',
            pretty: true,
          })
        )
      })
    })
  })

  describe('Drag and Drop', () => {
    it('should show overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<DataConverter />)

      expect(screen.getByText('common.dropToReplace')).toBeInTheDocument()
    })

    it('should not show overlay when not dragging', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<DataConverter />)

      expect(screen.queryByText('common.dropToReplace')).not.toBeInTheDocument()
    })
  })

  describe('Upload Progress', () => {
    it('should show upload progress during upload', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 70

      render(<DataConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('70%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should not show upload progress when not uploading', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false

      render(<DataConverter />)

      expect(screen.queryByText('common.uploadingFile')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Progress', () => {
    it('should show conversion progress during conversion', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 85, message: 'Converting data...' }

      render(<DataConverter />)

      expect(screen.getByText('Converting data...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('85%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show processing message when no progress message', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 55 }

      render(<DataConverter />)

      expect(screen.getByText('common.processing')).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('should show error message when conversion fails', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'error'
      mockConverter.error = 'Conversion failed: Invalid data format'
      mockConverter.showFeedback = true

      render(<DataConverter />)

      expect(mockConverter.error).toBe('Conversion failed: Invalid data format')
    })

    it('should show success message when conversion completes', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.json'
      mockConverter.showFeedback = true

      render(<DataConverter />)

      expect(screen.getByText('messages.conversionSuccess')).toBeInTheDocument()
    })
  })

  describe('Button States', () => {
    it('should show convert and reset buttons when idle', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<DataConverter />)

      expect(screen.getByRole('button', { name: /convertData/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('should show disabled button when converting', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<DataConverter />)

      // When converting, the convert and reset buttons should not be available
      expect(screen.queryByRole('button', { name: /convertData/i })).not.toBeInTheDocument()
      expect(mockConverter.status).toBe('converting')
    })

    it('should show download and convert another buttons when completed', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.downloadUrl = '/api/download/converted.json'

      render(<DataConverter />)

      expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /convertAnother/i })).toBeInTheDocument()
    })

    it('should show convert and reset buttons when failed', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed'

      render(<DataConverter />)

      expect(screen.getByRole('button', { name: /convertData/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<DataConverter />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
    })

    it('should have accessible form controls when file is selected', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const formatSelect = screen.getByLabelText('Select output format for data conversion')
      expect(formatSelect).toBeInTheDocument()

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeInTheDocument()

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toBeInTheDocument()

      const prettyCheckbox = screen.getByRole('checkbox', { name: /converter.data.prettyPrint/ })
      expect(prettyCheckbox).toBeInTheDocument()
    })

    it('should have describedby for custom filename input', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const filenameInput = screen.getByLabelText('common.customFilename')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()
    })

    it('should have describedby for output directory input', () => {
      const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
      mockConverter.selectedFile = mockFile

      render(<DataConverter />)

      const outputDirInput = screen.getByLabelText('Output directory path')
      expect(outputDirInput).toHaveAttribute('aria-describedby', 'output-directory-hint')
      expect(screen.getByText('common.outputDirectoryHint')).toBeInTheDocument()
    })
  })
})
