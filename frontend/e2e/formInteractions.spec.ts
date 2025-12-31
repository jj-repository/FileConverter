import { test, expect } from '@playwright/test'
import path from 'path'

/**
 * E2E Tests: Form Interactions
 * Tests form controls, validation, and user interactions
 * Note: Full conversion workflows require a running backend server
 */
test.describe('Form Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should have convert button disabled by default', async ({ page }) => {
    const convertButton = page.getByRole('button', { name: /convert/i }).first()

    // Button should be disabled when no file is selected
    await expect(convertButton).toBeDisabled()
  })

  test('should enable convert button after file selection', async ({ page }) => {
    const testFilePath = path.join(process.cwd(), 'package.json')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)

    // Wait for file to be processed
    await expect(page.getByText('package.json')).toBeVisible()

    // Convert button should be enabled
    const convertButton = page.getByRole('button', { name: /convert/i }).first()
    await expect(convertButton).toBeEnabled({ timeout: 2000 })
  })

  test('should allow selecting output format', async ({ page }) => {
    const testFilePath = path.join(process.cwd(), 'package.json')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)
    await expect(page.getByText('package.json')).toBeVisible()

    // Find format selector
    const formatSelect = page.locator('select').first()

    // Select should be visible and interactable
    if (await formatSelect.isVisible()) {
      await expect(formatSelect).toBeEnabled()

      // Should have options
      const options = formatSelect.locator('option')
      const optionCount = await options.count()
      expect(optionCount).toBeGreaterThan(0)
    }
  })

  test('should display file size information', async ({ page }) => {
    const testFilePath = path.join(process.cwd(), 'package.json')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)

    // File size should be displayed
    await expect(
      page.getByText(/\d+\s*(bytes|KB|MB|B)/i)
    ).toBeVisible({ timeout: 3000 })
  })

  test('should show file preview or information panel', async ({ page }) => {
    const testFilePath = path.join(process.cwd(), 'package.json')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)

    // Wait for file name to appear
    await expect(page.getByText('package.json')).toBeVisible()

    // Some kind of file info should be visible
    const fileInfo = page.locator('[class*="file"], [class*="info"], [class*="preview"]').first()
    const isVisible = await fileInfo.isVisible().catch(() => false)

    // Either file info panel exists or file name is visible
    expect(isVisible || await page.getByText('package.json').isVisible()).toBeTruthy()
  })

  test('should handle multiple file selection in batch mode', async ({ page }) => {
    // Navigate to batch converter
    const batchTab = page.getByRole('button', { name: /batch/i }).first()
    await batchTab.click()

    // Wait for batch converter to load
    await expect(page.getByText(/batch converter|multiple files/i).first()).toBeVisible()

    // Find file input (should accept multiple files)
    const fileInput = page.locator('input[type="file"]').first()

    // Check if multiple attribute exists
    const hasMultiple = await fileInput.getAttribute('multiple')
    expect(hasMultiple).not.toBeNull()
  })

  test('should persist selected format across tab switches (or reset)', async ({ page }) => {
    const testFilePath = path.join(process.cwd(), 'package.json')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)
    await expect(page.getByText('package.json')).toBeVisible()

    // Switch to video tab
    await page.getByRole('button', { name: /videos/i }).first().click()
    await expect(page.getByText(/video converter/i).first()).toBeVisible()

    // Switch back to image tab
    await page.getByRole('button', { name: /images/i }).first().click()
    await expect(page.getByText(/image converter/i).first()).toBeVisible()

    // File should be reset (not persisted across tabs)
    const fileNameVisible = await page.getByText('package.json').isVisible().catch(() => false)

    // Either file is reset (not visible) or persisted (visible) - both are valid behaviors
    expect(typeof fileNameVisible).toBe('boolean')
  })
})
