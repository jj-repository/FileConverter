import axios from 'axios';
import { ConversionResponse, ConversionOptions } from '../types/conversion';

const api = axios.create({
  baseURL: '/api',
});

// --- Factory for standard converter APIs ---

type OptionAppender = (formData: FormData, options: ConversionOptions) => void;

interface ConverterAPI {
  convert: (file: File, options: ConversionOptions) => Promise<ConversionResponse>;
  getFormats: () => Promise<{ input_formats: string[]; output_formats: string[]; notes?: Record<string, string> }>;
  downloadFile: (filename: string) => string;
}

function createConverterAPI(type: string, appendOptions: OptionAppender): ConverterAPI {
  return {
    convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('output_format', options.outputFormat!);
      appendOptions(formData, options);

      const response = await api.post<ConversionResponse>(`/${type}/convert`, formData, {
        onUploadProgress: (progressEvent) => {
          if (options.onUploadProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            options.onUploadProgress(percentCompleted);
          }
        },
      });
      return response.data;
    },

    getFormats: async () => {
      const response = await api.get(`/${type}/formats`);
      return response.data;
    },

    downloadFile: (filename: string) => `/api/${type}/download/${filename}`,
  };
}

// Helper to append optional form fields
function appendIf(formData: FormData, key: string, value: unknown) {
  if (value !== undefined && value !== null) {
    formData.append(key, String(value));
  }
}

// --- Converter APIs ---

export const imageAPI = createConverterAPI('image', (fd, o) => {
  appendIf(fd, 'quality', o.quality);
  appendIf(fd, 'width', o.width);
  appendIf(fd, 'height', o.height);
});

export const videoAPI = createConverterAPI('video', (fd, o) => {
  appendIf(fd, 'codec', o.codec);
  appendIf(fd, 'resolution', o.resolution);
  appendIf(fd, 'bitrate', o.bitrate);
});

export const audioAPI = createConverterAPI('audio', (fd, o) => {
  appendIf(fd, 'bitrate', o.bitrate);
  appendIf(fd, 'sample_rate', o.sampleRate);
  appendIf(fd, 'channels', o.channels);
});

export const documentAPI = createConverterAPI('document', (fd, o) => {
  appendIf(fd, 'preserve_formatting', o.preserveFormatting);
  appendIf(fd, 'toc', o.toc);
});

export const dataAPI = createConverterAPI('data', (fd, o) => {
  appendIf(fd, 'encoding', o.encoding);
  appendIf(fd, 'delimiter', o.delimiter);
  appendIf(fd, 'pretty', o.pretty);
});

export const archiveAPI = createConverterAPI('archive', (fd, o) => {
  appendIf(fd, 'compression_level', o.compressionLevel);
});

export const spreadsheetAPI = createConverterAPI('spreadsheet', (fd, o) => {
  appendIf(fd, 'sheet_name', o.sheetName);
  appendIf(fd, 'include_all_sheets', o.includeAllSheets);
  appendIf(fd, 'encoding', o.encoding);
  appendIf(fd, 'delimiter', o.delimiter);
});

export const subtitleAPI = {
  ...createConverterAPI('subtitle', (fd, o) => {
    appendIf(fd, 'encoding', o.encoding);
    appendIf(fd, 'fps', o.fps);
    appendIf(fd, 'keep_html_tags', o.keepHtmlTags);
  }),

  adjustTiming: async (file: File, offsetMs: number, onUploadProgress?: (progress: number) => void): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('offset_ms', offsetMs.toString());

    const response = await api.post<ConversionResponse>('/subtitle/adjust-timing', formData, {
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },
};

export const ebookAPI = createConverterAPI('ebook', () => {});

export const fontAPI = createConverterAPI('font', (fd, o) => {
  appendIf(fd, 'subset_text', o.subsetText);
  appendIf(fd, 'optimize', o.optimize);
});

// --- Batch API ---

export interface BatchConversionResult {
  filename: string;
  success: boolean;
  output_file?: string;
  download_url?: string;
  error?: string;
  index: number;
}

export interface BatchConversionResponse {
  session_id: string;
  total_files: number;
  successful: number;
  failed: number;
  results: BatchConversionResult[];
  message: string;
}

interface BatchZipResponse {
  zip_file: string;
  download_url: string;
  file_count: number;
}

export const batchAPI = {
  convert: async (files: File[], options: ConversionOptions): Promise<BatchConversionResponse> => {
    const formData = new FormData();

    files.forEach(file => {
      formData.append('files', file);
    });

    formData.append('output_format', options.outputFormat!);
    formData.append('parallel', 'true');

    // Add all optional parameters
    appendIf(formData, 'quality', options.quality);
    appendIf(formData, 'width', options.width);
    appendIf(formData, 'height', options.height);
    appendIf(formData, 'bitrate', options.bitrate);
    appendIf(formData, 'codec', options.codec);
    appendIf(formData, 'resolution', options.resolution);
    appendIf(formData, 'sample_rate', options.sampleRate);
    appendIf(formData, 'channels', options.channels);
    appendIf(formData, 'preserve_formatting', options.preserveFormatting);
    appendIf(formData, 'toc', options.toc);

    const response = await api.post<BatchConversionResponse>('/batch/convert', formData, {
      onUploadProgress: (progressEvent) => {
        if (options.onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          options.onUploadProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  createZip: async (sessionId: string, filenames: string[]): Promise<BatchZipResponse> => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    filenames.forEach(filename => {
      formData.append('filenames', filename);
    });

    const response = await api.post<BatchZipResponse>('/batch/download-zip', formData);
    return response.data;
  },
};
