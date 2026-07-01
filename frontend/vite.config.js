import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    // Vite usa src/ como raiz — os HTMLs legados em frontend/ permanecem intactos
    root: 'src',
    plugins: [
        vue(),
        tailwindcss(),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    server: {
        port: 5173,
        proxy: {
            // Durante dev, /api/* → FastAPI local
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        // Output relativo ao root (src/), então sobe um nível para frontend/dist/
        outDir: '../dist',
        emptyOutDir: true,
    },
})
