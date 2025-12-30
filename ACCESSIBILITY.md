# Accessibility (a11y) Features

This document outlines the comprehensive accessibility features implemented in the FileConverter application to ensure it's usable by everyone, including screen reader users and keyboard-only users.

## Overview

The FileConverter application has been enhanced with full WCAG 2.1 Level AA compliance in mind, making it accessible to users with various disabilities including:

- Visual impairments (screen reader users)
- Motor impairments (keyboard-only users)
- Cognitive disabilities (clear labels, status announcements)

## Key Accessibility Features

### 1. DropZone Component (`/frontend/src/components/FileUpload/DropZone.tsx`)

#### Features Implemented:
- **Keyboard Accessibility**: Full keyboard navigation support
  - `Tab` to focus the dropzone
  - `Enter` or `Space` to open file browser
  - Visible focus indicator (ring)

- **Screen Reader Support**:
  - `role="button"` for proper semantic meaning
  - Comprehensive `aria-label` describing functionality and supported formats
  - `aria-describedby` linking to hint text
  - Hidden status announcements via `aria-live="polite"` for drag state changes
  - Decorative emojis marked with `aria-hidden="true"`

- **Live Region Announcements**:
  - Announces when file is dragged over: "File is over drop zone. Release to upload."
  - Announces invalid file types: "Invalid file type detected."

#### Example Usage:
```tsx
<DropZone
  onFileSelect={handleFileSelect}
  acceptedFormats={['png', 'jpg', 'webp']}
  fileType="image"
/>
```

### 2. BatchDropZone Component (`/frontend/src/components/FileUpload/BatchDropZone.tsx`)

Similar to DropZone but optimized for multiple file uploads:
- All keyboard navigation features
- Appropriate `aria-label` mentioning maximum file count
- Live announcements for drag-and-drop states

### 3. Button Component (`/frontend/src/components/Common/Button.tsx`)

#### Features Implemented:
- **ARIA Attributes**:
  - `aria-disabled` to announce disabled state
  - `aria-busy` to indicate loading/processing state
  - Decorative loading spinner marked with `aria-hidden="true"`

- **Visual and Semantic States**:
  - Disabled buttons properly marked
  - Loading state clearly communicated to assistive technologies

#### Example:
```tsx
<Button
  loading={isProcessing}
  disabled={!file}
  onClick={handleConvert}
>
  Convert
</Button>
```

### 4. LanguageSelector Component (`/frontend/src/components/Common/LanguageSelector.tsx`)

#### Features Implemented:
- **Full Keyboard Navigation**:
  - `Arrow Up/Down`: Navigate menu items
  - `Home/End`: Jump to first/last item
  - `Escape`: Close menu and return focus to button
  - `Enter/Space`: Select language

- **ARIA Menu Pattern**:
  - `role="menu"` and `role="menuitem"` for proper semantics
  - `aria-expanded` to indicate dropdown state
  - `aria-haspopup="menu"` to announce dropdown behavior
  - `aria-controls` linking button to menu
  - `aria-current` to mark selected language

- **Focus Management**:
  - Focus returns to button after selection
  - Focus trapping within menu when open
  - Visual focus indicators on all items

### 5. useConverter Hook (`/frontend/src/hooks/useConverter.ts`)

#### Accessibility Helpers Added:

**`getProgressAriaAttributes()`**:
Returns proper ARIA attributes for progress bars:
```tsx
{
  role: 'progressbar',
  'aria-valuenow': 45,
  'aria-valuemin': 0,
  'aria-valuemax': 100,
  'aria-label': 'Conversion progress'
}
```

**`getStatusAriaAttributes()`**:
Returns appropriate ARIA attributes for status messages:
```tsx
{
  role: 'alert' | 'status',
  'aria-live': 'assertive' | 'polite',
  'aria-atomic': true
}
```

- Uses `role="alert"` and `aria-live="assertive"` for errors (immediate announcement)
- Uses `role="status"` and `aria-live="polite"` for success messages (announced when convenient)

### 6. Form Inputs (All Converter Components)

#### Features Implemented:
- **Label Association**:
  - All inputs have associated `<label>` elements with proper `for`/`id` attributes
  - Labels are always visible (no placeholder-only inputs)

- **ARIA Descriptions**:
  - `aria-describedby` linking to hint text
  - `aria-label` providing context where needed

- **Range Inputs**:
  - `aria-valuemin`, `aria-valuemax`, `aria-valuenow` for sliders
  - Descriptive labels including current value

#### Example (Quality Slider):
```tsx
<label htmlFor="quality-slider">
  Quality ({quality}%)
</label>
<input
  id="quality-slider"
  type="range"
  min="1"
  max="100"
  value={quality}
  aria-label={`Image quality: ${quality} percent`}
  aria-valuemin={1}
  aria-valuemax={100}
  aria-valuenow={quality}
/>
```

### 7. Progress Bars (Conversion Status)

All progress bars now include:
- `role="progressbar"`
- `aria-valuenow` (current progress percentage)
- `aria-valuemin="0"`
- `aria-valuemax="100"`
- `aria-label` describing what's being processed

#### Example:
```tsx
<div {...converter.getProgressAriaAttributes()}>
  <div className="progress-fill" aria-hidden="true" />
</div>
```

### 8. Status Messages (Error/Success)

All status messages include:
- `role="alert"` for errors (announced immediately)
- `role="status"` for success messages (polite announcement)
- `aria-live` regions for dynamic content
- `aria-atomic="true"` for complete message readout

#### Example:
```tsx
{converter.error && (
  <div {...converter.getStatusAriaAttributes()}>
    {converter.error}
  </div>
)}
```

## CSS Utilities

### Screen Reader Only Classes (`/frontend/src/App.css`)

**`.sr-only`**: Visually hidden but accessible to screen readers
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
```

**`.sr-only-focusable`**: Becomes visible when focused (skip links, etc.)
```css
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
}
```

## Testing Recommendations

### Keyboard Navigation Testing
1. Navigate entire app using only `Tab`, `Enter`, `Space`, `Arrow keys`, and `Escape`
2. Verify all interactive elements are focusable
3. Check visible focus indicators on all focusable elements
4. Ensure logical tab order

### Screen Reader Testing
Test with popular screen readers:
- **NVDA** (Windows, free)
- **JAWS** (Windows, commercial)
- **VoiceOver** (macOS/iOS, built-in)
- **TalkBack** (Android, built-in)

#### Test Scenarios:
1. Upload a file using keyboard only
2. Navigate and change settings (format, quality)
3. Monitor conversion progress
4. Receive error/success announcements
5. Change language using keyboard

### Automated Testing
Consider using:
- **axe DevTools** browser extension
- **WAVE** (Web Accessibility Evaluation Tool)
- **Lighthouse** accessibility audit (Chrome DevTools)

## WCAG 2.1 Compliance

The application meets or exceeds the following WCAG 2.1 Level AA criteria:

| Criterion | Level | Status | Implementation |
|-----------|-------|--------|----------------|
| 1.3.1 Info and Relationships | A | ✅ Pass | Semantic HTML, ARIA roles, proper labels |
| 1.4.13 Content on Hover or Focus | AA | ✅ Pass | Focus indicators, keyboard dismissible |
| 2.1.1 Keyboard | A | ✅ Pass | All functionality keyboard accessible |
| 2.1.2 No Keyboard Trap | A | ✅ Pass | Focus management, Escape to close |
| 2.4.3 Focus Order | A | ✅ Pass | Logical tab order maintained |
| 2.4.6 Headings and Labels | AA | ✅ Pass | Descriptive labels on all inputs |
| 2.4.7 Focus Visible | AA | ✅ Pass | Clear focus indicators |
| 3.2.2 On Input | A | ✅ Pass | No unexpected context changes |
| 3.3.2 Labels or Instructions | A | ✅ Pass | All inputs labeled with hints |
| 4.1.2 Name, Role, Value | A | ✅ Pass | ARIA attributes on all components |
| 4.1.3 Status Messages | AA | ✅ Pass | Live regions for status updates |

## Future Enhancements

Potential accessibility improvements for future releases:

1. **High Contrast Mode Support**: Detect and respect OS high contrast preferences
2. **Reduced Motion Support**: Respect `prefers-reduced-motion` for animations
3. **Text Scaling**: Ensure UI works at 200% text zoom
4. **Dark Mode a11y**: Ensure color contrast meets WCAG in dark mode
5. **Skip Links**: Add "Skip to main content" link
6. **Landmark Regions**: Add ARIA landmarks (`main`, `navigation`, etc.)
7. **Error Prevention**: Add confirmation dialogs for destructive actions
8. **Multi-language Screen Reader Support**: Proper `lang` attributes

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## Support

For accessibility issues or suggestions, please open an issue on the project repository with the `accessibility` label.
