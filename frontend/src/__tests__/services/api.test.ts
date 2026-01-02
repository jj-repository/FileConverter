// @ts-nocheck
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock axios BEFORE importing api module
const mockPost = vi.fn();
const mockGet = vi.fn();

vi.mock('axios', () => {
  const mockPostFn = vi.fn();
  const mockGetFn = vi.fn();

  return {
    default: {
      create: vi.fn(() => ({
        post: mockPostFn,
        get: mockGetFn,
      })),
    },
    mockPost: mockPostFn,
    mockGet: mockGetFn,
  };
});

// Now import the api module and axios
import axios from 'axios';
import {
  imageAPI,
  videoAPI,
  audioAPI,
  documentAPI,
  dataAPI,
  archiveAPI,
  spreadsheetAPI,
  subtitleAPI,
  ebookAPI,
  fontAPI,
  batchAPI,
} from '../../services/api';

// Get the mock functions from the axios instance
const axiosInstance = (axios.create as any)();
const mockedPost = axiosInstance.post;
const mockedGet = axiosInstance.get;

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedPost.mockResolvedValue({ data: {} });
    mockedGet.mockResolvedValue({ data: {} });
  });

  describe('imageAPI', () => {
    it('should call POST /api/image/convert with FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'test-123', output_file: 'output.png' },
      });

      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
      const options = { outputFormat: 'png' };

      await imageAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/image/convert',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data',
          }),
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('png');
    });

    it('should include quality, width, height in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'test-123', output_file: 'output.png' },
      });

      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
      const options = { outputFormat: 'png', quality: 90, width: 800, height: 600 };

      await imageAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('quality')).toBe('90');
      expect(formData.get('width')).toBe('800');
      expect(formData.get('height')).toBe('600');
    });

    it('should call GET /api/image/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['jpg', 'png'], output_formats: ['jpg', 'png', 'webp'] },
      });

      const result = await imageAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/image/formats');
      expect(result).toEqual({
        input_formats: ['jpg', 'png'],
        output_formats: ['jpg', 'png', 'webp'],
      });
    });

    it('should return correct download URL', () => {
      const url = imageAPI.downloadFile('test.png');
      expect(url).toBe('/api/image/download/test.png');
    });
  });

  describe('videoAPI', () => {
    it('should call POST /api/video/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'video-123', output_file: 'output.mp4' },
      });

      const file = new File(['video'], 'test.mov', { type: 'video/quicktime' });
      const options = { outputFormat: 'mp4' };

      await videoAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/video/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('mp4');
    });

    it('should include codec, resolution, bitrate in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'video-123', output_file: 'output.mp4' },
      });

      const file = new File(['video'], 'test.mov', { type: 'video/quicktime' });
      const options = {
        outputFormat: 'mp4',
        codec: 'h264',
        resolution: '1920x1080',
        bitrate: '5M',
      };

      await videoAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('codec')).toBe('h264');
      expect(formData.get('resolution')).toBe('1920x1080');
      expect(formData.get('bitrate')).toBe('5M');
    });

    it('should call GET /api/video/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['mov', 'avi'], output_formats: ['mp4', 'webm'] },
      });

      const result = await videoAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/video/formats');
      expect(result).toEqual({
        input_formats: ['mov', 'avi'],
        output_formats: ['mp4', 'webm'],
      });
    });

    it('should track upload progress', async () => {
      const mockOnProgress = vi.fn();
      let progressCallback: any;

      mockedPost.mockImplementation((url, data, config) => {
        progressCallback = config.onUploadProgress;
        return Promise.resolve({ data: {} });
      });

      const file = new File(['video'], 'test.mov');
      await videoAPI.convert(file, {
        outputFormat: 'mp4',
        onUploadProgress: mockOnProgress,
      });

      // Simulate progress event
      progressCallback({ loaded: 50, total: 100 });

      expect(mockOnProgress).toHaveBeenCalledWith(50);
    });
  });

  describe('audioAPI', () => {
    it('should call POST /api/audio/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'audio-123', output_file: 'output.mp3' },
      });

      const file = new File(['audio'], 'test.wav', { type: 'audio/wav' });
      const options = { outputFormat: 'mp3' };

      await audioAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/audio/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('mp3');
    });

    it('should include bitrate, sample_rate, channels in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'audio-123', output_file: 'output.mp3' },
      });

      const file = new File(['audio'], 'test.wav', { type: 'audio/wav' });
      const options = {
        outputFormat: 'mp3',
        bitrate: '320k',
        sampleRate: 44100,
        channels: 2,
      };

      await audioAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('bitrate')).toBe('320k');
      expect(formData.get('sample_rate')).toBe('44100');
      expect(formData.get('channels')).toBe('2');
    });

    it('should call GET /api/audio/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['wav', 'flac'], output_formats: ['mp3', 'aac', 'ogg'] },
      });

      const result = await audioAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/audio/formats');
      expect(result).toEqual({
        input_formats: ['wav', 'flac'],
        output_formats: ['mp3', 'aac', 'ogg'],
      });
    });

    it('should track upload progress', async () => {
      const mockOnProgress = vi.fn();
      let progressCallback: any;

      mockedPost.mockImplementation((url, data, config) => {
        progressCallback = config.onUploadProgress;
        return Promise.resolve({ data: {} });
      });

      const file = new File(['audio'], 'test.wav');
      await audioAPI.convert(file, {
        outputFormat: 'mp3',
        onUploadProgress: mockOnProgress,
      });

      // Simulate progress event
      progressCallback({ loaded: 75, total: 100 });

      expect(mockOnProgress).toHaveBeenCalledWith(75);
    });
  });

  describe('documentAPI', () => {
    it('should call POST /api/document/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'doc-123', output_file: 'output.pdf' },
      });

      const file = new File(['document'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const options = { outputFormat: 'pdf' };

      await documentAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/document/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('pdf');
    });

    it('should include preserve_formatting, toc in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'doc-123', output_file: 'output.pdf' },
      });

      const file = new File(['document'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const options = {
        outputFormat: 'pdf',
        preserveFormatting: true,
        toc: true,
      };

      await documentAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('preserve_formatting')).toBe('true');
      expect(formData.get('toc')).toBe('true');
    });

    it('should call GET /api/document/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['docx', 'odt'], output_formats: ['pdf', 'txt', 'html'] },
      });

      const result = await documentAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/document/formats');
      expect(result).toEqual({
        input_formats: ['docx', 'odt'],
        output_formats: ['pdf', 'txt', 'html'],
      });
    });

    it('should track upload progress', async () => {
      const mockOnProgress = vi.fn();
      let progressCallback: any;

      mockedPost.mockImplementation((url, data, config) => {
        progressCallback = config.onUploadProgress;
        return Promise.resolve({ data: {} });
      });

      const file = new File(['document'], 'test.docx');
      await documentAPI.convert(file, {
        outputFormat: 'pdf',
        onUploadProgress: mockOnProgress,
      });

      // Simulate progress event
      progressCallback({ loaded: 100, total: 100 });

      expect(mockOnProgress).toHaveBeenCalledWith(100);
    });
  });

  describe('dataAPI', () => {
    it('should call POST /api/data/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'data-123', output_file: 'output.json' },
      });

      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      const options = { outputFormat: 'json' };

      await dataAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/data/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('json');
    });

    it('should include encoding, delimiter, pretty in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'data-123', output_file: 'output.json' },
      });

      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      const options = {
        outputFormat: 'json',
        encoding: 'utf-8',
        delimiter: ',',
        pretty: true,
      };

      await dataAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('encoding')).toBe('utf-8');
      expect(formData.get('delimiter')).toBe(',');
      expect(formData.get('pretty')).toBe('true');
    });

    it('should call GET /api/data/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['csv', 'json'], output_formats: ['csv', 'json', 'xml'] },
      });

      const result = await dataAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/data/formats');
      expect(result).toEqual({
        input_formats: ['csv', 'json'],
        output_formats: ['csv', 'json', 'xml'],
      });
    });

    it('should return correct download URL', () => {
      const url = dataAPI.downloadFile('test.json');
      expect(url).toBe('/api/data/download/test.json');
    });
  });

  describe('archiveAPI', () => {
    it('should call POST /api/archive/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'archive-123', output_file: 'output.zip' },
      });

      const file = new File(['archive'], 'test.tar', { type: 'application/x-tar' });
      const options = { outputFormat: 'zip' };

      await archiveAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/archive/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('zip');
    });

    it('should include compression_level in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'archive-123', output_file: 'output.zip' },
      });

      const file = new File(['archive'], 'test.tar', { type: 'application/x-tar' });
      const options = {
        outputFormat: 'zip',
        compressionLevel: 9,
      };

      await archiveAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('compression_level')).toBe('9');
    });

    it('should call GET /api/archive/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['zip', 'tar', 'rar'], output_formats: ['zip', 'tar', '7z'] },
      });

      const result = await archiveAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/archive/formats');
      expect(result).toEqual({
        input_formats: ['zip', 'tar', 'rar'],
        output_formats: ['zip', 'tar', '7z'],
      });
    });

    it('should return correct download URL', () => {
      const url = archiveAPI.downloadFile('test.zip');
      expect(url).toBe('/api/archive/download/test.zip');
    });
  });

  describe('spreadsheetAPI', () => {
    it('should call POST /api/spreadsheet/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'sheet-123', output_file: 'output.csv' },
      });

      const file = new File(['spreadsheet'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const options = { outputFormat: 'csv' };

      await spreadsheetAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/spreadsheet/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('csv');
    });

    it('should include sheet_name, encoding, delimiter in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'sheet-123', output_file: 'output.csv' },
      });

      const file = new File(['spreadsheet'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const options = {
        outputFormat: 'csv',
        sheetName: 'Sheet1',
        encoding: 'utf-8',
        delimiter: ';',
      };

      await spreadsheetAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('sheet_name')).toBe('Sheet1');
      expect(formData.get('encoding')).toBe('utf-8');
      expect(formData.get('delimiter')).toBe(';');
    });

    it('should call GET /api/spreadsheet/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['xlsx', 'ods'], output_formats: ['csv', 'xlsx', 'pdf'] },
      });

      const result = await spreadsheetAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/spreadsheet/formats');
      expect(result).toEqual({
        input_formats: ['xlsx', 'ods'],
        output_formats: ['csv', 'xlsx', 'pdf'],
      });
    });

    it('should return correct download URL', () => {
      const url = spreadsheetAPI.downloadFile('test.csv');
      expect(url).toBe('/api/spreadsheet/download/test.csv');
    });
  });

  describe('subtitleAPI', () => {
    it('should call POST /api/subtitle/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'sub-123', output_file: 'output.srt' },
      });

      const file = new File(['subtitle'], 'test.vtt', { type: 'text/vtt' });
      const options = { outputFormat: 'srt' };

      await subtitleAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/subtitle/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('srt');
    });

    it('should include encoding, fps, keep_html_tags in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'sub-123', output_file: 'output.srt' },
      });

      const file = new File(['subtitle'], 'test.vtt', { type: 'text/vtt' });
      const options = {
        outputFormat: 'srt',
        encoding: 'utf-8',
        fps: 23.976,
        keepHtmlTags: true,
      };

      await subtitleAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('encoding')).toBe('utf-8');
      expect(formData.get('fps')).toBe('23.976');
      expect(formData.get('keep_html_tags')).toBe('true');
    });

    it('should call POST /api/subtitle/adjust-timing', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'sub-123', output_file: 'adjusted.srt' },
      });

      const file = new File(['subtitle'], 'test.srt', { type: 'text/plain' });
      const offsetMs = 2000;

      await subtitleAPI.adjustTiming(file, offsetMs);

      expect(mockedPost).toHaveBeenCalledWith(
        '/subtitle/adjust-timing',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('offset_ms')).toBe('2000');
    });

    it('should call GET /api/subtitle/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['srt', 'vtt', 'ass'], output_formats: ['srt', 'vtt', 'ass', 'sub'] },
      });

      const result = await subtitleAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/subtitle/formats');
      expect(result).toEqual({
        input_formats: ['srt', 'vtt', 'ass'],
        output_formats: ['srt', 'vtt', 'ass', 'sub'],
      });
    });

    it('should return correct download URL', () => {
      const url = subtitleAPI.downloadFile('test.srt');
      expect(url).toBe('/api/subtitle/download/test.srt');
    });
  });

  describe('ebookAPI', () => {
    it('should call POST /api/ebook/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'ebook-123', output_file: 'output.epub' },
      });

      const file = new File(['ebook'], 'test.mobi', { type: 'application/x-mobipocket-ebook' });
      const options = { outputFormat: 'epub' };

      await ebookAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/ebook/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('epub');
    });

    it('should call GET /api/ebook/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['epub', 'mobi', 'azw3'], output_formats: ['epub', 'mobi', 'pdf'] },
      });

      const result = await ebookAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/ebook/formats');
      expect(result).toEqual({
        input_formats: ['epub', 'mobi', 'azw3'],
        output_formats: ['epub', 'mobi', 'pdf'],
      });
    });

    it('should return correct download URL', () => {
      const url = ebookAPI.downloadFile('test.epub');
      expect(url).toBe('/api/ebook/download/test.epub');
    });

    it('should track upload progress', async () => {
      const mockOnProgress = vi.fn();
      let progressCallback: any;

      mockedPost.mockImplementation((url, data, config) => {
        progressCallback = config.onUploadProgress;
        return Promise.resolve({ data: {} });
      });

      const file = new File(['ebook'], 'test.mobi');
      await ebookAPI.convert(file, {
        outputFormat: 'epub',
        onUploadProgress: mockOnProgress,
      });

      // Simulate progress event
      progressCallback({ loaded: 80, total: 100 });

      expect(mockOnProgress).toHaveBeenCalledWith(80);
    });
  });

  describe('fontAPI', () => {
    it('should call POST /api/font/convert', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'font-123', output_file: 'output.woff2' },
      });

      const file = new File(['font'], 'test.ttf', { type: 'font/ttf' });
      const options = { outputFormat: 'woff2' };

      await fontAPI.convert(file, options);

      expect(mockedPost).toHaveBeenCalledWith(
        '/font/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('output_format')).toBe('woff2');
    });

    it('should include subset_text, optimize in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: { session_id: 'font-123', output_file: 'output.woff2' },
      });

      const file = new File(['font'], 'test.ttf', { type: 'font/ttf' });
      const options = {
        outputFormat: 'woff2',
        subsetText: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
        optimize: true,
      };

      await fontAPI.convert(file, options);

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('subset_text')).toBe('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz');
      expect(formData.get('optimize')).toBe('true');
    });

    it('should call GET /api/font/formats', async () => {
      mockedGet.mockResolvedValue({
        data: { input_formats: ['ttf', 'otf'], output_formats: ['woff', 'woff2', 'eot'] },
      });

      const result = await fontAPI.getFormats();

      expect(mockedGet).toHaveBeenCalledWith('/font/formats');
      expect(result).toEqual({
        input_formats: ['ttf', 'otf'],
        output_formats: ['woff', 'woff2', 'eot'],
      });
    });

    it('should return correct download URL', () => {
      const url = fontAPI.downloadFile('test.woff2');
      expect(url).toBe('/api/font/download/test.woff2');
    });
  });

  describe('batchAPI', () => {
    it('should call POST /api/batch/convert with multiple files', async () => {
      mockedPost.mockResolvedValue({
        data: {
          session_id: 'batch-123',
          total_files: 3,
          successful: 3,
          failed: 0,
          results: [],
          message: 'Batch conversion completed',
        },
      });

      const files = [
        new File(['1'], 'file1.jpg'),
        new File(['2'], 'file2.jpg'),
        new File(['3'], 'file3.jpg'),
      ];

      await batchAPI.convert(files, { outputFormat: 'png' });

      expect(mockedPost).toHaveBeenCalledWith(
        '/batch/convert',
        expect.any(FormData),
        expect.objectContaining({
          onUploadProgress: expect.any(Function),
        })
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.getAll('files')).toHaveLength(3);
      expect(formData.get('output_format')).toBe('png');
    });

    it('should include all files in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: {
          session_id: 'batch-123',
          total_files: 2,
          successful: 2,
          failed: 0,
          results: [],
          message: 'Batch conversion completed',
        },
      });

      const file1 = new File(['content1'], 'test1.jpg', { type: 'image/jpeg' });
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' });
      const files = [file1, file2];

      await batchAPI.convert(files, { outputFormat: 'png' });

      const formData = mockedPost.mock.calls[0][1] as FormData;
      const filesArray = formData.getAll('files');
      expect(filesArray).toContain(file1);
      expect(filesArray).toContain(file2);
    });

    it('should include parallel flag in FormData', async () => {
      mockedPost.mockResolvedValue({
        data: {
          session_id: 'batch-123',
          total_files: 1,
          successful: 1,
          failed: 0,
          results: [],
          message: 'Batch conversion completed',
        },
      });

      const files = [new File(['test'], 'test.jpg')];

      await batchAPI.convert(files, { outputFormat: 'png' });

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('parallel')).toBe('true');
    });

    it('should call POST /api/batch/download-zip', async () => {
      mockedPost.mockResolvedValue({
        data: { zip_file: 'batch-123.zip', download_url: '/api/batch/download/batch-123.zip' },
      });

      const sessionId = 'batch-123';
      const filenames = ['output1.png', 'output2.png', 'output3.png'];

      await batchAPI.createZip(sessionId, filenames);

      expect(mockedPost).toHaveBeenCalledWith(
        '/batch/download-zip',
        expect.any(FormData)
      );

      const formData = mockedPost.mock.calls[0][1] as FormData;
      expect(formData.get('session_id')).toBe('batch-123');
      expect(formData.getAll('filenames')).toEqual(['output1.png', 'output2.png', 'output3.png']);
    });
  });
});
