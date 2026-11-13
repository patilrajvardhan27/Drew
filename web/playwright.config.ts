import { defineConfig, devices } from "@playwright/test";

const port = Number(process.env.E2E_PORT ?? 8765);
const python = process.env.PYTHON ?? "python";

export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: "off",
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
  // The API serves the built web app and replays the recorded Extract fixture, so no Adobe key is needed.
  webServer: {
    command: `${python} -m uvicorn api.main:app --port ${port}`,
    cwd: "..",
    url: `http://127.0.0.1:${port}/api/health`,
    reuseExistingServer: !process.env.CI,
    env: {
      REDRAFT_ADOBE_MODE: "fixture",
      REDRAFT_DATABASE_URL: "sqlite:///./data/e2e.db",
      REDRAFT_STORAGE_DIR: "./data/e2e-files",
      REDRAFT_MAIL_BACKEND: "file",
    },
  },
});
