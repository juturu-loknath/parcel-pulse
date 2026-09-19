import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.DEV_API_PROXY_TARGET;
  return {
    plugins: [react()],
    // This only affects `vite dev`; production builds still use VITE_API_BASE_URL.
    server: {
      host: true,
      proxy: target ? { '/api': { target, changeOrigin: true } } : undefined,
    },
  };
});
