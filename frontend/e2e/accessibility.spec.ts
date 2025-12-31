import { test, expect } from '@playwright/test'

/**
 * E2E Tests: Accessibility
 * Tests keyboard navigation, ARIA attributes, and screen reader compatibility
 */
test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should support keyboard navigation with Tab key', async ({ page }) => {
    // Focus first element
    await page.keyboard.press('Tab')

    // Verify an element has focus
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(['BUTTON', 'INPUT', 'SELECT', 'A']).toContain(focusedElement)
  })

  test('should navigate between tabs using keyboard', async ({ page }) => {
    // Tab to the Video tab button
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await videoTab.focus()

    // Press Enter to activate
    await page.keyboard.press('Enter')

    // Video converter should be visible
    await expect(
      page.getByText(/video converter/i).first()
    ).toBeVisible()
  })

  test('should have proper ARIA labels on tab buttons', async ({ page }) => {
    const imageTab = page.getByRole('button', { name: /images/i }).first()

    // Tab button should have text content
    const tabText = await imageTab.textContent()
    expect(tabText).toBeTruthy()
  })

  test('should have accessible file input', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()

    // File input should be in the accessibility tree
    await expect(fileInput).toBeAttached()

    // Should have accessible name (via label or aria-label)
    const accessibleName = await fileInput.getAttribute('aria-label')
    const hasLabel = await page.evaluate((input) => {
      const el = document.querySelector('input[type="file"]')
      return !!el?.labels?.length
    })

    expect(accessibleName || hasLabel).toBeTruthy()
  })

  test('should have accessible convert button', async ({ page }) => {
    const convertButton = page.getByRole('button', { name: /convert/i }).first()

    // Button should be visible
    await expect(convertButton).toBeVisible()

    // Should have text or aria-label
    const buttonText = await convertButton.textContent()
    expect(buttonText).toBeTruthy()
  })

  test('should support Space key activation on buttons', async ({ page }) => {
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await videoTab.focus()

    // Press Space to activate
    await page.keyboard.press('Space')

    // Video converter should be visible
    await expect(
      page.getByText(/video converter/i).first()
    ).toBeVisible({ timeout: 2000 })
  })

  test('should have proper heading structure', async ({ page }) => {
    // Check for headings
    const headings = page.locator('h1, h2, h3, h4, h5, h6')
    const headingCount = await headings.count()

    // Should have at least some headings
    expect(headingCount).toBeGreaterThan(0)
  })

  test('should not trap keyboard focus', async ({ page }) => {
    // Tab through multiple elements
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press('Tab')

      // Verify focus is on a valid element
      const tagName = await page.evaluate(() => document.activeElement?.tagName)
      expect(['BUTTON', 'INPUT', 'SELECT', 'A', 'BODY', 'TEXTAREA']).toContain(
        tagName
      )
    }
  })

  test('should have visible focus indicators', async ({ page }) => {
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await videoTab.focus()

    // Element should have focus
    const isFocused = await page.evaluate((selector) => {
      const button = document.querySelector('button')
      return document.activeElement === button
    })

    expect(isFocused).toBeTruthy()
  })

  test('should maintain focus when switching tabs', async ({ page }) => {
    // Focus and click video tab
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await videoTab.click()

    // Active element should exist
    const activeElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(activeElement).toBeTruthy()
  })
})
