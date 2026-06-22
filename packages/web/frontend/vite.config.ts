import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  build: {
    outDir: "../ai_mini_box_web/static",
    emptyOutDir: true,
  },
});
