import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: {
    timeout: 20_000
  },
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4175",
    colorScheme: "dark",
    reducedMotion: "reduce",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    launchOptions: {
      // Exercise the same hardware path used by the in-app browser on Apple
      // Silicon. Non-macOS CI retains deterministic software WebGL fallback;
      // the assertions are statistical, never exact cross-GPU pixels.
      args: [
        process.platform === "darwin"
          ? "--use-angle=metal"
          : "--use-angle=swiftshader"
      ]
    }
  },
  webServer: {
    command: "npm run dev -- --port 4175 --strictPort",
    url: "http://127.0.0.1:4175",
    reuseExistingServer: false,
    timeout: 120_000
  }
});
