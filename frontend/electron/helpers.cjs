// Pure helpers extracted from main.cjs so they can be unit-tested without
// requiring the electron runtime. Keep side-effect free.

const path = require('path');

const DOWNLOAD_MAX_BYTES = 500 * 1024 * 1024; // 500 MB (H-NEW-2, F13)

/**
 * Check if realPath resolves inside one of allowedRoots.
 * Uses path.relative so it is safe against prefix-confusion bugs that
 * startsWith() has (e.g. "C:\foo" matching "C:\foobar"), and works on
 * Windows UNC paths (\\server\share).
 *
 * @param {string} realPath - already-resolved absolute path (e.g. via fs.realpathSync)
 * @param {string[]} allowedRoots - list of absolute directory roots
 * @returns {boolean}
 */
function isPathInAllowedRoots(realPath, allowedRoots) {
  if (!realPath || !Array.isArray(allowedRoots)) return false;
  return allowedRoots.some((root) => {
    if (!root) return false;
    const rel = path.relative(root, realPath);
    return rel !== '' && !rel.startsWith('..') && !path.isAbsolute(rel);
  });
}

/**
 * Check that an output path produced by path.join(dir, filename) actually
 * lives inside dir. Used for download destination validation (S4).
 *
 * @param {string} realDirectory
 * @param {string} outputPath
 * @returns {boolean}
 */
function isDownloadPathSafe(realDirectory, outputPath) {
  if (!realDirectory || !outputPath) return false;
  const rel = path.relative(realDirectory, outputPath);
  // rel === '' means outputPath === realDirectory itself — not a filename.
  return rel !== '' && !rel.startsWith('..') && !path.isAbsolute(rel);
}

/**
 * Guard for the streaming byte counter (F13). Returns true when the running
 * total is still under the hard cap.
 *
 * @param {number} currentBytes
 * @param {number} [maxBytes=DOWNLOAD_MAX_BYTES]
 * @returns {boolean}
 */
function isUnderSizeCap(currentBytes, maxBytes = DOWNLOAD_MAX_BYTES) {
  return typeof currentBytes === 'number' && currentBytes <= maxBytes;
}

module.exports = {
  DOWNLOAD_MAX_BYTES,
  isPathInAllowedRoots,
  isDownloadPathSafe,
  isUnderSizeCap,
};
