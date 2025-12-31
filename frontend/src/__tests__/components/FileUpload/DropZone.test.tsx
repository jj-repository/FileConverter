import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DropZone } from '../../../components/FileUpload/DropZone'

// Mock react-dropzone
const mockGetRootProps = vi.fn(() => ({}))
const mockGetInputProps = vi.fn(() => ({ type: 'file' }))
const mockOpen = vi.fn()
let mockIsDragActive = false
let mockIsDragReject = false
let mockOnDropCallback: ((files: File[]) => void) | null = null
let mockAcceptConfig: any = null

vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn((options) => {
    // Store the onDrop callback and accept config for testing
    mockOnDropCallback = options.onDrop
    mockAcceptConfig = options.accept

    return {
      getRootProps: mockGetRootProps,
      getInputProps: mockGetInputProps,
      isDragActive: mockIsDragActive,
      isDragReject: mockIsDragReject,
      open: mockOpen,
    }
  }),
}))

// Import after mock
import { useDropzone } from 'react-dropzone'

describe('DropZone', () => {
  const mockOnFileSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockIsDragActive = false
    mockIsDragReject = false
    mockOnDropCallback = null
    mockAcceptConfig = null
    mockGetRootProps.mockReturnValue({})
    mockGetInputProps.mockReturnValue({ type: 'file' })
  })

  // ===== RENDERING TESTS (6 tests) =====
  describe('Rendering', () => {
    it('should render drop zone with role="button"', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should render correct file icon for image fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText('🖼️')).toBeInTheDocument()
    })

    it('should render correct file icon for video fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="video" />)
      expect(screen.getByText('🎥')).toBeInTheDocument()
    })

    it('should render correct file icon for audio fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="audio" />)
      expect(screen.getByText('🎵')).toBeInTheDocument()
    })

    it('should render correct file icon for document fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="document" />)
      expect(screen.getByText('📄')).toBeInTheDocument()
    })

    it('should render correct file icon for unknown fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="unknown" />)
      expect(screen.getByText('📁')).toBeInTheDocument()
    })

    it('should render instruction text with fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText(/Drag & drop a image file here, or click to select/)).toBeInTheDocument()
    })

    it('should render supported formats list when acceptedFormats provided', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={['jpg', 'png', 'gif']}
        />
      )
      expect(screen.getByText('Supported formats: JPG, PNG, GIF')).toBeInTheDocument()
    })

    it('should render "All formats supported" when no acceptedFormats', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText('All formats supported')).toBeInTheDocument()
    })

    it('should render hidden file input', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const input = container.querySelector('input[type="file"]')
      expect(input).toBeInTheDocument()
    })
  })

  // ===== ARIA AND ACCESSIBILITY TESTS (8 tests) =====
  describe('ARIA and Accessibility', () => {
    it('should have proper aria-label with fileType and formats', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={['jpg', 'png']}
        />
      )
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute(
        'aria-label',
        'Upload image file. Supported formats: JPG, PNG. Press Enter or Space to browse files, or drag and drop a file here.'
      )
    })

    it('should have aria-label with "all formats" when no acceptedFormats', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="video" />)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute(
        'aria-label',
        'Upload video file. Supported formats: all formats. Press Enter or Space to browse files, or drag and drop a file here.'
      )
    })

    it('should have aria-describedby pointing to hint and status', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-describedby', 'dropzone-hint dropzone-status')
    })

    it('should have tabIndex={0} for keyboard focus', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('tabIndex', '0')
    })

    it('should have role="status" for screen reader announcements', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const status = container.querySelector('[role="status"]')
      expect(status).toBeInTheDocument()
      expect(status).toHaveAttribute('id', 'dropzone-status')
    })

    it('should have aria-live="polite" and aria-atomic="true"', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const status = container.querySelector('[role="status"]')
      expect(status).toHaveAttribute('aria-live', 'polite')
      expect(status).toHaveAttribute('aria-atomic', 'true')
    })

    it('file input should have aria-label', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const input = container.querySelector('input[type="file"]')
      expect(input).toHaveAttribute('aria-label', 'Select image file to convert')
    })

    it('should show sr-only status div', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const status = container.querySelector('#dropzone-status')
      expect(status).toHaveClass('sr-only')
    })

    it('icon should have aria-hidden="true"', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const iconContainer = container.querySelector('[aria-hidden="true"]')
      expect(iconContainer).toBeInTheDocument()
      expect(iconContainer?.textContent).toBe('🖼️')
    })
  })

  // ===== FILE TYPE ICONS TESTS (5 tests) =====
  describe('File Type Icons', () => {
    it('should show 🖼️ for image fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText('🖼️')).toBeInTheDocument()
    })

    it('should show 🎥 for video fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="video" />)
      expect(screen.getByText('🎥')).toBeInTheDocument()
    })

    it('should show 🎵 for audio fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="audio" />)
      expect(screen.getByText('🎵')).toBeInTheDocument()
    })

    it('should show 📄 for document fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="document" />)
      expect(screen.getByText('📄')).toBeInTheDocument()
    })

    it('should show 📁 for unknown fileType', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="other" />)
      expect(screen.getByText('📁')).toBeInTheDocument()
    })
  })

  // ===== DRAG STATES TESTS (6 tests) =====
  describe('Drag States', () => {
    it('should show "Drop the file here..." when isDragActive and not rejected', () => {
      mockIsDragActive = true
      mockIsDragReject = false
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText('Drop the file here...')).toBeInTheDocument()
    })

    it('should show "Invalid file type!" when isDragReject', () => {
      mockIsDragActive = false
      mockIsDragReject = true
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      expect(screen.getByText('Invalid file type!')).toBeInTheDocument()
    })

    it('should apply border-primary-500 bg-primary-50 classes when isDragActive', () => {
      mockIsDragActive = true
      mockIsDragReject = false
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-primary-500', 'bg-primary-50')
    })

    it('should apply border-red-500 bg-red-50 classes when isDragReject', () => {
      mockIsDragActive = false
      mockIsDragReject = true
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-red-500', 'bg-red-50')
    })

    it('should show screen reader message "File is over drop zone. Release to upload." when dragging', () => {
      mockIsDragActive = true
      mockIsDragReject = false
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const status = container.querySelector('#dropzone-status')
      expect(status?.textContent).toBe('File is over drop zone. Release to upload.')
    })

    it('should show screen reader message "Invalid file type detected." when rejected', () => {
      mockIsDragActive = false
      mockIsDragReject = true
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const status = container.querySelector('#dropzone-status')
      expect(status?.textContent).toBe('Invalid file type detected.')
    })
  })

  // ===== FILE SELECTION TESTS (5 tests) =====
  describe('File Selection', () => {
    it('should call onFileSelect when file is dropped', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      // Simulate file drop
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      mockOnDropCallback?.([file])

      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
      expect(mockOnFileSelect).toHaveBeenCalledTimes(1)
    })

    it('should call onFileSelect with first file only (maxFiles: 1)', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      // Simulate multiple files dropped
      const file1 = new File(['content1'], 'test1.jpg', { type: 'image/jpeg' })
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' })
      mockOnDropCallback?.([file1, file2])

      expect(mockOnFileSelect).toHaveBeenCalledWith(file1)
      expect(mockOnFileSelect).toHaveBeenCalledTimes(1)
    })

    it('should accept file when format matches acceptedFormats', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={['jpg', 'png']}
        />
      )

      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
      mockOnDropCallback?.([file])

      expect(mockOnFileSelect).toHaveBeenCalledWith(file)
    })

    it('should configure react-dropzone with maxFiles: 1 and multiple: false', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          maxFiles: 1,
          multiple: false,
        })
      )
    })

    it('should handle file input click', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const input = container.querySelector('input[type="file"]') as HTMLInputElement

      expect(input).toBeInTheDocument()
    })
  })

  // ===== KEYBOARD INTERACTION TESTS (4 tests) =====
  describe('Keyboard Interaction', () => {
    it('should trigger file input on Enter key', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      const input = container.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(input, 'click')

      fireEvent.keyDown(button, { key: 'Enter' })

      expect(clickSpy).toHaveBeenCalled()
    })

    it('should trigger file input on Space key', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      const input = container.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(input, 'click')

      fireEvent.keyDown(button, { key: ' ' })

      expect(clickSpy).toHaveBeenCalled()
    })

    it('should not trigger on other keys', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')
      const input = container.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(input, 'click')

      fireEvent.keyDown(button, { key: 'a' })
      fireEvent.keyDown(button, { key: 'Escape' })

      expect(clickSpy).not.toHaveBeenCalled()
    })

    it('should have focus:ring styles', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-primary-500', 'focus:ring-offset-2')
    })
  })

  // ===== ACCEPTED FORMATS TESTS (4 tests) =====
  describe('Accepted Formats', () => {
    it('should display formats in uppercase', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={['jpg', 'png', 'gif']}
        />
      )

      expect(screen.getByText('Supported formats: JPG, PNG, GIF')).toBeInTheDocument()
    })

    it('should join multiple formats with comma', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="document"
          acceptedFormats={['pdf', 'doc', 'docx', 'txt']}
        />
      )

      expect(screen.getByText('Supported formats: PDF, DOC, DOCX, TXT')).toBeInTheDocument()
    })

    it('should create correct accept object for react-dropzone with image type', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={['jpg', 'png']}
        />
      )

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: {
            'image/*': ['.jpg', '.png'],
          },
        })
      )
    })

    it('should create correct accept object for react-dropzone with video type', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="video"
          acceptedFormats={['mp4', 'avi']}
        />
      )

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: {
            'video/*': ['.mp4', '.avi'],
          },
        })
      )
    })

    it('should create correct accept object for react-dropzone with audio type', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="audio"
          acceptedFormats={['mp3', 'wav']}
        />
      )

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: {
            'audio/*': ['.mp3', '.wav'],
          },
        })
      )
    })

    it('should create correct accept object for react-dropzone with document type', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="document"
          acceptedFormats={['pdf', 'doc']}
        />
      )

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: {
            'application/*,text/*': ['.pdf', '.doc'],
          },
        })
      )
    })

    it('should handle empty acceptedFormats array', () => {
      render(
        <DropZone
          onFileSelect={mockOnFileSelect}
          fileType="image"
          acceptedFormats={[]}
        />
      )

      expect(screen.getByText('All formats supported')).toBeInTheDocument()
    })

    it('should pass undefined accept when no acceptedFormats provided', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          accept: undefined,
        })
      )
    })
  })

  // ===== EDGE CASES TESTS (3 tests) =====
  describe('Edge Cases', () => {
    it('should handle onDrop with empty files array', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      mockOnDropCallback?.([])

      expect(mockOnFileSelect).not.toHaveBeenCalled()
    })

    it('should handle onDrop with multiple files (only select first)', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      const file1 = new File(['content1'], 'test1.jpg', { type: 'image/jpeg' })
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' })
      const file3 = new File(['content3'], 'test3.jpg', { type: 'image/jpeg' })
      mockOnDropCallback?.([file1, file2, file3])

      expect(mockOnFileSelect).toHaveBeenCalledTimes(1)
      expect(mockOnFileSelect).toHaveBeenCalledWith(file1)
    })

    it('should prevent default on keyboard events', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      const enterEvent = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })
      const spaceEvent = new KeyboardEvent('keydown', { key: ' ', bubbles: true })

      const preventDefaultSpy1 = vi.spyOn(enterEvent, 'preventDefault')
      const preventDefaultSpy2 = vi.spyOn(spaceEvent, 'preventDefault')

      fireEvent(button, enterEvent)
      fireEvent(button, spaceEvent)

      expect(preventDefaultSpy1).toHaveBeenCalled()
      expect(preventDefaultSpy2).toHaveBeenCalled()
    })
  })

  // ===== ADDITIONAL COMPREHENSIVE TESTS =====
  describe('Integration and Behavior', () => {
    it('should render with default border-gray-300 when not dragging', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      expect(button).toHaveClass('border-gray-300')
    })

    it('should have cursor-pointer class', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      expect(button).toHaveClass('cursor-pointer')
    })

    it('should have transition-colors class for smooth animations', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      expect(button).toHaveClass('transition-colors', 'duration-200')
    })

    it('should have proper border-dashed and rounded-lg styling', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const button = screen.getByRole('button')

      expect(button).toHaveClass('border-2', 'border-dashed', 'rounded-lg')
    })

    it('should call useDropzone with onDrop callback', () => {
      render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)

      expect(useDropzone).toHaveBeenCalledWith(
        expect.objectContaining({
          onDrop: expect.any(Function),
        })
      )
    })

    it('should have dropzone-hint id on instruction paragraph', () => {
      const { container } = render(<DropZone onFileSelect={mockOnFileSelect} fileType="image" />)
      const hint = container.querySelector('#dropzone-hint')

      expect(hint).toBeInTheDocument()
      expect(hint?.textContent).toContain('Drag & drop a image file here')
    })
  })
})
