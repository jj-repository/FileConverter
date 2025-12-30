import i18n from '../i18n';

/**
 * Maps technical error messages to user-friendly translation keys
 * @param error - The technical error message from the backend/API
 * @returns Translation key for user-friendly error message
 */
export const getFriendlyErrorMessage = (error: string): string => {
  if (!error) {
    return i18n.t('errors.unknown');
  }

  const errorLower = error.toLowerCase();

  // FFmpeg and conversion errors
  if (
    errorLower.includes('ffmpeg') ||
    errorLower.includes('codec') ||
    errorLower.includes('encoding') ||
    errorLower.includes('decoding') ||
    errorLower.includes('corrupted') ||
    errorLower.includes('invalid stream')
  ) {
    return i18n.t('errors.conversionFailed');
  }

  // File not found errors
  if (
    errorLower.includes('file not found') ||
    errorLower.includes('no such file') ||
    errorLower.includes('enoent') ||
    errorLower.includes('does not exist')
  ) {
    return i18n.t('errors.fileNotFound');
  }

  // Timeout errors
  if (
    errorLower.includes('timeout') ||
    errorLower.includes('timed out') ||
    errorLower.includes('deadline exceeded') ||
    errorLower.includes('took too long')
  ) {
    return i18n.t('errors.timeout');
  }

  // Format errors
  if (
    errorLower.includes('format not supported') ||
    errorLower.includes('unsupported format') ||
    errorLower.includes('invalid format') ||
    errorLower.includes('unknown format') ||
    errorLower.includes('format error')
  ) {
    return i18n.t('errors.formatError');
  }

  // Network errors
  if (
    errorLower.includes('network') ||
    errorLower.includes('connection') ||
    errorLower.includes('econnrefused') ||
    errorLower.includes('econnreset') ||
    errorLower.includes('etimedout') ||
    errorLower.includes('fetch failed') ||
    errorLower.includes('failed to fetch')
  ) {
    return i18n.t('errors.networkError');
  }

  // File too large errors
  if (
    errorLower.includes('file too large') ||
    errorLower.includes('file size') ||
    errorLower.includes('exceeds maximum') ||
    errorLower.includes('too big') ||
    errorLower.includes('payload too large') ||
    errorLower.includes('413')
  ) {
    return i18n.t('errors.fileTooLarge');
  }

  // Permission errors
  if (
    errorLower.includes('permission') ||
    errorLower.includes('access denied') ||
    errorLower.includes('eacces') ||
    errorLower.includes('unauthorized') ||
    errorLower.includes('forbidden')
  ) {
    return i18n.t('errors.permissionDenied');
  }

  // Disk space errors
  if (
    errorLower.includes('no space') ||
    errorLower.includes('disk full') ||
    errorLower.includes('enospc') ||
    errorLower.includes('out of space')
  ) {
    return i18n.t('errors.diskSpace');
  }

  // Server errors
  if (
    errorLower.includes('500') ||
    errorLower.includes('internal server error') ||
    errorLower.includes('server error')
  ) {
    return i18n.t('errors.serverError');
  }

  // Default fallback
  return i18n.t('errors.unknown');
};

/**
 * Gets a friendly error message with fallback to raw error
 * @param error - The technical error message
 * @returns User-friendly error message string
 */
export const getErrorMessage = (error: string): string => {
  const friendlyMessage = getFriendlyErrorMessage(error);

  // If translation is missing, return a generic message
  if (friendlyMessage === error) {
    return i18n.t('errors.unknown');
  }

  return friendlyMessage;
};
