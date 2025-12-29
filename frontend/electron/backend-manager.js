const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');

class BackendManager {
  constructor(isDev = false) {
    this.isDev = isDev;
    this.process = null;
    this.port = 8000;
    this.isReady = false;
  }

  /**
   * Get the backend executable path
   * In production, uses the bundled PyInstaller executable
   * In development, returns null (will use Python + uvicorn)
   */
  getBackendExecutablePath() {
    if (this.isDev) {
      return null; // Use Python in dev mode
    } else {
      // In production, use the bundled backend-server executable
      const exeName = process.platform === 'win32' ? 'backend-server.exe' : 'backend-server';
      return path.join(process.resourcesPath, 'backend', 'dist', exeName);
    }
  }

  /**
   * Get the Python executable path (only used in dev mode)
   */
  getPythonPath() {
    if (this.isDev) {
      // In development, use the venv Python
      const backendPath = path.join(__dirname, '../../backend');
      if (process.platform === 'win32') {
        return path.join(backendPath, 'venv/Scripts/python.exe');
      } else {
        return path.join(backendPath, 'venv/bin/python');
      }
    } else {
      // Not used in production - using bundled executable instead
      return null;
    }
  }

  /**
   * Get the backend directory path
   */
  getBackendPath() {
    if (this.isDev) {
      return path.join(__dirname, '../../backend');
    } else {
      // In production, backend is in resources
      const { app } = require('electron');
      return path.join(process.resourcesPath, 'backend');
    }
  }

  /**
   * Check if a port is available
   */
  async isPortAvailable(port) {
    return new Promise((resolve) => {
      const server = net.createServer();

      server.once('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          resolve(false);
        } else {
          resolve(false);
        }
      });

      server.once('listening', () => {
        server.close();
        resolve(true);
      });

      server.listen(port);
    });
  }

  /**
   * Find an available port
   */
  async findAvailablePort() {
    let port = this.port;
    while (port < this.port + 10) {
      if (await this.isPortAvailable(port)) {
        return port;
      }
      port++;
    }
    throw new Error('No available ports found');
  }

  /**
   * Wait for the server to be ready
   */
  async waitForServer(timeout = 30000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      try {
        const response = await fetch(`http://localhost:${this.port}/health`);
        if (response.ok) {
          return true;
        }
      } catch (error) {
        // Server not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    throw new Error('Backend server failed to start within timeout');
  }

  /**
   * Start the backend server
   */
  async start() {
    if (this.process) {
      console.log('Backend server is already running');
      return;
    }

    // Find available port
    this.port = await this.findAvailablePort();
    console.log(`Starting backend server on port ${this.port}`);

    const backendExecutable = this.getBackendExecutablePath();

    if (backendExecutable) {
      // Production mode - use bundled executable
      if (!fs.existsSync(backendExecutable)) {
        throw new Error(`Backend executable not found at ${backendExecutable}`);
      }

      const args = [
        '--host', '0.0.0.0',
        '--port', this.port.toString()
      ];

      console.log(`Executing: ${backendExecutable} ${args.join(' ')}`);

      this.process = spawn(backendExecutable, args, {
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      });
    } else {
      // Development mode - use Python + uvicorn
      const pythonPath = this.getPythonPath();
      const backendPath = this.getBackendPath();

      // Check if Python exists
      if (!fs.existsSync(pythonPath)) {
        throw new Error(`Python not found at ${pythonPath}. Please ensure the virtual environment is set up.`);
      }

      // Start the server
      const args = [
        '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', this.port.toString(),
        '--log-level', 'info'
      ];

      console.log(`Executing: ${pythonPath} ${args.join(' ')}`);
      console.log(`Working directory: ${backendPath}`);

      this.process = spawn(pythonPath, args, {
        cwd: backendPath,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      });
    }

    // Handle stdout
    this.process.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    // Handle stderr
    this.process.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    // Handle process exit
    this.process.on('exit', (code, signal) => {
      console.log(`Backend process exited with code ${code} and signal ${signal}`);
      this.process = null;
      this.isReady = false;
    });

    // Handle process errors
    this.process.on('error', (error) => {
      console.error('Failed to start backend process:', error);
      throw error;
    });

    // Wait for server to be ready
    await this.waitForServer();
    this.isReady = true;
    console.log('Backend server is ready');
  }

  /**
   * Stop the backend server
   */
  async stop() {
    if (!this.process) {
      return;
    }

    return new Promise((resolve) => {
      this.process.once('exit', () => {
        this.process = null;
        this.isReady = false;
        resolve();
      });

      // Send SIGTERM on Unix, kill on Windows
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', this.process.pid, '/f', '/t']);
      } else {
        this.process.kill('SIGTERM');
      }

      // Force kill after 5 seconds if still running
      setTimeout(() => {
        if (this.process) {
          this.process.kill('SIGKILL');
        }
      }, 5000);
    });
  }

  /**
   * Check if the server is running
   */
  isRunning() {
    return this.process !== null && this.isReady;
  }

  /**
   * Get the server port
   */
  getPort() {
    return this.port;
  }
}

module.exports = BackendManager;
