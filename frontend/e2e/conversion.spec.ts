import { test, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * End-to-end conversion flow: uploads a real image, converts it, verifies the
 * backend produced a download link. Requires the FastAPI backend running on
 * http://localhost:8000; the test is skipped when the backend is unreachable
 * so developer runs without the backend don't produce noisy failures.
 */

test.describe('Full conversion flow (requires backend)', () => {
  test.beforeAll(async ({ request }) => {
    let reachable = false
    try {
      const res = await request.get('http://localhost:8000/health', {
        timeout: 2_000,
      })
      reachable = res.ok()
    } catch {
      reachable = false
    }
    test.skip(!reachable, 'Backend not running on :8000 — skipping real conversion test')
  })

  test('converts a PNG to JPG via the UI', async ({ page }) => {
    await page.goto('/')

    const imageTab = page.getByRole('button', { name: /images?/i }).first()
    await imageTab.click()

    const fileInput = page.locator('input[type="file"]').first()
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test-image.png'))

    const formatSelect = page.getByLabel(/output format/i).first()
    await formatSelect.selectOption('jpg')

    const convertButton = page
      .getByRole('button', { name: /convert/i })
      .first()
    await convertButton.click()

    // Completion signal — the browser-mode app exposes a "Download" action.
    await expect(
      page.getByRole('button', { name: /download|convert another/i }).first()
    ).toBeVisible({ timeout: 30_000 })
  })
})
