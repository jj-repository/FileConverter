#!/usr/bin/env node

/**
 * Test script to validate desktop app setup
 * This checks all prerequisites before running the Electron app
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

console.log('🔍 FileConverter Desktop App - Setup Validation\n');

const checks = {
  passed: 0,
  failed: 0,
  warnings: 0
};

function pass(msg) {
  console.log(`✅ ${msg}`);
  checks.passed++;
}

function fail(msg) {
  console.log(`❌ ${msg}`);
  checks.failed++;
}

function warn(msg) {
  console.log(`⚠️  ${msg}`);
  checks.warnings++;
}

// Check 1: Electron files exist
console.log('📦 Checking Electron files...');
const electronFiles = ['main.js', 'preload.js', 'backend-manager.js'];
electronFiles.forEach(file => {
  const filePath = path.join(__dirname, 'electron', file);
  if (fs.existsSync(filePath)) {
    pass(`Found electron/${file}`);
  } else {
    fail(`Missing electron/${file}`);
  }
});

// Check 2: Node modules
console.log('\n📚 Checking dependencies...');
const requiredModules = ['electron', 'electron-builder', 'concurrently', 'wait-on'];
requiredModules.forEach(module => {
  const modulePath = path.join(__dirname, 'node_modules', module);
  if (fs.existsSync(modulePath)) {
    pass(`Dependency installed: ${module}`);
  } else {
    fail(`Missing dependency: ${module}`);
  }
});

// Check 3: Package.json scripts
console.log('\n📝 Checking package.json scripts...');
const packageJson = require('./package.json');
if (packageJson.scripts['electron:dev']) {
  pass('electron:dev script configured');
} else {
  fail('electron:dev script missing');
}

if (packageJson.scripts['electron:build']) {
  pass('electron:build script configured');
} else {
  fail('electron:build script missing');
}

// Check 4: Backend directory
console.log('\n🐍 Checking backend setup...');
const backendPath = path.join(__dirname, '..', 'backend');
if (fs.existsSync(backendPath)) {
  pass('Backend directory exists');

  // Check venv
  const venvPath = path.join(backendPath, 'venv');
  if (fs.existsSync(venvPath)) {
    pass('Python virtual environment exists');

    // Check for Python executable
    const pythonExe = process.platform === 'win32'
      ? path.join(venvPath, 'Scripts', 'python.exe')
      : path.join(venvPath, 'bin', 'python');

    if (fs.existsSync(pythonExe)) {
      pass('Python executable found in venv');
    } else {
      fail('Python executable not found in venv');
    }
  } else {
    fail('Python virtual environment not found');
  }

  // Check requirements.txt
  const reqPath = path.join(backendPath, 'requirements.txt');
  if (fs.existsSync(reqPath)) {
    pass('requirements.txt exists');
  } else {
    fail('requirements.txt not found');
  }
} else {
  fail('Backend directory not found');
}

// Check 5: System dependencies
console.log('\n🔧 Checking system dependencies...');

function checkCommand(cmd, name) {
  return new Promise((resolve) => {
    const proc = spawn(cmd, ['--version'], { shell: true, stdio: 'pipe' });

    let found = false;
    proc.on('error', () => {
      fail(`${name} not found in PATH`);
      resolve(false);
    });

    proc.on('exit', (code) => {
      if (code === 0 && !found) {
        pass(`${name} is installed`);
        found = true;
        resolve(true);
      } else if (!found) {
        warn(`${name} check returned code ${code} (may not be installed)`);
        resolve(false);
      }
    });

    // Timeout after 2 seconds
    setTimeout(() => {
      if (!found) {
        proc.kill();
        warn(`${name} check timed out`);
        resolve(false);
      }
    }, 2000);
  });
}

(async () => {
  await checkCommand('ffmpeg', 'FFmpeg');
  await checkCommand('pandoc', 'Pandoc');

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 Validation Summary:');
  console.log('='.repeat(50));
  console.log(`✅ Passed: ${checks.passed}`);
  console.log(`❌ Failed: ${checks.failed}`);
  console.log(`⚠️  Warnings: ${checks.warnings}`);
  console.log('='.repeat(50));

  if (checks.failed === 0) {
    console.log('\n🎉 All critical checks passed!');
    console.log('\n📝 Next steps:');
    console.log('   1. Run: npm run electron:dev');
    console.log('   2. The desktop app should launch automatically');
    console.log('   3. Try converting a file to test functionality\n');

    if (checks.warnings > 0) {
      console.log('⚠️  Note: Some warnings were found.');
      console.log('   FFmpeg and Pandoc are required for video/document conversion.');
      console.log('   Install them to enable all features.\n');
    }
  } else {
    console.log('\n❌ Some checks failed!');
    console.log('   Please fix the issues above before running the app.\n');
    process.exit(1);
  }
})();
