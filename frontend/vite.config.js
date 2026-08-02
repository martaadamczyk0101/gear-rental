import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  preview: {
    // Vite's preview server otherwise rejects requests whose Host header
    // doesn't match a known allowlist - needed since Railway proxies
    // requests through its own *.up.railway.app / custom domain.
    allowedHosts: true,
  },
})
