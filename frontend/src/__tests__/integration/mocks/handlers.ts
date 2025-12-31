import { http, HttpResponse, delay } from 'msw'

/**
 * MSW handlers for mocking API endpoints in integration tests
 */

export const handlers = [
  // Image API
  http.post('/api/image/convert', async () => {
    await delay(100) // Simulate processing time
    return HttpResponse.json({
      session_id: 'test-session-image-123',
      status: 'completed',
      message: 'Image conversion completed successfully',
      download_url: '/api/image/download/converted-image.png',
    })
  }),

  http.get('/api/image/formats', () => {
    return HttpResponse.json({
      input_formats: ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff', 'svg'],
      output_formats: ['jpg', 'png', 'webp', 'gif', 'bmp', 'tiff'],
    })
  }),

  // Video API
  http.post('/api/video/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-video-123',
      status: 'completed',
      message: 'Video conversion completed successfully',
      download_url: '/api/video/download/converted-video.mp4',
    })
  }),

  http.get('/api/video/formats', () => {
    return HttpResponse.json({
      input_formats: ['mp4', 'avi', 'mkv', 'mov', 'webm', 'flv'],
      output_formats: ['mp4', 'avi', 'mkv', 'mov', 'webm'],
    })
  }),

  // Audio API
  http.post('/api/audio/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-audio-123',
      status: 'completed',
      message: 'Audio conversion completed successfully',
      download_url: '/api/audio/download/converted-audio.mp3',
    })
  }),

  http.get('/api/audio/formats', () => {
    return HttpResponse.json({
      input_formats: ['mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'],
      output_formats: ['mp3', 'wav', 'flac', 'ogg', 'aac'],
    })
  }),

  // Document API
  http.post('/api/document/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-document-123',
      status: 'completed',
      message: 'Document conversion completed successfully',
      download_url: '/api/document/download/converted-document.pdf',
    })
  }),

  http.get('/api/document/formats', () => {
    return HttpResponse.json({
      input_formats: ['docx', 'doc', 'odt', 'rtf', 'txt', 'md', 'html'],
      output_formats: ['pdf', 'docx', 'odt', 'rtf', 'txt', 'html'],
    })
  }),

  // Data API
  http.post('/api/data/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-data-123',
      status: 'completed',
      message: 'Data conversion completed successfully',
      download_url: '/api/data/download/converted-data.json',
    })
  }),

  http.get('/api/data/formats', () => {
    return HttpResponse.json({
      input_formats: ['json', 'xml', 'yaml', 'toml', 'csv'],
      output_formats: ['json', 'xml', 'yaml', 'toml'],
    })
  }),

  // Archive API
  http.post('/api/archive/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-archive-123',
      status: 'completed',
      message: 'Archive conversion completed successfully',
      download_url: '/api/archive/download/converted-archive.zip',
    })
  }),

  http.get('/api/archive/formats', () => {
    return HttpResponse.json({
      input_formats: ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z', 'rar'],
      output_formats: ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z'],
    })
  }),

  // Spreadsheet API
  http.post('/api/spreadsheet/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-spreadsheet-123',
      status: 'completed',
      message: 'Spreadsheet conversion completed successfully',
      download_url: '/api/spreadsheet/download/converted-spreadsheet.xlsx',
    })
  }),

  http.get('/api/spreadsheet/formats', () => {
    return HttpResponse.json({
      input_formats: ['xlsx', 'xls', 'csv', 'ods'],
      output_formats: ['xlsx', 'csv', 'ods', 'html'],
    })
  }),

  // Subtitle API
  http.post('/api/subtitle/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-subtitle-123',
      status: 'completed',
      message: 'Subtitle conversion completed successfully',
      download_url: '/api/subtitle/download/converted-subtitle.srt',
    })
  }),

  http.get('/api/subtitle/formats', () => {
    return HttpResponse.json({
      input_formats: ['srt', 'vtt', 'ass', 'ssa', 'sub'],
      output_formats: ['srt', 'vtt', 'ass', 'sub'],
    })
  }),

  // Ebook API
  http.post('/api/ebook/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-ebook-123',
      status: 'completed',
      message: 'Ebook conversion completed successfully',
      download_url: '/api/ebook/download/converted-ebook.epub',
    })
  }),

  http.get('/api/ebook/formats', () => {
    return HttpResponse.json({
      input_formats: ['epub', 'mobi', 'azw3', 'pdf'],
      output_formats: ['epub', 'mobi', 'azw3', 'pdf'],
    })
  }),

  // Font API
  http.post('/api/font/convert', async () => {
    await delay(100)
    return HttpResponse.json({
      session_id: 'test-session-font-123',
      status: 'completed',
      message: 'Font conversion completed successfully',
      download_url: '/api/font/download/converted-font.woff2',
    })
  }),

  http.get('/api/font/formats', () => {
    return HttpResponse.json({
      input_formats: ['ttf', 'otf', 'woff', 'woff2'],
      output_formats: ['ttf', 'otf', 'woff', 'woff2'],
    })
  }),

  // Batch API
  http.post('/api/batch/convert', async () => {
    await delay(150)
    return HttpResponse.json({
      session_id: 'test-session-batch-123',
      total_files: 3,
      successful: 3,
      failed: 0,
      results: [
        {
          filename: 'file1.jpg',
          success: true,
          download_url: '/api/batch/download/file1-converted.png',
          index: 0,
          message: 'Converted successfully',
        },
        {
          filename: 'file2.jpg',
          success: true,
          download_url: '/api/batch/download/file2-converted.png',
          index: 1,
          message: 'Converted successfully',
        },
        {
          filename: 'file3.jpg',
          success: true,
          download_url: '/api/batch/download/file3-converted.png',
          index: 2,
          message: 'Converted successfully',
        },
      ],
      message: 'Batch conversion completed: 3 successful, 0 failed',
    })
  }),

  http.post('/api/batch/zip', async () => {
    await delay(100)
    return HttpResponse.json({
      message: 'ZIP file created successfully',
      download_url: '/api/batch/download/batch-converted.zip',
    })
  }),
]

/**
 * Error handlers for testing error scenarios
 */
export const errorHandlers = {
  networkError: http.post('/api/image/convert', () => {
    return HttpResponse.error()
  }),

  serverError: http.post('/api/image/convert', () => {
    return HttpResponse.json(
      {
        detail: 'Internal server error occurred',
      },
      { status: 500 }
    )
  }),

  conversionError: http.post('/api/image/convert', () => {
    return HttpResponse.json(
      {
        detail: 'FFmpeg encoding error: Invalid codec parameters',
      },
      { status: 400 }
    )
  }),

  unsupportedFormat: http.post('/api/image/convert', () => {
    return HttpResponse.json(
      {
        detail: 'Unsupported file format',
      },
      { status: 400 }
    )
  }),

  fileSizeExceeded: http.post('/api/image/convert', () => {
    return HttpResponse.json(
      {
        detail: 'File size exceeds maximum limit of 100MB',
      },
      { status: 413 }
    )
  }),
}
