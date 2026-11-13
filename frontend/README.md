# GembaONE Platform Frontend

React + TypeScript + Vite frontend for the Ericsson GembaONE Platform.

## Prerequisites

- Node.js 20.19+ or 22.12+
- npm

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will start on port 5173 (or the next available port) and proxy `/api` requests to the backend on port 9000.

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Testing

Run unit tests:
```bash
npm test
```

Run E2E tests:
```bash
npx playwright test
```

## Linting and Type Checking

```bash
npm run lint
npm run type-check
```

## Project Structure

- `src/lib/` - Core utilities (API client, auth context)
- `src/components/` - Reusable components
  - `auth/` - Authentication components
  - `layout/` - Layout components (Header, Sidebar, Layout)
- `src/pages/` - Page components (one per route)
- `src/types/` - TypeScript type definitions
- `e2e/` - End-to-end tests

## Environment Variables

- `VITE_API_URL` - API base URL (default: `/api` for same-origin)
- `BACKEND_PORT` - Backend port for Vite proxy (default: 9000)

## Design System

This project uses the IBM Carbon Design System:
- Components from `@carbon/react`
- Icons from `@carbon/icons-react`
- Styles from `@carbon/styles`

## Routes

All routes are declared in `src/App.tsx`:
- `/` - Home page (protected)
- `/login` - Login page (public)
- `/templates` - Checklist templates list (protected)
- `/templates/:id` - Template builder (protected)
- `/checklists` - Checklists list (protected)
- `/checklists/:id` - Checklist execution/review (protected)
- `/ingestions` - Ingestions list (protected)
- `/ingestions/upload` - Upload page (protected)
- `/ingestions/:id` - Ingestion results (protected)
- `/mappings` - Mappings list (protected)
- `/mappings/:id` - Mapping editor (protected)

## Seed Credentials

Demo users for local development:
- Admin: `admin@example.com` / `admin123`
- Engineer: `engineer@example.com` / `engineer123`
- Reviewer: `reviewer@example.com` / `reviewer123`
- ASP User: `asp@example.com` / `asp123`
