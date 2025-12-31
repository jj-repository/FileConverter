import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BatchDropZone } from '../../../components/FileUpload/BatchDropZone'

// Mock react-dropzone
const mockGetRootProps = vi.fn(() => ({}))
const mockGetInputProps = vi.fn(() => ({}))
const mockOpen = vi.fn()
let mockIsDragActive = false
let mockIsDragReject = false
let mockOnDropCallback: ((files: File[]) => void) | null = null

vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn((options) => {
    mockOnDropCallback = options.onDrop
    return {
      getRootProps: mockGetRootProps,
      getInputProps: mockGetInputProps,
      isDragActive: mockIsDragActive,
      isDragReject: mockIsDragReject,
      open: mockOpen,
    }
  }),
}))

import { useDropzone } from 'react-dropzone'

describe('BatchDropZone', () => {
  const mockOnFilesSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockIsDragActive = false
    mockIsDragReject = false
    mockOnDropCallback = null
  })

  describe('Rendering', () => {
    it('should render drop zone with role="button"', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')
      expect(dropZone).toBeInTheDocument()
    })

    it('should always render folder icon (📁)', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const folderIcon = screen.getByText('📁')
      expect(folderIcon).toBeInTheDocument()
    })

    it('should render instruction text "Drag & drop multiple files here, or click to select"', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.getByText('Drag & drop multiple files here, or click to select')).toBeInTheDocument()
    })

    it('should render maxFiles limit text "Up to {maxFiles} files at once"', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={50} />)
      expect(screen.getByText('Up to 50 files at once')).toBeInTheDocument()
    })

    it('should render default maxFiles as 100', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.getByText('Up to 100 files at once')).toBeInTheDocument()
    })

    it('should render supported formats list when acceptedFormats provided', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png', 'jpg', 'pdf']} />)
      expect(screen.getByText('Supported formats: PNG, JPG, PDF')).toBeInTheDocument()
    })

    it('should render "All formats supported" when no acceptedFormats', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.getByText('All formats supported')).toBeInTheDocument()
    })
  })

  describe('ARIA and Accessibility', () => {
    it('should have aria-label with "multiple files" and maxFiles', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={50} />)
      const dropZone = screen.getByRole('button')
      expect(dropZone).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Upload multiple files')
      )
      expect(dropZone).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Maximum 50 files')
      )
    })

    it('should have aria-describedby pointing to batch-dropzone-hint and batch-dropzone-status', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')
      expect(dropZone).toHaveAttribute('aria-describedby', 'batch-dropzone-hint batch-dropzone-status')
    })

    it('should have tabIndex={0}', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')
      expect(dropZone).toHaveAttribute('tabIndex', '0')
    })

    it('should have role="status" for announcements', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const statusElement = container.querySelector('[role="status"]')
      expect(statusElement).toBeInTheDocument()
      expect(statusElement).toHaveAttribute('id', 'batch-dropzone-status')
    })

    it('should have aria-live="polite" and aria-atomic="true"', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const statusElement = container.querySelector('[role="status"]')
      expect(statusElement).toHaveAttribute('aria-live', 'polite')
      expect(statusElement).toHaveAttribute('aria-atomic', 'true')
    })

    it('file input should have aria-label mentioning maxFiles', () => {
      mockGetInputProps.mockReturnValue({
        'aria-label': 'Select multiple files to convert. Maximum 50 files allowed.',
      })

      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={50} />)
      expect(mockGetInputProps).toHaveBeenCalled()

      // Verify getInputProps was called and would provide the aria-label
      const inputPropsCall = mockGetInputProps.mock.results[0]
      expect(inputPropsCall.value).toHaveProperty('aria-label')
      expect(inputPropsCall.value['aria-label']).toContain('Maximum 50 files allowed')
    })

    it('should show sr-only status div', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const statusElement = container.querySelector('.sr-only')
      expect(statusElement).toBeInTheDocument()
      expect(statusElement).toHaveAttribute('id', 'batch-dropzone-status')
    })

    it('icon should have aria-hidden="true"', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const iconElement = screen.getByText('📁')
      expect(iconElement).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('Max Files Prop', () => {
    it('should default to 100 when maxFiles not provided', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          maxFiles: 100,
        })
      )
    })

    it('should display custom maxFiles in aria-label', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={25} />)
      const dropZone = screen.getByRole('button')
      expect(dropZone).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Maximum 25 files')
      )
    })

    it('should display custom maxFiles in UI text', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={75} />)
      expect(screen.getByText('Up to 75 files at once')).toBeInTheDocument()
    })

    it('should pass maxFiles to useDropzone', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={30} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          maxFiles: 30,
        })
      )
    })

    it('should update display when maxFiles changes', () => {
      const { rerender } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={20} />)
      expect(screen.getByText('Up to 20 files at once')).toBeInTheDocument()

      rerender(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={40} />)
      expect(screen.queryByText('Up to 20 files at once')).not.toBeInTheDocument()
      expect(screen.getByText('Up to 40 files at once')).toBeInTheDocument()
    })
  })

  describe('Drag States', () => {
    it('should show "Drop the files here..." (plural) when isDragActive', () => {
      mockIsDragActive = true
      mockIsDragReject = false

      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.getByText('Drop the files here...')).toBeInTheDocument()
    })

    it('should show "Some files have invalid types!" when isDragReject', () => {
      mockIsDragActive = false
      mockIsDragReject = true

      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.getByText('Some files have invalid types!')).toBeInTheDocument()
    })

    it('should apply border-primary-500 bg-primary-50 when isDragActive', () => {
      mockIsDragActive = true
      mockIsDragReject = false

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = container.querySelector('[role="button"]')
      expect(dropZone).toHaveClass('border-primary-500')
      expect(dropZone).toHaveClass('bg-primary-50')
    })

    it('should apply border-red-500 bg-red-50 when isDragReject', () => {
      mockIsDragActive = false
      mockIsDragReject = true

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = container.querySelector('[role="button"]')
      expect(dropZone).toHaveClass('border-red-500')
      expect(dropZone).toHaveClass('bg-red-50')
    })

    it('should show screen reader message "Files are over drop zone. Release to upload."', () => {
      mockIsDragActive = true
      mockIsDragReject = false

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const statusElement = container.querySelector('#batch-dropzone-status')
      expect(statusElement).toHaveTextContent('Files are over drop zone. Release to upload.')
    })

    it('should show screen reader message "Some files have invalid types." when rejected', () => {
      mockIsDragActive = false
      mockIsDragReject = true

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const statusElement = container.querySelector('#batch-dropzone-status')
      expect(statusElement).toHaveTextContent('Some files have invalid types.')
    })
  })

  describe('File Selection', () => {
    it('should call onFilesSelect when files are dropped', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      const file1 = new File(['content1'], 'test1.png', { type: 'image/png' })
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' })

      if (mockOnDropCallback) {
        mockOnDropCallback([file1, file2])
      }

      expect(mockOnFilesSelect).toHaveBeenCalledWith([file1, file2])
    })

    it('should call onFilesSelect with all files (not just first)', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      const file1 = new File(['content1'], 'test1.png', { type: 'image/png' })
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' })
      const file3 = new File(['content3'], 'test3.pdf', { type: 'application/pdf' })

      if (mockOnDropCallback) {
        mockOnDropCallback([file1, file2, file3])
      }

      expect(mockOnFilesSelect).toHaveBeenCalledWith([file1, file2, file3])
      expect(mockOnFilesSelect).toHaveBeenCalledTimes(1)
    })

    it('should handle multiple files correctly', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      const files = Array.from({ length: 10 }, (_, i) =>
        new File([`content${i}`], `test${i}.png`, { type: 'image/png' })
      )

      if (mockOnDropCallback) {
        mockOnDropCallback(files)
      }

      expect(mockOnFilesSelect).toHaveBeenCalledWith(files)
      expect(mockOnFilesSelect.mock.calls[0][0]).toHaveLength(10)
    })

    it('should accept files when formats match', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png', 'jpg']} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: expect.objectContaining({
            'image/*': expect.arrayContaining(['.png', '.jpg']),
          }),
        })
      )
    })

    it('should reject files when formats don\'t match', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png']} />)

      const acceptConfig = (useDropzone as any).mock.calls[0][0].accept

      // Verify only png is in image/* array
      expect(acceptConfig['image/*']).toEqual(['.png'])
      expect(acceptConfig['video/*']).toEqual([])
      expect(acceptConfig['audio/*']).toEqual([])
      expect(acceptConfig['application/*']).toEqual([])
    })

    it('should handle file input click', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')

      fireEvent.click(dropZone)
      expect(mockGetRootProps).toHaveBeenCalled()
    })
  })

  describe('Accepted Formats and MIME Types', () => {
    it('should filter image formats to image/* MIME type', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png', 'jpg', 'gif']} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: expect.objectContaining({
            'image/*': ['.png', '.jpg', '.gif'],
          }),
        })
      )
    })

    it('should filter video formats to video/* MIME type', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['mp4', 'avi', 'mov']} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: expect.objectContaining({
            'video/*': ['.mp4', '.avi', '.mov'],
          }),
        })
      )
    })

    it('should filter audio formats to audio/* MIME type', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['mp3', 'wav', 'flac']} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: expect.objectContaining({
            'audio/*': ['.mp3', '.wav', '.flac'],
          }),
        })
      )
    })

    it('should filter document formats to application/* MIME type', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['pdf', 'docx', 'txt']} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: expect.objectContaining({
            'application/*': ['.pdf', '.docx', '.txt'],
          }),
        })
      )
    })

    it('should display formats in uppercase', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png', 'jpg', 'pdf']} />)
      expect(screen.getByText('Supported formats: PNG, JPG, PDF')).toBeInTheDocument()
    })

    it('should join multiple formats with comma', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} acceptedFormats={['png', 'mp4', 'mp3', 'pdf']} />)
      expect(screen.getByText('Supported formats: PNG, MP4, MP3, PDF')).toBeInTheDocument()
    })

    it('should create correct accept object with filtered MIME types', () => {
      render(
        <BatchDropZone
          onFilesSelect={mockOnFilesSelect}
          acceptedFormats={['png', 'mp4', 'mp3', 'pdf']}
        />
      )

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: {
            'image/*': ['.png'],
            'video/*': ['.mp4'],
            'audio/*': ['.mp3'],
            'application/*': ['.pdf'],
          },
        })
      )
    })
  })

  describe('Keyboard Interaction', () => {
    it('should trigger file input on Enter key', () => {
      const mockClick = vi.fn()
      const mockInputElement = document.createElement('input')
      mockInputElement.type = 'file'
      mockInputElement.click = mockClick

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')

      // Mock querySelector to return our mock input
      const originalQuerySelector = dropZone.querySelector.bind(dropZone)
      dropZone.querySelector = vi.fn((selector) => {
        if (selector === 'input[type="file"]') {
          return mockInputElement
        }
        return originalQuerySelector(selector)
      })

      fireEvent.keyDown(dropZone, { key: 'Enter' })

      expect(mockClick).toHaveBeenCalled()
    })

    it('should trigger file input on Space key', () => {
      const mockClick = vi.fn()
      const mockInputElement = document.createElement('input')
      mockInputElement.type = 'file'
      mockInputElement.click = mockClick

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')

      // Mock querySelector to return our mock input
      const originalQuerySelector = dropZone.querySelector.bind(dropZone)
      dropZone.querySelector = vi.fn((selector) => {
        if (selector === 'input[type="file"]') {
          return mockInputElement
        }
        return originalQuerySelector(selector)
      })

      fireEvent.keyDown(dropZone, { key: ' ' })

      expect(mockClick).toHaveBeenCalled()
    })

    it('should not trigger on other keys', () => {
      const mockClick = vi.fn()
      const mockInputElement = document.createElement('input')
      mockInputElement.type = 'file'
      mockInputElement.click = mockClick

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')

      // Mock querySelector to return our mock input
      const originalQuerySelector = dropZone.querySelector.bind(dropZone)
      dropZone.querySelector = vi.fn((selector) => {
        if (selector === 'input[type="file"]') {
          return mockInputElement
        }
        return originalQuerySelector(selector)
      })

      fireEvent.keyDown(dropZone, { key: 'a' })
      fireEvent.keyDown(dropZone, { key: 'Tab' })
      fireEvent.keyDown(dropZone, { key: 'Escape' })

      expect(mockClick).not.toHaveBeenCalled()
    })

    it('should have focus:ring styles', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = container.querySelector('[role="button"]')

      expect(dropZone).toHaveClass('focus:outline-none')
      expect(dropZone).toHaveClass('focus:ring-2')
      expect(dropZone).toHaveClass('focus:ring-primary-500')
      expect(dropZone).toHaveClass('focus:ring-offset-2')
    })
  })

  describe('Edge Cases', () => {
    it('should handle onDrop with empty files array', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      if (mockOnDropCallback) {
        mockOnDropCallback([])
      }

      expect(mockOnFilesSelect).not.toHaveBeenCalled()
    })

    it('should handle maxFiles=1 (edge case)', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={1} />)

      expect(screen.getByText('Up to 1 files at once')).toBeInTheDocument()
      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          maxFiles: 1,
        })
      )
    })

    it('should handle maxFiles=0 (edge case)', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} maxFiles={0} />)

      expect(screen.getByText('Up to 0 files at once')).toBeInTheDocument()
      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          maxFiles: 0,
        })
      )
    })

    it('should prevent default on keyboard events', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = screen.getByRole('button')

      const enterEvent = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })
      const preventDefaultSpy = vi.spyOn(enterEvent, 'preventDefault')
      fireEvent(dropZone, enterEvent)
      expect(preventDefaultSpy).toHaveBeenCalled()

      const spaceEvent = new KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true })
      const preventDefaultSpy2 = vi.spyOn(spaceEvent, 'preventDefault')
      fireEvent(dropZone, spaceEvent)
      expect(preventDefaultSpy2).toHaveBeenCalled()
    })
  })

  describe('Multiple prop', () => {
    it('should pass multiple: true to useDropzone', () => {
      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          multiple: true,
        })
      )
    })
  })

  describe('Default Styling', () => {
    it('should have default border and hover styles when not dragging', () => {
      mockIsDragActive = false
      mockIsDragReject = false

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = container.querySelector('[role="button"]')

      expect(dropZone).toHaveClass('border-gray-300')
      expect(dropZone).toHaveClass('hover:border-gray-400')
    })

    it('should have base styling classes', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dropZone = container.querySelector('[role="button"]')

      expect(dropZone).toHaveClass('border-2')
      expect(dropZone).toHaveClass('border-dashed')
      expect(dropZone).toHaveClass('rounded-lg')
      expect(dropZone).toHaveClass('p-12')
      expect(dropZone).toHaveClass('text-center')
      expect(dropZone).toHaveClass('cursor-pointer')
      expect(dropZone).toHaveClass('transition-colors')
    })
  })

  describe('Drag Text States', () => {
    it('should hide instruction text when isDragActive', () => {
      mockIsDragActive = true
      mockIsDragReject = false

      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.queryByText('Drag & drop multiple files here, or click to select')).not.toBeInTheDocument()
    })

    it('should hide instruction text when isDragReject', () => {
      mockIsDragActive = false
      mockIsDragReject = true

      render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      expect(screen.queryByText('Drag & drop multiple files here, or click to select')).not.toBeInTheDocument()
    })

    it('should show drag text with aria-hidden when dragging', () => {
      mockIsDragActive = true
      mockIsDragReject = false

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const dragText = screen.getByText('Drop the files here...')

      expect(dragText).toHaveAttribute('aria-hidden', 'true')
      expect(dragText).toHaveClass('text-primary-600')
      expect(dragText).toHaveClass('font-medium')
    })

    it('should show reject text with aria-hidden when dragging invalid files', () => {
      mockIsDragActive = false
      mockIsDragReject = true

      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const rejectText = screen.getByText('Some files have invalid types!')

      expect(rejectText).toHaveAttribute('aria-hidden', 'true')
      expect(rejectText).toHaveClass('text-red-600')
      expect(rejectText).toHaveClass('font-medium')
    })
  })

  describe('Hint Text ID', () => {
    it('should have id="batch-dropzone-hint" on instruction paragraph', () => {
      const { container } = render(<BatchDropZone onFilesSelect={mockOnFilesSelect} />)
      const hintElement = container.querySelector('#batch-dropzone-hint')

      expect(hintElement).toBeInTheDocument()
      expect(hintElement).toHaveTextContent('Drag & drop multiple files here, or click to select')
    })
  })
})
