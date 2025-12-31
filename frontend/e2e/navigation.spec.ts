import { test, expect } from '@playwright/test'

/**
 * E2E Tests: Navigation and Tab Switching
 * Tests basic navigation between different converter tabs
 */
test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should load the home page with Image converter by default', async ({
    page,
  }) => {
    // Check that page loaded
    await expect(page).toHaveTitle(/FileConverter/i)

    // Image tab should be active by default
    const imageTab = page.getByRole('button', { name: /images/i }).first()
    await expect(imageTab).toBeVisible()

    // Image converter content should be visible
    await expect(
      page.getByText(/image converter|upload.*image/i).first()
    ).toBeVisible()
  })

  test('should navigate to Video converter tab', async ({ page }) => {
    // Click on Video tab
    const videoTab = page.getByRole('button', { name: /videos/i }).first()
    await videoTab.click()

    // Video converter should be visible
    await expect(
      page.getByText(/video converter|upload.*video/i).first()
    ).toBeVisible()
  })

  test('should navigate to Audio converter tab', async ({ page }) => {
    // Click on Audio tab
    const audioTab = page.getByRole('button', { name: /audio/i }).first()
    await audioTab.click()

    // Audio converter should be visible
    await expect(
      page.getByText(/audio converter|upload.*audio/i).first()
    ).toBeVisible()
  })

  test('should navigate to Document converter tab', async ({ page }) => {
    // Click on Document tab
    const documentTab = page.getByRole('button', { name: /documents/i }).first()
    await documentTab.click()

    // Document converter should be visible
    await expect(
      page.getByText(/document converter|upload.*document/i).first()
    ).toBeVisible()
  })

  test('should navigate to Batch converter tab', async ({ page }) => {
    // Click on Batch tab
    const batchTab = page.getByRole('button', { name: /batch/i }).first()
    await batchTab.click()

    // Batch converter should be visible
    await expect(
      page.getByText(/batch converter|upload.*multiple/i).first()
    ).toBeVisible()
  })

  test('should switch between tabs multiple times', async ({ page }) => {
    // Image -> Video
    await page.getByRole('button', { name: /videos/i }).first().click()
    await expect(
      page.getByText(/video converter/i).first()
    ).toBeVisible()

    // Video -> Audio
    await page.getByRole('button', { name: /audio/i }).first().click()
    await expect(
      page.getByText(/audio converter/i).first()
    ).toBeVisible()

    // Audio -> Image
    await page.getByRole('button', { name: /images/i }).first().click()
    await expect(
      page.getByText(/image converter/i).first()
    ).toBeVisible()
  })

  test('should display all converter tabs', async ({ page }) => {
    // Check that all main tabs are present
    const tabNames = [
      /images/i,
      /videos/i,
      /audio/i,
      /documents/i,
      /batch/i,
    ]

    for (const tabName of tabNames) {
      const tab = page.getByRole('button', { name: tabName }).first()
      await expect(tab).toBeVisible()
    }
  })
})
