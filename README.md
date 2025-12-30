# FileConverter

[![Backend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml)
[![codecov](https://codecov.io/gh/jj-repository/FileConverter/branch/main/graph/badge.svg)](https://codecov.io/gh/jj-repository/FileConverter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, full-stack file conversion platform supporting 50+ file formats with real-time progress tracking, smart caching, and batch processing.

## ✨ Features

- 🎨 **Modern UI**: Clean, responsive interface built with React and TailwindCSS
- ⚡ **Real-time Updates**: WebSocket-based progress tracking
- 🚀 **High Performance**: Smart LRU caching, concurrent processing
- 🔒 **Secure**: Input validation, rate limiting, path traversal prevention
- 📦 **Batch Conversion**: Process multiple files simultaneously
- 🎯 **10+ File Types**: Images, videos, audio, documents, archives, and more

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **System Dependencies**: FFmpeg, Pandoc, LibreOffice

### Backend Setup
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir -p uploads temp cache
uvicorn app.main:app --reload
# Backend runs at http://localhost:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

## 📖 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend**: [backend/README.md](backend/README.md)
- **Frontend**: [frontend/README.md](frontend/README.md)
- **Build Guide**: [RELEASE_BUILD_GUIDE.md](RELEASE_BUILD_GUIDE.md)

## 🧪 Testing

### Backend (192 tests)
```bash
cd backend
pytest                    # Run all tests
pytest --cov=app         # With coverage
pytest -m security       # Security tests only
```

### Frontend
```bash
cd frontend
npm test
npm run test:coverage
```

## 🏗️ Architecture

```
FileConverter/
├── backend/           # FastAPI backend (192 tests, 50%+ coverage)
│   ├── app/          # 13 routers, 14 converters
│   └── tests/        # Unit + integration tests
├── frontend/         # React + TailwindCSS
│   └── src/          # 11 converter pages
└── .github/
    └── workflows/    # CI/CD pipelines
```

## 🔒 Security

- ✅ Input validation (file type, size, extension)
- ✅ Path traversal prevention
- ✅ Rate limiting (10 connections/min per IP)
- ✅ Session management (1-hour expiration)
- ✅ Automated security scanning (bandit, safety)

## 📊 Performance

| Metric | Value |
|--------|-------|
| Cache Hit Rate | 60-80% |
| Concurrent Conversions | 100+ |
| Memory Usage | 200-500MB |
| API Response | <100ms (cached) |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file
