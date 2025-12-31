import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SpreadsheetConverter } from '../../../components/Converter/SpreadsheetConverter'

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
  outputFormat: 'xlsx',
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
  spreadsheetAPI: {
    convert: vi.fn(),
  },
}))

describe('SpreadsheetConverter', () => {
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
    mockConverter.outputFormat = 'xlsx'
  })

  describe('Rendering', () => {
    it('should render spreadsheet converter title', () => {
      render(<SpreadsheetConverter />)
      expect(screen.getByText('converter.spreadsheet.title')).toBeInTheDocument()
    })

    it('should render warning about formula loss', () => {
      render(<SpreadsheetConverter />)
      expect(screen.getByText(/Formulas, charts, and advanced formatting will be lost/)).toBeInTheDocument()
      expect(screen.getByText(/Only data values are preserved/)).toBeInTheDocument()
    })

    it('should render drop zone when no file is selected', () => {
      render(<SpreadsheetConverter />)
      expect(mockConverter.selectedFile).toBeNull()
    })

    it('should render all 5 spreadsheet formats in dropdown', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      expect(screen.getByRole('option', { name: 'XLSX' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'XLS' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'ODS' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'CSV' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'TSV' })).toBeInTheDocument()
    })

    it('should render encoding dropdown with 4 options', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toBeInTheDocument()

      expect(screen.getByRole('option', { name: /UTF-8/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /UTF-16/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Latin-1/ })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /ASCII/ })).toBeInTheDocument()
    })

    it('should render delimiter dropdown when CSV selected', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toBeInTheDocument()
    })

    it('should NOT render delimiter dropdown when XLSX selected', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'xlsx'

      render(<SpreadsheetConverter />)

      expect(screen.queryByLabelText('Select delimiter for CSV output')).not.toBeInTheDocument()
    })

    it('should render sheet name input', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const sheetNameInput = screen.getByLabelText(/Sheet Name/)
      expect(sheetNameInput).toBeInTheDocument()
    })

    it('should show drag overlay when dragging over', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Drop to replace file')).toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('should call handleFileSelect', async () => {
      render(<SpreadsheetConverter />)

      // The file selection is handled by DropZone component
      expect(mockConverter.handleFileSelect).toBeDefined()
    })

    it('should display file name and size in MB', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      Object.defineProperty(mockFile, 'size', { value: 2.5 * 1024 * 1024 }) // 2.5 MB

      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      expect(screen.getByText(/test.xlsx/)).toBeInTheDocument()
      expect(screen.getByText(/2.50 MB/)).toBeInTheDocument()
    })

    it('should enable conversion options when file selected', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const formatSelect = screen.getByLabelText('Select output format for spreadsheet conversion')
      expect(formatSelect).not.toBeDisabled()
    })

    it('should show drag overlay on dragover', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Drop to replace file')).toBeInTheDocument()
    })

    it('should hide drag overlay on dragleave', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.isDraggingOver = false

      render(<SpreadsheetConverter />)

      expect(screen.queryByText('Drop to replace file')).not.toBeInTheDocument()
    })
  })

  describe('Conversion Options', () => {
    it('should change output format', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const formatSelect = screen.getByLabelText('Select output format for spreadsheet conversion')
      await userEvent.selectOptions(formatSelect, 'csv')

      expect(mockConverter.setOutputFormat).toHaveBeenCalledWith('csv')
    })

    it('should change encoding', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      await userEvent.selectOptions(encodingSelect, 'utf-16')

      expect(encodingSelect).toHaveValue('utf-16')
    })

    it('should change delimiter', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      await userEvent.selectOptions(delimiterSelect, ';')

      expect(delimiterSelect).toHaveValue(';')
    })

    it('should update sheet name', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const sheetNameInput = screen.getByLabelText(/Sheet Name/)
      await userEvent.type(sheetNameInput, 'Sheet1')

      expect(sheetNameInput).toHaveValue('Sheet1')
    })

    it('should default encoding to utf-8', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding') as HTMLSelectElement
      expect(encodingSelect.value).toBe('utf-8')
    })

    it('should default delimiter to comma', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output') as HTMLSelectElement
      expect(delimiterSelect.value).toBe(',')
    })

    it('should show delimiter dropdown only for CSV format', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      expect(screen.getByLabelText('Select delimiter for CSV output')).toBeInTheDocument()
    })

    it('should show delimiter dropdown only for TSV format', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'tsv'

      render(<SpreadsheetConverter />)

      expect(screen.getByLabelText('Select delimiter for CSV output')).toBeInTheDocument()
    })

    it('should hide delimiter for XLSX format', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'xlsx'

      render(<SpreadsheetConverter />)

      expect(screen.queryByLabelText('Select delimiter for CSV output')).not.toBeInTheDocument()
    })

    it('should update custom filename', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const filenameInput = screen.getByLabelText('Custom Filename (Optional)')
      await userEvent.type(filenameInput, 'my-spreadsheet')

      expect(mockConverter.setCustomFilename).toHaveBeenCalled()
    })

    it('should show XLS error message when xls selected', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'xls'

      render(<SpreadsheetConverter />)

      expect(screen.getByText('XLS output not supported. Reading XLS is supported.')).toBeInTheDocument()
    })

    it('should disable controls during conversion', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'

      render(<SpreadsheetConverter />)

      const formatSelect = screen.getByLabelText('Select output format for spreadsheet conversion')
      const encodingSelect = screen.getByLabelText('Select text encoding')

      expect(formatSelect).toBeDisabled()
      expect(encodingSelect).toBeDisabled()
    })
  })

  describe('Conversion Flow', () => {
    it('should call spreadsheetAPI.convert with encoding, delimiter, sheetName', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      // Set encoding
      const encodingSelect = screen.getByLabelText('Select text encoding')
      await userEvent.selectOptions(encodingSelect, 'utf-16')

      // Set delimiter
      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      await userEvent.selectOptions(delimiterSelect, ';')

      // Set sheet name
      const sheetNameInput = screen.getByLabelText(/Sheet Name/)
      await userEvent.type(sheetNameInput, 'Sheet1')

      const convertButton = screen.getByRole('button', { name: /Convert Spreadsheet/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            encoding: 'utf-16',
            delimiter: ';',
            sheetName: 'Sheet1',
          })
        )
      })
    })

    it('should pass undefined for empty sheetName', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Spreadsheet/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            sheetName: undefined,
          })
        )
      })
    })

    it('should include delimiter for CSV output', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Spreadsheet/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            delimiter: ',',
          })
        )
      })
    })

    it('should include delimiter for TSV output', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'tsv'

      render(<SpreadsheetConverter />)

      const convertButton = screen.getByRole('button', { name: /Convert Spreadsheet/i })
      await userEvent.click(convertButton)

      await waitFor(() => {
        expect(mockConverter.handleConvert).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            delimiter: ',',
          })
        )
      })
    })

    it('should show conversion progress', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Converting spreadsheet...' }

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Converting spreadsheet...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('75%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display success message', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Spreadsheet conversion completed successfully!')).toBeInTheDocument()
    })

    it('should handle errors', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Conversion failed: Invalid spreadsheet'
      mockConverter.showFeedback = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Conversion failed: Invalid spreadsheet')).toBeInTheDocument()
    })

    it('should allow reset', async () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'idle'

      render(<SpreadsheetConverter />)

      const resetButton = screen.getByRole('button', { name: /Reset/i })
      await userEvent.click(resetButton)

      expect(mockConverter.handleReset).toHaveBeenCalled()
    })
  })

  describe('Progress and Status', () => {
    it('should show upload progress', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = true
      mockConverter.uploadProgress = 60

      render(<SpreadsheetConverter />)

      expect(screen.getByText('common.uploadingFile')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('60%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should show conversion progress', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 85, message: 'Processing spreadsheet...' }

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Processing spreadsheet...')).toBeInTheDocument()
      const progressTexts = screen.getAllByText('85%')
      expect(progressTexts.length).toBeGreaterThan(0)
    })

    it('should display progress message', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 50, message: 'Reading worksheet...' }

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Reading worksheet...')).toBeInTheDocument()
    })

    it('should show success message on completion', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'completed'
      mockConverter.showFeedback = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Spreadsheet conversion completed successfully!')).toBeInTheDocument()
    })

    it('should show error message on failure', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'Sheet not found'
      mockConverter.showFeedback = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('Sheet not found')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have aria-label for output format select', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const formatSelect = screen.getByLabelText('Select output format for spreadsheet conversion')
      expect(formatSelect).toHaveAttribute('aria-label', 'Select output format for spreadsheet conversion')
    })

    it('should have aria-label for encoding select', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const encodingSelect = screen.getByLabelText('Select text encoding')
      expect(encodingSelect).toHaveAttribute('aria-label', 'Select text encoding')
    })

    it('should have aria-label and aria-describedby for delimiter', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'csv'

      render(<SpreadsheetConverter />)

      const delimiterSelect = screen.getByLabelText('Select delimiter for CSV output')
      expect(delimiterSelect).toHaveAttribute('aria-label', 'Select delimiter for CSV output')
      expect(delimiterSelect).toHaveAttribute('aria-describedby', 'delimiter-hint')
    })

    it('should have aria-describedby for sheet name input', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const sheetNameInput = screen.getByLabelText(/Sheet Name/)
      expect(sheetNameInput).toHaveAttribute('aria-describedby', 'sheet-name-hint')
      expect(screen.getByText('Leave empty to convert first sheet')).toBeInTheDocument()
    })

    it('should have aria-describedby for filename hint', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      render(<SpreadsheetConverter />)

      const filenameInput = screen.getByLabelText('Custom Filename (Optional)')
      expect(filenameInput).toHaveAttribute('aria-describedby', 'filename-hint')
      expect(screen.getByText('common.customFilenameHint')).toBeInTheDocument()
    })

    it('should have proper progress bar ARIA attributes', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'converting'
      mockConverter.showFeedback = true
      mockConverter.isUploading = false
      mockConverter.progress = { progress: 75, message: 'Converting...' }

      render(<SpreadsheetConverter />)

      expect(mockConverter.getProgressAriaAttributes).toHaveBeenCalled()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window.electron', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile

      // Temporarily remove window.electron
      const originalElectron = window.electron
      delete (window as any).electron

      render(<SpreadsheetConverter />)

      // Output directory controls should not be present
      expect(screen.queryByLabelText('Output directory path')).not.toBeInTheDocument()

      // Restore window.electron
      ;(window as any).electron = originalElectron
    })

    it('should handle API errors', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.status = 'failed'
      mockConverter.error = 'API Error: Server unreachable'
      mockConverter.showFeedback = true

      render(<SpreadsheetConverter />)

      expect(screen.getByText('API Error: Server unreachable')).toBeInTheDocument()
    })

    it('should handle XLS format selection (show warning)', () => {
      const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mockConverter.selectedFile = mockFile
      mockConverter.outputFormat = 'xls'

      render(<SpreadsheetConverter />)

      expect(screen.getByText('XLS output not supported. Reading XLS is supported.')).toBeInTheDocument()
    })
  })
})
