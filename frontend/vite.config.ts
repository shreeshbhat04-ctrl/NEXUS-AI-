import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const backend = env.VITE_API_BASE_URL ?? 'https://cure-quest-api-315569715049.us-central1.run.app';

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
      proxy: {
        '/health': backend,
        '/demo': backend,
        '/patient': backend,
        '/calendar': backend,
        '/drug': backend,
        '/orchestration': backend,
        '/medical-memory': backend,
        '/medical-models': backend,
        '/api/finance': backend,
      },
    },
  };
});
