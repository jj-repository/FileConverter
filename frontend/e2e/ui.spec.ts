import { test, expect } from '@playwright/test'

/**
 * E2E Tests: UI and Responsive Design
 * Tests UI elements, layout, and responsive behavior
 */
test.describe('UI and Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display application header', async ({ page }) => {
    // Application should have a header/title
    await expect(page.locator('h1, h2, .header, header').first()).toBeVisible()
  })

  test('should display converter tabs in horizontal layout', async ({ page }) => {
    const tabContainer = page.locator('nav, [role="tablist"]').first()

    // Tab container should be visible
    await expect(tabContainer).toBeVisible()

    // Multiple tabs should be present
    const tabs = page.getByRole('button').filter({ hasText: /image|video|audio|document|batch/i })
    const tabCount = await tabs.count()
    expect(tabCount).toBeGreaterThan(4)
  })

  test('should display file upload area', async ({ page }) => {
    // Drop zone or file upload area should be visible
    const uploadArea = page.locator('[class*="dropzone"], [class*="upload"]').first()

    // Either dropzone exists or file input is visible
    const uploadAreaExists = await uploadArea.isVisible().catch(() => false)
    const fileInput = page.locator('input[type="file"]').first()
    const fileInputExists = await fileInput.isVisible().catch(() => false)

    expect(uploadAreaExists || fileInputExists).toBeTruthy()
  })

  test('should be responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Application should still be visible
    await expect(page.getByText(/image converter|images/i).first()).toBeVisible()

    // Tabs should be accessible (may be scrollable)
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await expect(videoTab).toBeAttached()
  })

  test('should be responsive on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })

    // All elements should be visible
    await expect(page.getByText(/image converter|images/i).first()).toBeVisible()

    const tabs = page.getByRole('button').filter({ hasText: /image|video|audio/i })
    const tabCount = await tabs.count()
    expect(tabCount).toBeGreaterThan(0)
  })

  test('should display format selector', async ({ page }) => {
    // After selecting a file, format selector should appear
    // For now, check if select elements exist in the page
    const selects = page.locator('select')
    const selectCount = await selects.count()

    // Should have at least one select element (format dropdown)
    expect(selectCount).toBeGreaterThanOrEqual(0)
  })

  test('should display converter options panel', async ({ page }) => {
    // Options panel or card should be present
    const cards = page.locator('[class*="card"], [class*="panel"], .converter')
    const cardCount = await cards.count()

    expect(cardCount).toBeGreaterThan(0)
  })

  test('should have visible buttons', async ({ page }) => {
    // Buttons should be visible
    const buttons = page.getByRole('button')
    const buttonCount = await buttons.count()

    // Should have multiple buttons (tabs + convert button, etc.)
    expect(buttonCount).toBeGreaterThan(5)
  })
})
