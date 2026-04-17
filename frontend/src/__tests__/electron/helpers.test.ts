import { describe, it, expect } from 'vitest';
import { createRequire } from 'node:module';
import path from 'node:path';

// helpers.cjs is CommonJS; use createRequire so the test stays ESM.
const require = createRequire(import.meta.url);
const {
  DOWNLOAD_MAX_BYTES,
  isPathInAllowedRoots,
  isDownloadPathSafe,
  isUnderSizeCap,
} = require('../../../electron/helpers.cjs') as {
  DOWNLOAD_MAX_BYTES: number;
  isPathInAllowedRoots: (p: string, roots: string[]) => boolean;
  isDownloadPathSafe: (dir: string, outputPath: string) => boolean;
  isUnderSizeCap: (n: number, max?: number) => boolean;
};

describe('Electron helpers (H-NEW-2 / S4 / F13 coverage)', () => {
  describe('isPathInAllowedRoots', () => {
    const home = '/home/alice';
    const downloads = '/home/alice/Downloads';
    const userData = '/home/alice/.config/FileConverter';
    const tmp = '/tmp';
    const roots = [home, userData, downloads, tmp];

    it('accepts a path inside home', () => {
      expect(isPathInAllowedRoots('/home/alice/Documents/file.pdf', roots)).toBe(true);
    });

    it('accepts a path inside downloads', () => {
      expect(isPathInAllowedRoots('/home/alice/Downloads/a.zip', roots)).toBe(true);
    });

    it('accepts a path inside tmp', () => {
      expect(isPathInAllowedRoots('/tmp/work/foo.bin', roots)).toBe(true);
    });

    it('rejects /etc/shadow (H-NEW-2 canonical case)', () => {
      expect(isPathInAllowedRoots('/etc/shadow', roots)).toBe(false);
    });

    it('rejects /root/.ssh/id_rsa', () => {
      expect(isPathInAllowedRoots('/root/.ssh/id_rsa', roots)).toBe(false);
    });

    it('rejects prefix-confusion attack (/home/alice-evil/…)', () => {
      // Classic startsWith bug: "/home/alice-evil" startsWith "/home/alice" is true.
      // isPathInAllowedRoots uses path.relative, so this must still be rejected.
      expect(isPathInAllowedRoots('/home/alice-evil/secret.txt', roots)).toBe(false);
    });

    it('rejects root itself (rel === "")', () => {
      // Empty relative path means the input equals the root — not a filename.
      expect(isPathInAllowedRoots(home, roots)).toBe(false);
    });

    it('rejects when allowedRoots is not an array', () => {
      // @ts-expect-error intentional misuse
      expect(isPathInAllowedRoots('/home/alice/a.txt', null)).toBe(false);
    });

    it('rejects when realPath is empty', () => {
      expect(isPathInAllowedRoots('', roots)).toBe(false);
    });
  });

  describe('isDownloadPathSafe (S4)', () => {
    const dir = '/home/alice/Downloads';

    it('accepts a normal filename inside dir', () => {
      expect(isDownloadPathSafe(dir, path.join(dir, 'output.jpg'))).toBe(true);
    });

    it('rejects traversal via ..', () => {
      expect(isDownloadPathSafe(dir, path.join(dir, '..', 'etc', 'passwd'))).toBe(false);
    });

    it('rejects absolute escape', () => {
      expect(isDownloadPathSafe(dir, '/etc/passwd')).toBe(false);
    });

    it('rejects dir itself (no filename)', () => {
      expect(isDownloadPathSafe(dir, dir)).toBe(false);
    });
  });

  describe('isUnderSizeCap (F13)', () => {
    it('accepts zero', () => {
      expect(isUnderSizeCap(0)).toBe(true);
    });

    it('accepts just under 500 MB', () => {
      expect(isUnderSizeCap(DOWNLOAD_MAX_BYTES - 1)).toBe(true);
    });

    it('accepts exactly the cap', () => {
      expect(isUnderSizeCap(DOWNLOAD_MAX_BYTES)).toBe(true);
    });

    it('rejects one byte over the cap', () => {
      expect(isUnderSizeCap(DOWNLOAD_MAX_BYTES + 1)).toBe(false);
    });

    it('rejects non-number input', () => {
      // @ts-expect-error intentional misuse
      expect(isUnderSizeCap('500')).toBe(false);
    });

    it('honors a custom cap override', () => {
      expect(isUnderSizeCap(100, 50)).toBe(false);
      expect(isUnderSizeCap(50, 50)).toBe(true);
    });

    it('exposes DOWNLOAD_MAX_BYTES as 500 MB exactly', () => {
      expect(DOWNLOAD_MAX_BYTES).toBe(500 * 1024 * 1024);
    });
  });
});
