import { defineConfig } from "vitest/config";

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 5173
  },
  test: {
    // Physics-heavy suites contend badly when Vitest runs files in parallel on M1.
    fileParallelism: false
  }
});
