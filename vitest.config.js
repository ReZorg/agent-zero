import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "happy-dom",
    include: ["webui/js/__tests__/**/*.test.js"],
    coverage: {
      provider: "v8",
      include: ["webui/js/**/*.js"],
      exclude: [
        "webui/js/__tests__/**",
        "webui/js/transformers@*.js",
        "webui/js/sw.js",
      ],
      reporter: ["text", "lcov"],
    },
  },
});
