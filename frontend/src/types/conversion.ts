export type FileType = 'image' | 'video' | 'audio' | 'document' | 'data' | 'archive' | 'batch';

export type ConversionStatus = 'idle' | 'uploading' | 'converting' | 'completed' | 'failed';

export interface ConversionOptions {
  outputFormat: string;
  quality?: number;
  width?: number;
  height?: number;
  bitrate?: string;
  codec?: string;
  resolution?: string;
  sampleRate?: number;
  channels?: number;
  preserveFormatting?: boolean;
  toc?: boolean;
  encoding?: string;
  delimiter?: string;
  pretty?: boolean;
  compressionLevel?: number;
}

export interface ConversionResponse {
  session_id: string;
  status: ConversionStatus;
  message: string;
  output_file?: string;
  download_url?: string;
  error?: string;
}

export interface ProgressUpdate {
  session_id: string;
  progress: number;
  status: ConversionStatus;
  message: string;
  current_operation?: string;
}

export interface FileInfo {
  filename: string;
  size: number;
  format: string;
  metadata?: Record<string, any>;
}
