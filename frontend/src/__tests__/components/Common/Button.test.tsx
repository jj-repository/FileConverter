import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../../../components/Common/Button'

describe('Button Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render children text', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByText('Click me')).toBeInTheDocument()
    })

    it('should render with primary variant by default', () => {
      const { container } = render(<Button>Primary Button</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveClass('btn')
      expect(button).toHaveClass('btn-primary')
    })

    it('should render with primary variant explicitly', () => {
      const { container } = render(<Button variant="primary">Primary Button</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveClass('btn-primary')
    })

    it('should render with secondary variant', () => {
      const { container } = render(<Button variant="secondary">Secondary Button</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveClass('btn')
      expect(button).toHaveClass('btn-secondary')
    })

    it('should render with custom className', () => {
      const { container } = render(
        <Button className="custom-class">Styled Button</Button>
      )
      const button = container.querySelector('button')
      expect(button).toHaveClass('btn')
      expect(button).toHaveClass('btn-primary')
      expect(button).toHaveClass('custom-class')
    })

    it('should render with both variant and custom className', () => {
      const { container } = render(
        <Button variant="secondary" className="extra-styles">
          Fancy Button
        </Button>
      )
      const button = container.querySelector('button')
      expect(button).toHaveClass('btn')
      expect(button).toHaveClass('btn-secondary')
      expect(button).toHaveClass('extra-styles')
    })

    it('should support multiple children elements', () => {
      render(
        <Button>
          <span>Icon</span>
          <span>Text</span>
        </Button>
      )
      expect(screen.getByText('Icon')).toBeInTheDocument()
      expect(screen.getByText('Text')).toBeInTheDocument()
    })
  })

  describe('Interaction', () => {
    it('should call onClick when clicked', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click me</Button>)

      const button = screen.getByRole('button', { name: 'Click me' })
      const user = userEvent.setup()
      await user.click(button)

      expect(handleClick).toHaveBeenCalledOnce()
    })

    it('should not call onClick when disabled prop is true', async () => {
      const handleClick = vi.fn()
      render(
        <Button onClick={handleClick} disabled>
          Click me
        </Button>
      )

      const button = screen.getByRole('button', { name: 'Click me' })
      const user = userEvent.setup()
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('should not call onClick when loading is true', async () => {
      const handleClick = vi.fn()
      render(
        <Button onClick={handleClick} loading>
          Click me
        </Button>
      )

      const button = screen.getByRole('button')
      const user = userEvent.setup()
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('should be keyboard accessible', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Press me</Button>)

      const button = screen.getByRole('button', { name: 'Press me' })
      const user = userEvent.setup()

      // Simulate pressing Enter key
      await user.tab()
      await user.keyboard('{Enter}')

      expect(handleClick).toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('should show spinner SVG when loading is true', () => {
      const { container } = render(<Button loading>Loading</Button>)
      const spinner = container.querySelector('svg')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveClass('animate-spin')
    })

    it('should show "Processing..." text when loading is true', () => {
      render(<Button loading>Button</Button>)
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    it('should not show children text when loading is true', () => {
      render(<Button loading>Button Text</Button>)
      expect(screen.queryByText('Button Text')).not.toBeInTheDocument()
    })

    it('should display spinner and Processing text together', () => {
      const { container } = render(<Button loading>Submit</Button>)
      const spinner = container.querySelector('svg')
      const processingText = screen.getByText('Processing...')

      expect(spinner).toBeInTheDocument()
      expect(processingText).toBeInTheDocument()

      // Both should be in the same span with flex layout
      const flexSpan = spinner?.parentElement
      expect(flexSpan).toHaveClass('flex')
      expect(flexSpan).toHaveClass('items-center')
      expect(flexSpan).toHaveClass('gap-2')
    })

    it('should be disabled when loading is true', () => {
      render(<Button loading>Loading</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should have aria-busy attribute set to true when loading', () => {
      render(<Button loading>Loading</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-busy', 'true')
    })

    it('should have aria-busy attribute set to false when not loading', () => {
      render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-busy', 'false')
    })
  })

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should have aria-disabled attribute set to true when disabled', () => {
      render(<Button disabled>Disabled Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'true')
    })

    it('should have aria-disabled attribute set to false when not disabled', () => {
      render(<Button>Enabled Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'false')
    })

    it('should show different visual state when disabled', () => {
      const { container } = render(<Button disabled>Disabled Button</Button>)
      const button = container.querySelector('button')
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('disabled')
    })

    it('should be disabled when both disabled and loading are true', () => {
      render(
        <Button disabled loading>
          Disabled Loading
        </Button>
      )
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria-disabled attribute', () => {
      const { rerender } = render(<Button>Enabled</Button>)
      let button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'false')

      rerender(<Button disabled>Disabled</Button>)
      button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'true')
    })

    it('should have proper aria-busy attribute', () => {
      const { rerender } = render(<Button>Not Loading</Button>)
      let button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-busy', 'false')

      rerender(<Button loading>Loading</Button>)
      button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-busy', 'true')
    })

    it('should have aria-hidden on spinner SVG', () => {
      const { container } = render(<Button loading>Loading</Button>)
      const spinner = container.querySelector('svg')
      expect(spinner).toHaveAttribute('aria-hidden', 'true')
    })

    it('should be keyboard accessible with Tab key', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Press Tab</Button>)

      const button = screen.getByRole('button')
      const user = userEvent.setup()

      // Tab to the button
      await user.tab()
      expect(button).toHaveFocus()
    })

    it('should activate on Space key', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Press Space</Button>)

      const button = screen.getByRole('button')
      const user = userEvent.setup()

      await user.tab()
      await user.keyboard(' ')

      expect(handleClick).toHaveBeenCalled()
    })

    it('should maintain semantic HTML structure', () => {
      const { container } = render(
        <Button variant="primary" className="test-class">
          Semantic Button
        </Button>
      )

      const button = container.querySelector('button')
      expect(button?.tagName).toBe('BUTTON')
      expect(button).toBeInTheDocument()
    })

    it('should have accessible role when rendering as button', () => {
      render(<Button>Accessible Button</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })
  })

  describe('HTML Attributes', () => {
    it('should spread additional props to button element', () => {
      const { container } = render(
        <Button data-testid="custom-button" title="Test Title">
          Test
        </Button>
      )

      const button = container.querySelector('[data-testid="custom-button"]')
      expect(button).toHaveAttribute('title', 'Test Title')
    })

    it('should support type attribute', () => {
      const { container } = render(<Button type="submit">Submit</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveAttribute('type', 'submit')
    })

    it('should support name attribute', () => {
      const { container } = render(<Button name="action-button">Click</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveAttribute('name', 'action-button')
    })

    it('should support id attribute', () => {
      const { container } = render(<Button id="submit-button">Submit</Button>)
      const button = container.querySelector('button')
      expect(button).toHaveAttribute('id', 'submit-button')
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty children', () => {
      const { container } = render(<Button />)
      const button = container.querySelector('button')
      expect(button).toBeInTheDocument()
    })

    it('should render with both variant and loading state', () => {
      render(<Button variant="secondary" loading>Button</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('btn-secondary')
      expect(button).toHaveAttribute('aria-busy', 'true')
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    it('should handle className with multiple classes', () => {
      const { container } = render(
        <Button className="class1 class2 class3">Multi Class</Button>
      )
      const button = container.querySelector('button')
      expect(button).toHaveClass('class1')
      expect(button).toHaveClass('class2')
      expect(button).toHaveClass('class3')
    })

    it('should properly toggle loading state on rerender', () => {
      const { rerender } = render(<Button>Not Loading</Button>)
      expect(screen.queryByText('Processing...')).not.toBeInTheDocument()

      rerender(<Button loading>Loading</Button>)
      expect(screen.getByText('Processing...')).toBeInTheDocument()

      rerender(<Button>Not Loading</Button>)
      expect(screen.queryByText('Processing...')).not.toBeInTheDocument()
    })

    it('should handle rapid click events when not disabled', async () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Rapid Click</Button>)

      const button = screen.getByRole('button')
      const user = userEvent.setup()

      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(3)
    })
  })
})
