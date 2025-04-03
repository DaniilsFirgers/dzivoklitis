import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 81,
    hmr: {
      port: 81,
      host: "0.0.0.0",
      path: "/__vite_hmr",
    },
  },
});
