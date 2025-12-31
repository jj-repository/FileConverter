import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TabNavigation } from '../../../components/Layout/TabNavigation'
import { FileType } from '../../../types/conversion'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key, // Return the key as-is for testing
  }),
}))

describe('TabNavigation', () => {
  const mockOnTabChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ============================================================================
  // RENDERING TESTS (12 tests)
  // ============================================================================

  describe('Rendering', () => {
    it('should render nav element with aria-label="Tabs"', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const nav = screen.getByRole('navigation', { name: 'Tabs' })
      expect(nav).toBeInTheDocument()
    })

    it('should render all 11 tabs', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')
      expect(buttons).toHaveLength(11)
    })

    it('should render image tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })
      expect(imageButton).toHaveTextContent('🖼️')
    })

    it('should render video tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveTextContent('🎥')
    })

    it('should render audio tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const audioButton = screen.getByRole('button', { name: /nav.audio/ })
      expect(audioButton).toHaveTextContent('🎵')
    })

    it('should render document tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const documentButton = screen.getByRole('button', { name: /nav.documents/ })
      expect(documentButton).toHaveTextContent('📄')
    })

    it('should render batch tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const batchButton = screen.getByRole('button', { name: /nav.batch/ })
      expect(batchButton).toHaveTextContent('📦')
    })

    it('should render data tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const dataButton = screen.getByRole('button', { name: /nav.data/ })
      expect(dataButton).toHaveTextContent('📊')
    })

    it('should render archive tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const archiveButton = screen.getByRole('button', { name: /nav.archives/ })
      expect(archiveButton).toHaveTextContent('🗜️')
    })

    it('should render spreadsheet tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const spreadsheetButton = screen.getByRole('button', { name: /nav.spreadsheets/ })
      expect(spreadsheetButton).toHaveTextContent('📈')
    })

    it('should render subtitle tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const subtitleButton = screen.getByRole('button', { name: /nav.subtitles/ })
      expect(subtitleButton).toHaveTextContent('💬')
    })

    it('should render ebook tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const ebookButton = screen.getByRole('button', { name: /nav.ebooks/ })
      expect(ebookButton).toHaveTextContent('📚')
    })

    it('should render font tab icon correctly', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const fontButton = screen.getByRole('button', { name: /nav.fonts/ })
      expect(fontButton).toHaveTextContent('🔤')
    })
  })

  // ============================================================================
  // TAB CONTENT TESTS (11 tests)
  // ============================================================================

  describe('Tab Content', () => {
    it('should display translation key for image tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.images')).toBeInTheDocument()
    })

    it('should display translation key for video tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.videos')).toBeInTheDocument()
    })

    it('should display translation key for audio tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.audio')).toBeInTheDocument()
    })

    it('should display translation key for document tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.documents')).toBeInTheDocument()
    })

    it('should display translation key for batch tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.batch')).toBeInTheDocument()
    })

    it('should display translation key for data tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.data')).toBeInTheDocument()
    })

    it('should display translation key for archive tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.archives')).toBeInTheDocument()
    })

    it('should display translation key for spreadsheet tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.spreadsheets')).toBeInTheDocument()
    })

    it('should display translation key for subtitle tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.subtitles')).toBeInTheDocument()
    })

    it('should display translation key for ebook tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.ebooks')).toBeInTheDocument()
    })

    it('should display translation key for font tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      expect(screen.getByText('nav.fonts')).toBeInTheDocument()
    })
  })

  // ============================================================================
  // ACTIVE TAB STYLING TESTS (6 tests)
  // ============================================================================

  describe('Active Tab Styling', () => {
    it('should apply border-primary-600 to active tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })
      expect(imageButton).toHaveClass('border-primary-600')
    })

    it('should apply text-primary-600 to active tab', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })
      expect(imageButton).toHaveClass('text-primary-600')
    })

    it('should apply active styles when activeTab="image"', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })
      expect(imageButton).toHaveClass('border-primary-600', 'text-primary-600')
    })

    it('should apply active styles when activeTab="video"', () => {
      render(<TabNavigation activeTab="video" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('border-primary-600', 'text-primary-600')
    })

    it('should apply active styles when activeTab changes', () => {
      const { rerender } = render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)

      let imageButton = screen.getByRole('button', { name: /nav.images/ })
      let videoButton = screen.getByRole('button', { name: /nav.videos/ })

      expect(imageButton).toHaveClass('border-primary-600', 'text-primary-600')
      expect(videoButton).not.toHaveClass('border-primary-600', 'text-primary-600')

      rerender(<TabNavigation activeTab="video" onTabChange={mockOnTabChange} />)

      imageButton = screen.getByRole('button', { name: /nav.images/ })
      videoButton = screen.getByRole('button', { name: /nav.videos/ })

      expect(imageButton).not.toHaveClass('border-primary-600', 'text-primary-600')
      expect(videoButton).toHaveClass('border-primary-600', 'text-primary-600')
    })

    it('should NOT apply active styles to inactive tabs', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      const audioButton = screen.getByRole('button', { name: /nav.audio/ })

      expect(videoButton).not.toHaveClass('border-primary-600')
      expect(videoButton).not.toHaveClass('text-primary-600')
      expect(audioButton).not.toHaveClass('border-primary-600')
      expect(audioButton).not.toHaveClass('text-primary-600')
    })
  })

  // ============================================================================
  // INACTIVE TAB STYLING TESTS (5 tests)
  // ============================================================================

  describe('Inactive Tab Styling', () => {
    it('should apply border-transparent to inactive tabs', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('border-transparent')
    })

    it('should apply text-gray-500 to inactive tabs', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('text-gray-500')
    })

    it('should have hover:text-gray-700 class', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('hover:text-gray-700')
    })

    it('should have hover:border-gray-300 class', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('hover:border-gray-300')
    })

    it('should have transition-colors class', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      expect(videoButton).toHaveClass('transition-colors')
    })
  })

  // ============================================================================
  // CLICK HANDLER TESTS (11 tests)
  // ============================================================================

  describe('Click Handlers', () => {
    it('should call onTabChange with "image" when image tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="video" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })

      await user.click(imageButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('image')
    })

    it('should call onTabChange with "video" when video tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })

      await user.click(videoButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('video')
    })

    it('should call onTabChange with "audio" when audio tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const audioButton = screen.getByRole('button', { name: /nav.audio/ })

      await user.click(audioButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('audio')
    })

    it('should call onTabChange with "document" when document tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const documentButton = screen.getByRole('button', { name: /nav.documents/ })

      await user.click(documentButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('document')
    })

    it('should call onTabChange with "batch" when batch tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const batchButton = screen.getByRole('button', { name: /nav.batch/ })

      await user.click(batchButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('batch')
    })

    it('should call onTabChange with "data" when data tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const dataButton = screen.getByRole('button', { name: /nav.data/ })

      await user.click(dataButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('data')
    })

    it('should call onTabChange with "archive" when archive tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const archiveButton = screen.getByRole('button', { name: /nav.archives/ })

      await user.click(archiveButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('archive')
    })

    it('should call onTabChange with "spreadsheet" when spreadsheet tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const spreadsheetButton = screen.getByRole('button', { name: /nav.spreadsheets/ })

      await user.click(spreadsheetButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('spreadsheet')
    })

    it('should call onTabChange with "subtitle" when subtitle tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const subtitleButton = screen.getByRole('button', { name: /nav.subtitles/ })

      await user.click(subtitleButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('subtitle')
    })

    it('should call onTabChange with "ebook" when ebook tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const ebookButton = screen.getByRole('button', { name: /nav.ebooks/ })

      await user.click(ebookButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('ebook')
    })

    it('should call onTabChange with "font" when font tab clicked', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const fontButton = screen.getByRole('button', { name: /nav.fonts/ })

      await user.click(fontButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(1)
      expect(mockOnTabChange).toHaveBeenCalledWith('font')
    })
  })

  // ============================================================================
  // ACCESSIBILITY TESTS (5 tests)
  // ============================================================================

  describe('Accessibility', () => {
    it('should have aria-label="Tabs" on nav', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const nav = screen.getByRole('navigation', { name: 'Tabs' })
      expect(nav).toHaveAttribute('aria-label', 'Tabs')
    })

    it('should render all tabs as buttons', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      buttons.forEach(button => {
        expect(button.tagName).toBe('BUTTON')
      })
    })

    it('should have proper button structure for screen readers', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const imageButton = screen.getByRole('button', { name: /nav.images/ })

      // Button should contain both icon and text
      expect(imageButton).toHaveTextContent('🖼️')
      expect(imageButton).toHaveTextContent('nav.images')
    })

    it('should have whitespace-nowrap for text wrapping', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      buttons.forEach(button => {
        expect(button).toHaveClass('whitespace-nowrap')
      })
    })

    it('should maintain tab order in DOM', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      const expectedOrder = [
        'nav.images', 'nav.videos', 'nav.audio', 'nav.documents', 'nav.batch',
        'nav.data', 'nav.archives', 'nav.spreadsheets', 'nav.subtitles',
        'nav.ebooks', 'nav.fonts'
      ]

      buttons.forEach((button, index) => {
        expect(button).toHaveTextContent(expectedOrder[index])
      })
    })
  })

  // ============================================================================
  // STYLING AND LAYOUT TESTS (4 tests)
  // ============================================================================

  describe('Styling and Layout', () => {
    it('should have flex layout with space-x-8', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const nav = screen.getByRole('navigation', { name: 'Tabs' })
      expect(nav).toHaveClass('flex', 'space-x-8')
    })

    it('should have py-4 px-1 padding on buttons', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      buttons.forEach(button => {
        expect(button).toHaveClass('py-4', 'px-1')
      })
    })

    it('should have border-b-2 on buttons', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      buttons.forEach(button => {
        expect(button).toHaveClass('border-b-2')
      })
    })

    it('should have font-medium text-sm classes', () => {
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)
      const buttons = screen.getAllByRole('button')

      buttons.forEach(button => {
        expect(button).toHaveClass('font-medium', 'text-sm')
      })
    })
  })

  // ============================================================================
  // EDGE CASES TESTS (3 tests)
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle rapid tab switching', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)

      const imageButton = screen.getByRole('button', { name: /nav.images/ })
      const videoButton = screen.getByRole('button', { name: /nav.videos/ })
      const audioButton = screen.getByRole('button', { name: /nav.audio/ })

      await user.click(videoButton)
      await user.click(audioButton)
      await user.click(imageButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(3)
      expect(mockOnTabChange).toHaveBeenNthCalledWith(1, 'video')
      expect(mockOnTabChange).toHaveBeenNthCalledWith(2, 'audio')
      expect(mockOnTabChange).toHaveBeenNthCalledWith(3, 'image')
    })

    it('should handle same tab clicked twice', async () => {
      const user = userEvent.setup()
      render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)

      const imageButton = screen.getByRole('button', { name: /nav.images/ })

      await user.click(imageButton)
      await user.click(imageButton)

      expect(mockOnTabChange).toHaveBeenCalledTimes(2)
      expect(mockOnTabChange).toHaveBeenNthCalledWith(1, 'image')
      expect(mockOnTabChange).toHaveBeenNthCalledWith(2, 'image')
    })

    it('should maintain styling when activeTab prop changes', () => {
      const { rerender } = render(<TabNavigation activeTab="image" onTabChange={mockOnTabChange} />)

      const allTabs: FileType[] = [
        'image', 'video', 'audio', 'document', 'batch', 'data',
        'archive', 'spreadsheet', 'subtitle', 'ebook', 'font'
      ]

      allTabs.forEach(tab => {
        rerender(<TabNavigation activeTab={tab} onTabChange={mockOnTabChange} />)
        const buttons = screen.getAllByRole('button')

        buttons.forEach(button => {
          // All buttons should maintain base styling classes
          expect(button).toHaveClass('py-4', 'px-1', 'border-b-2', 'font-medium', 'text-sm', 'transition-colors', 'whitespace-nowrap')
        })
      })
    })
  })
})
