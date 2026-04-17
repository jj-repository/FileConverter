import React from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { ebookAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';
import { EBOOK_FORMATS } from '../../config/constants';


export const EbookConverter: React.FC = () => {
  const { t } = useTranslation();

  const converter = useConverter({ defaultOutputFormat: 'epub' });

  const handleConvert = async () => {
    await converter.handleConvert(ebookAPI, {});
  };

  const getStatusColor = () => {
    switch (converter.status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'converting':
      case 'uploading':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    if (converter.progress?.message) return converter.progress.message;

    switch (converter.status) {
      case 'uploading':
        return t('ebook.uploading', 'Uploading file...');
      case 'converting':
        return t('ebook.converting', 'Converting eBook...');
      case 'completed':
        return t('ebook.complete', 'Conversion complete!');
      case 'failed':
        return converter.error || t('ebook.failed', 'Conversion failed');
      default:
        return t('ebook.ready', 'Ready to convert');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">{t('converter.ebook.title')}</h3>
        <p className="text-sm text-blue-800">
          {t('ebook.description', 'Convert between eBook formats. Supports EPUB, TXT, HTML, and PDF.')}
        </p>
        <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
          <li>{t('ebook.format_epub_txt', 'EPUB to TXT: Extract plain text content')}</li>
          <li>{t('ebook.format_epub_html', 'EPUB to HTML: Export as single HTML file with styling')}</li>
          <li>{t('ebook.format_epub_pdf', 'EPUB to PDF: Generate PDF with text content')}</li>
          <li>{t('ebook.format_txt_epub', 'TXT/HTML to EPUB: Create basic EPUB eBook')}</li>
        </ul>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>{t('ebook.note_label', 'Note:')}</strong> {t('ebook.note_text', 'Conversions may lose advanced formatting, images, and metadata. EPUB is recommended for preservation of structure and content.')}
        </p>
      </div>

      <Card>
        <div className="space-y-6">
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={EBOOK_FORMATS}
            fileType="ebook"
          />

          {converter.selectedFile && (
            <>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">{t('ebook.selected_file', 'Selected file:')}</p>
                <p className="font-medium">{converter.selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(converter.selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>

              <div>
                <label htmlFor="output-format" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('ebook.output_format', 'Output Format')}
                </label>
                <select
                  id="output-format"
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="input"
                  aria-label="Select output format for ebook conversion"
                >
                  {EBOOK_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {window.electron?.isElectron && (
                <div>
                  <label htmlFor="custom-filename" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('ebook.custom_filename', 'Custom Filename (optional)')}
                  </label>
                  <input
                    id="custom-filename"
                    type="text"
                    value={converter.customFilename}
                    onChange={(e) => converter.setCustomFilename(e.target.value)}
                    placeholder={`${converter.selectedFile.name.split('.')[0]}.${converter.outputFormat}`}
                    className="input"
                  />
                </div>
              )}

              {window.electron?.isElectron && (
                <div>
                  <label htmlFor="output-directory" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('ebook.output_directory', 'Output Directory')}
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="output-directory"
                      type="text"
                      value={converter.outputDirectory || t('ebook.default_downloads', 'Default Downloads folder')}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      aria-label="Output directory path"
                    />
                    <Button
                      onClick={converter.handleSelectOutputDirectory}
                      variant="secondary"
                      aria-label="Browse for output directory"
                    >
                      {t('ebook.browse', 'Browse')}
                    </Button>
                  </div>
                </div>
              )}

              <Button
                onClick={handleConvert}
                disabled={converter.status === 'uploading' || converter.status === 'converting'}
                className="w-full"
              >
                {converter.status === 'uploading' || converter.status === 'converting' ? t('ebook.converting_short', 'Converting...') : t('ebook.convert_button', 'Convert eBook')}
              </Button>

              {converter.showFeedback && (
                <div className={`text-center ${getStatusColor()}`}>
                  <p className="font-medium">{getStatusText()}</p>
                  {converter.isUploading ? (
                    <div className="mt-2">
                      <div
                        {...converter.getUploadProgressAriaAttributes()}
                        className="w-full bg-gray-200 rounded-full h-2"
                      >
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${converter.uploadProgress}%` }}
                          aria-hidden="true"
                        />
                      </div>
                      <p className="text-sm mt-1">{converter.uploadProgress}%</p>
                    </div>
                  ) : converter.progress ? (
                    <div className="mt-2">
                      <div
                        {...converter.getProgressAriaAttributes()}
                        className="w-full bg-gray-200 rounded-full h-2"
                      >
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${converter.progress.progress}%` }}
                          aria-hidden="true"
                        />
                      </div>
                      <p className="text-sm mt-1">{converter.progress.progress}%</p>
                    </div>
                  ) : null}
                </div>
              )}

              {converter.status === 'completed' && (
                <div className="flex gap-4">
                  {!window.electron?.isElectron && converter.downloadUrl && (
                    <Button onClick={() => converter.handleDownload?.()} className="flex-1">
                      {t('ebook.download_button', 'Download Converted eBook')}
                    </Button>
                  )}
                  <Button onClick={converter.handleReset} variant="secondary">
                    {t('common.convertAnother')}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </Card>
    </div>
  );
};
