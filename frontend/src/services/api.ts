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
