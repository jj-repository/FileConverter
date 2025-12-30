import axios from 'axios';
import { ConversionResponse, ConversionOptions } from '../types/conversion';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export const imageAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.quality !== undefined) {
      formData.append('quality', options.quality.toString());
    }
    if (options.width) {
      formData.append('width', options.width.toString());
    }
    if (options.height) {
      formData.append('height', options.height.toString());
    }

    const response = await api.post<ConversionResponse>('/image/convert', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/image/formats');
    return response.data;
  },

  downloadFile: (filename: string): string => {
    return `/api/image/download/${filename}`;
  },
};

export const videoAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.codec) {
      formData.append('codec', options.codec);
    }
    if (options.resolution) {
      formData.append('resolution', options.resolution);
    }
    if (options.bitrate) {
      formData.append('bitrate', options.bitrate);
    }

    const response = await api.post<ConversionResponse>('/video/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/video/formats');
    return response.data;
  },
};

export const audioAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.bitrate) {
      formData.append('bitrate', options.bitrate);
    }
    if (options.sampleRate) {
      formData.append('sample_rate', options.sampleRate.toString());
    }
    if (options.channels) {
      formData.append('channels', options.channels.toString());
    }

    const response = await api.post<ConversionResponse>('/audio/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/audio/formats');
    return response.data;
  },
};

export const documentAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.preserveFormatting !== undefined) {
      formData.append('preserve_formatting', options.preserveFormatting.toString());
    }
    if (options.toc !== undefined) {
      formData.append('toc', options.toc.toString());
    }

    const response = await api.post<ConversionResponse>('/document/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/document/formats');
    return response.data;
  },
};

export const dataAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.encoding) {
      formData.append('encoding', options.encoding);
    }
    if (options.delimiter) {
      formData.append('delimiter', options.delimiter);
    }
    if (options.pretty !== undefined) {
      formData.append('pretty', options.pretty.toString());
    }

    const response = await api.post<ConversionResponse>('/data/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/data/formats');
    return response.data;
  },

  downloadFile: (filename: string): string => {
    return `/api/data/download/${filename}`;
  },
};

export const archiveAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.compressionLevel !== undefined) {
      formData.append('compression_level', options.compressionLevel.toString());
    }

    const response = await api.post<ConversionResponse>('/archive/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/archive/formats');
    return response.data;
  },

  downloadFile: (filename: string): string => {
    return `/api/archive/download/${filename}`;
  },
};

export const spreadsheetAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.sheetName) {
      formData.append('sheet_name', options.sheetName);
    }
    if (options.includeAllSheets !== undefined) {
      formData.append('include_all_sheets', options.includeAllSheets.toString());
    }
    if (options.encoding) {
      formData.append('encoding', options.encoding);
    }
    if (options.delimiter) {
      formData.append('delimiter', options.delimiter);
    }

    const response = await api.post<ConversionResponse>('/spreadsheet/convert', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/spreadsheet/formats');
    return response.data;
  },

  downloadFile: (filename: string): string => {
    return `/api/spreadsheet/download/${filename}`;
  },
};

export const subtitleAPI = {
  convert: async (file: File, options: ConversionOptions): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', options.outputFormat);

    if (options.encoding) {
      formData.append('encoding', options.encoding);
    }
    if (options.fps !== undefined) {
      formData.append('fps', options.fps.toString());
    }
    if (options.keepHtmlTags !== undefined) {
      formData.append('keep_html_tags', options.keepHtmlTags.toString());
    }

    const response = await api.post<ConversionResponse>('/subtitle/convert', formData);
    return response.data;
  },

  adjustTiming: async (file: File, offsetMs: number): Promise<ConversionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('offset_ms', offsetMs.toString());

    const response = await api.post<ConversionResponse>('/subtitle/adjust-timing', formData);
    return response.data;
  },

  getFormats: async (): Promise<{ input_formats: string[]; output_formats: string[] }> => {
    const response = await api.get('/subtitle/formats');
    return response.data;
  },

  downloadFile: (filename: string): string => {
    return `/api/subtitle/download/${filename}`;
  },
};

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

export const batchAPI = {
  convert: async (files: File[], options: ConversionOptions): Promise<BatchConversionResponse> => {
    const formData = new FormData();

    // Append all files
    files.forEach(file => {
      formData.append('files', file);
    });

    formData.append('output_format', options.outputFormat);
    formData.append('parallel', 'true');

    // Add all optional parameters
    if (options.quality !== undefined) {
      formData.append('quality', options.quality.toString());
    }
    if (options.width) {
      formData.append('width', options.width.toString());
    }
    if (options.height) {
      formData.append('height', options.height.toString());
    }
    if (options.bitrate) {
      formData.append('bitrate', options.bitrate);
    }
    if (options.codec) {
      formData.append('codec', options.codec);
    }
    if (options.resolution) {
      formData.append('resolution', options.resolution);
    }
    if (options.sampleRate) {
      formData.append('sample_rate', options.sampleRate.toString());
    }
    if (options.channels) {
      formData.append('channels', options.channels.toString());
    }
    if (options.preserveFormatting !== undefined) {
      formData.append('preserve_formatting', options.preserveFormatting.toString());
    }
    if (options.toc !== undefined) {
      formData.append('toc', options.toc.toString());
    }

    const response = await api.post<BatchConversionResponse>('/batch/convert', formData);
    return response.data;
  },

  createZip: async (sessionId: string, filenames: string[]): Promise<any> => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    filenames.forEach(filename => {
      formData.append('filenames', filename);
    });

    const response = await api.post('/batch/download-zip', formData);
    return response.data;
  },
};
