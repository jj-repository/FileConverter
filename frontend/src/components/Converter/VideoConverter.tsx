import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { videoAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';

const VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp', '3g2', 'mts', 'm2ts', 'vob', 'ts', 'ogv'];

const CODECS = [
  { value: 'libx264', label: 'H.264 (Most Compatible)' },
  { value: 'libx265', label: 'H.265/HEVC (Better Compression)' },
  { value: 'libvpx-vp9', label: 'VP9 (For WebM)' },
];

const RESOLUTIONS = [
  { value: 'original', label: 'Original' },
  { value: '480p', label: '480p (SD)' },
  { value: '720p', label: '720p (HD)' },
  { value: '1080p', label: '1080p (Full HD)' },
  { value: '4k', label: '4K (Ultra HD)' },
];

const BITRATES = [
  { value: '1M', label: '1 Mbps (Low)' },
  { value: '2M', label: '2 Mbps (Medium)' },
  { value: '5M', label: '5 Mbps (High)' },
  { value: '10M', label: '10 Mbps (Very High)' },
];

export const VideoConverter: React.FC = () => {
  const { t } = useTranslation();
  const [codec, setCodec] = useState<string>('libx264');
  const [resolution, setResolution] = useState<string>('original');
  const [bitrate, setBitrate] = useState<string>('2M');

  const converter = useConverter({ defaultOutputFormat: 'mp4' });

  const handleConvert = async () => {
    await converter.handleConvert(videoAPI, { codec, resolution, bitrate });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + ' KB';
    }
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.video.title')}</h2>

        {!converter.selectedFile ? (
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={VIDEO_FORMATS}
            fileType="video"
          />
        ) : (
          <div
            className="space-y-6 relative"
            onDragOver={converter.handleDragOver}
            onDragLeave={converter.handleDragLeave}
            onDrop={converter.handleDrop}
          >
            {/* Drag and drop overlay */}
            {converter.isDraggingOver && (
              <div className="absolute inset-0 z-10 bg-primary-500 bg-opacity-20 border-4 border-primary-500 border-dashed rounded-lg flex items-center justify-center">
                <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
                  <p className="text-primary-600 font-semibold text-lg">{t('common.dropToReplace')}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.file')}:</span> {converter.selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.size')}:</span> {formatFileSize(converter.selectedFile.size)}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 {t('dropzone.dragActive')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="output-format" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.outputFormat')}
                </label>
                <select
                  id="output-format"
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                  aria-label="Select output format for video conversion"
                >
                  {VIDEO_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="video-codec" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.video.codecLabel')}
                </label>
                <select
                  id="video-codec"
                  value={codec}
                  onChange={(e) => setCodec(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                  aria-label="Select video codec"
                >
                  {CODECS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="video-resolution" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.video.resolutionLabel')}
                </label>
                <select
                  id="video-resolution"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                  aria-label="Select video resolution"
                >
                  {RESOLUTIONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="video-bitrate" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.video.bitrateLabel')}
                </label>
                <select
                  id="video-bitrate"
                  value={bitrate}
                  onChange={(e) => setBitrate(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                  aria-label="Select video bitrate"
                >
                  {BITRATES.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="custom-filename" className="block text-sm font-medium text-gray-700 mb-2">
                {t('common.customFilename')}
              </label>
              <input
                id="custom-filename"
                type="text"
                value={converter.customFilename}
                onChange={(e) => converter.setCustomFilename(e.target.value)}
                placeholder={t('common.customFilenamePlaceholder')}
                className="input w-full"
                disabled={converter.status === 'converting'}
                aria-describedby="filename-hint"
              />
              <p id="filename-hint" className="text-xs text-gray-500 mt-1">
                {t('common.customFilenameHint')}
              </p>
            </div>

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
                    disabled={converter.status === 'converting'}
                    aria-describedby="output-directory-hint"
                    aria-label="Output directory path"
                  />
                  <Button
                    onClick={converter.handleSelectOutputDirectory}
                    variant="secondary"
                    disabled={converter.status === 'converting'}
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

            {converter.status === 'converting' && converter.showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{converter.progress?.message || t('common.processing')}</span>
                  <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
                </div>
                <div
                  {...converter.getProgressAriaAttributes()}
                  className="w-full bg-gray-200 rounded-full h-3"
                >
                  <div
                    className="bg-primary-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end px-2"
                    style={{ width: `${converter.progress?.progress || 0}%` }}
                    aria-hidden="true"
                  >
                    {(converter.progress?.progress || 0) > 10 && (
                      <span className="text-xs text-white font-medium">
                        {converter.progress?.progress.toFixed(0) || 0}%
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Video conversion may take several minutes depending on file size and settings
                </p>
              </div>
            )}

            {converter.error && converter.showFeedback && (
              <div
                {...converter.getStatusAriaAttributes()}
                className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
              >
                {converter.error}
              </div>
            )}

            {converter.status === 'completed' && converter.showFeedback && (
              <div
                {...converter.getStatusAriaAttributes()}
                className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg"
              >
                {t('messages.conversionSuccess')}
              </div>
            )}

            <div className="flex gap-4">
              {converter.status === 'idle' || converter.status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {t('converter.video.convertVideo')}
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    {t('common.reset')}
                  </Button>
                </>
              ) : converter.status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  {t('common.converting')}
                </Button>
              ) : converter.status === 'completed' ? (
                <>
                  <Button onClick={converter.handleDownload} className="flex-1">
                    {t('common.download')}
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    {t('common.convertAnother')}
                  </Button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
