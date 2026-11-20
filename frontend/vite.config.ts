import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api хүсэлтийг backend рүү дамжуулна (docker-д BACKEND_URL=http://backend:8000)
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { "/api": process.env.BACKEND_URL ?? "http://localhost:8000" },
  },
});
