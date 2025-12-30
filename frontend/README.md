# FileConverter Frontend

[![Frontend Tests](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/jj-repository/FileConverter/actions/workflows/frontend-tests.yml)
[![codecov](https://codecov.io/gh/jj-repository/FileConverter/branch/main/graph/badge.svg?flag=frontend)](https://codecov.io/gh/jj-repository/FileConverter)

Modern React frontend for the FileConverter application, built with TypeScript, Vite, and TailwindCSS.

## 🛠️ Tech Stack

- **Framework**: React 18.3
- **Build Tool**: Vite 6.0
- **Language**: TypeScript 5.7
- **Styling**: TailwindCSS 3.4
- **Internationalization**: i18next 25.7, react-i18next 16.5
- **HTTP Client**: Axios 1.7
- **File Upload**: react-dropzone 14.3
- **Desktop**: Electron 39.2

## 🧪 Testing

### Test Stack

- **Framework**: Vitest 4.0
- **Testing Library**: React Testing Library 16.3
- **Test Environment**: jsdom 27.4
- **User Interactions**: @testing-library/user-event 14.6
- **Assertions**: @testing-library/jest-dom 6.9

### Test Coverage

**52 tests total** - 100% passing

- ✅ **Error Messages** (21 tests) - Error message mapping for all error types
- ✅ **useConverter Hook** (12 tests) - File conversion hook lifecycle
- ✅ **ImageConverter Component** (19 tests) - Image converter UI and interactions

### Running Tests

```bash
# Run tests in watch mode
npm test

# Run tests once
npm run test:run

# Run tests with coverage
npm run test:coverage

# Open Vitest UI
npm run test:ui
```

### Coverage Reports

Coverage reports are generated in `coverage/` directory:

- **HTML Report**: `coverage/index.html` - Interactive coverage browser
- **LCOV**: `coverage/lcov.info` - For CI/CD integration
- **JSON**: `coverage/coverage-final.json` - Machine-readable format

### Test Structure

```
src/
├── __tests__/
│   ├── components/          # Component tests
│   │   └── ImageConverter.test.tsx
│   ├── hooks/               # Custom hooks tests
│   │   └── useConverter.test.ts
│   └── utils/               # Utility function tests
│       └── errorMessages.test.ts
└── test/
    └── setup.ts             # Test environment setup
```

### Mock Infrastructure

All browser APIs are mocked in `src/test/setup.ts`:

- **localStorage** - getItem, setItem, removeItem, clear
- **window.matchMedia** - Responsive design queries
- **ResizeObserver** - Layout change detection
- **IntersectionObserver** - Visibility tracking
- **window.electron** - Electron IPC renderer
- **FileReader** - File operations

## 🚀 Development

### Prerequisites

- Node.js 18+ (recommended: 20 or 22)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs at http://localhost:5173
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview

# Build for Electron
npm run electron:build
```

### Type Checking

```bash
# Run TypeScript compiler without emitting files
npx tsc --noEmit
```

## 📁 Project Structure

```
frontend/
├── electron/              # Electron main process
├── public/                # Static assets
├── src/
│   ├── __tests__/         # Test files
│   ├── components/        # React components
│   │   ├── Converter/     # Converter components (Image, Video, etc.)
│   │   ├── Layout/        # Layout components
│   │   └── UI/            # Reusable UI components
│   ├── hooks/             # Custom React hooks
│   ├── i18n/              # Internationalization
│   ├── services/          # API services
│   ├── test/              # Test setup
│   ├── types/             # TypeScript types
│   ├── utils/             # Utility functions
│   ├── App.tsx            # Root component
│   └── main.tsx           # Entry point
├── vitest.config.ts       # Vitest configuration
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── tailwind.config.js     # TailwindCSS configuration
```

## 🌍 Internationalization

Supports multiple languages using i18next:

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Japanese (ja)
- Chinese (zh)

Translation files are in `src/i18n/locales/`.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Vite Configuration

Build and development settings in `vite.config.ts`:

- Path aliases (@/ → src/)
- React plugin with Fast Refresh
- Build optimization settings

## 🎨 Styling

- **TailwindCSS**: Utility-first CSS framework
- **Custom Theme**: Defined in `tailwind.config.js`
- **Responsive Design**: Mobile-first approach
- **Dark Mode**: Ready (toggle implementation pending)

## 📦 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm test` | Run tests in watch mode |
| `npm run test:run` | Run tests once |
| `npm run test:ui` | Open Vitest UI |
| `npm run test:coverage` | Generate coverage report |
| `npm run electron:dev` | Start Electron in development |
| `npm run electron:build` | Build Electron app |

## 🤝 Contributing

1. Write tests for new features
2. Ensure all tests pass (`npm test`)
3. Check TypeScript types (`npx tsc --noEmit`)
4. Follow existing code style
5. Update tests for bug fixes

## 📝 License

MIT License - see [LICENSE](../LICENSE) file for details
