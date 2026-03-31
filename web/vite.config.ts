import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: {
      '/graph': 'http://localhost:8000',
      '/plan': 'http://localhost:8000'
    }
  }
});
