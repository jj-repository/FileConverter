/**
 * Script to create test fixture files for E2E tests
 * Run with: node e2e/fixtures/create-test-files.js
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create a minimal 1x1 pixel PNG image (base64 decoded)
// This is a valid PNG file
const pngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
const pngBuffer = Buffer.from(pngBase64, 'base64');

// Create a minimal text file
const textContent = 'This is a test file for E2E testing.';

// Create a minimal JSON file
const jsonContent = JSON.stringify({ test: 'data', value: 123 }, null, 2);

// Write files
const fixturesDir = __dirname;

fs.writeFileSync(path.join(fixturesDir, 'test-image.png'), pngBuffer);
fs.writeFileSync(path.join(fixturesDir, 'test-file.txt'), textContent);
fs.writeFileSync(path.join(fixturesDir, 'test-data.json'), jsonContent);

console.log('✅ Test fixture files created:');
console.log('  - test-image.png (1x1 pixel PNG)');
console.log('  - test-file.txt');
console.log('  - test-data.json');
