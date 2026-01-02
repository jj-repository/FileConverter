# CI/CD Pipeline Guide

Complete documentation for the FileConverter CI/CD pipeline using GitHub Actions.

## 🔄 Overview

The CI/CD pipeline consists of multiple workflows:

1. **CI Workflow** (`ci.yml`) - Main continuous integration
2. **Backend Tests** (`backend-tests.yml`) - Comprehensive backend testing
3. **Frontend Tests** (`frontend-tests.yml`) - Comprehensive frontend testing
4. **Build & Release** (`build-release.yml`) - Multi-platform builds and releases
5. **Dependabot** (`dependabot.yml`) - Automated dependency updates

## 📋 Workflow Details

### 1. CI Workflow (ci.yml)

**Triggers**: Push/PR to `main` or `develop` branches

**Jobs**:
- **backend-tests**: Tests on Python 3.11, 3.12, 3.13
  - Installs system dependencies (FFmpeg, Pandoc, LibreOffice, etc.)
  - Runs 1,393 tests with 99.90% coverage
  - Uploads coverage to Codecov

- **frontend-tests**: Tests on Node 18, 20, 22
  - Runs 934 tests (100% pass rate)
  - Generates coverage reports
  - Uploads coverage to Codecov

- **backend-lint**: Code quality checks
  - Flake8 for Python code style
  - Black for code formatting
  - isort for import sorting

- **frontend-lint**: Frontend code quality
  - TypeScript type checking
  - ESLint (if configured)

- **frontend-build**: Build verification
  - Ensures production build succeeds
  - Archives build artifacts

- **security-scan**: Security checks
  - Safety check for vulnerable dependencies
  - Bandit for Python security issues

- **ci-summary**: Final status summary
  - Aggregates all job results
  - Creates GitHub step summary
  - Fails if critical jobs fail

**Success Criteria**:
- All tests pass (backend + frontend)
- Code quality checks pass
- Build succeeds
- Coverage >= 90% (backend)

### 2. Backend Tests Workflow (backend-tests.yml)

**Triggers**: Push/PR affecting `backend/**` or workflow file

**Matrix Testing**:
- Python versions: 3.11, 3.12, 3.13
- OS: Ubuntu Latest

**Test Execution**:
```bash
pytest tests/ \
  --cov=app \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=90 \
  -v
```

**Coverage Requirements**:
- Overall: 90%+
- Current: 99.90%
- Only 3 lines uncovered (uncoverable code)

**Additional Jobs**:
- **lint**: flake8, black, isort checks
- **security**: safety and bandit scans
- **test-summary**: Aggregated results

**Artifacts**:
- Coverage reports (HTML)
- Test results (on failure)
- Security scan reports

### 3. Frontend Tests Workflow (frontend-tests.yml)

**Triggers**: Push/PR affecting `frontend/**` or workflow file

**Matrix Testing**:
- Node versions: 18, 20, 22
- OS: Ubuntu Latest

**Test Execution**:
```bash
npm run test:run -- --coverage
```

**Test Coverage**:
- Total tests: 934
- Pass rate: 100%
- Components: Fully tested
- Integration: Complete

**Additional Jobs**:
- **lint**: TypeScript type checking, ESLint
- **build**: Production build verification

**Artifacts**:
- Coverage reports
- Build artifacts
- Test results (on failure)

### 4. Build & Release Workflow (build-release.yml)

**Triggers**:
- Tags matching `v*.*.*` (e.g., v1.0.0)
- Manual dispatch

**Multi-Platform Builds**:
- **Linux**: AppImage, .deb
- **Windows**: .exe installer
- **macOS**: .dmg, .zip

**Build Process**:
1. Setup Node.js 20 and Python 3.11
2. Install dependencies
3. Build frontend (React + Vite)
4. Build backend (PyInstaller)
5. Download binaries:
   - FFmpeg (video/audio processing)
   - Pandoc (document conversion)
6. Build Electron app with electron-builder
7. Upload platform-specific artifacts

**Release Creation**:
- Automatic GitHub release
- Includes all platform builds
- Auto-generated release notes
- Not marked as draft or prerelease

**Build Artifacts**:
- `linux-release/`: AppImage, .deb packages
- `windows-release/`: .exe installer
- `macos-release/`: .dmg and .zip files

### 5. Dependabot Configuration

**Update Schedule**: Weekly (Mondays)

**Monitored Ecosystems**:
1. **Python (pip)**: Backend dependencies
2. **npm**: Frontend dependencies
3. **GitHub Actions**: Workflow dependencies

**Configuration**:
- Max 5 PRs for pip/npm
- Max 3 PRs for GitHub Actions
- Auto-assigns to repository maintainers
- Labels: `dependencies`, `backend`, `frontend`, `ci/cd`

**Ignored Updates**:
- FastAPI, Uvicorn: Major version updates blocked
- React, React-DOM: Major version updates blocked

## 🚀 Running CI Locally

### Backend Tests
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
pip install pytest-cov

# Run tests like CI
python -m pytest tests/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-fail-under=90 \
  -v

# Run linting
flake8 app/ --count --select=E9,F63,F7,F82
black --check app/ tests/
isort --check-only app/ tests/

# Run security checks
safety check
bandit -r app/
```

### Frontend Tests
```bash
cd frontend

# Install dependencies
npm ci

# Run tests like CI
npm run test:run -- --coverage

# Run type checking
npx tsc --noEmit

# Run build
npm run build
```

## 📊 Coverage Reports

### Backend Coverage
- **Location**: `backend/htmlcov/index.html`
- **Codecov**: https://codecov.io/gh/jj-repository/FileConverter
- **Threshold**: 90% minimum
- **Current**: 99.90%

### Frontend Coverage
- **Location**: `frontend/coverage/index.html`
- **Codecov**: https://codecov.io/gh/jj-repository/FileConverter
- **Current**: High coverage on all components

## 🔐 Required Secrets

### GitHub Secrets
Configure these in repository settings:

1. **CODECOV_TOKEN** (optional but recommended)
   - Get from: https://codecov.io
   - Used for: Coverage uploads
   - Scope: Public repositories don't require this

2. **GITHUB_TOKEN** (automatic)
   - Provided by: GitHub Actions
   - Used for: Release creation, artifact uploads
   - No configuration needed

## 🎯 Status Badges

Add to README.md:
```markdown
[![CI](https://github.com/jj-repository/FileConverter/actions/workflows/ci.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/ci.yml)
[![Backend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/backend-tests.yml)
[![Frontend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml)
[![codecov](https://codecov.io/gh/jj-repository/FileConverter/branch/main/graph/badge.svg)](https://codecov.io/gh/jj-repository/FileConverter)
```

## 🐛 Troubleshooting

### Tests Failing in CI but Pass Locally

**Common Causes**:
1. **Missing system dependencies**: Check workflow installs FFmpeg, Pandoc, etc.
2. **Environment differences**: CI uses fresh Ubuntu, different Python/Node versions
3. **Timing issues**: Tests may be timing-sensitive

**Solutions**:
```bash
# Test with specific Python version
python3.13 -m pytest tests/

# Test with specific Node version
nvm use 22 && npm test

# Run in Docker (similar to CI)
docker run -it ubuntu:latest
```

### Coverage Below Threshold

**Check**:
```bash
# Generate detailed coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Fix**:
1. Identify uncovered lines in report
2. Add tests for uncovered code
3. Verify tests run: `pytest tests/path/to/test.py -v`

### Build Failures

**Backend Build**:
```bash
# Test PyInstaller build locally
cd backend
pip install pyinstaller
pyinstaller backend-server.spec --clean
```

**Frontend Build**:
```bash
# Test production build locally
cd frontend
npm run build

# Check build output
ls -lh dist/
```

### Security Scan Failures

**Safety Issues**:
```bash
# Check for vulnerable dependencies
safety check --json

# Update vulnerable packages
pip install --upgrade package-name
```

**Bandit Issues**:
```bash
# Run bandit locally
bandit -r app/ -f screen

# Fix security issues in flagged files
```

## 📝 Best Practices

### Pull Requests
1. ✅ Ensure all CI checks pass before merging
2. ✅ Review coverage reports for new code
3. ✅ Address linting issues
4. ✅ Fix security warnings

### Releases
1. ✅ Use semantic versioning (v1.0.0)
2. ✅ Test builds on all platforms
3. ✅ Update CHANGELOG.md
4. ✅ Create release notes

### Maintenance
1. ✅ Review Dependabot PRs weekly
2. ✅ Keep GitHub Actions updated
3. ✅ Monitor CI performance
4. ✅ Update documentation

## 🔗 Useful Links

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com)
- [pytest Documentation](https://docs.pytest.org)
- [Vitest Documentation](https://vitest.dev)
- [electron-builder](https://www.electron.build)

## 📈 CI/CD Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Backend Test Coverage | 90%+ | 99.90% |
| Frontend Test Pass Rate | 100% | 100% |
| CI Pipeline Duration | <15 min | ~12 min |
| Build Success Rate | 95%+ | ~98% |
| Security Issues | 0 | 0 |

## 🎉 Success Criteria

### For Merging PRs
- ✅ All CI jobs pass
- ✅ Code coverage maintained/improved
- ✅ No new security vulnerabilities
- ✅ Linting passes
- ✅ Build succeeds

### For Releases
- ✅ All tests pass
- ✅ Builds succeed on all platforms
- ✅ Security scans clean
- ✅ Version tags follow semver
- ✅ Release notes complete
