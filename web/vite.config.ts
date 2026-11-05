import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development, /api is proxied to the local Azure Functions host (func start).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:7071",
    },
  },
});
