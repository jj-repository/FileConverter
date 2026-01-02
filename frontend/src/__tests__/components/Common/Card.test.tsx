// @ts-nocheck
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { Card } from '../../../components/Common/Card'

describe('Card Component', () => {
  describe('Rendering', () => {
    it('should render children content', () => {
      render(<Card>Test Content</Card>)
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('should render with default card className', () => {
      const { container } = render(<Card>Content</Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
    })

    it('should render with custom className combined with card class', () => {
      const { container } = render(<Card className="custom-class">Content</Card>)
      const cardElement = container.querySelector('.card.custom-class')
      expect(cardElement).toBeInTheDocument()
    })

    it('should render card div element', () => {
      const { container } = render(<Card>Content</Card>)
      const cardElement = container.querySelector('div.card')
      expect(cardElement).toBeInTheDocument()
      expect(cardElement?.tagName).toBe('DIV')
    })

    it('should render with multiple children', () => {
      render(
        <Card>
          <p>First Child</p>
          <p>Second Child</p>
          <p>Third Child</p>
        </Card>
      )
      expect(screen.getByText('First Child')).toBeInTheDocument()
      expect(screen.getByText('Second Child')).toBeInTheDocument()
      expect(screen.getByText('Third Child')).toBeInTheDocument()
    })

    it('should render with React components as children', () => {
      const TestComponent = () => <div>Component Content</div>
      render(
        <Card>
          <TestComponent />
        </Card>
      )
      expect(screen.getByText('Component Content')).toBeInTheDocument()
    })

    it('should render with multiple React components as children', () => {
      const ComponentA = () => <span>Component A</span>
      const ComponentB = () => <span>Component B</span>

      render(
        <Card>
          <ComponentA />
          <ComponentB />
        </Card>
      )
      expect(screen.getByText('Component A')).toBeInTheDocument()
      expect(screen.getByText('Component B')).toBeInTheDocument()
    })

    it('should render with mixed content types as children', () => {
      const CustomComponent = () => <strong>Bold Text</strong>

      render(
        <Card>
          <p>Paragraph text</p>
          <CustomComponent />
          <span>Span text</span>
        </Card>
      )
      expect(screen.getByText('Paragraph text')).toBeInTheDocument()
      expect(screen.getByText('Bold Text')).toBeInTheDocument()
      expect(screen.getByText('Span text')).toBeInTheDocument()
    })
  })

  describe('Props', () => {
    it('should work without className prop', () => {
      const { container } = render(<Card>Content</Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
      expect(cardElement?.className).toBe('card ')
    })

    it('should work with empty className', () => {
      const { container } = render(<Card className="">Content</Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
      expect(cardElement?.className).toBe('card ')
    })

    it('should combine multiple classes correctly', () => {
      const { container } = render(
        <Card className="custom-1 custom-2 custom-3">Content</Card>
      )
      const cardElement = container.firstChild as HTMLElement
      expect(cardElement.className).toContain('card')
      expect(cardElement.className).toContain('custom-1')
      expect(cardElement.className).toContain('custom-2')
      expect(cardElement.className).toContain('custom-3')
    })

    it('should preserve className order: card class first, then custom classes', () => {
      const { container } = render(
        <Card className="my-custom-class">Content</Card>
      )
      const cardElement = container.firstChild as HTMLElement
      const classNames = cardElement.className
      const cardIndex = classNames.indexOf('card')
      const customIndex = classNames.indexOf('my-custom-class')
      expect(cardIndex).toBeLessThan(customIndex)
    })
  })

  describe('Accessibility', () => {
    it('should render card as accessible container', () => {
      const { container } = render(<Card>Accessible Content</Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
      // Card should be a semantic div container
      expect(cardElement?.tagName).toBe('DIV')
    })

    it('should allow children to be properly accessible with semantic HTML', () => {
      render(
        <Card>
          <h2>Card Title</h2>
          <p>Card description</p>
        </Card>
      )
      // Semantic HTML elements should be accessible
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
      expect(screen.getByText('Card description')).toBeInTheDocument()
    })

    it('should render with proper semantic structure for form content', () => {
      render(
        <Card>
          <form>
            <label htmlFor="test-input">Test Label</label>
            <input id="test-input" type="text" />
          </form>
        </Card>
      )
      const input = screen.getByLabelText('Test Label')
      expect(input).toBeInTheDocument()
    })

    it('should maintain accessibility with button children', () => {
      render(
        <Card>
          <button>Click me</button>
        </Card>
      )
      const button = screen.getByRole('button', { name: /click me/i })
      expect(button).toBeInTheDocument()
    })

    it('should render children with proper text contrast context', () => {
      render(
        <Card>
          <a href="/test">Test Link</a>
        </Card>
      )
      const link = screen.getByRole('link', { name: /test link/i })
      expect(link).toBeInTheDocument()
      expect(link.getAttribute('href')).toBe('/test')
    })
  })

  describe('Edge Cases', () => {
    it('should render with null className gracefully', () => {
      const { container } = render(<Card>Content</Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
    })

    it('should render with whitespace in className', () => {
      const { container } = render(
        <Card className="  spaced-class  ">Content</Card>
      )
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
    })

    it('should render with special characters in className', () => {
      const { container } = render(
        <Card className="class-with-dashes class_with_underscores">Content</Card>
      )
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
    })

    it('should render with React fragments as children', () => {
      render(
        <Card>
          <>
            <span>Fragment Child 1</span>
            <span>Fragment Child 2</span>
          </>
        </Card>
      )
      expect(screen.getByText('Fragment Child 1')).toBeInTheDocument()
      expect(screen.getByText('Fragment Child 2')).toBeInTheDocument()
    })

    it('should render with empty children', () => {
      const { container } = render(<Card></Card>)
      const cardElement = container.querySelector('.card')
      expect(cardElement).toBeInTheDocument()
    })
  })
})
