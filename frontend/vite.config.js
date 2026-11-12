import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development (`npm run dev`) the React app runs on http://localhost:5173
// and every request starting with /api is forwarded to the Flask backend.
// Keep the port below in sync with PORT in backend/config.py.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5050",
    },
  },
  // `npm run build` writes the production files to frontend/dist,
  // which Flask serves at http://127.0.0.1:5050
  build: {
    outDir: "dist",
  },
});
