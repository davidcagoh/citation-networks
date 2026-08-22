import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: "./test-results",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3100",
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: [
    {
      command:
        "UV_CACHE_DIR=/private/tmp/literature-workbench-uv-cache WORKBENCH_DATABASE_URL=sqlite:////private/tmp/literature-workbench-e2e.db WORKBENCH_ALLOWED_ORIGINS=http://127.0.0.1:3100 uv run --extra dev uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8100",
      cwd: "../backend",
      url: "http://127.0.0.1:8100/health",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command:
        "NEXT_PUBLIC_API_URL=http://127.0.0.1:8100 npm run dev -- --hostname 127.0.0.1 --port 3100",
      cwd: ".",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
