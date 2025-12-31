import { test, expect } from '@playwright/test'
import path from 'path'

/**
 * E2E Tests: File Upload Interactions
 * Tests file selection and upload UI interactions
 * Note: Full conversion testing requires a running backend
 */
test.describe('File Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display file input element', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]').first()
    await expect(fileInput).toBeAttached()
  })

  test('should allow selecting a file via file input', async ({ page }) => {
    // Use test image file
    const testFilePath = path.join(__dirname, 'fixtures', 'test-image.png')

    // Get the file input
    const fileInput = page.locator('input[type="file"]').first()

    // Set files on the input
    await fileInput.setInputFiles(testFilePath)

    // Verify file was selected (filename should appear in UI)
    await expect(page.getByText('test-image.png')).toBeVisible({ timeout: 10000 })
  })

  test('should display file information after selection', async ({ page }) => {
    const testFilePath = path.join(__dirname, 'fixtures', 'test-image.png')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)

    // File name should be visible
    await expect(page.getByText('test-image.png')).toBeVisible({ timeout: 10000 })

    // File size should be displayed (in some format)
    await expect(
      page.getByText(/\d+\s*(bytes|KB|MB|B)/i)
    ).toBeVisible({ timeout: 5000 })
  })

  test('should enable convert button after file selection', async ({ page }) => {
    const testFilePath = path.join(__dirname, 'fixtures', 'test-image.png')
    const fileInput = page.locator('input[type="file"]').first()

    // Select file
    await fileInput.setInputFiles(testFilePath)

    // Wait for file to be processed
    await expect(page.getByText('test-image.png')).toBeVisible({ timeout: 10000 })

    // Convert button should now be enabled (look for any button with "convert" text)
    const convertButton = page.locator('button').filter({ hasText: /convert/i }).first()
    await expect(convertButton).toBeEnabled({ timeout: 5000 })
  })

  test('should show format selector after file upload', async ({ page }) => {
    const testFilePath = path.join(__dirname, 'fixtures', 'test-image.png')
    const fileInput = page.locator('input[type="file"]').first()

    await fileInput.setInputFiles(testFilePath)

    // Wait for file to be selected
    await expect(page.getByText('test-image.png')).toBeVisible({ timeout: 10000 })

    // Format selector should be visible
    const formatSelect = page.locator('select').first()
    await expect(formatSelect).toBeVisible({ timeout: 5000 })
  })
})
