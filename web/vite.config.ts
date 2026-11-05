import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Build for static hosting (GitHub Pages), while keeping local API proxy behavior.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:7071",
    },
  },
});
