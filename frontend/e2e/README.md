# E2E Tests with Playwright

This directory contains end-to-end (E2E) tests for the FileConverter frontend application using Playwright.

## Test Files

- **navigation.spec.ts** - Tab navigation and page routing tests
- **fileUpload.spec.ts** - File selection and upload UI interactions
- **accessibility.spec.ts** - Keyboard navigation, ARIA attributes, focus management
- **ui.spec.ts** - UI layout, responsive design, visual elements
- **formInteractions.spec.ts** - Form controls, validation, user interactions

## Running E2E Tests

### Prerequisites

Ensure you have Playwright installed and browsers downloaded:

```bash
npm install -D @playwright/test
npx playwright install chromium
```

### Run All E2E Tests

```bash
npx playwright test
```

### Run Specific Test File

```bash
npx playwright test e2e/navigation.spec.ts
```

### Run with UI Mode (Interactive)

```bash
npx playwright test --ui
```

### Run in Headed Mode (Show Browser)

```bash
npx playwright test --headed
```

### Debug Tests

```bash
npx playwright test --debug
```

### View Test Report

After running tests, view the HTML report:

```bash
npx playwright show-report
```

## Test Configuration

Configuration is in `playwright.config.ts` at the project root.

Key settings:
- **Base URL**: http://localhost:5173
- **Test Directory**: ./e2e
- **Browsers**: Chromium (Desktop Chrome)
- **Web Server**: Automatically starts `npm run dev` before tests

## Important Notes

### Frontend-Only Tests

The current E2E tests focus on **frontend-only interactions**:
- Navigation and tab switching
- File selection UI
- Form interactions
- Accessibility features
- Responsive design

### Full Conversion Testing

**Full conversion workflows** (upload → convert → download) require:
- A running backend server on `http://localhost:8000`
- Proper CORS configuration
- Backend API endpoints operational

To enable full conversion testing:
1. Start the backend server: `cd ../backend && uvicorn app.main:app --reload`
2. Verify backend is running: `curl http://localhost:8000/health`
3. Run E2E tests: `npx playwright test`

### Mock vs Real Backend

Current tests are designed to work **without a backend** by testing:
- UI rendering
- User interactions
- Navigation flows
- Accessibility compliance

For **production E2E testing**, integrate with the real backend or use:
- Mock Service Worker (MSW) in the browser
- Backend stubs/mocks
- Test fixtures with predefined responses

## CI/CD Integration

To run E2E tests in CI/CD:

```yaml
- name: Install Playwright Browsers
  run: npx playwright install --with-deps chromium

- name: Run E2E Tests
  run: npx playwright test

- name: Upload Test Report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-report
    path: playwright-report/
```

## Debugging Tips

1. **Use --headed** to see the browser:
   ```bash
   npx playwright test --headed
   ```

2. **Use --debug** to step through tests:
   ```bash
   npx playwright test --debug
   ```

3. **Take screenshots on failure** (automatic in config):
   - Screenshots saved to `test-results/`

4. **View traces**:
   - Traces captured on first retry
   - Open with: `npx playwright show-trace trace.zip`

## Writing New Tests

Example test structure:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should do something', async ({ page }) => {
    // Arrange
    const element = page.getByRole('button', { name: /click me/i })

    // Act
    await element.click()

    // Assert
    await expect(page.getByText(/success/i)).toBeVisible()
  })
})
```

## Best Practices

1. **Use semantic locators**: Prefer `getByRole`, `getByLabel`, `getByText` over CSS selectors
2. **Wait for elements**: Use `expect(...).toBeVisible()` instead of hard waits
3. **Keep tests isolated**: Each test should be independent
4. **Test user flows**: Focus on what users actually do
5. **Avoid implementation details**: Test behavior, not internals

## Test Coverage

Current E2E test coverage:
- ✅ Navigation between tabs
- ✅ File upload interactions
- ✅ Keyboard accessibility
- ✅ ARIA compliance
- ✅ Form validation
- ✅ Responsive design
- ⏳ Full conversion workflows (requires backend)
- ⏳ Error handling with real API
- ⏳ Download verification

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
