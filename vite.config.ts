import { defineConfig } from "vitest/config";

export default defineConfig(({ command }) => ({
  base: command === "build" ? "./" : "/",
  server: {
    host: "127.0.0.1",
    port: 5173
  },
  build: {
    manifest: true,
    chunkSizeWarningLimit: 550,
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "three-core",
              test: /node_modules[\\/]three[\\/]build[\\/]three/,
              priority: 10
            }
          ]
        }
      }
    }
  },
  test: {
    // Physics-heavy suites contend badly when Vitest runs files in parallel on M1.
    fileParallelism: false
  }
}));
