import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    proxy: {
      "/scan": { target: "http://localhost:8000", changeOrigin: true },
      "/fix": { target: "http://localhost:8000", changeOrigin: true },
      "/export": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  preview: { port: 5173 },
});
