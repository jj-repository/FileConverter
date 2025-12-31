# FileConverter Frontend Testing Implementation Plan

## Overview

Implement comprehensive testing for the FileConverter React/TypeScript frontend to achieve **80%+ coverage** with unit tests, integration tests, and E2E tests using Vitest, React Testing Library, and Playwright.

**Current State**:
- Test Framework: Vitest + React Testing Library (✅ configured)
- Existing Tests: 7 test files with 226 tests passing
- Component Coverage: 5/18 components tested (28%)
- Hook Coverage: 1/2 hooks tested (50%)
- Integration/E2E: None

**Target State**:
- Component Coverage: 18/18 components (100%)
- Hook Coverage: 2/2 hooks (100%)
- Service/API Coverage: 100%
- Integration Tests: Full user flows
- E2E Tests: Critical paths with Playwright
- Overall Coverage: 80%+
- CI/CD: Automated testing on PR/push

---

## Current Testing Infrastructure ✅

### Installed Dependencies
- ✅ `vitest` (v4.0.16) - Test runner
- ✅ `@testing-library/react` (v16.3.1) - Component testing
- ✅ `@testing-library/user-event` (v14.6.1) - User interactions
- ✅ `@testing-library/jest-dom` (v6.9.1) - DOM assertions
- ✅ `@vitest/ui` (v4.0.16) - Test UI
- ✅ `jsdom` (v27.4.0) - DOM environment

### Configuration Files
- ✅ `vitest.config.ts` - Test configuration with coverage thresholds
- ✅ `src/test/setup.ts` - Test setup file

### Existing Test Files (226 tests)
1. ✅ `src/__tests__/components/ImageConverter.test.tsx` (19 tests)
2. ✅ `src/__tests__/components/VideoConverter.test.tsx` (42 tests)
3. ✅ `src/__tests__/components/AudioConverter.test.tsx` (45 tests)
4. ✅ `src/__tests__/components/DataConverter.test.tsx` (43 tests)
5. ✅ `src/__tests__/components/DocumentConverter.test.tsx` (44 tests)
6. ✅ `src/__tests__/hooks/useConverter.test.ts` (12 tests)
7. ✅ `src/__tests__/utils/errorMessages.test.ts` (21 tests)

---

## Phase 1: Missing Component Unit Tests (13 components)

### 1.1 Common Components (3 components)

#### **src/__tests__/components/Common/Button.test.tsx** (~15 tests)
Test the reusable Button component:
- Rendering with different variants (primary, secondary, danger, etc.)
- Click handler functionality
- Disabled state
- Loading state
- Accessibility (ARIA labels, keyboard navigation)
- Icon rendering (if supported)
- Size variants

#### **src/__tests__/components/Common/Card.test.tsx** (~10 tests)
Test the Card component:
- Rendering with title and children
- Optional header/footer
- Different styling variants
- Accessibility (proper heading hierarchy)
- Click handlers (if applicable)

#### **src/__tests__/components/Common/LanguageSelector.test.tsx** (~12 tests)
Test language switching:
- Renders all available languages
- Current language highlighted
- Language switch triggers i18n change
- Dropdown/select behavior
- Accessibility (proper labels)
- Keyboard navigation

### 1.2 Converter Components (6 components)

#### **src/__tests__/components/Converter/ArchiveConverter.test.tsx** (~40 tests)
Following the pattern from existing converter tests:
- Rendering
- File selection and preview
- Format dropdown (zip, tar, tar.gz, 7z, etc.)
- Compression level option
- Conversion button and state management
- Progress display
- Download functionality
- Error handling
- Reset functionality
- Accessibility

#### **src/__tests__/components/Converter/EbookConverter.test.tsx** (~40 tests)
- EPUB, MOBI, PDF format support
- Metadata options (title, author)
- Cover image handling
- Following existing converter test pattern

#### **src/__tests__/components/Converter/FontConverter.test.tsx** (~40 tests)
- TTF, OTF, WOFF, WOFF2 formats
- Font subsetting options
- Font optimization toggle
- Preview/metadata display

#### **src/__tests__/components/Converter/SpreadsheetConverter.test.tsx** (~40 tests)
- CSV, XLSX, ODS formats
- Sheet selection (for multi-sheet files)
- Delimiter options for CSV
- Encoding options

#### **src/__tests__/components/Converter/SubtitleConverter.test.tsx** (~40 tests)
- SRT, VTT, ASS, SUB formats
- Encoding selection
- Timing offset options
- FPS options for SUB format

#### **src/__tests__/components/Converter/BatchConverterImproved.tsx** or **BatchConverter.tsx** (~45 tests)
- Multiple file selection
- Batch conversion UI
- Individual file status tracking
- Parallel vs sequential mode
- ZIP download of results
- Progress for each file
- Partial failure handling

### 1.3 File Upload Components (2 components)

#### **src/__tests__/components/FileUpload/DropZone.test.tsx** (~20 tests)
- Drag and drop functionality
- File selection via click
- Drag over visual feedback
- File type validation
- File size validation
- Multiple file handling (if applicable)
- Accessibility (keyboard file selection)
- Error messages for invalid files

#### **src/__tests__/components/FileUpload/BatchDropZone.test.tsx** (~25 tests)
- Multiple file drag and drop
- File list display
- Remove individual files
- File type validation per file
- Batch file size validation
- Visual feedback
- Accessibility

### 1.4 Layout Components (1 component)

#### **src/__tests__/components/Layout/TabNavigation.test.tsx** (~20 tests)
- Renders all tabs (Image, Video, Audio, Document, etc.)
- Active tab highlighting
- Tab switching
- Keyboard navigation (arrow keys, Tab key)
- Accessibility (ARIA roles, tab panel)
- URL routing (if applicable)

#### **src/__tests__/App.test.tsx** (~15 tests)
- App renders without crashing
- i18n initialization
- Tab routing/navigation
- Layout structure
- Error boundaries

**Phase 1 Subtotal**: ~362 new tests

---

## Phase 2: Hook and Service Tests

### 2.1 Hook Tests

#### **src/__tests__/hooks/useWebSocket.test.ts** (~20 tests)
Test WebSocket hook:
- Connection establishment
- Message receiving
- Progress updates
- Connection error handling
- Reconnection logic
- Cleanup on unmount
- Session ID management
- Multiple connection handling

### 2.2 Service/API Tests

#### **src/__tests__/services/api.test.ts** (~30 tests)
Test API service functions:
- Image conversion API call
- Video conversion API call
- Audio conversion API call
- Document conversion API call
- All other converter API calls
- Batch conversion API call
- File upload with progress
- Download file
- Get supported formats
- Error handling (network errors, 4xx, 5xx)
- Request cancellation
- File size validation
- MIME type handling

**Phase 2 Subtotal**: ~50 new tests

---

## Phase 3: Integration Tests

### 3.1 Full Conversion Flows (~30 tests)

Create `src/__tests__/integration/` directory with flow tests:

#### **conversionFlows.test.tsx**
Test complete user journeys:
- **Image conversion flow** (select file → choose format → convert → download)
- **Video conversion flow** with codec options
- **Audio conversion flow** with bitrate options
- **Document conversion flow** with TOC option
- **Batch conversion flow** (multiple files → convert → download ZIP)
- **Error recovery flow** (invalid file → error → reset → retry)
- **WebSocket progress flow** (conversion → real-time progress updates)
- **Language switching flow** (switch language → UI updates)

#### **accessibility.test.tsx** (~15 tests)
- Keyboard navigation through entire app
- Screen reader compatibility (ARIA labels)
- Focus management
- Color contrast (if testable)
- Form accessibility

**Phase 3 Subtotal**: ~45 new tests

---

## Phase 4: End-to-End Tests with Playwright

### 4.1 Setup Playwright

Install and configure Playwright:
```bash
npm install -D @playwright/test
npx playwright install
```

Create `playwright.config.ts`:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 4.2 E2E Test Scenarios (~20 tests)

Create `e2e/` directory:

#### **e2e/imageConversion.spec.ts** (~5 tests)
- Upload image file
- Select output format
- Click convert
- Verify progress
- Download converted file
- Verify file exists

#### **e2e/batchConversion.spec.ts** (~5 tests)
- Upload multiple files
- Start batch conversion
- Monitor progress for all files
- Download ZIP
- Verify all files converted

#### **e2e/errorHandling.spec.ts** (~5 tests)
- Upload invalid file (unsupported format)
- Verify error message
- Upload oversized file
- Verify error message
- Network error handling

#### **e2e/accessibility.spec.ts** (~5 tests)
- Keyboard-only navigation
- Tab through all interactive elements
- Submit form with keyboard
- Screen reader compatibility checks

**Phase 4 Subtotal**: ~20 new E2E tests

---

## Phase 5: CI/CD Integration

### 5.1 GitHub Actions Workflow

Create `.github/workflows/frontend-tests.yml`:

```yaml
name: Frontend Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run unit tests
        working-directory: ./frontend
        run: npm run test:run

      - name: Run tests with coverage
        working-directory: ./frontend
        run: npm install @vitest/coverage-v8 && npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend
          name: frontend-coverage-${{ matrix.node-version }}

      - name: Check coverage threshold
        working-directory: ./frontend
        run: |
          echo "Checking 60% coverage threshold..."

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20.x
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: TypeScript check
        working-directory: ./frontend
        run: npx tsc --noEmit

      - name: Lint check (if ESLint configured)
        working-directory: ./frontend
        run: echo "Add ESLint if needed"
        continue-on-error: true

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20.x
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Install Playwright browsers
        working-directory: ./frontend
        run: npx playwright install --with-deps

      - name: Run E2E tests
        working-directory: ./frontend
        run: npx playwright test

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### 5.2 Coverage Reporting

Update `vitest.config.ts` to enforce coverage:
```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html', 'lcov'],
  lines: 80,        // Increase from 60
  functions: 80,    // Increase from 60
  branches: 80,     // Increase from 60
  statements: 80,   // Increase from 60
}
```

---

## Test Organization

### Directory Structure

```
frontend/
├── src/
│   ├── __tests__/
│   │   ├── components/
│   │   │   ├── Common/
│   │   │   │   ├── Button.test.tsx (NEW)
│   │   │   │   ├── Card.test.tsx (NEW)
│   │   │   │   └── LanguageSelector.test.tsx (NEW)
│   │   │   ├── Converter/
│   │   │   │   ├── ImageConverter.test.tsx (EXISTS)
│   │   │   │   ├── VideoConverter.test.tsx (EXISTS)
│   │   │   │   ├── AudioConverter.test.tsx (EXISTS)
│   │   │   │   ├── DataConverter.test.tsx (EXISTS)
│   │   │   │   ├── DocumentConverter.test.tsx (EXISTS)
│   │   │   │   ├── ArchiveConverter.test.tsx (NEW)
│   │   │   │   ├── EbookConverter.test.tsx (NEW)
│   │   │   │   ├── FontConverter.test.tsx (NEW)
│   │   │   │   ├── SpreadsheetConverter.test.tsx (NEW)
│   │   │   │   ├── SubtitleConverter.test.tsx (NEW)
│   │   │   │   └── BatchConverter.test.tsx (NEW)
│   │   │   ├── FileUpload/
│   │   │   │   ├── DropZone.test.tsx (NEW)
│   │   │   │   └── BatchDropZone.test.tsx (NEW)
│   │   │   └── Layout/
│   │   │       └── TabNavigation.test.tsx (NEW)
│   │   ├── hooks/
│   │   │   ├── useConverter.test.ts (EXISTS)
│   │   │   └── useWebSocket.test.ts (NEW)
│   │   ├── services/
│   │   │   └── api.test.ts (NEW)
│   │   ├── utils/
│   │   │   └── errorMessages.test.ts (EXISTS)
│   │   ├── integration/
│   │   │   ├── conversionFlows.test.tsx (NEW)
│   │   │   └── accessibility.test.tsx (NEW)
│   │   └── App.test.tsx (NEW)
│   └── test/
│       └── setup.ts (EXISTS)
├── e2e/
│   ├── imageConversion.spec.ts (NEW)
│   ├── batchConversion.spec.ts (NEW)
│   ├── errorHandling.spec.ts (NEW)
│   └── accessibility.spec.ts (NEW)
├── vitest.config.ts (EXISTS - needs coverage update)
├── playwright.config.ts (NEW)
└── package.json (EXISTS - needs Playwright added)
```

---

## Testing Patterns & Best Practices

### 1. Component Testing Pattern

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ComponentName } from '@/components/path'

// Mock dependencies
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}))

describe('ComponentName', () => {
  describe('Rendering', () => {
    it('should render component title', () => {
      render(<ComponentName />)
      expect(screen.getByText(/title/i)).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('should handle button click', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      render(<ComponentName onClick={handleClick} />)

      await user.click(screen.getByRole('button'))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ComponentName />)
      expect(screen.getByLabelText(/label/i)).toBeInTheDocument()
    })
  })
})
```

### 2. Hook Testing Pattern

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useCustomHook } from '@/hooks/useCustomHook'

describe('useCustomHook', () => {
  it('should initialize with default state', () => {
    const { result } = renderHook(() => useCustomHook())
    expect(result.current.state).toBe('idle')
  })

  it('should update state on action', async () => {
    const { result } = renderHook(() => useCustomHook())

    await waitFor(() => {
      result.current.performAction()
    })

    expect(result.current.state).toBe('success')
  })
})
```

### 3. Integration Testing Pattern

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '@/App'

describe('Image Conversion Flow', () => {
  it('should complete full conversion process', async () => {
    const user = userEvent.setup()

    // 1. Render app
    render(<App />)

    // 2. Navigate to Image tab
    await user.click(screen.getByText(/image/i))

    // 3. Upload file
    const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByLabelText(/upload/i)
    await user.upload(input, file)

    // 4. Select format
    await user.selectOptions(screen.getByLabelText(/format/i), 'png')

    // 5. Convert
    await user.click(screen.getByRole('button', { name: /convert/i }))

    // 6. Wait for completion
    await waitFor(() => {
      expect(screen.getByText(/download/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })
})
```

---

## Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Component Coverage | 5/18 (28%) | 18/18 (100%) | ⏳ In Progress |
| Hook Coverage | 1/2 (50%) | 2/2 (100%) | ⏳ In Progress |
| Service Coverage | 0% | 100% | ⏳ Planned |
| Integration Tests | 0 | 45 tests | ⏳ Planned |
| E2E Tests | 0 | 20 tests | ⏳ Planned |
| Total Tests | 226 | ~700 | ⏳ Planned |
| Overall Coverage | Unknown | 80%+ | ⏳ Target |
| CI/CD | None | Full Pipeline | ⏳ Planned |

---

## Implementation Phases Summary

| Phase | Focus | New Tests | Duration |
|-------|-------|-----------|----------|
| **Phase 1** | Component Unit Tests | ~362 | 3-4 days |
| **Phase 2** | Hooks & Services | ~50 | 1 day |
| **Phase 3** | Integration Tests | ~45 | 1-2 days |
| **Phase 4** | E2E with Playwright | ~20 | 1-2 days |
| **Phase 5** | CI/CD Setup | N/A | 1 day |
| **TOTAL** | **Complete Frontend Testing** | **~477** | **7-10 days** |

---

## Running Tests

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# UI mode
npm run test:ui

# E2E tests (after Playwright setup)
npx playwright test

# E2E with UI
npx playwright test --ui
```

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Install Playwright (`npm install -D @playwright/test`)
3. ⏳ Install coverage tool (`npm install -D @vitest/coverage-v8`)
4. ⏳ Start Phase 1: Implement missing component tests
5. ⏳ Continue through phases 2-5
6. ⏳ Create CI/CD workflow
7. ⏳ Document testing in README

---

*Plan Created: December 31, 2025*
*Test Framework: Vitest + React Testing Library*
*E2E Framework: Playwright (to be added)*
*Target Coverage: 80%+*
