import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { subtitleAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';

const SUBTITLE_FORMATS = ['srt', 'vtt', 'ass', 'ssa', 'sub'];

const ENCODINGS = [
  { value: 'utf-8', label: 'UTF-8 (Default)' },
  { value: 'utf-16', label: 'UTF-16' },
  { value: 'latin-1', label: 'Latin-1' },
  { value: 'ascii', label: 'ASCII' },
];

const FPS_PRESETS = [
  { value: 23.976, label: '23.976 (Film)' },
  { value: 24, label: '24 (Cinema)' },
  { value: 25, label: '25 (PAL)' },
  { value: 29.97, label: '29.97 (NTSC)' },
  { value: 30, label: '30' },
  { value: 60, label: '60' },
];

export const SubtitleConverter: React.FC = () => {
  const { t } = useTranslation();
  const [encoding, setEncoding] = useState<string>('utf-8');
  const [fps, setFps] = useState<number>(23.976);
  const [keepHtmlTags, setKeepHtmlTags] = useState<boolean>(false);
  const [timingOffset, setTimingOffset] = useState<number>(0);
  const [adjustTimingMode, setAdjustTimingMode] = useState<boolean>(false);

  const converter = useConverter({ defaultOutputFormat: 'srt' });

  const handleConvert = async () => {
    if (adjustTimingMode) {
      await converter.handleConvert(subtitleAPI.adjustTiming as any, { timingOffset });
    } else {
      await converter.handleConvert(subtitleAPI, { encoding, fps, keepHtmlTags });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.subtitle.title')}</h2>

        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Supported formats:</strong> SRT (SubRip), VTT (WebVTT), ASS/SSA (Advanced SubStation Alpha), SUB (MicroDVD)
          </p>
        </div>

        {!converter.selectedFile ? (
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={SUBTITLE_FORMATS}
            fileType="subtitle"
          />
        ) : (
          <div
            className="space-y-6 relative"
            onDragOver={converter.handleDragOver}
            onDragLeave={converter.handleDragLeave}
            onDrop={converter.handleDrop}
          >
            {converter.isDraggingOver && (
              <div className="absolute inset-0 z-10 bg-primary-500 bg-opacity-20 border-4 border-primary-500 border-dashed rounded-lg flex items-center justify-center">
                <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
                  <p className="text-primary-600 font-semibold text-lg">Drop to replace file</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">File:</span> {converter.selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Size:</span>{' '}
                {(converter.selectedFile.size / 1024).toFixed(2)} KB
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 {t('dropzone.dragActive')}
              </p>
            </div>

            <div className="border-b border-gray-200">
              <div className="flex space-x-4">
                <button
                  className={`py-2 px-4 font-medium border-b-2 transition-colors ${
                    !adjustTimingMode
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setAdjustTimingMode(false)}
                >
                  Convert Format
                </button>
                <button
                  className={`py-2 px-4 font-medium border-b-2 transition-colors ${
                    adjustTimingMode
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setAdjustTimingMode(true)}
                >
                  Adjust Timing
                </button>
              </div>
            </div>

            {!adjustTimingMode ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Output Format
                    </label>
                    <select
                      value={converter.outputFormat}
                      onChange={(e) => converter.setOutputFormat(e.target.value)}
                      className="input"
                      disabled={converter.status === 'converting'}
                    >
                      {SUBTITLE_FORMATS.map((format) => (
                        <option key={format} value={format}>
                          {format.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Encoding
                    </label>
                    <select
                      value={encoding}
                      onChange={(e) => setEncoding(e.target.value)}
                      className="input"
                      disabled={converter.status === 'converting'}
                    >
                      {ENCODINGS.map((enc) => (
                        <option key={enc.value} value={enc.value}>
                          {enc.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {converter.outputFormat === 'sub' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Frame Rate (FPS)
                      </label>
                      <select
                        value={fps}
                        onChange={(e) => setFps(Number(e.target.value))}
                        className="input"
                        disabled={converter.status === 'converting'}
                      >
                        {FPS_PRESETS.map((preset) => (
                          <option key={preset.value} value={preset.value}>
                            {preset.label}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        Required for SUB format timing
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      HTML Tags
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={keepHtmlTags}
                        onChange={(e) => setKeepHtmlTags(e.target.checked)}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        disabled={converter.status === 'converting'}
                      />
                      <span className="text-sm text-gray-600">
                        Keep HTML formatting tags
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Preserve &lt;b&gt;, &lt;i&gt;, etc.
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Offset (milliseconds)
                  </label>
                  <input
                    type="number"
                    value={timingOffset}
                    onChange={(e) => setTimingOffset(Number(e.target.value))}
                    placeholder="e.g., 2000 (delay) or -2000 (advance)"
                    className="input w-full"
                    disabled={converter.status === 'converting'}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Positive = delay subtitles, Negative = advance subtitles
                  </p>
                  <p className="text-xs text-gray-500">
                    Example: +2000ms delays by 2 seconds, -1500ms advances by 1.5 seconds
                  </p>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Filename (Optional)
              </label>
              <input
                type="text"
                value={converter.customFilename}
                onChange={(e) => converter.setCustomFilename(e.target.value)}
                placeholder={t('common.customFilenamePlaceholder')}
                className="input w-full"
                disabled={converter.status === 'converting'}
              />
              <p className="text-xs text-gray-500 mt-1">
                {t('common.customFilenameHint')}
              </p>
            </div>

            {window.electron?.isElectron && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Directory (Optional)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={converter.outputDirectory || t('common.defaultDownloads')}
                    readOnly
                    className="input flex-1"
                    disabled={converter.status === 'converting'}
                  />
                  <Button
                    onClick={converter.handleSelectOutputDirectory}
                    variant="secondary"
                    disabled={converter.status === 'converting'}
                  >
                    Browse
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  💡 When set, files will be saved directly to this directory
                </p>
              </div>
            )}

            {converter.status === 'converting' && converter.showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{converter.progress?.message || t('common.processing')}</span>
                  <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${converter.progress?.progress || 0}%` }}
                  />
                </div>
              </div>
            )}

            {converter.error && converter.showFeedback && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {converter.error}
              </div>
            )}

            {converter.status === 'completed' && converter.showFeedback && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                {adjustTimingMode
                  ? `Subtitle timing adjusted by ${timingOffset}ms successfully!`
                  : 'Subtitle conversion completed successfully!'}
              </div>
            )}

            <div className="flex gap-4">
              {converter.status === 'idle' || converter.status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {adjustTimingMode ? 'Adjust Timing' : 'Convert Subtitle'}
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    Reset
                  </Button>
                </>
              ) : converter.status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  {adjustTimingMode ? 'Adjusting...' : 'Converting...'}
                </Button>
              ) : converter.status === 'completed' ? (
                <>
                  <Button onClick={converter.handleDownload} className="flex-1">
                    Download
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    Convert Another
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
