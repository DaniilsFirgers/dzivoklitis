import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());

  const isDev = mode === "development";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true,
      port: 81,
      strictPort: true,
      hmr: {
        protocol: "ws",
        clientPort: 8080,
        host: "0.0.0.0",
        path: "/__vite_hmr",
      },
      ...(isDev && {
        allowedHosts: ["localhost", "127.0.0.1", env.VITE_ALLOWED_HOST],
      }),
    },
  };
});
