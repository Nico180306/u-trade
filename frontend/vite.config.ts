import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devApiTarget = env.VITE_DEV_API_TARGET || 'http://localhost:8000'
  const internalProxySecret = env.INTERNAL_PROXY_SECRET || 'dev-local-proxy-secret'

  return {
    plugins: [
      react(),
      tailwindcss(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg'],
        workbox: {
          navigateFallbackDenylist: [/^\/api\//, /^\/admin\//],
          runtimeCaching: [
            {
              urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
              handler: 'NetworkOnly',
            },
          ],
        },
        manifest: {
          name: 'U-Trade',
          short_name: 'U-Trade',
          description: 'Reservas y ventas estudiantiles en campus con entrega presencial via QR.',
          theme_color: '#0f172a',
          background_color: '#ffffff',
          display: 'standalone',
          start_url: '/',
          icons: [
            {
              src: 'favicon.svg',
              sizes: 'any',
              type: 'image/svg+xml',
              purpose: 'any maskable',
            },
          ],
        },
      }),
    ],
    server: {
      proxy: {
        '/api': {
          target: devApiTarget,
          changeOrigin: true,
          headers: {
            'X-Internal-Proxy-Secret': internalProxySecret,
            'X-Client-IP': '127.0.0.1',
          },
        },
      },
    },
  }
})
