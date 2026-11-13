import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),
  retries: 0,
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
  },
  webServer: [
    {
      command: `.venv/bin/python -m alembic upgrade head && .venv/bin/python -m app.seed && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port ${process.env.E2E_BACKEND_PORT ?? '9000'}`,
      cwd: '../backend',
      url: `http://127.0.0.1:${process.env.E2E_BACKEND_PORT ?? '9000'}/health`,
      reuseExistingServer: true,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        DATABASE_URL: process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db',
        RATE_LIMIT_ENABLED: 'false',
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${process.env.E2E_FRONTEND_PORT ?? '5173'} --strictPort`,
      url: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
      reuseExistingServer: true,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: process.env.E2E_BACKEND_PORT ?? '9000',
      },
    },
  ],
})
