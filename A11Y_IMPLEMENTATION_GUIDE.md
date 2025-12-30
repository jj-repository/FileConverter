# Accessibility Implementation Guide

This guide provides code examples for implementing accessibility features in remaining converter components.

## Quick Reference: Apply to All Converters

Use these patterns in VideoConverter, AudioConverter, DocumentConverter, and all other converter components.

### 1. Form Input Labels (htmlFor + id)

**Before:**
```tsx
<label className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.outputFormat')}
</label>
<select
  value={converter.outputFormat}
  onChange={(e) => converter.setOutputFormat(e.target.value)}
  className="input"
>
```

**After:**
```tsx
<label htmlFor="output-format" className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.outputFormat')}
</label>
<select
  id="output-format"
  value={converter.outputFormat}
  onChange={(e) => converter.setOutputFormat(e.target.value)}
  className="input"
  aria-label="Select output format for conversion"
>
```

### 2. Input with Hint Text (aria-describedby)

**Before:**
```tsx
<label className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.customFilename')}
</label>
<input
  type="text"
  value={converter.customFilename}
  onChange={(e) => converter.setCustomFilename(e.target.value)}
  className="input w-full"
/>
<p className="text-xs text-gray-500 mt-1">
  {t('common.customFilenameHint')}
</p>
```

**After:**
```tsx
<label htmlFor="custom-filename" className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.customFilename')}
</label>
<input
  id="custom-filename"
  type="text"
  value={converter.customFilename}
  onChange={(e) => converter.setCustomFilename(e.target.value)}
  className="input w-full"
  aria-describedby="filename-hint"
/>
<p id="filename-hint" className="text-xs text-gray-500 mt-1">
  {t('common.customFilenameHint')}
</p>
```

### 3. Range Slider (with aria-value* attributes)

**Before:**
```tsx
<label className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.quality')} ({quality}%)
</label>
<input
  type="range"
  min="1"
  max="100"
  value={quality}
  onChange={(e) => setQuality(Number(e.target.value))}
  className="w-full"
/>
```

**After:**
```tsx
<label htmlFor="quality-slider" className="block text-sm font-medium text-gray-700 mb-2">
  {t('common.quality')} ({quality}%)
</label>
<input
  id="quality-slider"
  type="range"
  min="1"
  max="100"
  value={quality}
  onChange={(e) => setQuality(Number(e.target.value))}
  className="w-full"
  aria-label={`Quality: ${quality} percent`}
  aria-valuemin={1}
  aria-valuemax={100}
  aria-valuenow={quality}
/>
```

### 4. Progress Bar (with role="progressbar")

**Before:**
```tsx
{converter.status === 'converting' && converter.showFeedback && (
  <div className="space-y-2">
    <div className="flex justify-between text-sm text-gray-600">
      <span>{converter.progress?.message || t('common.processing')}</span>
      <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="bg-primary-600 h-2 rounded-full transition-all"
        style={{ width: `${converter.progress?.progress || 0}%` }}
      />
    </div>
  </div>
)}
```

**After:**
```tsx
{converter.status === 'converting' && converter.showFeedback && (
  <div className="space-y-2">
    <div className="flex justify-between text-sm text-gray-600">
      <span>{converter.progress?.message || t('common.processing')}</span>
      <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
    </div>
    <div
      {...converter.getProgressAriaAttributes()}
      className="w-full bg-gray-200 rounded-full h-2"
    >
      <div
        className="bg-primary-600 h-2 rounded-full transition-all"
        style={{ width: `${converter.progress?.progress || 0}%` }}
        aria-hidden="true"
      />
    </div>
  </div>
)}
```

### 5. Error Messages (with role="alert")

**Before:**
```tsx
{converter.error && converter.showFeedback && (
  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
    {converter.error}
  </div>
)}
```

**After:**
```tsx
{converter.error && converter.showFeedback && (
  <div
    {...converter.getStatusAriaAttributes()}
    className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
  >
    {converter.error}
  </div>
)}
```

### 6. Success Messages (with role="status")

**Before:**
```tsx
{converter.status === 'completed' && converter.showFeedback && (
  <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
    {t('messages.conversionSuccess')}
  </div>
)}
```

**After:**
```tsx
{converter.status === 'completed' && converter.showFeedback && (
  <div
    {...converter.getStatusAriaAttributes()}
    className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg"
  >
    {t('messages.conversionSuccess')}
  </div>
)}
```

### 7. Output Directory Selection

**Before:**
```tsx
{window.electron?.isElectron && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {t('common.outputDirectory')}
    </label>
    <div className="flex gap-2">
      <input
        type="text"
        value={converter.outputDirectory || t('common.defaultDownloads')}
        readOnly
        className="input flex-1"
      />
      <Button
        onClick={converter.handleSelectOutputDirectory}
        variant="secondary"
      >
        {t('common.browse')}
      </Button>
    </div>
    <p className="text-xs text-gray-500 mt-1">
      💡 {t('common.outputDirectoryHint')}
    </p>
  </div>
)}
```

**After:**
```tsx
{window.electron?.isElectron && (
  <div>
    <label htmlFor="output-directory" className="block text-sm font-medium text-gray-700 mb-2">
      {t('common.outputDirectory')}
    </label>
    <div className="flex gap-2">
      <input
        id="output-directory"
        type="text"
        value={converter.outputDirectory || t('common.defaultDownloads')}
        readOnly
        className="input flex-1"
        aria-describedby="output-directory-hint"
        aria-label="Output directory path"
      />
      <Button
        onClick={converter.handleSelectOutputDirectory}
        variant="secondary"
        aria-label="Browse for output directory"
      >
        {t('common.browse')}
      </Button>
    </div>
    <p id="output-directory-hint" className="text-xs text-gray-500 mt-1">
      {t('common.outputDirectoryHint')}
    </p>
  </div>
)}
```

## Components Already Updated

The following components have complete accessibility implementations:

1. ✅ **DropZone.tsx** - Full keyboard support, ARIA labels, live regions
2. ✅ **BatchDropZone.tsx** - Full keyboard support, ARIA labels, live regions
3. ✅ **Button.tsx** - aria-busy, aria-disabled attributes
4. ✅ **LanguageSelector.tsx** - Complete keyboard navigation, ARIA menu pattern
5. ✅ **useConverter.ts** - Helper functions for progress and status ARIA
6. ✅ **ImageConverter.tsx** - Example implementation with all patterns
7. ✅ **App.css** - .sr-only utility class added

## Components Needing Updates

Apply the patterns above to:

1. ⏳ **VideoConverter.tsx**
2. ⏳ **AudioConverter.tsx**
3. ⏳ **DocumentConverter.tsx**
4. ⏳ **DataConverter.tsx**
5. ⏳ **ArchiveConverter.tsx**
6. ⏳ **SpreadsheetConverter.tsx**
7. ⏳ **SubtitleConverter.tsx**
8. ⏳ **EbookConverter.tsx**
9. ⏳ **FontConverter.tsx**
10. ⏳ **BatchConverter.tsx**
11. ⏳ **BatchConverterImproved.tsx**

## Common Issues to Avoid

### ❌ Don't Do This:

```tsx
// Missing label association
<label>Quality</label>
<input type="range" value={quality} />

// Placeholder as label
<input placeholder="Enter filename" />

// No ARIA on progress
<div className="progress-bar" style={{ width: `${progress}%` }} />

// No live region for errors
<div className="error">{error}</div>
```

### ✅ Do This Instead:

```tsx
// Proper label association
<label htmlFor="quality">Quality</label>
<input id="quality" type="range" value={quality} aria-label={`Quality: ${quality}%`} />

// Label + placeholder
<label htmlFor="filename">Custom Filename</label>
<input id="filename" placeholder="Enter filename" />

// ARIA on progress
<div
  role="progressbar"
  aria-valuenow={progress}
  aria-valuemin={0}
  aria-valuemax={100}
  aria-label="Conversion progress"
>
  <div style={{ width: `${progress}%` }} aria-hidden="true" />
</div>

// Live region for errors
<div role="alert" aria-live="assertive">
  {error}
</div>
```

## Testing Checklist

For each component you update, verify:

- [ ] All inputs have visible labels with proper `htmlFor`/`id`
- [ ] Tab order is logical
- [ ] All interactive elements focusable with keyboard
- [ ] Visible focus indicators (ring) on all focusable elements
- [ ] Progress bars have `role="progressbar"` and aria-value* attributes
- [ ] Error messages have `role="alert"`
- [ ] Success messages have `role="status"`
- [ ] Range sliders have aria-valuemin, aria-valuemax, aria-valuenow
- [ ] Hint text linked with `aria-describedby`
- [ ] Buttons have descriptive `aria-label` when text alone isn't clear

## Quick Apply Script

You can use find/replace to quickly update multiple files:

### Find Pattern 1 (Labels):
```
<label className="block text-sm font-medium text-gray-700 mb-2">
  {t\('([^']+)'\)}
</label>
<(select|input)
  (type="[^"]+"\s+)?
  value=
```

### Replace With:
```
<label htmlFor="UNIQUE_ID" className="block text-sm font-medium text-gray-700 mb-2">
  {t('$1')}
</label>
<$2
  id="UNIQUE_ID"
  $3value=
```

(Then manually replace UNIQUE_ID with appropriate values)

## Need Help?

- See ACCESSIBILITY.md for detailed documentation
- Check ImageConverter.tsx for complete example
- Review WCAG 2.1 guidelines: https://www.w3.org/WAI/WCAG21/quickref/
